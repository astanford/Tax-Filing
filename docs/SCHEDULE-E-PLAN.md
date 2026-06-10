# Schedule E (Rental Real Estate) — Requirements Plan

What this repo needs in order to support Schedule E Part I (rental real
estate) end-to-end, following the same architecture as the existing
Schedule C support: curated references → calculation scripts → skill
workflows → audit checks.

Status: **IMPLEMENTED** (June 2026). What was built:

- Curated references: `reference/curated/schedule-e-guide.md`,
  `rental-depreciation.md`, `passive-activity-losses.md` — extracted
  from the 2025 Schedule E Instructions, Pub 527 (2025), Pub 946
  (2025), Form 8582 Instructions (2025), Form 4562 Instructions, and
  the 2025 Schedule E form (raw PDFs in `reference/Raw/`)
- New script: `.claude/skills/tax-cheatsheet/scripts/schedule_e_calculator.py`
  (per-property P&L, MACRS table depreciation 27.5/39-yr, §469
  classification for short/mid/long-term rentals, simplified Form 8582
  with $25K allowance, GA bonus-depreciation addback)
- Script wiring: `what_if.py` (`schedule_e_net`), `cross_check.py`
  (Schedule E Line 26 = Schedule 1 Line 5), `completeness_check.py`
  (1099-MISC and `Rental (...)` documents → Schedule E / 8582 / 4562)
- Skills: tax-prep rental-records CSV convention; tax-cheatsheet
  Schedule E workflow; tax-audit pitfalls 11–14
- Single-member LLCs: disregarded — reported on the owner's Schedule E
  [Schedule E Instructions (2025), p. 2]

The sections below are the original requirements plan, kept for
reference; section 5 (information needed per property) is still the
intake checklist.

---

## 1. New Curated Reference Files

Per `reference/HOW-TO-CURATE.md`, every rule must trace to an official
source. Download these to `reference/Raw/` first:

| Source | File | Why |
|--------|------|-----|
| 2025 Schedule E + Instructions | irs.gov/pub/irs-pdf/f1040se.pdf, i1040se.pdf | Line-by-line authority |
| Publication 527 — Residential Rental Property | p527.pdf | Income/expense rules, personal use, depreciation basics |
| Publication 946 — How To Depreciate Property | p946.pdf | MACRS tables, conventions, basis |
| Form 8582 + Instructions | f8582.pdf, i8582.pdf | Passive activity loss limits |
| Form 4562 + Instructions | f4562.pdf, i4562.pdf | Depreciation reporting (first-year property) |

Then create three curated files:

### `schedule-e-guide.md`
- Part I line-by-line: Line 3 rents received → Lines 5–19 expenses
  (advertising, auto/travel, cleaning, commissions, insurance, legal,
  management fees, mortgage interest Line 12, repairs, supplies, taxes,
  utilities, depreciation Line 18, other) → Line 21 income/(loss) →
  Line 22 deductible loss after Form 8582.
- Per-property columns (A/B/C), property type codes, fair rental days
  vs. personal use days, and the §280A vacation-home limits when
  personal use exceeds the greater of 14 days / 10% of rental days.
- Repairs vs. improvements (improvements must be capitalized and
  depreciated, not expensed) — a top audit trigger.
- 1099-MISC Box 1 (rents) reporting when a property manager collects.

### `rental-depreciation.md`
- Residential rental building: **27.5-year straight-line MACRS,
  mid-month convention**. Land is NOT depreciable — basis must be split
  between building and land (county tax assessment ratio is the usual
  method; DeKalb County assessment works here).
- "Allowed or allowable" rule: depreciation reduces basis (and is
  recaptured at sale, §1250) whether or not you actually claimed it —
  skipping depreciation only hurts you.
- 5/7/15-year property (appliances, carpets, land improvements) and
  bonus depreciation / §179 interactions.
- **Georgia addback:** GA has NOT adopted IRC §168(k) bonus
  depreciation, and §179 is adopted only partially (not for certain
  real property). If bonus is claimed federally, a GA Schedule 1
  addition is required and separate GA depreciation schedules must be
  tracked thereafter. *(Source: georgia-500-guide.md, Key Structural
  Facts; GA DOR, Income Tax Federal Tax Changes)*

### `passive-activity-losses.md`
- Rental real estate is passive by default; losses only offset passive
  income unless an exception applies.
- **$25,000 special allowance** for actively-participating landlords,
  phased out at 50¢ per dollar of MAGI between **$100,000 and
  $150,000** (gone at $150K — same threshold for MFJ and Single).
- Suspended losses carry forward on Form 8582 and release fully in the
  year of a taxable disposition.
- Real estate professional rules (probably out of scope — note and link).

### Updates to existing references
- `niit-form-8960.md` — add: net rental income is investment income
  for the 3.8% NIIT (MAGI > $250K MFJ).
- `self-employment-qbi.md` — add: rental income is NOT subject to SE
  tax; QBI eligibility via the Rev. Proc. 2019-38 safe harbor (250
  hours + records) or §162 trade-or-business status. Georgia doesn't
  allow QBI, but no GA adjustment is needed (starts from federal AGI).
- `georgia-500-guide.md` — already notes: rental income flows through
  federal AGI with no special GA treatment; rental income not subject
  to SE tax counts as *unearned* retirement income for the GA
  retirement exclusion (age 62+). [IT-511 (2025), p. 24]

## 2. New Script: `schedule_e_calculator.py`

Lives in `.claude/skills/tax-cheatsheet/scripts/`, same JSON-in/JSON-out
Decimal pattern as `schedule_c_calculator.py`.

**Inputs (per property):** rents received; each expense category
(Lines 5–17, 19); depreciation inputs — cost basis, land value,
placed-in-service date, prior accumulated depreciation, current-year
improvements/assets; fair rental days and personal use days.

**Computes:**
1. Straight-line 27.5-year depreciation with mid-month convention
   (first/last year proration) per property.
2. Net income/(loss) per property and Schedule E totals (Lines 23a–26).
3. Passive loss limitation: $25K allowance with the $100K–$150K MAGI
   phase-out, suspended-loss carryforward in/out (simplified Form 8582).
4. Flags: personal-use limits triggered, NIIT exposure, GA bonus
   depreciation addback amount for Form 500 Schedule 1.

## 3. Updates to Existing Scripts

| Script | Change |
|--------|--------|
| `what_if.py` | Add `schedule_e_net` to income (no SE tax on it). GA flows automatically via federal AGI; bonus-depreciation addback uses the existing `ga_additions` input. Possible new scenario: passive-loss release / expense timing. |
| `cross_check.py` | New check: Schedule 1 Line 5 = Schedule E Line 26, and 1040 Line 8 includes it. |
| `completeness_check.py` | Map `1099-MISC` → Schedule E in `DOC_TO_FORMS`; require Schedule E when 1099-MISC rents or rental rows exist in the CSV; require Form 4562 in first year an asset is placed in service; require Form 8582 when there's a rental loss. |
| `validate_extraction.py` | Recognize 1099-MISC and rental-statement rows; warn if a rental property has income but $0 depreciation ("allowed or allowable"). |

## 4. Skill (SKILL.md) Updates

- **tax-prep:** Add 1099-MISC (Box 1 rents) to Supported Document
  Types. Bigger change: most rental data does NOT arrive on IRS forms.
  Define a CSV convention for user-provided records — document label
  `Rental (123 Main St)`, one row per Schedule E line item, sourced
  from property-manager annual statements, mortgage 1098, county
  property tax bill, and the user's expense log.
- **tax-cheatsheet:** Add Schedule E / Form 4562 / Form 8582 rows to
  the Supported Forms table; add a "Schedule E Workflow" mirroring the
  Schedule C one: gather per-property records → reconcile 1099-MISC
  gross vs. management statements → categorize expenses (repair vs.
  improvement triage) → run `schedule_e_calculator.py` → flag passive
  loss limits and downstream forms.
- **tax-audit:** Add pitfalls — depreciation claimed every year; land
  not depreciated; rental loss disallowed at MAGI ≥ $150K; NIIT on
  rental income; GA bonus addback present if bonus claimed federally;
  Schedule E Line 26 ties to Schedule 1 Line 5.
- **tax-advisor:** Rental scenarios (timing repairs, cost segregation
  flag — refer out, suspended-loss planning).
- **docs/KNOWN-PITFALLS.md:** add the audit pitfalls above with citations.

## 5. Information Needed From You (per property)

1. Property address, type, and % ownership
2. Date placed in service (first available for rent)
3. Purchase price + closing costs, and the land/building split
   (DeKalb County assessment ratio is acceptable)
4. Prior depreciation taken (from last year's return, Form 4562/
   depreciation schedule)
5. Prior suspended passive losses (last year's Form 8582, if any)
6. Rents received (and any 1099-MISC from a property manager)
7. Expenses by category; mortgage interest (Form 1098) and property tax
8. Capital improvements made this year (separate from repairs)
9. Fair rental days vs. personal use days
10. Whether you actively participate (approve tenants/repairs) — gates
    the $25,000 loss allowance
11. Expected MAGI (gates the allowance phase-out and NIIT)

## 6. Suggested Build Order

1. Download raw IRS sources; write the three curated files (largest task)
2. `schedule_e_calculator.py` + unit smoke tests
3. tax-prep CSV convention + 1099-MISC support
4. tax-cheatsheet Schedule E workflow
5. Audit checks + pitfalls
6. Advisor scenarios (optional, last)
