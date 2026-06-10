# Georgia Form 500 — Resident Income Tax Return Guide

## Source
- 2025 IT-511 Individual Income Tax Instruction Booklet, Georgia Department of Revenue (downloaded from dor.georgia.gov; local copy at `reference/Raw/2025-it511-booklet.pdf`), pp. 5, 13–27, 34–36
- 2025 Georgia Form 500 (Rev. 07/09/25), `reference/Raw/2025-ga-form-500.pdf`
- Georgia HB 111 (2025 Session) — income tax rate reduction to 5.19% for tax year 2025
- Georgia DOR, "Income Tax Federal Tax Changes" (dor.georgia.gov/taxes/tax-rules-and-policies/income-tax-federal-tax-changes)

## Applicable To
- **Forms:** GA Form 500 (all lines), Form 500 Schedule 1 (adjustments), Schedule 2 (credits), Schedule 3 (part-year/nonresident), Form IND-CR
- **Workflow Steps:** Step 2 (Investment Income — U.S. obligation interest), Step 10 (Georgia 500)

---

## Rules

### Key Structural Facts

- Georgia has a **flat income tax**: **5.19%** of Georgia taxable income for tax year 2025. [IT-511 (2025), Form 500 Instructions, Line 16, p. 17; HB 111]
- There is **no preferential rate** for capital gains or qualified dividends — all Georgia taxable income is taxed at the flat rate. [IT-511 (2025), Line 16, p. 17]
- Georgia has **no county or city income tax** — Form 500 has no local tax line. [Form 500 (2025)]
- Georgia conforms to the IRC as enacted on or before **January 1, 2025**. Georgia has **NOT adopted the One Big Beautiful Bill Act (OBBBA)** (signed July 4, 2025). Adjustments may be required for federal changes Georgia hasn't adopted (Schedule 1 addition: "Adjustments due to Federal tax changes"). [IT-511 (2025), p. 5]
- Georgia has **not adopted IRC §168(k) bonus depreciation** (30%/50%/100%). Section 179 is adopted at the increased limits but NOT for certain real property. Depreciation differences require Schedule 1 adjustments. [GA DOR, Income Tax Federal Tax Changes]
- Georgia does **not allow the 20% QBI deduction (IRC §199A)** — but because Georgia starts from federal AGI (which excludes the QBI deduction, taken below the line), **no adjustment is needed**. [IT-511 (2025), p. 21]

### Line-by-Line Reference (Key Lines)

#### Setup Section (Page 1)
- **Lines 1–3:** Name, address, SSN, date of birth. (Leave SSN blank in any saved outputs per CLAUDE.md rules.)
- **Line 4:** Residency status: 1 = full-year resident, 2 = part-year, 3 = nonresident. Part-year/nonresidents must complete Schedule 3 and skip Lines 9–14. [IT-511 (2025), p. 15]
- **Line 5:** Filing status (A = Single, B = MFJ, C = MFS, D = HoH/QSS) — must match the federal return. [IT-511 (2025), p. 15]
- **Line 6:** Reserved (no personal exemptions for self/spouse after 12/31/2023). [IT-511 (2025), p. 16]
- **Lines 7a–d:** Dependents. 7a = qualified dependents (federal rules), 7b = unborn dependents, 7c = total (7a + 7b). [IT-511 (2025), p. 16]

#### Income Section
- **Line 8:** Federal AGI from Form 1040 — **NOT federal taxable income**. If Line 8 > $40,000 or less than total W-2 income, attach federal 1040 + Schedule 1. [IT-511 (2025), Line 8, p. 16]
- **Line 9:** Georgia adjustments from Form 500 Schedule 1 (net total — see Additions/Subtractions below). [IT-511 (2025), Line 9, p. 16]
- **Line 10:** Georgia AGI = Line 8 + Line 9. [IT-511 (2025), p. 16]

#### Deduction Section
- **Line 11:** Georgia **standard deduction** (leave blank if you itemize federally):

| Filing Status | 2025 GA Standard Deduction |
|--------------|---------------------------|
| Married filing jointly | **$24,000** |
| Single | **$12,000** |
| Married filing separately | **$12,000** |
| Head of household | **$12,000** |
| Qualifying surviving spouse | **$12,000** |

  [IT-511 (2025), Line 11, p. 16]

  ⚠️ Note: Georgia HoH standard deduction is $12,000 — unlike federal, HoH gets no premium over Single.

- **Deduction lock-in rule:** If you used the **standard deduction federally, you MUST use the Georgia standard deduction**. If you **itemized federally** (or are MFS and your spouse itemizes), you **MUST itemize on the Georgia return** — include a copy of federal Schedule A. [IT-511 (2025), Lines 11 and 12a–c, pp. 16–17]
- **Line 12a:** Itemized deductions from federal Schedule A (total).
- **Line 12b:** Adjustments: **income taxes other than Georgia** (i.e., other states' income taxes deducted on Schedule A) plus investment interest expense for production of income exempt from Georgia tax. Georgia income tax itself is NOT backed out. If federal SALT was limited, prorate: other-state income taxes ÷ total taxes on Schedule A Line 5d × the lesser of Line 5d or the federal limit. [IT-511 (2025), Line 12b, p. 17]
- **Line 12c:** = Line 12a − Line 12b (Georgia itemized deduction).
- **Line 13:** = Line 10 − (Line 11 or 12c).
- **Line 14:** **Dependent exemption = Line 7c × $4,000**. No personal exemption for taxpayer/spouse. [IT-511 (2025), Line 14, p. 17]

#### Tax Computation
- **Line 15a:** Georgia taxable income before NOL = Line 13 − Line 14 (or Schedule 3, Line 14 for part-year/nonresidents).
- **Line 15b:** Georgia NOL utilized — post-2018 NOLs limited to 80% of Georgia income before NOL (worksheet on p. 17). [IT-511 (2025), Lines 15a–b, p. 17]
- **Line 15c:** = Line 15a − Line 15b.
- **Line 16:** **Tax = Line 15c × 5.19%**, rounded to nearest dollar. [IT-511 (2025), Line 16, p. 17]

#### Credits
- **Line 17 (a–c):** **Low Income Credit** — available if federal AGI < $20,000 and you can't be claimed as a dependent. [IT-511 (2025), Line 17, p. 17]
- **Line 18:** **Other state(s) tax credit** — must attach a copy of the other state's return. [IT-511 (2025), Line 18, p. 18]
- **Line 19:** **Georgia Eligible Itemizer Tax Credit** — up to **$300 per taxpayer** for a full-year or part-year resident (183+ days, or living in GA on Dec 31) who itemized. Cannot exceed Line 16 tax. [IT-511 (2025), Line 19, p. 18]
- **Line 20:** IND-CR credits (Series 200, e.g., disabled person home purchase, caregiver, National Guard).
- **Line 21:** Schedule 2 credits (Series 100 — return must be e-filed if claimed).
- **Line 22:** Total credits (Lines 17–21) — cannot exceed Line 16.
- **Line 23:** = Line 16 − Line 22 (zero floor).

#### Payments and Balance Due
- **Line 24:** **Georgia income tax withheld from W-2s (Box 17, state = GA) and 1099s.** Attach the statements or the amount is disallowed. [IT-511 (2025), Line 24, p. 18]
- **Line 25:** Withholding on G2-A, G2-FL, G2-LP, G2-RP (nonresident/pass-through/real estate withholding). [IT-511 (2025), Line 25, p. 18]
- **Line 26:** Estimated tax payments (Form 500-ES) + amounts credited from prior year + Form IT-560 extension payments. [IT-511 (2025), Line 26, p. 18]
- **Line 27:** Schedule 2B refundable credits (e-file required).
- **Line 28:** Total payments = Lines 24–27.
- **Line 29:** Balance due = Line 23 − Line 28 (if positive).
- **Line 30:** Overpayment = Line 28 − Line 23 (if positive).
- **Line 31:** Amount credited to next year's estimated tax.
- **Lines 32–41:** Charitable checkoff donations.
- **Line 42:** Estimated tax penalty (Form 500 UET). [IT-511 (2025), Line 42, p. 19]
- **Line 46 / 46a:** Refund and direct deposit info. (Leave bank fields blank in any saved outputs per CLAUDE.md rules.)

### Schedule 1 — Additions (most common)
- **Interest on non-Georgia municipal bonds** (and mutual fund dividends derived from them). [IT-511 (2025), Additions #1, p. 20]
- **Depreciation differences** — including federal bonus depreciation (§168(k)) not adopted by Georgia. [IT-511 (2025), Additions #4–5, p. 20; GA DOR Federal Tax Changes]
- **Adjustments due to federal tax changes Georgia hasn't adopted** (includes OBBBA items that changed federal AGI). [IT-511 (2025), Additions #5, p. 20]
- **Federal NOL carryover** deducted on the federal return. [IT-511 (2025), Additions #6, p. 20]
- Taxable Path2College 529 withdrawals. [IT-511 (2025), Additions #8, p. 21]

### Schedule 1 — Subtractions (most common)
- **Retirement income exclusion** (complete Schedule 1, page 2; date of birth required):

| Age | Max Exclusion (per qualifying spouse) |
|-----|--------------------------------------|
| 62–64 (or permanently disabled) | **$35,000** |
| 65 or older | **$65,000** |

  Each spouse must qualify separately; jointly-owned income splits 50/50; max **$5,000** of the exclusion may be earned income. Rental/royalty/partnership income NOT subject to SE tax counts as unearned retirement income for the exclusion. [IT-511 (2025), Subtractions #1, p. 21; Retirement Income Exclusion, p. 24]

- **Military retirement exclusion:** up to $17,500 under age 62, plus an additional $17,500 with more than $17,500 of Georgia earned income. [IT-511 (2025), Subtractions #2, p. 21]
- **U.S. Government obligation interest** (T-bills, T-notes, T-bonds, savings bonds) — reduced by attributable expenses. **FNMA, GNMA, and FHLB interest is NOT exempt.** [IT-511 (2025), Subtractions #4, p. 22]
- **Social Security / Railroad Retirement** included in federal AGI. [IT-511 (2025), Subtractions #5, p. 22]
- **Income tax refunds from states other than Georgia** included in federal AGI (do NOT subtract Georgia refunds — but note: Georgia surplus tax refunds are not taxable for Georgia purposes). [IT-511 (2025), Subtractions #9, p. 22; p. 21]
- **Path2College 529 contributions:** up to **$4,000 per beneficiary** ($8,000 MFJ). [IT-511 (2025), Subtractions #15, p. 23]
- **100% of HDHP premiums** not deducted elsewhere. [IT-511 (2025), Subtractions #19, p. 23]
- Organ donation expenses (up to $25,000), combat zone pay, disabled first responder payments, Hurricane Helene relief payments (2025–2029). [IT-511 (2025), Subtractions #17–18, #23, #29, p. 23, p. 25]
- **No deduction** for Georgia ABLE program contributions. [IT-511 (2025), p. 24]

### Filing Requirements
Full-year residents must file if required to file a federal return, if they have income not federally taxed but taxable in Georgia, or if income exceeds the standard deduction ($24,000 MFJ; $12,000 all other statuses). [IT-511 (2025), Filing Requirements, p. 13]

### Estimated Tax
Required if you expect gross income exceeding (dependent exemptions + estimated deductions + $1,000 of income not subject to withholding). Quarterly deadlines: Apr 15 / Jun 15 / Sep 15 / Jan 15. Underpayment penalty computed on Form 500 UET. [IT-511 (2025), Estimated Tax, p. 14; Line 42, p. 19]

---

## Your Situation Notes

<!-- Add notes specific to your filing situation here.
     Example: "Our AGI is ~$X, which means [phase-out/threshold] applies."
     See reference/HOW-TO-CURATE.md for the recommended format. -->
