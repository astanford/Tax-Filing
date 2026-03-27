# Known Pitfalls — Common Tax Filing Mistakes

Reference document for the `/tax-audit` skill. Each pitfall includes
a description, how to verify, and a citation to the relevant curated
reference file.

---

## Pitfall 1: AGI Breakdown Must Include ALL Income

- **Mistake:** When splitting AGI between spouses (for MD two-income
  subtraction or other purposes), only including W-2 wages and
  forgetting interest, dividends, capital gains, and Schedule C income.
- **How to verify:** Sum each spouse's W-2 wages + their share of
  investment income + Schedule C income. The total must equal federal AGI
  (1040 Line 11).
- **Citation:** *(Source: maryland-502-guide.md, Two-Income Subtraction)*

## Pitfall 2: All Math Must Be Verified Through Python

- **Mistake:** Eyeballing numbers or doing mental arithmetic instead
  of running values through the calculation scripts.
- **How to verify:** Every computed value on the return should have a
  corresponding script output. Use `cross_check.py` for verification.
- **Citation:** *(Source: CLAUDE.md, Rules)*

## Pitfall 3: State Rules Differ From Federal

- **Mistake:** Applying federal deduction rules on the state return.
  Maryland has its own itemized deduction calculation (federal itemized
  minus state/local income taxes, then subject to 7.5% phase-out above
  $200,000 FAGI). The SALT cap does NOT apply to Maryland.
- **How to verify:** Confirm MD 502 Line 17 uses MD-specific
  calculation, not the federal Schedule A total.
- **Citation:** *(Source: maryland-502-guide.md, Itemized Deduction
  for Maryland; Itemized Deduction Phase-Out)*

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

## Pitfall 6: SALT Cap Applies to Schedule A, Not State Return

- **Mistake:** Applying the $40,000 SALT cap when computing Maryland
  deductions. The SALT cap only limits the federal Schedule A
  deduction. Maryland computes its own itemized deductions separately.
- **How to verify:** Confirm Schedule A Line 5e respects the SALT cap.
  Confirm MD 502 does NOT apply the SALT cap.
- **Citation:** *(Source: salt-deduction-2025.md, Overall SALT Cap;
  maryland-502-guide.md, Itemized Deduction for Maryland)*

## Pitfall 7: MD 502 Line 1 Must Equal Federal AGI

- **Mistake:** MD 502 Line 1 not matching 1040 Line 11 exactly.
  This is the starting point for the Maryland return and must be
  an exact copy of federal AGI.
- **How to verify:** `cross_check.py` performs this check automatically
  (check `fed_state_agi_match`).
- **Citation:** *(Source: maryland-502-guide.md, Line-by-Line
  Reference, Line 1)*

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
