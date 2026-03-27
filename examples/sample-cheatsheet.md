# Sample Cheat Sheet Output

> This example uses **obviously fake data** to demonstrate what a `/tax-cheatsheet` output looks like. No real taxpayer information is included.

---

## Cheat Sheet: Form 1040 — Income (Lines 1–8)

Based on your extracted data from `analysis/tax-doc-summary.csv` (5 documents, 32 values).

| Line | What It Means | Your Value | Source Document | Tax Rule | Applies? |
|------|---------------|------------|-----------------|----------|----------|
| **1a** | Total wages, salaries, and tips from all W-2s. This is your combined gross pay before any deductions. | $85,000.00 | W-2 (Alex Rivera - Acme Widget Co), Box 1 = $85,000.00 | *(Source: 1040-line-by-line.md, Income Section)* | **Yes** |
| 1b | Household employee wages not reported on a W-2. Only if you paid a household employee and didn't issue a W-2. | — | Direct entry | *(Source: 1040-line-by-line.md, Income Section)* | **No — Leave blank** |
| 1c | Tip income not included in Line 1a. Only if you received tips your employer didn't include on your W-2. | — | Form 4137 | *(Source: 1040-line-by-line.md, Income Section)* | **No — Leave blank** |
| 1d–1i | Other wage-type income (Medicaid waivers, dependent care benefits, adoption benefits, Form 8919, disability pensions, combat pay). | — | Various | *(Source: 1040-line-by-line.md, Income Section)* | **No — Leave blank** (none of these apply) |
| **1z** | Sum of Lines 1a through 1i. Your total wages. | $85,000.00 | Calculated: same as 1a (no other wage lines apply) | *(Source: 1040-line-by-line.md, Income Section)* | **Yes** |
| **2a** | Tax-exempt interest. Interest from municipal bonds or tax-exempt funds — reported but not taxed. | $0.00 | No tax-exempt interest in CSV | *(Source: investment-income.md, Interest Income)* | **No — Leave blank** |
| **2b** | Taxable interest from all bank and brokerage accounts. | $200.00 | 1099-INT (First National Bank), Box 1 = $200.00 | *(Source: investment-income.md, Interest Income)* | **Yes** |
| **3a** | Qualified dividends — the portion of your dividends eligible for lower capital gains tax rates (0%/15%/20%). | $275.00 | 1099-DIV (Sample Investments), Box 1b = $275.00 | *(Source: investment-income.md, Dividend Income)* | **Yes** |
| **3b** | Ordinary dividends — total dividends received (includes qualified dividends). | $350.00 | 1099-DIV (Sample Investments), Box 1a = $350.00 | *(Source: investment-income.md, Dividend Income)* | **Yes** |
| 4a/4b | IRA distributions (total and taxable). Only if you took money out of a traditional or Roth IRA. | — | No 1099-R in CSV | *(Source: 1040-line-by-line.md, Income Section)* | **No — Leave blank** |
| 5a/5b | Pensions and annuities (total and taxable). Only if you received pension or annuity payments. | — | No 1099-R in CSV | *(Source: 1040-line-by-line.md, Income Section)* | **No — Leave blank** |
| 6a/6b | Social Security benefits. Only if you received SSA-1099. | — | No SSA-1099 in CSV | *(Source: 1040-line-by-line.md, Income Section)* | **No — Leave blank** |
| **7** | Capital gain or (loss). Net gain/loss from selling stocks, bonds, or other capital assets. | $0.00 | No 1099-B in CSV | *(Source: investment-income.md, Capital Gains)* | **No — Leave blank** (no capital asset sales) |
| **8** | Other income from Schedule 1, Line 10. Includes business income/loss, rental income, unemployment, etc. | $0.00 | [See Schedule 1] | *(Source: 1040-line-by-line.md, Income Section)* | **Maybe** — Do you have any Schedule 1 income (business, rental, alimony, unemployment)? |

### Cross-References

- **Line 7** pulls from Schedule D, Line 16. If you sold any stocks or investments, you'll need Schedule D. Would you like a cheat sheet for Schedule D?
- **Line 8** pulls from Schedule 1, Line 10. If you have business income, student loan interest, or other adjustments, you'll need Schedule 1. Would you like a cheat sheet for Schedule 1?

### Standard vs. Itemized Preview (Line 12a)

Since we're looking at your income section, here's a preview of your deduction comparison for when you reach Line 12a:

| Path | Amount |
|------|--------|
| Standard Deduction (MFJ) | $31,500.00 |
| Itemized Deductions | $12,700.00 |
| **Recommendation** | **Standard by $18,800.00** |

Itemized breakdown: SALT $3,200.00 (property tax only, under $40K cap) + Mortgage interest $9,500.00 + Charitable $0.00 + Medical $0.00. The standard deduction saves you $18,800 more.

*(Source: 2025-tax-numbers.md, Standard Deduction; salt-deduction-2025.md, Overall SALT Cap)*

### Notes

- **Schedule B not required:** Your taxable interest ($200) is under $1,500. *(Source: investment-income.md, Schedule B Required)*
- **Qualified dividends:** Your $275 in qualified dividends will be taxed at the 0% or 15% rate (depending on taxable income), not your ordinary rate. *(Source: investment-income.md, QDCG Rates)*

---

*Disclaimer: This cheat sheet assists with tax return preparation. It does not constitute tax advice. Verify all numbers against source documents. Consult a qualified tax professional for your specific situation.*
