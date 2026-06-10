# Known Pitfalls — Common Tax Filing Mistakes

Reference document for the `/tax-audit` skill. Each pitfall includes
a description, how to verify, and a citation to the relevant curated
reference file.

---

## Pitfall 1: AGI Breakdown Must Include ALL Income

- **Mistake:** When reconciling AGI (e.g., for the GA retirement income
  exclusion's per-spouse allocation, or other purposes), only including
  W-2 wages and forgetting interest, dividends, capital gains, and
  Schedule C income.
- **How to verify:** Sum each spouse's W-2 wages + their share of
  investment income + Schedule C income. The total must equal federal AGI
  (1040 Line 11).
- **Citation:** *(Source: georgia-500-guide.md, Schedule 1 — Subtractions;
  1040-line-by-line.md, Income Section)*

## Pitfall 2: All Math Must Be Verified Through Python

- **Mistake:** Eyeballing numbers or doing mental arithmetic instead
  of running values through the calculation scripts.
- **How to verify:** Every computed value on the return should have a
  corresponding script output. Use `cross_check.py` for verification.
- **Citation:** *(Source: CLAUDE.md, Rules)*

## Pitfall 3: State Rules Differ From Federal

- **Mistake:** Choosing the GA deduction independently of the federal
  return. Georgia LOCKS the deduction type: if you itemized federally
  you MUST itemize on Form 500 (Lines 12a–c); if you took the federal
  standard deduction you MUST take the GA standard deduction (Line 11).
  Also, GA's HoH standard deduction is only $12,000 — no premium over
  Single, unlike federal.
- **How to verify:** Confirm the GA deduction type matches the federal
  return, and that Line 12b backs out only OTHER states' income taxes
  (Georgia income tax stays deductible). If itemizing, check the
  Eligible Itemizer Tax Credit (Line 19, up to $300/taxpayer).
- **Citation:** *(Source: georgia-500-guide.md, Deduction Section,
  Lines 11–12c; Credits, Line 19)*

## Pitfall 4: Cross-Form References Must Pull From Completed Forms

- **Mistake:** Entering a value on Form 1040 Line 7 that does not
  match Schedule D Line 21 (or using an estimate instead of the
  actual computed value).
- **How to verify:** For each line that references another form,
  trace the value back to the source form and confirm they match.
- **Citation:** *(Source: 1040-line-by-line.md, Income Section)*

## Pitfall 5: W-2 Box 5 (Medicare Wages) >= Box 1 (Wages)

- **Mistake:** Not noticing when Medicare wages are less than regular
  wages, which can indicate pre-tax benefits were applied differently.
  This affects Additional Medicare Tax calculations on Form 8959.
- **How to verify:** For each W-2, confirm Box 5 >= Box 1. If not,
  verify pre-tax benefit treatment is correct.
- **Citation:** *(Source: additional-medicare-tax.md, Form 8959
  Line-by-Line)*

## Pitfall 6: SALT Cap Applies to Schedule A; GA Starts Post-Cap

- **Mistake:** Recomputing uncapped SALT on the Georgia return. The
  $40,000 SALT cap limits the federal Schedule A deduction; GA Form 500
  Line 12a starts from the federal Schedule A TOTAL (after the cap),
  then Line 12b removes other states' income taxes (prorated if SALT
  was limited).
- **How to verify:** Confirm Schedule A Line 5e respects the SALT cap.
  Confirm GA 500 Line 12a equals the post-cap federal itemized total.
- **Citation:** *(Source: salt-deduction-2025.md, Overall SALT Cap;
  georgia-500-guide.md, Lines 12a–c)*

## Pitfall 7: GA 500 Line 8 Must Equal Federal AGI

- **Mistake:** GA Form 500 Line 8 not matching 1040 Line 11 exactly —
  especially entering federal TAXABLE income instead of federal AGI
  (the IT-511 instructions warn against this specifically). Line 8 is
  the starting point for the Georgia return.
- **How to verify:** `cross_check.py` performs this check automatically
  (check `fed_state_agi_match`).
- **Citation:** *(Source: georgia-500-guide.md, Income Section, Line 8)*

## Pitfall 8: Student Loan Interest May Be $0 Despite Having 1098-E

- **Mistake:** Claiming a student loan interest deduction when MAGI
  exceeds the phase-out range. Having a 1098-E does not guarantee
  you get the deduction — it depends on MAGI.
- **How to verify:** Check MAGI against the $170,000–$200,000 MFJ
  phase-out range. If MAGI >= $200,000, deduction is $0 regardless
  of the 1098-E amount.
- **Citation:** *(Source: student-loan-interest.md, MAGI Phase-Out)*

## Pitfall 9: QBI Deduction Is $0 if Schedule C Shows a Net Loss

- **Mistake:** Entering a QBI deduction when the business had a loss.
  Negative QBI produces $0 deduction (but the loss carries forward
  to future years).
- **How to verify:** If Schedule C Line 31 is negative, Form 8995
  Line 15 must be $0. File Form 8995 anyway to establish the
  carryforward on Line 16.
- **Citation:** *(Source: self-employment-qbi.md, QBI Loss
  Carryforward)*

## Pitfall 10: Additional Medicare Tax Threshold Mismatch

- **Mistake:** Assuming that because neither spouse individually
  exceeds $200,000 in wages, no Additional Medicare Tax is due. The
  employer withholds at $200,000 per individual employee, but the MFJ
  threshold is $250,000 on combined wages. Combined wages over $250,000
  trigger the tax even if neither spouse alone triggers employer
  withholding.
- **How to verify:** Sum both spouses' W-2 Box 5. If total > $250,000
  (MFJ), Form 8959 is required. Check whether the withholding credit
  (Form 8959 Line 22) covers the liability or leaves a balance due.
- **Citation:** *(Source: additional-medicare-tax.md, How Employer
  Withholding Works)*

## Pitfall 11: Rental Depreciation Must Be Claimed Every Year

- **Mistake:** Skipping Line 18 depreciation on a rental property
  (or forgetting to split basis between building and land — land is
  never depreciable). Depreciation is "allowed or allowable": basis
  is reduced and §1250 recapture applies at sale whether or not you
  claimed the deduction.
- **How to verify:** Every rental property with a building basis must
  show Line 18 depreciation from `schedule_e_calculator.py`. Land
  portion excluded from the depreciable basis.
- **Citation:** *(Source: rental-depreciation.md, Allowed or
  Allowable; Basis Allocation)*

## Pitfall 12: Short-Term Rentals Are Not Ordinary Rentals

- **Mistake:** Treating an Airbnb-style property (average stay ≤ 7
  days) like a long-term rental. It is NOT a §469 rental activity:
  no $25,000 loss allowance; passive unless you materially
  participate. With substantial services (regular cleaning, linen),
  it belongs on Schedule C with SE tax. Transient/hotel-like use can
  also push depreciation from 27.5-year to 39-year.
- **How to verify:** Classify every property by average rental period
  and services in `schedule_e_calculator.py`; check the resulting
  §469 bucket and recovery period.
- **Citation:** *(Source: passive-activity-losses.md, Exceptions;
  schedule-e-guide.md, Schedule C Boundary; rental-depreciation.md)*

## Pitfall 13: Rental Loss Allowance Phases Out With MAGI

- **Mistake:** Deducting rental losses in full when MAGI ≥ $150,000.
  The $25,000 active-participation allowance phases out 50¢ per
  dollar of MAGI over $100,000 and is $0 at $150,000 — losses must
  be suspended on Form 8582, not deducted.
- **How to verify:** `schedule_e_calculator.py` computes the
  allowance and suspended carryforward; confirm Schedule E Line 22
  matches.
- **Citation:** *(Source: passive-activity-losses.md, Special
  $25,000 Allowance)*

## Pitfall 14: Georgia Bonus Depreciation Addback

- **Mistake:** Claiming federal bonus depreciation (§168(k)) on
  rental assets and copying federal AGI to GA Form 500 Line 8 with
  no adjustment. Georgia has not adopted bonus depreciation — an
  addition is required on GA Schedule 1, and GA depreciation must be
  tracked separately for those assets afterward.
- **How to verify:** `schedule_e_calculator.py` reports
  `ga_bonus_depreciation_addback`; confirm it appears on GA Form 500
  Schedule 1.
- **Citation:** *(Source: georgia-500-guide.md, Key Structural
  Facts; rental-depreciation.md, Georgia Notes)*
