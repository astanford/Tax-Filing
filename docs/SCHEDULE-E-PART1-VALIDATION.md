# Schedule E Part I Validation — Phase 2 Gate

*Date: 2026-07-03*
*Scope: the never-independently-verified Schedule E Part I work — the rental
curated references and `schedule_e_calculator.py` — validated against the
official IRS sources committed in `reference/Raw/` (f1040se.pdf, i1040se.pdf,
p946.pdf, i8582.pdf, p527.pdf), per the opening requirement of the K-1 /
Part II follow-on design (docs/superpowers/specs/2026-06-22, "Out of scope
and the planned follow-on").*

## Verdict Summary

| Artifact | Verdict | Outcome |
|---|---|---|
| Calculator line mapping (Lines 3–21, 23a) | **GO** | 2 cosmetic fixes applied |
| Curated `schedule-e-guide.md` | **GO** | no changes needed |
| MACRS percentage tables (year 1 + steady) | **GO** | moved to shared module |
| MACRS final-year handling | **NO-GO → FIXED** | full printed tables implemented |
| Curated `rental-depreciation.md` | **GO** | no changes (it was right; the code wasn't) |
| §469 classification (short/mid-term, services) | **GO** | no changes |
| $25K allowance computation | **GO** | no changes |
| Simplified Form 8582 flow | **FIX → FIXED** | allowance-base netting bug fixed |
| Curated `passive-activity-losses.md` | **GO** | no changes (documented the rule the code missed) |

**Gate: PROCEED to Part II / K-1 computation.** All fixes are implemented,
regression-tested, and the corrected behavior is verified against the printed
IRS tables and the i8582 worked example.

## Findings and Fixes

### 1. MACRS final/penultimate recovery years (NO-GO — the big one)

The calculator used a flat steady-state rate until "exhaustion," then $0.
Pub 946 Tables A-6/A-7a (pp. 73–74) print partial rates for the last years:

- **A-6 year 28**: Jan–Jun placements get 1.970%–3.485%, not 3.636%.
  Worst case ~$4,581/yr overstated on a $275K basis (January placement).
- **A-6 year 29**: Jul–Dec placements still get 0.152%–1.667%; the code
  returned $0 with a factually wrong "exhausted — verify" note
  (~$4,584 missed, December placement).
- **A-7a year 40**: month-dependent 0.107%–2.461%, not 2.564%
  (~$6,757/yr overstated, January placement).
- **A-6 years 10–27 alternation**: the flat 3.636% ignores the printed
  3.636/3.637 alternation — a $2.75/yr error at a $275K basis, above the $1
  audit tolerance for any basis over $100K (the old comment claimed
  otherwise).

**Fix:** `engine/macrs_tables.py` now encodes the complete printed tables
(year-1 rows, steady years, alternation parity, partial years 28/29/40) with
a tested invariant that every placement-month column sums to exactly 100%.
`compute_building_depreciation` looks up `(recovery, table_year, month)`
directly. Notably, `rental-depreciation.md` had documented all of these
partial-year rates correctly — the code simply didn't implement its own
cited reference.

### 2. Form 8582 allowance base ignored rental income (FIX)

Form 8582 line 4 = smaller of the **line 1d net rental loss** or the line 3
loss (i8582 pp. 10–11, worked example). The code capped the allowance base
at gross `rental_losses + prior_suspended` without netting rental *income*,
so a profitable rental plus non-rental passive losses over-deducted
(repro: rentals +$2,000/−$3,000 + short-term −$5,000 at MAGI $90K → code
allowed $5,000 and suspended $3,000; correct is allowed $3,000, suspended
$5,000, Schedule E net −$1,000).

**Fix:** allowance base is now
`min(remaining_loss, max(0, rental_losses + prior_suspended − rental_income))`.
Regression test reproduces the i8582 pattern.

### 3. Cosmetic / disclosure fixes

- Aggregate output keys renamed to the official roll-up lines:
  `line_23e_total_expenses` (sum of Line 20s), `line_23d_total_depreciation`
  (sum of Line 18s). Per-property line numbers were already correct.
- Line 18 label expanded to the form caption "Depreciation expense or
  depletion".
- `building_basis` input contract now states it must EXCLUDE non-depreciable
  land (the curated ref documents the allocation method; the code never said
  so).
- Documented simplifications in the 8582 block: `prior_suspended_loss` is
  attributed entirely to the rental-RE active-participation bucket (line 1c);
  CRD ordering not handled.

## Validated-correct (no action)

- All 14 expense-line mappings and Lines 18/20/21/23a match the 2025 form.
- All 24 year-1 depreciation percentages and both steady rates match Pub 946.
- §469 exception encoding (≤7-day, ≤30-day + significant services,
  substantial services → Schedule C) matches i8582 p.3–4 and Pub 527 p.18.
- Allowance numbers ($25K/$12.5K/$0; 50% phase-out $100K–$150K and
  $50K–$75K MFS-apart) match i8582 p.4.
- Passive-income-absorbs-first and rental-keeps-its-allowance behaviors match
  the real form's Part I/II structure.
- The three curated references passed every spot-check, including verbatim
  quotes; `schedule-e-guide.md` carries all four 2025 "What's New" items
  relevant to Part I (70¢ mileage, 100% bonus restoration, §179 limits,
  §163(j) add-back).

## Out-of-scope notes carried forward to Part II work

- Royalties (Lines 4/23b) remain unsupported (rental-only tool).
- Lines 22/24/25 are folded into the `form_8582` block and Line 26 rather
  than emitted separately — the Phase 3 engine should emit them explicitly
  when assembling the real form.
- i1040se.pdf 2025 "What's New" items peripheral to Part I (car-loan
  interest / Schedule 1-A, Form 7203/7205 reminders) — the Form 7203
  (S-corp shareholder basis) reminder becomes RELEVANT in Part II.
