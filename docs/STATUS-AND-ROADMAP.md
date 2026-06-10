# Status and Roadmap

*Last updated: June 10, 2026*

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

## ⚠️ Known Limitation: K-1s Are NOT Supported

The system does **not** handle Schedule K-1s (Forms 1065, 1120-S, or 1041) or
**Schedule E Part II** (partnerships and S corporations). Only single-member
LLCs taxed as disregarded entities are supported. If any LLC has multiple
members or elects S-corp treatment, its K-1 cannot be processed by these
skills — consult a tax professional or handle that form manually. Also out of
scope: foreign income, Schedule F, and complex credits (CTC, education, EIC).

## Next Steps

**To file the 2025 return:**
1. Drop documents in `my-tax-docs/` and prior-year returns in
   `my-tax-docs/prior-years/`; run `/tax-prep`
2. Gather per-property data — checklist in `docs/SCHEDULE-E-PLAN.md` §5
   (basis, placed-in-service dates, prior depreciation, suspended losses,
   days rented, services provided)
3. `/tax-cheatsheet` per form → `/tax-audit` before filing → `/tax-advisor`
   after

**Possible enhancements (in rough priority order):**
- K-1 / Schedule E Part II support (would need new curated refs and Part II
  line handling)
- Full Form 8582 computation (current version is simplified) and a Form 4562
  detail calculator (current handles building SL; other assets entered as
  amounts)
- NIIT (Form 8960) computation inside `what_if.py` (currently flag-only)
- Curated reference for estimated-tax safe harbor rules (currently marked
  "verify on IRS.gov")
- Unit tests + CI for the calculation scripts; demo mode with fictional data
- 2026 tax-year update (per `reference/HOW-TO-CURATE.md` — watch for the GA
  rate stepping down toward 4.99%)
