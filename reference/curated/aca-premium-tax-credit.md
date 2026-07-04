# ACA Premium Tax Credit & APTC Reconciliation (Form 8962)

## Source
- Instructions for Form 8962, Premium Tax Credit (PTC) (2025), IRS Catalog Number 60401R, rev. Oct 1, 2025 — pages 1–23
- Form 8962 (2025) — the form itself (Parts I–V line structure)
- Rev. Proc. 2024-40, Section 2.07 (2025 inflation-adjusted items) — §36B(f)(2)(B) excess-APTC repayment limitation, pages 9–10
- Form 1040 Instructions (2025) — Schedule 2, Line 1a (page 111); Schedule 3, Line 9 (pages 116–117)

## Applicable To
- **Forms:** Form 8962 (all parts); Form 1095-A (input document, Part III columns A/B/C); Schedule 3 (Form 1040), Line 9 (net PTC); Schedule 2 (Form 1040), Line 1a (excess APTC repayment)
- **Workflow Steps:** Document extraction (1095-A), Form 8962 computation in the return engine, pre-filing audit (reconciliation check), next-year APTC planning

---

## Rules

### Who Must File Form 8962 (Mandatory Reconciliation)
Exact text [Form 8962 Instructions (2025), Page 3]:

> "You must file Form 8962 with your income tax return (Form 1040,
> 1040-SR, or 1040-NR) if any of the following apply to you.
> • You are taking the PTC.
> • APTC was paid for you or another individual in your tax family.
> • APTC was paid for an individual you told the Marketplace would be in
> your tax family and neither you nor anyone else included that individual
> in a tax family."

- "If any of the circumstances above apply to you, you must file an income tax return and attach Form 8962 even if you are not otherwise required to file." [Form 8962 Instructions (2025), Page 3]
- "If APTC was paid on your behalf, or if APTC was not paid on your behalf but you wish to take the PTC, you must file Form 8962 and attach it to your tax return (Form 1040, 1040-SR, or 1040-NR)." [Form 8962 Instructions (2025), Page 2]
- The instructions warn that Form 8962 mistakes can "delay the processing of your return or refund." [Form 8962 Instructions (2025), Page 22] The commonly stated consequence that the IRS **rejects** an e-filed return showing APTC on a 1095-A when Form 8962 is missing is not stated in these instructions — I cannot verify this — check IRS.gov.
- A dependent claimed on someone else's return does not file Form 8962; the person claiming them reconciles the APTC. [Form 8962 Instructions (2025), Page 3]

### Who Can Take the PTC — Applicable Taxpayer
You can take the PTC for 2025 only if all three hold [Form 8962 Instructions (2025), Page 3]:
1. For at least 1 month, an individual in your tax family was enrolled in a Marketplace qualified health plan on the first day of the month; was not eligible for other MEC (employer coverage, Medicare, Medicaid, etc. — individual-market coverage doesn't count) for the month; and your share of the enrollment premium for the month was paid by the return's unextended due date (or the premium was fully covered by APTC, or enough was paid to avoid termination). [Form 8962 Instructions (2025), Page 3]
2. "No one can claim you as a dependent for the year." [Form 8962 Instructions (2025), Page 3]
3. You are an **applicable taxpayer**: (a) household income ≥ 100% of the FPL for your family size (with below-100% exceptions, see Line 5, below), and (b) if married at the end of 2025, generally you must file a joint return. [Form 8962 Instructions (2025), Page 3]
- Employer coverage is treated as affordable for 2025 — making the family ineligible for PTC if they could have enrolled — "if your share of the annual cost for coverage for yourself and the other members of your tax family allowed to enroll in the coverage is not more than 9.02% of your household income." [Form 8962 Instructions (2025), Page 5]
- No PTC for any period an individual is not lawfully present in the U.S., and no PTC for 2025 Marketplace coverage of anyone covered under an individual coverage HRA. [Form 8962 Instructions (2025), Page 3]

### Tax Family, Family Size (Line 1), and Coverage Family
- **Tax family** = you, your spouse if filing jointly (each only if not claimable as a dependent on someone else's 2025 return), and the dependents you claim on your 2025 return; "Your family size equals the number of qualifying individuals in your tax family (including yourself)." [Form 8962 Instructions (2025), Page 3] Enter tax family size on line 1. [Form 8962 Instructions (2025), Page 7]
- **Coverage family** = individuals in the tax family who are enrolled in a qualified health plan and not eligible for other MEC; the monthly credit amount is "the lesser of: • The enrollment premiums... for the month..., or • The amount of the monthly applicable second lowest cost silver plan (SLCSP) premium... less your monthly contribution amount." [Form 8962 Instructions (2025), Page 4]
- **1095-A mapping:** enrollment premiums = Part III, column A; applicable SLCSP premium = column B; APTC = column C. [Form 8962 Instructions (2025), Page 4] If a Form 1095-A arrives with the "VOID" box checked, do not use it; if "CORRECTED," use only the corrected version. The Marketplace must provide the 2025 Form 1095-A by January 31, 2026. [Form 8962 Instructions (2025), Page 2]

### MAGI for PTC — Line 2a, Line 2b, Line 3 (Household Income)
- **Modified AGI (PTC definition):** "modified AGI is the AGI on your tax return plus certain income that is not subject to tax (foreign earned income, tax-exempt interest, and the portion of social security benefits that is not taxable)." [Form 8962 Instructions (2025), Page 4]
- **Worksheet 1-1 (Line 2a), exact components** [Form 8962 Instructions (2025), Page 8]:
  1. AGI from Form 1040/1040-SR/1040-NR, line 11a
  2. Tax-exempt interest (Form 1040, line 2a)
  3. Excluded foreign earned income/housing (Form 2555, lines 45 and 50)
  4. Nontaxable Social Security: if Form 1040 line 6a > line 6b, add (line 6a − line 6b)
- **Household income (Line 3) = filer (and spouse, if MFJ) modified AGI + dependents' modified AGI**, but only for "each individual whom you claim as a dependent and who is required to file an income tax return because their income meets the income tax return filing threshold." Dependents filing only to claim a refund of withheld/estimated tax are excluded. [Form 8962 Instructions (2025), Page 4] Dependents' combined modified AGI is figured on Worksheet 1-2 and entered on Line 2b. [Form 8962 Instructions (2025), Page 8]
- Line 3 = line 2a + line 2b, "even if one or both of them are negative. If the total is less than zero, enter -0- on line 3." [Form 8962 Instructions (2025), Page 8]

### Federal Poverty Line — Line 4 (2024 Guidelines Apply for 2025 Coverage)
- "(For 2025, the 2024 federal poverty lines are used for this purpose and are shown below.)" Check the state-of-residence box; Georgia uses Table 1-1 (48 contiguous states and DC). [Form 8962 Instructions (2025), Page 8]
- **Table 1-1 — Federal Poverty Line, 48 contiguous states + DC** [Form 8962 Instructions (2025), Page 8]:

| Family size (line 1) | Line 4 amount |
|---|---|
| 1 | $15,060 |
| 2 | $20,440 |
| 3 | $25,820 |
| 4 | $31,200 |
| 5 | $36,580 |

- Family size above 8: add $5,380 per additional person. [Form 8962 Instructions (2025), Page 8] (Alaska Table 1-2 and Hawaii Table 1-3 are on page 9 — not applicable to a Georgia filer; if spouses lived in different states, use the table with the higher amounts. [Form 8962 Instructions (2025), Pages 8–9])

### Line 5 — Percentage of FPL and Its Rounding Rule (Truncation)
- Worksheet 2, exact rule: "Divide the amount on line 1 above by the amount on line 2 above. Do not round; instead, multiply this number by 100 (to express it as a percentage) and then drop any numbers after the decimal point. For example, for 0.9984, enter the result as 99; for 1.8565, enter the result as 185; and for 3.997, enter the result as 399." [Form 8962 Instructions (2025), Page 9]
- **Above 400%:** if household income (line 3) is more than 4.0 × line 4, "The amount on line 1 above is more than 400% of the federal poverty line. Enter 401 here and on line 5 of Form 8962." [Form 8962 Instructions (2025), Page 9]
- **No 400% cliff for 2025:** "For tax year 2025, taxpayers with household income that exceeds 400% of the federal poverty line for their family size may be allowed a PTC." [Form 8962 Instructions (2025), Page 1, What's New]
- Below 100%: generally not an applicable taxpayer, but PTC is still allowed if, among other conditions, the Marketplace estimated at enrollment that household income would be ≥100% FPL and APTC was paid — see *Estimated household income at least 100% of the federal poverty line*. [Form 8962 Instructions (2025), Page 9]

### Line 7 — Applicable Figure (Table 2), 2025
Verified against the actual 2025 Table 2: **the ARPA/IRA enhanced structure still applies in 2025** — 0.0000 at ≤150% FPL, an 8.5% cap, and no 400% cliff. Header rule, exact text: "If the amount on line 5 is 150 or less, your applicable figure is 0.0000. If the amount on line 5 is 400 or more, your applicable figure is 0.0850." [Form 8962 Instructions (2025), Page 11, Table 2]

Extracted anchor rows [Form 8962 Instructions (2025), Page 11, Table 2]:

| Line 5 (% of FPL) | Applicable figure |
|---|---|
| less than 150 (incl. 133) | 0.0000 |
| 150 | 0.0000 |
| 176 | 0.0104 |
| 200 | 0.0200 |
| 250 | 0.0400 |
| 300 | 0.0600 |
| 350 | 0.0725 |
| 400 or more | 0.0850 |

- **Structure / interpolation:** Table 2 lists a figure for every whole percentage point from 151 through 399, so line 5 (always a truncated whole number, or 401) maps to exactly one row — the engine never interpolates a fractional percentage. The printed rows follow linear interpolation between band endpoints, rounded to 4 decimal places: 150→200 runs 0.0000→0.0200 (0.0004/point, e.g., 151 = 0.0004, 176 = 0.0104, 199 = 0.0196); 200→250 runs 0.0200→0.0400 and 250→300 runs 0.0400→0.0600 (0.0004/point, e.g., 251 = 0.0404); 300→400 runs 0.0600→0.0850 (0.00025/point, rounded half-up to 4 decimals, e.g., 301 = 0.0603, 302 = 0.0605, 353 = 0.0733). [Form 8962 Instructions (2025), Page 11, Table 2] An engine module should embed the exact table rows (or the band formula with round-half-up to 4 decimals validated against the printed rows) rather than recompute ad hoc.
- Rev. Proc. 2024-40 contains **no** §36B applicable-percentage indexing table for 2025 (its only §36B item is the repayment limitation in Section 2.07) — consistent with the statutory ARPA/IRA percentages applying unindexed through 2025.

### Computation Flow — Lines 8a–29
- **Line 8a (annual contribution amount):** "Multiply line 3 by line 7 and enter the result on line 8a, rounded to the nearest whole dollar amount." [Form 8962 Instructions (2025), Page 12]
- **Line 8b (monthly contribution):** "Divide line 8a by 12.0 and enter the result on line 8b, rounded to the nearest whole dollar amount." [Form 8962 Instructions (2025), Page 12]
- **Line 9:** "No" unless allocating policy amounts with another taxpayer (Part IV) or electing the alternative calculation for year of marriage (Part V). [Form 8962 Instructions (2025), Page 12]
- **Line 10 — annual (line 11) vs. monthly (lines 12–23):** Check "Yes" and use line 11 only if, for each plan: "You were enrolled in the qualified health plan for all 12 months during 2025," the enrollment premium (1095-A col. A) "was the same for every month of 2025," and the SLCSP premium (col. B) "is the same for every month of 2025." Otherwise (including enrollment for fewer than 12 months), check "No" and complete lines 12–23. [Form 8962 Instructions (2025), Page 14]
- **Line 11 columns (annual totals):** (a) annual enrollment premiums = 1095-A line 33, column A; (b) annual applicable SLCSP premium = 1095-A line 33, column B; (c) = line 8a; "(d) Subtract the amount in column (c) from the amount in column (b). If the result is zero or less, enter -0-."; "(e) Enter the lesser of the amount in column (a) or the amount in column (d)."; (f) APTC = 1095-A line 33, column C. [Form 8962 Instructions (2025), Page 15] So annual PTC = lesser of total premiums (col. A) or SLCSP (col. B) minus contribution, floored at 0. Monthly lines 12–23 use the identical column logic with 1095-A lines 21–32 and line 8b in column (c). [Form 8962 Instructions (2025), Pages 16–17]
- **Line 24 (total PTC):** line 11(e), or sum of lines 12(e)–23(e). [Form 8962 Instructions (2025), Page 17] **Line 25 (total APTC):** line 11(f), or sum of lines 12(f)–23(f). [Form 8962 Instructions (2025), Page 18]
- **Net PTC (line 24 > line 25):** line 26 = line 24 − line 25; "Also enter the amount from line 26 on Schedule 3 (Form 1040), line 9. Skip lines 27 through 29." Equal → enter -0- and skip 27–29. [Form 8962 Instructions (2025), Page 18] Confirmed on the 1040 side: "your net premium tax credit will be shown on Form 8962, line 26. Enter that amount, if any, on line 9." [Form 1040 Instructions (2025), Schedule 3 Line 9, Pages 116–117]
- **Excess APTC (line 25 > line 24):** leave line 26 blank, go to Part III; line 27 = line 25 − line 24. [Form 8962 Instructions (2025), Page 18]
- **Line 28 — repayment limitation (Table 5)** [Form 8962 Instructions (2025), Page 18]:

| Line 5 (% of FPL) | Single | Any other filing status (incl. MFJ) |
|---|---|---|
| Less than 200 | $375 | $750 |
| At least 200 but less than 300 | $975 | $1,950 |
| At least 300 but less than 400 | $1,625 | $3,250 |
| 400 or more | leave line 28 blank | leave line 28 blank |

  "If your entry on Form 8962, line 5, is 400 or more, there is no repayment limitation. You must repay the amount shown on line 27." [Form 8962 Instructions (2025), Page 18] Cross-checked: the identical caps ($375/$750, $975/$1,950, $1,625/$3,250) appear in the §36B(f)(2)(B) limitation table. [Rev. Proc. 2024-40, §2.07, Pages 9–10]
- **Line 29 (repayment):** smaller of line 27 or line 28 (line 27 if line 28 is blank); "Also enter the amount from Form 8962, line 29, on Schedule 2 (Form 1040), line 1a." [Form 8962 Instructions (2025), Page 18] Confirmed on the 2025 Schedule 2 itself: line 1a is "Excess advance premium tax credit repayment. Attach Form 8962." [Form 8962 (2025) / Schedule 2 (Form 1040) (2025), Line 1a; Form 1040 Instructions (2025), Page 111] **Note:** in pre-2025 layouts this was Schedule 2, line 2; the 2025 Schedule 2 puts it at line 1a.

### Self-Employed Health Insurance Deduction — Circular Calculation (engine-BLOCK)
If the filer deducts Marketplace premiums as the self-employed health insurance deduction, the deduction and the PTC are mutually dependent: the deduction reduces AGI → household income → which changes the PTC → which changes the deductible (unsubsidized) premium share. The instructions punt to Pub. 974: "If you are claiming the self-employed health insurance deduction, see Pub. 974" [Form 8962 Instructions (2025), Page 2], and, for the repayment cap, "If you are self-employed and are claiming the self-employed health insurance deduction, see Self-Employed Health Insurance Deduction and PTC in Pub. 974 for the amount to enter on line 28." [Form 8962 Instructions (2025), Page 18] Pub. 974 prescribes an iterative/simultaneous calculation. **Engine-BLOCK:** do not compute Form 8962 with a naive one-pass formula if the SE health insurance deduction is claimed for Marketplace premiums — route to the Pub. 974 iterative method or flag for the accountant. Also note: "You cannot deduct the portion of your health insurance premium on your tax return that is paid for by the PTC or APTC." [Form 8962 Instructions (2025), Page 2]

### Married Filing Separately — Generally Ineligible
"If you file as married filing separately and are not a victim of domestic abuse or spousal abandonment... you are not an applicable taxpayer and you cannot take the PTC," and you must generally repay all APTC for a policy covering only your tax family (half, if the policy also covered your spouse's tax family), subject to the line 28 limitation. [Form 8962 Instructions (2025), Page 7] Exceptions: Exception 1 (certain married persons living apart who qualify for HoH/single treatment) and Exception 2 (domestic abuse or spousal abandonment — check box A above Part I; 3-consecutive-year limit). [Form 8962 Instructions (2025), Pages 6–7]

### Shared Policy Allocation / Mid-Year Changes (engine-BLOCK)
If a policy covered a member of your tax family and a member of another tax family (divorce, MFS, an ex-spouse enrolling a child you claim, etc.), the 1095-A amounts (columns A/B/C) must be allocated between tax families on Part IV, per Table 3's four Allocation Situations; check "Yes" on line 9. [Form 8962 Instructions (2025), Pages 12–13] Mid-year changes in circumstances (marriage, family-size changes, moves, gaining employer MEC) force the monthly method (lines 12–23), may require redetermining the correct SLCSP premium when the Marketplace wasn't notified, and marriage during the year may permit the optional Part V alternative calculation. [Form 8962 Instructions (2025), Pages 12, 14] **Engine-BLOCK:** any Part IV allocation or Part V election is out of scope for the calculator — flag for the accountant.

### Engine Flow Map (Simple All-Year Case, No Allocations)
For an MFJ filer with full-year coverage, one 1095-A, constant premiums, and no Part IV/V situations, the computation reduces to:

| Step | Form 8962 line | Computation | Source |
|---|---|---|---|
| 1 | 1 | tax family size | [Form 8962 Instructions (2025), Page 7] |
| 2 | 2a–3 | household income = MAGI (Worksheets 1-1/1-2) | [Form 8962 Instructions (2025), Pages 4, 8] |
| 3 | 4 | 2024 FPL from Table 1-1 (GA) | [Form 8962 Instructions (2025), Page 8] |
| 4 | 5 | floor(line 3 ÷ line 4 × 100); 401 if > 400% | [Form 8962 Instructions (2025), Page 9] |
| 5 | 7 | Table 2 applicable figure | [Form 8962 Instructions (2025), Page 11] |
| 6 | 8a/8b | round(line 3 × line 7); round(8a ÷ 12) | [Form 8962 Instructions (2025), Page 12] |
| 7 | 11(a)–(f) | annual: min(col A, max(0, col B − 8a)); APTC = col C | [Form 8962 Instructions (2025), Page 15] |
| 8 | 24/25/26 | PTC vs APTC; net PTC → Schedule 3, line 9 | [Form 8962 Instructions (2025), Page 18] |
| 9 | 27/28/29 | excess APTC, capped by Table 5 → Schedule 2, line 1a | [Form 8962 Instructions (2025), Page 18] |

### Engine Validation Checks (from "How To Avoid Common Mistakes")
- **Whole dollars only:** "Form 8962 and the IRS electronic filing program provide for entries of dollars only. Your Form 1095-A may include amounts in dollars and cents. You should round the amounts on Form 1095-A to the nearest whole dollar." [Form 8962 Instructions (2025), Page 22]
- Line 11 uses only 1095-A line 33 annual totals; lines 12–23 use only the monthly lines 21–32 — never mix; complete line 11 or lines 12–23, not both. [Form 8962 Instructions (2025), Page 23]
- Line 2b only for dependents required to file; "If you are not required to complete line 2b, enter your modified AGI from line 2a on line 3." [Form 8962 Instructions (2025), Page 22]
- Line 26 amount must land on Schedule 3 (Form 1040), line 9; line 29 amount must land on Schedule 2 (Form 1040), line 1a. [Form 8962 Instructions (2025), Page 23]
- Line 6 of the 2025 form is "Reserved for future use"; Form 8962 filers cannot file Form 1040-SS. [Form 8962 (2025), Line 6; Form 8962 Instructions (2025), Page 3]

---

## Your Situation Notes

<!-- Placeholder — confirm against extracted 1095-A and the converged return before relying on these. -->
- **MFJ, ~$36K expected household income, Marketplace coverage all year, no employer coverage, Form 1095-A expected.** Tax family size 2 (no dependents assumed) → Georgia uses Table 1-1: line 4 = $20,440. Illustrative Python run (scripts, not prose, per Rule 3): $36,000 ÷ $20,440 → line 5 = **176** (truncated), Table 2 applicable figure **0.0104**, line 8a ≈ **$374**/yr — i.e., the household's expected contribution is small and most of the SLCSP premium should be covered by PTC. Recompute with actual line 3 in the engine.
- **Coverage all year with no plan/premium changes expected** → line 10 = "Yes", annual calculation on line 11 from 1095-A line 33; verify columns A and B are constant across lines 21–32 before using it.
- **Repayment exposure if income comes in higher than projected:** at line 5 < 200, excess-APTC repayment is capped at **$750** (MFJ); 200–299 → $1,950; 300–399 → $3,250; 401 → uncapped.
- **Interaction to watch:** if any Marketplace premiums are claimed as a self-employed health insurance deduction (K-1/SE income), the Pub. 974 iterative calculation applies — engine-BLOCK above.
