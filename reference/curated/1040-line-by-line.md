# Form 1040 — Line-by-Line Reference (2025)

## Source
- Instructions for Form 1040 (2025), Catalog Number 24811V, Feb 25, 2026
- Form 1040, U.S. Individual Income Tax Return (2025)

## Applicable To
- **Forms:** Form 1040 (all lines), Schedules 1, 1-A, 2, 3, A, B, C, D
- **Workflow Steps:** Steps 1–9 (all federal steps)

---

## Income Section (Lines 1–8)

| Line | Description | Source / Schedule | Curated Reference |
|------|-------------|-------------------|-------------------|
| **1a** | Total wages, salaries, tips | W-2, Box 1 (both spouses combined) | — |
| 1b | Household employee wages not on W-2 | Direct entry | — |
| 1c | Tip income not on Line 1a | Form 4137 | — |
| 1d | Medicaid waiver payments | Form 1099-MISC/NEC | — |
| 1e | Taxable dependent care benefits | Form 2441, Line 26 | — |
| 1f | Employer-provided adoption benefits | Form 8839, Line 31 | — |
| 1g | Wages from Form 8919 | Form 8919, Line 6 | — |
| 1h | Other earned income | Disability pensions, excess deferrals | — |
| 1i | Nontaxable combat pay election | Military only | — |
| **1z** | **Total wages** | Sum of 1a through 1i | — |
| **2a** | Tax-exempt interest | 1099-INT Box 8 / 1099-DIV Box 12 | investment-income.md |
| **2b** | Taxable interest | 1099-INT Box 1 (all payers) | investment-income.md |
| **3a** | Qualified dividends | 1099-DIV Box 1b | investment-income.md |
| **3b** | Ordinary dividends | 1099-DIV Box 1a | investment-income.md |
| 4a/4b | IRA distributions | Form 1099-R | — |
| 5a/5b | Pensions and annuities | Form 1099-R | — |
| 6a/6b | Social Security benefits | Form SSA-1099 | — |
| **7** | Capital gain or (loss) | Schedule D, Line 16 (or 1099-DIV Box 2a if no Sch D) | investment-income.md |
| **8** | Other income from Schedule 1, Line 10 | Schedule 1 | — |

[Form 1040 Instructions (2025), Pages 23–33]

## Total Income and AGI (Lines 9–11)

| Line | Description | Calculation |
|------|-------------|-------------|
| **9** | Total income | Sum of Lines 1z, 2b, 3b, 4b, 5b, 6b, 7, 8 |
| **10** | Adjustments to income | Schedule 1, Line 26 |
| **11** | **Adjusted Gross Income (AGI)** | Line 9 − Line 10 |
| 11b | Modified AGI (for Schedule 1-A) | Line 11 + certain excluded income |

[Form 1040 Instructions (2025), Page 33]

## Deductions (Lines 12–15)

| Line | Description | Source | Curated Reference |
|------|-------------|--------|-------------------|
| **12a** | Standard deduction OR Itemized (Schedule A, Line 18) | Check box if standard; enter Schedule A total if itemizing | salt-deduction-2025.md, mortgage-interest.md |
| **13a** | Qualified business income deduction (Form 8995) | Form 8995, Line 15 | self-employment-qbi.md |
| **13b** | Schedule 1-A deductions | Schedule 1-A, Line 38 | schedule-1a-deductions.md |
| **14** | Total deductions | Line 12a + 13a + 13b |
| **15** | **Taxable income** | Line 11 − Line 14 (not less than $0) |

[Form 1040 Instructions (2025), Pages 33–35]

**Standard Deduction (2025 MFJ): $31,500** *(See 2025-tax-numbers.md)*

## Tax Computation (Line 16)

| Line | Description | Source | Curated Reference |
|------|-------------|--------|-------------------|
| **16** | Tax | Tax Table, Tax Computation Worksheet, OR Qualified Dividends and Capital Gain Tax Worksheet | 2025-tax-numbers.md |

[Form 1040 Instructions (2025), Pages 35–38]

- If you have qualified dividends (Line 3a > 0) or net capital gain (Schedule D, Line 15 > 0), use the **Qualified Dividends and Capital Gain Tax Worksheet** (or Schedule D Tax Worksheet if applicable).
- The QDCG worksheet applies lower rates (0%/15%/20%) to qualified dividends and long-term capital gains.

## Credits (Lines 17–21)

| Line | Description | Source |
|------|-------------|--------|
| 17 | Credits from Schedule 3, Line 8 | Education, foreign tax, child care, etc. |
| 19 | Child tax credit / credit for other dependents | Schedule 8812 |
| 20 | Amount from Schedule 3, Line 15 | Other credits |
| 21 | Sum of Lines 19 + 20 | |
| **22** | Tax after credits | Line 16 − Line 17 − Line 21 (not less than $0) |

## Other Taxes (Lines 23–24)

| Line | Description | Source | Curated Reference |
|------|-------------|--------|-------------------|
| **23** | Other taxes from Schedule 2, Line 21 | SE tax, Additional Medicare Tax, etc. | additional-medicare-tax.md |
| **24** | **Total tax** | Line 22 + Line 23 |

- **Schedule 2, Line 11:** Additional Medicare Tax (Form 8959).
- **Schedule 2, Line 21:** Total additional taxes → Form 1040, Line 23.

## Payments (Lines 25–33)

| Line | Description | Source |
|------|-------------|--------|
| **25a** | Federal income tax withheld from W-2s | W-2, Box 2 (both spouses) |
| 25b | Federal income tax withheld from 1099s | 1099 forms |
| 25c | Other forms of withholding | W-2G, etc. |
| **25d** | Total federal tax withheld | Sum of 25a + 25b + 25c + Form 8959 withholding credit |
| **26** | Estimated tax payments | Form 1040-ES payments made |
| 27a-c | Earned income credit | If eligible |
| 28 | Additional child tax credit | Schedule 8812 |
| 29 | American opportunity credit | Form 8863 |
| 32 | Net premium tax credit | Form 8962 |
| **33** | **Total payments** | Sum of Lines 25d through 32 |

## Refund or Amount Owed (Lines 34–37)

| Line | Description | Calculation |
|------|-------------|-------------|
| **34** | Overpayment (if Line 33 > Line 24) | Line 33 − Line 24 |
| 35a | Refund (direct deposit or check) | Amount of Line 34 to be refunded |
| 36 | Applied to next year's estimated tax | Amount of Line 34 applied to 2026 |
| **37** | **Amount you owe** (if Line 24 > Line 33) | Line 24 − Line 33 |
| 38 | Estimated tax penalty | Form 2210 (if applicable) |

[Form 1040 Instructions (2025), Pages 39–65]

### Underpayment Penalty (Form 2210)
- May apply if balance owed > $1,000 AND total payments < lesser of:
  - 90% of current year tax, OR
  - 100% of prior year tax ($36,508 in 2024)
- Safe harbor: If payments ≥ 100% of prior year tax, no penalty regardless of current year balance.

---

## Schedule 1 — Key Lines

| Line | Description | Part |
|------|-------------|------|
| **3** | Business income or (loss) from Schedule C | Part I — Income |
| 10 | Total additional income (sum of Part I) | Part I |
| 21 | Student loan interest deduction | Part II — Adjustments |
| 26 | Total adjustments (sum of Part II) → Form 1040, Line 10 | Part II |

## Schedule 2 — Key Lines

| Line | Description |
|------|-------------|
| 11 | Additional Medicare Tax (Form 8959) |
| 21 | Total additional taxes → Form 1040, Line 23 |

---

## Your Situation Notes

<!-- Add notes specific to your filing situation here.
     Example: "Our AGI is ~$X, which means [phase-out/threshold] applies."
     See reference/HOW-TO-CURATE.md for the recommended format. -->

