# Status and Roadmap

*Last updated: June 22, 2026*

## What's Been Done

This fork (from the original Maryland-based project) has been adapted for a
Georgia filer with rental properties. All changes merged via PR #2 after
subagent review.

1. **Georgia conversion (tax year 2025)** — `reference/curated/georgia-500-guide.md`
   built from the official 2025 IT-511 booklet (committed at `reference/Raw/`):
   flat 5.19% rate, $24K/$12K standard deduction with the federal lock-in rule,
   $4,000/dependent exemption, $300 Eligible Itemizer Credit. All scripts,
   skills, docs, and examples converted from Maryland. No local income tax in
   Georgia.

2. **Schedule E rental support** — three curated references from 2025 IRS
   sources (`schedule-e-guide.md`, `rental-depreciation.md`,
   `passive-activity-losses.md`) and a new `schedule_e_calculator.py`:
   per-property P&L, 27.5/39-year MACRS depreciation, §469 classification for
   long/mid/short-term rentals, simplified Form 8582 ($25K allowance + MAGI
   phase-out), and the Georgia bonus-depreciation addback. **Single-member LLCs
   are disregarded entities — their rentals report on the owner's Schedule E.**

3. **Prior-year return ingestion (2023/2024)** — `docs/PRIOR-YEAR-DATA.md`:
   full returns stay in gitignored `my-tax-docs/prior-years/`; extracted
   carryovers become amounts-only JSON in gitignored `analysis/`, gate-checked
   by `validate_prior_year.py` (PII scanner). Three paths: Claude extracts,
   the local Hermes Agent extracts (template:
   `.claude/skills/tax-prep/templates/hermes-extraction-request.md`), or
   manual entry.

4. **Prior-year ingestion — Phase 0 (validate Path B)** — merged via PR #4.
   Added a `tests/` pytest harness (26 tests) validating the PII firewall and
   carryover schema; audited the extraction prompt + downstream wiring; made
   the carryover schema/validator **passthrough/K-1 aware** (basis §704(d)/
   §1366(d), at-risk §465, suspended passive, PTP flag, passthrough QBI); and
   hardened the PII firewall to also block name/taxpayer/spouse/dependent key
   fragments. Gate = PROCEED. Design + plan + findings:
   `docs/superpowers/specs/2026-06-22-prior-year-ingest-design.md`,
   `docs/superpowers/plans/2026-06-22-prior-year-ingest-phase0.md`,
   `docs/PATH-B-VALIDATION.md`.

5. **Phase 1 foundations + Phase 2 opening (July 2026)** — per
   `docs/FULL-RETURN-PLAN.md`: shared cited constants module
   (`engine/constants_2025.py`, all-status brackets verified against
   Rev. Proc. 2024-40 — fixing a wrong MFJ top-bracket base tax), pytest
   suite (130+ tests) with CI, and the **Schedule E Part I validation gate:
   PROCEED** (`docs/SCHEDULE-E-PART1-VALIDATION.md`). The validation fixed
   two real calculator bugs: MACRS partial final-year depreciation
   (now full printed Pub 946 tables in `engine/macrs_tables.py`) and a
   Form 8582 allowance-base netting error.

6. **Phases 3–6: return engine, interview, form output, audit upgrade
   (July 2026)** — per `docs/FULL-RETURN-PLAN.md`:
   - **Engine (`engine/return_engine.py`)**: full federal + GA computation
     into a cited *return manifest* — Schedule B, Schedule D/8949 with the
     QDCG worksheet (new curated `schedule-d-8949-guide.md`), Schedule SE,
     Forms 8959/8960/8995, 1040 assembly, GA 500, and the estimated-tax
     safe harbor (new curated `estimated-tax-safe-harbor.md` — closes the
     old "verify on IRS.gov" gap). Compute-with-citation-or-BLOCK design:
     8995-A, AMT (screened), Schedule D Tax Worksheet cases, and penalty
     amounts route to the accountant.
   - **`/tax-interview`**: builds `analysis/return-inputs.json` from the CSV
     + carryovers (`engine/inputs_from_csv.py`), loops on the engine's
     missing-inputs until the return converges.
   - **`/tax-return`**: fills official PDFs via pypdf (quarantined in
     `.venv`, `engine/requirements.txt`) using visually-verified field maps
     (`engine/field_maps/`, f1040 done; `engine/dump_fields.py` sentinel
     method for the rest), read-back diff, Rule 5 hard guard, and
     `engine/accountant_package.py` (memo + blocked items + citations).
   - **`/tax-audit`**: three-way check (CSV ↔ manifest ↔ filled PDFs) +
     safe-harbor exposure flag.

7. **ACA Premium Tax Credit + exact Tax Table (July 2026)** — new curated
   `aca-premium-tax-credit.md` (2025 keeps the ARPA/IRA enhanced structure;
   FPL, applicable-figure bands, repayment caps all extracted and verified)
   and `engine/aca.py` (Form 8962 annual method: net PTC → Schedule 3
   line 9; excess APTC → Schedule 2 line 1a with Table 5 caps; BLOCKs for
   MFS/shared-policy/year-of-marriage/below-100%-FPL/monthly-method/SE
   circularity). The engine also now uses the exact **IRS Tax Table**
   (midpoint rule, verified against printed cells) under $100K instead of
   the bracket formula — load-bearing for a ~$36K filer.

## K-1 Support Status (Phase 2)

K-1 computation (Forms 1065, 1120-S, 1041 → Schedule E Parts II/III) is now
supported via `k1_passthrough_calculator.py`: the §704(d)/§1366(d) →
§465 → §469 limitation cascade, PTP per-entity segregation, a combined
Form 8582 with Part I rentals, and next-year carryovers in the prior-year
schema. Curated references: `k1-guide.md`,
`passthrough-loss-limitations.md`.

**Remaining K-1 limitations** (disclosed in the calculator's notes): basis
and at-risk capacity must be supplied (Form 7203 / basis worksheets — the
tool BLOCKS loss entities rather than guessing); suspended-loss allocation
is pro-rata rather than the form's per-activity worksheets; §461(l) excess
business loss is flagged, not computed; Form 8995-A territory (above the
QBI threshold) goes to the accountant. Still out of scope: foreign income
(Schedule K-3), Schedule F, and complex credits (CTC, education, EIC).

## Next Steps

**To file the 2025 return:**
1. Drop documents in `my-tax-docs/` and prior-year returns in
   `my-tax-docs/prior-years/`; run `/tax-prep`
2. Gather per-property data — checklist in `docs/SCHEDULE-E-PLAN.md` §5
   (basis, placed-in-service dates, prior depreciation, suspended losses,
   days rented, services provided)
3. `/tax-cheatsheet` per form → `/tax-audit` before filing → `/tax-advisor`
   after

**In progress — prior-year ingestion subsystem:**
- **Phase 1 (next): the `ingest/` subsystem** — a quarantined in-repo module
  that automates Hermes Agent extraction end-to-end (staging → PII firewall →
  verify → explicit-approve), reusing the validated validator/schema. Needs a
  short brainstorm → plan first; open items: pin the exact Hermes invocation
  (one-shot subprocess) and whether `verify.py` shows source page images.
- Phase 2 (optional): multi-year analysis + intake-priming briefing.

**Possible enhancements (in rough priority order):**
- **K-1 / Schedule E Part II *computation*** — a separate planned follow-on
  design covering the K-1 input forms (1065/1120-S/1041) and Schedule E; it
  opens by validating the existing Schedule E Part I rental work, then adds
  Part II (would need new curated refs and Part II line handling)
- Full Form 8582 computation (current version is simplified) and a Form 4562
  detail calculator (current handles building SL; other assets entered as
  amounts)
- NIIT (Form 8960) computation inside `what_if.py` (currently flag-only)
- Curated reference for estimated-tax safe harbor rules (currently marked
  "verify on IRS.gov")
- CI to run the test suite (a `tests/` pytest harness now exists from Phase 0,
  covering the prior-year validator; the calculation scripts still lack tests);
  demo mode with fictional data
- 2026 tax-year update (per `reference/HOW-TO-CURATE.md` — watch for the GA
  rate stepping down toward 4.99%)
