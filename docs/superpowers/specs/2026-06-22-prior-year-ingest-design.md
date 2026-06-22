# Prior-Year Ingestion Subsystem — Design

*Date: 2026-06-22*
*Status: Approved (brainstorming) — pending implementation plan*

## Problem

The 2025 tax-filing repo already ships a prior-year (2023/2024) ingestion
path ("Path B") authored by Claude Fable: a JSON carryover schema, a Hermes
extraction prompt, a PII-firewall validator, and downstream wiring into the
four skills. The owner wants to (a) **review/validate** that work, since it
was never independently verified, and (b) **automate** the extraction with
human checkpoints and verification, plus an optional richer review/planning
layer.

The "Vision LLM" already running locally is the **NousResearch Hermes
Agent** (`~/.hermes/hermes-agent`) — a full agent framework with a CLI
(`run_agent.py`/`cli.py`/`hermes`), an MCP server (`mcp_serve.py`), a batch
runner (`batch_runner.py`), and Ollama-backed local models. "Automate the
orchestration" therefore means driving Hermes through one of those
interfaces, not calling a library.

## Decision: build here, as a quarantined subsystem (not a new repo)

Considered three structures:

- **A — new separate repo.** Rejected. Optimizes runtime cleanliness (the
  one thing that isn't a problem) while forcing duplication of the PII
  firewall + carryover schema across two repos and a cross-repo copy step
  every run. For a solo personal project that is sync overhead and a new
  place for PII rules to drift. The coupling is to data that lives *here*.
- **B — fold into the existing skills.** Rejected. Pulls Hermes/network
  deps into the clean core, and markdown skills are a poor fit for a
  deterministic, checkpoint-driven pipeline.
- **C — quarantined in-repo subsystem (chosen).** A top-level `ingest/`
  module with its own deps, CLI, and README, physically separate from the
  tax-skills core but **reusing** the validated validator + schema (single
  source of truth) and writing output where the skills already read it.

### Guiding principle: validate-then-wrap

Path B is treated as a **credible draft**, not scrapped. We validate each
artifact, fix what's weak, and only then automate on top of the validated
pieces.

## Phases (each independently reviewable; gated)

### Phase 0 — Validate Path B

Audit the existing artifacts, each against an authority already in the repo,
and produce a **standalone `docs/PATH-B-VALIDATION.md`** with a per-artifact
verdict (GO / FIX / NO-GO) and a punch-list of fixes.

| Artifact | Validated against | Key checks |
|---|---|---|
| `prior-year-carryovers-template.json` (schema) | carryover map in `docs/PRIOR-YEAR-DATA.md` + curated refs | every 2025-affecting carryover has a field; field names match the form lines they claim (1040 L11, 8995 L16, GA 500 L15b, etc.); no orphan fields |
| `hermes-extraction-request.md` (extraction prompt) | the schema + GA-500/1040 line refs | field-by-field source map correct; redaction rules complete; output contract matches the validator |
| `validate_prior_year.py` (PII firewall) | `docs/PRIVATE-DATA.md` rules | PII patterns actually catch SSNs / account# / DOB / etc. (adversarial fixtures with **fabricated** data); schema-shape checks correct; no false-accepts |
| Downstream wiring | the four skills + calculators | every carryover the skills *read* exists in the schema with matching keys (e.g. `rentals[].suspended_passive_loss_form_8582` → `schedule_e_calculator.py`); no consumed-but-never-produced fields |
| Round-trip | end-to-end | a fabricated full-fixture return → expected JSON → validator accepts → a skill consumes it correctly |

**Gate:** Phase 1 does not start until the findings are reviewed and any
fixes are made. Rules held inviolate: every line-number claim cites a
curated reference (Rule 1); all PII test fixtures use obviously fabricated
data — e.g. SSN `000-00-0000`, "Jane Testfiler" (Rules 4/5).

**Passthrough/K-1 carryover ingestion (in scope for this spec).** Phase 0
also extends the schema + extraction prompt to capture passthrough
carryovers from prior-year returns, so the schema does not have to be
re-opened when the separate K-1 computation feature lands. New carryover
fields to validate/add:

- Partner/shareholder **basis** carryforward (§704(d) / §1366(d)).
- **At-risk** carryforward (§465).
- Suspended **passive** K-1 losses (Form 8582, the passthrough rows — not
  just the Schedule E Part I rental rows already covered).
- **PTP** (publicly traded partnership) suspended losses, tracked per PTP.
- QBI from passthroughs feeding the existing QBI carryforward field.

These are *extraction/carryover* fields only. Computing the current-year
limitation ordering from them is the follow-on design's job, not this one.

### Phase 1 — `ingest/` subsystem

```
ingest/
  README.md            # what it is, how to run, its deps
  requirements.txt     # Hermes/HTTP/PDF deps — quarantined here, never in the core
  run_ingest.py        # the orchestrator CLI (pipeline + checkpoints)
  hermes_client.py     # thin wrapper over the Hermes interface
  verify.py            # post-extraction verification checks
  # reuses (imports, never copies):
  #   .claude/skills/tax-prep/scripts/validate_prior_year.py   (PII firewall)
  #   .claude/skills/tax-prep/templates/*.json + hermes-extraction-request.md
```

**Pipeline (checkpoints + verification built in):**

1. **Discover** PDFs in `my-tax-docs/prior-years/<year>/`.
2. **Checkpoint 1** — show which files + which tax year; user confirms before
   anything runs.
3. **Extract** — hand Hermes the validated `hermes-extraction-request.md` +
   the PDFs; capture JSON to a **staging** file (not the real output).
4. **PII firewall** — run `validate_prior_year.py` on staging; hard-stop on
   any violation.
5. **Verify** (`verify.py`) — automated sanity checks (amounts parse as
   Decimal, tax_year sane, refund/balance-due signs coherent, ranges sane)
   **and** a human-readable side-by-side of every extracted value for
   eyeballing against the actual PDF.
6. **Checkpoint 2** — user explicitly approves; only then is staging
   **promoted** to `analysis/prior-year-carryovers-<year>.json`.

**Locked decisions:**

- **Hermes interface = one-shot subprocess** (`run_agent.py` / `batch_runner.py`
  style), not the MCP server: a batch "here are the PDFs, return JSON per
  this schema" call is deterministic, scriptable, and needs no long-running
  service. Exact invocation pinned during planning by reading Hermes' own
  `AGENTS.md`/`README`.
- **Checkpoint style = staging-file + explicit approve**, not a live
  interactive prompt: leaves an auditable artifact to diff; nothing reaches
  `analysis/` without a deliberate second step.

### Phase 2 — optional analysis/planning layer

Built only after Phase 1 works; structured so it never blocks the core
pipeline. Reasons over the already-extracted, already-validated carryover
JSONs (2023 + 2024 + eventually prior 2025) — touches no PDFs and no PII.

- **Multi-year comparison (deterministic, Python).** YoY deltas, recurring
  document/income detection, swing flags — all arithmetic in Python (Rule 3).
- **Intake-priming briefing (the new capability).** A "what to expect /
  what to gather / what to plan" markdown that primes the current-year
  `/tax-prep`. Any tax-rule statement cites a curated ref (Rule 1);
  unverifiable items carry the "check IRS.gov" disclaimer (Rule 2).
- **Positioning — extend, don't duplicate.** Complements the existing
  `/tax-advisor` (already uses prior-year totals as a baseline) and
  `/tax-audit` (already flags YoY swings) rather than forking a parallel
  analyzer. Likely a thin skill plus a Python comparison script in `ingest/`.

## Cross-cutting constraints

- **Single source of truth.** The PII validator and carryover schema live
  once (under `.claude/skills/tax-prep/`); `ingest/` imports them. No copies.
- **PII firewall is mandatory.** No PDF-derived data reaches `analysis/`
  without passing `validate_prior_year.py`. Source PDFs stay in gitignored
  `my-tax-docs/`; extracted data stays in gitignored `analysis/`.
- **Repo Rules apply unchanged.** Citation discipline (Rule 1), unverifiable
  disclaimer (Rule 2), Python-only math (Rule 3), no PII in committed files
  (Rule 4), blank SSN/bank/signature fields (Rule 5). See `CLAUDE.md`
  "How Global Rules Map Here."
- **CLAUDE.md note.** Add a short pointer noting `ingest/` is a quarantined
  runnable subsystem with its own deps, distinct from the Claude-driven
  skills core.
- **Reusability.** The subsystem is year-agnostic and intended to be re-run
  for future filings (e.g. 2026), not a one-shot for 2025.

## Out of scope (and the planned follow-on)

**In scope here:** passthrough/K-1 *carryover ingestion* (see Phase 0) — the
prior-year extraction side only.

**Deferred to a separate follow-on design** (its own design → spec → plan):
current-year **K-1 / Schedule E Part II computation**. That follow-on covers
two flowing-together pieces:

1. **K-1 input forms** — partnership/S-corp/trust filings (Forms 1065 /
   1120-S / 1041), needing new curated references for their line meanings.
2. **Schedule E** reporting — where K-1 passthrough income/loss lands
   (Part II), plus the basis → at-risk → passive limitation ordering
   (§704(d) → §465 → §469) and QBI from passthroughs.

This ingestion subsystem is built to *feed* that follow-on: the carryover
schema is made passthrough-aware now so the follow-on consumes it without a
schema re-open.

**Still fully out of scope:** foreign income, Schedule F, and complex
credits — unchanged by this design.

## Open items for the implementation plan

- Exact Hermes invocation + output-capture contract (read Hermes
  `AGENTS.md`/`README`; confirm Ollama vision model handles the PDF/image
  input format).
- Whether `verify.py`'s side-by-side renders from the staging JSON alone or
  also re-displays source page images for comparison.
- Phase 2 briefing format and which curated refs it draws on.
