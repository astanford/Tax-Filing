# Tax Planning Report

> This example uses **obviously fake data** to demonstrate what a `/tax-advisor` output looks like. No real taxpayer information is included.

---

Based on your 2025 filed return. Filing status: **MFJ**. AGI: **$85,550**.

## Scenario Summary

| # | Strategy | Federal Savings | GA State Savings | Total Savings |
|---|----------|-----------------|---------------|---------------|
| 1 | Max 401(k) — primary | $2,100 | $908 | **$3,008** |
| 2 | Max HSA (family) | $1,026 | $444 | **$1,470** |
| 3 | Increase charitable ($5,000) | $0 | $0 | **$0** |

## Scenario Details

### 1. Max 401(k) — Primary Spouse

**What:** Increase 401(k) elective deferrals from $6,000 to $23,500 (the 2025 limit).

**Impact:**
- Additional pre-tax contribution: $17,500
- Current federal tax: $6,197
- Modified federal tax: $4,097
- **Federal savings: $2,100** (12% marginal rate)
- **GA state savings: $908** (5.19% flat rate)
- **Total annual savings: $3,008** (Georgia has no local income tax)

**Notes:**
- This reduces AGI from $85,550 to $68,050
- Drops you from the 12% bracket to the 12% bracket (stays in same bracket but reduces dollars taxed at 12%)
- Does NOT reduce Medicare wages or Social Security wages
- *(Source: retirement-hsa-limits.md, 401(k) Limits)*
- Verify current contribution limits at irs.gov

### 2. Max HSA (Family Coverage)

**What:** Contribute the full $8,550 family HSA limit (requires HDHP enrollment).

**Impact:**
- HSA contribution: $8,550 (above-the-line deduction)
- Current federal tax: $6,197
- Modified federal tax: $5,171
- **Federal savings: $1,026** (12% marginal rate)
- **GA state savings: $444** (5.19% flat rate)
- **Total annual savings: $1,470** (Georgia has no local income tax)

**Notes:**
- Requires enrollment in a High Deductible Health Plan (HDHP)
- HSA contributions are deductible for federal AND Georgia state taxes
- Funds grow tax-free and can be used for qualified medical expenses
- *(Source: retirement-hsa-limits.md, HSA Limits)*
- Verify HSA eligibility requirements at irs.gov

### 3. Increase Charitable Giving ($5,000)

**What:** Donate an additional $5,000 to qualified charities.

**Impact:**
- **Total savings: $0**

**Why $0:** At AGI $85,550 with the MFJ standard deduction of $31,500, your itemized deductions ($12,000 mortgage + $4,500 real estate tax + $5,000 charitable = $21,500) are still below the standard deduction. The additional charitable contribution does not change your tax.

**Note:** Charitable giving would provide tax savings only if your total itemized deductions exceed $31,500. You would need approximately $15,000 in additional itemized deductions to break even with the standard deduction.

---

## Combined Impact

If you implemented strategies **1 + 2** (max 401(k) + max HSA):

- Current total tax: **$9,391** (federal $6,197 + GA $3,194)
- Projected total tax: **$4,913** (federal $3,071 + GA $1,842)
- **Total annual savings: $4,478**
- Effective rate: 11.0% → 5.7%

*Note: Combined scenario run as a single calculation — not a simple sum of individual scenarios, because bracket interactions matter.*

---

*Disclaimer: This planning report assists with tax planning. It does not constitute tax advice. Verify all contribution limits and eligibility at irs.gov. Consult a qualified tax professional for your specific situation.*
