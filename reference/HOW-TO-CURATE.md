# How to Curate Tax Reference Files

## What Are Curated Reference Files?

Curated reference files are focused markdown extractions from IRS publications, form
instructions, and state tax documents. They contain **only** the rules, thresholds, and
procedures relevant to common filing situations (MFJ, W-2 income, investment income,
mortgage, small business, Georgia state).

Every tax rule cited by downstream skills (`/tax-cheatsheet`, `/tax-audit`, `/tax-advisor`)
**must** trace back to a curated file in `reference/curated/`. If a rule cannot be verified,
the skill must say: *"I cannot verify this — check IRS.gov."*

## Where to Download IRS Publications

| Source | URL | What's There |
|--------|-----|-------------|
| IRS Forms & Instructions (PDF) | `https://www.irs.gov/pub/irs-pdf/` | Current-year forms (f1040.pdf), instructions (i1040gi.pdf), publications (p936.pdf) |
| IRS Prior-Year Forms | `https://www.irs.gov/pub/irs-prior/` | Prior-year versions when current isn't posted yet |
| IRS Publications (HTML) | `https://www.irs.gov/publications/` | Same content as PDFs but browsable (e.g., /p17, /p550, /p936, /p970) |
| IRS Newsroom | `https://www.irs.gov/newsroom/` | Tax year announcements, standard mileage rates, new legislation guidance |
| Georgia Dept. of Revenue | `https://dor.georgia.gov/` | Form 500, IT-511 booklet, rate changes, tax credits |
| GA Forms & Instructions | `https://dor.georgia.gov/taxes/taxes-individuals` | Current-year GA forms and instructions |
| GA Legislation | `https://www.legis.ga.gov/` | Bills affecting tax rates (e.g., HB 111) |

### Key Documents for 2025

| Document | Filename Pattern | Purpose |
|----------|-----------------|---------|
| Form 1040 Instructions | `i1040gi--2025.pdf` | Line-by-line guidance, standard deduction, brackets, Schedule 1-A |
| Publication 936 | `p936.pdf` | Mortgage interest deduction rules |
| Publication 970 | `p970.pdf` | Student loan interest deduction (Chapter 4) |
| Publication 550 | `p550.pdf` | Investment income — interest, dividends, capital gains |
| Schedule A Instructions | via IRS website | SALT deduction, itemized deduction rules |
| Schedule C Instructions | via IRS website | Business income/expenses |
| GA IT-511 Booklet | `2025-it511-booklet.pdf` | Form 500 instructions, flat rate, deductions, exemptions, credits |
| GA Form 500 | `2025-ga-form-500.pdf` | The return itself — line numbers and schedules |

## How to Extract Relevant Sections

1. **Identify the topic** (e.g., SALT deduction, mortgage interest, Georgia 500).
2. **Find the authoritative source** — always prefer IRS form instructions and publications over practitioner articles.
3. **Read only the relevant pages** — don't dump entire 100-page publications.
4. **Extract rules that apply** to the filing situation: MFJ, W-2 income, investment income, mortgage, Georgia residency.
5. **Skip irrelevant topics** — farm income, foreign tax credit, adoption credit, etc.
6. **Include exact citations** for every rule: `[Source Name, Page/Section X]`.

## Markdown Template

Every curated file must follow this structure:

```markdown
# [Topic Title]

## Source
- [Official source 1 with edition/date/page range]
- [Official source 2]

## Applicable To
- **Forms:** [Form numbers and line numbers]
- **Workflow Steps:** [Step numbers and names]

---

## Rules

### [Rule Category 1]
- Rule text with citation [Source Name, Page/Section X]
- Tables for thresholds and brackets

### [Rule Category 2]
...

---

## Your Situation Notes
- **[Key parameter]:** [Specific value] — [implication for your return]
- **Prior-year comparison:** [Year-over-year change]
```

### Citation Format

Every rule must include a citation in square brackets:
- `[Pub 936 (2025), Page 2]`
- `[Form 1040 Instructions (2025), Page 6]`
- `[Schedule A Instructions (2025), Line 5e]`
- `[IT-511 (2025), Line 16, p. 17]`
- `[IRC §199A]`

If a rule cannot be cited to a specific source: **do not include it**. Instead, note
"I cannot verify this — check IRS.gov."

## How to Verify Extracted Rules

1. **Cross-check numbers against 2+ sources.** For example, verify federal brackets from both the Form 1040 Instructions and the Bipartisan Policy Center tables.
2. **Compare with the form itself.** Read the actual form (f1040.pdf, f1040sa.pdf) to confirm line numbers match the instructions.
3. **Check "What's New" sections.** The first few pages of Form 1040 Instructions list all changes for the tax year. Any threshold that changed should be flagged.
4. **Verify state-specific rules** against the official Georgia IT-511 booklet and dor.georgia.gov — not just practitioner analysis articles.
5. **Test breakeven calculations** with Python scripts (per CLAUDE.md: no LLM arithmetic).

## How to Update for Future Tax Years

1. Download the new year's Form 1040 Instructions — check "What's New" (pages 1-9) for updated thresholds.
2. Check `irs.gov/newsroom/` for any new legislation or rate changes.
3. For Georgia, download the new IT-511 booklet from `dor.georgia.gov` and check for rate-change legislation (the flat rate is scheduled to step down 0.10%/year toward 4.99%, contingent on revenue conditions).
4. Update every threshold in `2025-tax-numbers.md` first — this is the foundation file referenced by all others.
5. Update each topic file's thresholds, phase-outs, and "Your Situation Notes."
6. Verify cross-references between files remain consistent.

## Current Curated Files

| File | Primary Source | Topic |
|------|---------------|-------|
| `2025-tax-numbers.md` | Form 1040 Instructions, Bipartisan Policy Center, GA IT-511 | Brackets, standard deduction, SALT cap, AMT, mileage rate |
| `salt-deduction-2025.md` | Schedule A Instructions, OBBBA | $40K SALT cap mechanics and phase-out |
| `mortgage-interest.md` | Publication 936 | Home mortgage interest deduction |
| `student-loan-interest.md` | Publication 970, Chapter 4 | Student loan interest deduction and phase-out |
| `investment-income.md` | Publication 550, Schedule B Instructions | Interest, dividends, capital gains |
| `schedule-c-guide.md` | Schedule C Instructions, Publication 17 | Business income/expenses, hobby loss |
| `self-employment-qbi.md` | Form 8995 Instructions, IRC §199A | SE tax basics and QBI deduction |
| `additional-medicare-tax.md` | Form 8959, IRC §3101(b)(2) | Additional 0.9% Medicare tax |
| `georgia-500-guide.md` | GA IT-511 Booklet (2025), HB 111, GA DOR | Georgia Form 500 line-by-line |
| `schedule-e-guide.md` | Schedule E Instructions (2025), Pub 527 (2025), Schedule E form | Rental real estate, SMLLC, STR/MTR/LTR classification |
| `rental-depreciation.md` | Pub 946 (2025), Pub 527 (2025), Form 4562 Instructions (2025) | MACRS 27.5/39-yr tables, basis, bonus depreciation, GA addback |
| `passive-activity-losses.md` | Form 8582 Instructions (2025), Pub 527 (2025) | $25K allowance, MAGI phase-out, 7-day/30-day exceptions |
| `schedule-1a-deductions.md` | Form 1040 Instructions pp. 101-115, OBBBA | New OBBBA deductions (tips, overtime, car loan, senior) |
| `1040-line-by-line.md` | Form 1040 Instructions pp. 23-65 | Form 1040 line-by-line with cross-references |
