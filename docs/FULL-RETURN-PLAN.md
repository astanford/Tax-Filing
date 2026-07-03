# Suitability Assessment & Plan: Accountant-Ready Finalized Returns

*Date: 2026-07-03*
*Status: Proposal — awaiting owner review*

## Goal

Beyond the assistance goals in CLAUDE.md, the repo should produce a **finalized
tax return** — federal Form 1040 with all required schedules plus Georgia Form
500 — asking the user whatever questions are needed along the way, packaged so
an accountant can review (and file) it.

## Suitability Verdict: Not Yet

The repo is a strong **assistant** (extraction, cheatsheets, verification of
human-entered values, planning) but it is not a **return generator**. Today no
component computes an assembled 1040 or GA 500, and nothing emits a filled
form. Concretely:

| Gap | Detail |
|---|---|
| No return assembly | `/tax-audit` verifies *human-entered* 1040/500 line values; nothing computes them. The closest engine, `what_if.py`, computes planning deltas, not a filing. |
| No form output | No skill or script fills a PDF or writes anything to `output/`. The "forms saved to output/ leave SSN blank" rule is aspirational — no code path exists. |
| Missing computations | Schedule D / Form 8949 / Qualified Dividends & Cap Gain worksheet (preferential rates computed nowhere), Schedule B (detection only), Form 8960 NIIT (flag only), Form 8959 (planning engine only), Form 8995 QBI limits (flat 20% only, no income-limit/SSTB handling), full Form 8582 (simplified only), Form 4562 beyond building straight-line, Form 2210 / safe harbor, AMT check, GA 500 assembly (planning engine only). |
| Filing-status coverage | `cross_check.py` bracket verification is MFJ-only; other statuses get a warning, not a check. |
| No interview mechanism | "Asking any questions needed" has no systematic support — gaps surface ad hoc during cheatsheet sessions. |
| K-1 / Sch E Part II | Explicitly unsupported (see `docs/STATUS-AND-ROADMAP.md`); a follow-on design is planned but not started. |
| Engineering debt | 2025 constants duplicated across `cross_check.py`, `standard_vs_itemized.py`, `salt_cap_calculator.py`, and `what_if.py` (MFJ table in cross_check already diverges in coverage from what_if); zero tests on the calculators (the new `tests/` covers only the prior-year validator); `what_if.py` docstring still says Maryland; CLAUDE.md's "no separate unit-test suite" note is now stale. |

None of this is a criticism of the architecture — extraction → curated rules →
Python math → audit is exactly the right spine. The pieces missing are the
**engine** (compute every line), the **interview** (collect every missing
input), and the **emitter** (fill the official forms + accountant package).

## CLAUDE.md Assumptions Review

**Rule 3 (all math via Python, no LLM arithmetic) — keep; do not switch to a
calculator plugin.** A calculator plugin/MCP is objectively *worse* here: it
performs one arithmetic operation per call with no memory, no versioning, and
no testability. Tax computation is multi-step conditional logic (worksheets,
phase-outs, orderings) that must be reproducible, diffable, unit-testable, and
auditable months later — which is precisely what committed Python scripts give
and a plugin cannot. The real improvements to Rule 3's implementation are:
1. **Centralize constants** — one `engine/constants_2025.py`, every constant
   annotated with its `reference/curated/` citation; all scripts import it.
2. **Use `Decimal` everywhere** (the prior-year validator already does; the
   calculators mix floats).
3. **Test the calculators** against worked examples from the IRS instructions.

**Rule 1 (cite curated references) — keep.** For the engine, strengthen it:
every computed line in the return manifest carries its citation, making the
accountant package self-documenting.

**Rule 2 (unverifiable → say so) — keep, and make it structural**: the engine
never guesses; a line it cannot compute with a citation becomes a `BLOCKED`
item routed to the interview or flagged for the accountant.

**Rule 4 (no PII in skill files) / Rule 5 (SSN/bank/signature blank) — keep.**
Rule 5 is actually convenient for the accountant-review goal: the accountant
adds identity fields at filing. An optional *local-only* identity overlay
(never staged, never committed) could be added later if hand-writing SSNs
becomes annoying — decision deferred.

**Stale items to fix:** CLAUDE.md "this repo has no separate unit-test suite"
(a `tests/` pytest harness now exists); `what_if.py` docstring references
Maryland.

## The Plan

Phases are sequential gates in the repo's established style (design → plan →
implement → review). Phases 1–4 produce the accountant-ready return; 5–6
harden and extend.

### Phase 1 — Foundations (prerequisite hardening)

- `engine/constants_2025.py`: single source for brackets (all four statuses),
  standard deductions, SALT cap, SE/Medicare/NIIT thresholds, GA numbers,
  MACRS tables — each with a curated citation comment. Refactor the four
  existing scripts to import it.
- Pytest coverage for `schedule_c_calculator.py`, `schedule_e_calculator.py`,
  `standard_vs_itemized.py`, `salt_cap_calculator.py`, `cross_check.py`,
  `what_if.py`, using fabricated fixtures and worked examples from
  `reference/Raw/` instructions (e.g. Pub 946 tables, i8582 examples).
- GitHub Actions CI running the full pytest suite on PRs.
- Extend `cross_check.py` brackets to Single/HoH/MFS via the shared constants.
- Fix the stale docstring and CLAUDE.md test note.

*Gate: all calculators tested and passing CI; constants live in one place.*

### Phase 2 — Return computation engine (`engine/`)

A deterministic Python package (sibling of the planned `ingest/`, same
quarantine pattern) that consumes `analysis/tax-doc-summary.csv` +
`analysis/prior-year-carryovers-*.json` + `analysis/interview-answers.json`
and produces a **return manifest**: one JSON with every form, every line,
every value, plus per-line `source` (which document/box or which computation)
and `citation` (which curated ref). Computation order:

1. Income schedules: B, C (existing calc), D/8949 + QDCG worksheet (new),
   E Part I (existing calc), Schedule 1.
2. Adjustments and SE: Schedule SE (new — currently only inside what_if),
   IRA/HSA/student-loan (curated refs exist).
3. Deduction: Schedule A vs standard (existing calc), SALT (existing calc).
4. QBI: Form 8995 with the taxable-income threshold test; **above the 8995
   threshold, emit BLOCKED → accountant** rather than attempt 8995-A.
5. Loss limits: full Form 8582 (upgrade from simplified), Form 4562 for new
   assets (building SL exists; add §179/other-life handling or BLOCK).
6. Other taxes: Form 8959, Form 8960 (new), AMT *screen* (compute the 6251
   trigger test; if triggered, BLOCK → accountant rather than model AMT).
7. Assemble Form 1040 + Schedules 1/2/3, then GA Form 500 (reuse the GA flow
   from `what_if.py`, extracted into the engine).
8. Payments/penalty: withholding roll-up, estimated payments, 2210 safe-harbor
   check (needs a new curated ref — currently "verify on IRS.gov").

Design rule: **compute with citation, or BLOCK — never estimate.** BLOCKED
items become interview questions (missing input) or accountant flags (beyond
scope, e.g. 8995-A, AMT, K-1 until Phase 6).

*Gate: engine reproduces the prior-year return's key lines from prior-year
inputs within rounding (regression test), and computes a full fabricated-
fixture return end-to-end.*

### Phase 3 — Interview skill (`/tax-interview`)

- Engine emits `analysis/missing-inputs.json` (each item: form/line, why
  needed, citation).
- New skill walks the user through the questions in batches, writes validated
  answers to `analysis/interview-answers.json` (PII-scanned by the same
  firewall pattern as the prior-year validator), reruns the engine, repeats
  until no missing inputs remain.
- Also absorbs the existing per-property Schedule E checklist
  (`docs/SCHEDULE-E-PLAN.md` §5) as structured questions.

*Gate: a fabricated scenario with deliberately missing data converges to a
complete manifest purely through the interview loop.*

### Phase 4 — Form output + accountant package (`/tax-return`)

- **PDF filling**: map manifest lines to AcroForm field names of the official
  IRS PDFs (f1040, schedules) and GA 500 using `pypdf` (deps quarantined in
  `engine/requirements.txt`). Output to gitignored `output/`. SSN, bank, and
  signature fields stay blank (Rule 5). First task is a field-map audit:
  confirm each target PDF actually has fillable AcroForm fields; any flat
  (non-fillable) form falls back to a line/value overlay sheet the accountant
  transcribes.
- **Read-back verification**: script re-reads each filled PDF and diffs
  against the manifest — no silent field-mapping errors.
- **Accountant review package** (markdown + the PDFs): cover memo listing
  positions taken, simplifications (e.g. simplified 8582 assumptions if any
  remain), all BLOCKED/accountant-flag items, open questions; source-document
  index; prior-year reconciliation (YoY line deltas); citation appendix.

*Gate: `/tax-audit` (upgraded, Phase 5 overlap) passes on the emitted return;
read-back diff is empty; package reviewed by owner.*

### Phase 5 — Audit upgrade

- `/tax-audit` gains a third input: the engine manifest. It becomes a
  three-way check (source CSV ↔ manifest ↔ filled PDFs) instead of verifying
  hand-entered values.
- Curate the estimated-tax safe-harbor reference; add the 2210 check.

### Phase 6 — K-1 / Schedule E Part II (conditional)

The already-designed follow-on (see `docs/superpowers/specs/`): validate the
existing Schedule E Part I work, then add Part II with the §704(d) → §465 →
§469 ordering, consuming the passthrough-aware carryover schema from Phase 0.
**Only needed if the 2025 documents actually include K-1s** — an open
question below. The in-flight `ingest/` Phase 1 (Hermes automation) proceeds
independently and feeds Phases 2–3 with prior-year data.

## Tooling: Plugins, MCPs, Skills

**Adopt**
- `pypdf` (Python lib, not a plugin) for AcroForm filling — consistent with
  Rule 3, testable, offline.
- **GitHub Actions** CI for the pytest suite (roadmap already wants this).
- **QuickBooks MCP** (already connected in this environment): pull P&L /
  transaction detail per rental property or business directly into the
  Schedule E/C expense workflow instead of manual statement transcription —
  worth wiring into `/tax-prep` if the books live in QBO.
- **Google Drive MCP** (already connected): fetch tax documents into
  `my-tax-docs/` intake if they're stored in Drive (download only; PII rules
  unchanged — files land in the gitignored folder).
- **deep-research skill** during reference curation: multi-source verification
  of IRS/GA rules *feeding* `HOW-TO-CURATE.md` → `reference/curated/` — never
  a runtime substitute for citations (Rule 1 unchanged).
- **Todoist MCP** (optional, already connected): mirror the filing checklist /
  interview follow-ups as tasks.

**Reject**
- **Calculator plugin/MCP** — strictly worse than tested Python (see
  assumptions review).
- **Third-party tax-calc APIs/services** — sends PII off-machine and breaks
  citation discipline; the curated-reference + local-Python model is the
  feature, not the limitation.
- **New repo / framework rewrite** — the quarantined-subsystem pattern
  (`ingest/`, now `engine/`) already fits.

**New skills this plan adds:** `/tax-interview` (Phase 3), `/tax-return`
(Phase 4). Existing four skills keep their roles; `/tax-cheatsheet` becomes
optional explanation rather than the primary filing path.

## Open Questions (answers change scope, not direction)

1. **Filing status for 2025?** Determines which bracket/status paths get
   first-class regression tests (engine will support all four regardless).
2. **Do the 2025 documents include K-1s or brokerage 1099-Bs?** K-1s → Phase 6
   is required before "finalized"; 1099-B → Schedule D/8949 in Phase 2 is
   load-bearing (it's included regardless, since it's cheap to keep).
3. **Identity overlay:** keep Rule 5 as-is (accountant adds SSN/signature), or
   add a local-only, never-committed overlay step? Default: keep as-is.
4. **E-filing is out of scope** (the accountant reviews and files) — confirm.

## Verification

- Every phase gate above names its acceptance test.
- End-to-end proof for the whole plan: a **demo-mode fabricated taxpayer**
  (fictional W-2 + 1099s + two rentals + prior-year carryovers, all
  `000-00-0000`-style data, committable under `examples/`) that runs
  `/tax-prep` → engine → interview → `/tax-return` → `/tax-audit` and yields a
  complete, internally consistent package. This doubles as the CI regression
  suite and the roadmap's wished-for "demo mode."
