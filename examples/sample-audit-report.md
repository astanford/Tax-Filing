# Tax Audit Report

> This example uses **obviously fake data** to demonstrate what a `/tax-audit` output looks like. No real taxpayer information is included.

---

Audited against `analysis/tax-doc-summary.csv` (4 documents, 20 values).
Filing status: **MFJ**. Forms reviewed: Form 1040, Schedule A, MD 502.

## 1. Income Verification

| Check | Status | Expected (CSV) | Form Value | Diff | Detail |
|-------|--------|-----------------|------------|------|--------|
| Wages match W-2 | **PASS** | $85,000.00 | $85,000.00 | $0.00 | W-2 (Jane Doe - Acme Corp) Box 1 |
| Interest matches 1099-INT | **PASS** | $200.00 | $200.00 | $0.00 | 1099-INT (First National Bank) Box 1 |
| Dividends match 1099-DIV | **PASS** | $350.00 | $350.00 | $0.00 | 1099-DIV (Sample Investments) Box 1a |

## 2. AGI Math

| Check | Status | Expected | Actual | Detail |
|-------|--------|----------|--------|--------|
| Total income (Line 9) | **PASS** | $85,550.00 | $85,550.00 | $85,000 + $200 + $350 |
| Adjustments (Line 10) | **PASS** | $0.00 | $0.00 | No Schedule 1 adjustments |
| AGI (Line 11) | **PASS** | $85,550.00 | $85,550.00 | Line 9 - Line 10 |

## 3. Deduction Verification

| Check | Status | Expected | Actual | Detail |
|-------|--------|----------|--------|--------|
| Standard deduction (Line 12a) | **PASS** | $31,500.00 | $31,500.00 | MFJ standard deduction *(Source: 2025-tax-numbers.md)* |
| QBI deduction (Line 13a) | **PASS** | $0.00 | $0.00 | No Schedule C income |
| Taxable income (Line 15) | **PASS** | $54,050.00 | $54,050.00 | $85,550 - $31,500 |

## 4. Tax Bracket Verification

| Check | Status | Detail |
|-------|--------|--------|
| Tax (Line 16) | **PASS** | $54,050 taxable → $6,197 tax (10% on $23,850 + 12% on $30,200). Matches within $1 tolerance. |

## 5. Withholding Match

| Check | Status | Expected (W-2 sum) | Form Value | Diff |
|-------|--------|---------------------|------------|------|
| Federal withholding (Line 25a) | **PASS** | $9,500.00 | $9,500.00 | $0.00 |
| State withholding (MD 502 Line 40) | **PASS** | $3,850.00 | $3,850.00 | $0.00 |

## 6. Cross-Return Consistency

| Check | Status | Federal AGI | MD 502 Line 1 | Detail |
|-------|--------|-------------|----------------|--------|
| Fed AGI = MD 502 Line 1 | **PASS** | $85,550.00 | $85,550.00 | Exact match |

## 7. Document Completeness

| Check | Status | Detail |
|-------|--------|--------|
| All CSV documents mapped | **PASS** | 4/4 documents have corresponding form entries |
| Required forms present | **PASS** | No Schedule B required (interest < $1,500) |
| Orphaned documents | **PASS** | None |

## 8. Common Pitfalls

| Pitfall | Status | Detail |
|---------|--------|--------|
| AGI includes all income | **PASS** | Wages + interest + dividends = $85,550 |
| Math verified via Python | **PASS** | All computed values from cross_check.py |
| State rules differ from federal | **PASS** | MD 502 uses MD-specific deduction |
| W-2 Box 5 >= Box 1 | **PASS** | $85,000 >= $85,000 |
| SALT cap on Schedule A only | **N/A** | Using standard deduction |
| MD 502 Line 1 = Federal AGI | **PASS** | See Cross-Return check |
| Student loan phase-out | **N/A** | No 1098-E in CSV |
| QBI = $0 if Schedule C loss | **N/A** | No Schedule C |
| Additional Medicare Tax threshold | **PASS** | Combined wages $85,000 < $250,000 MFJ threshold |

---

## Verdict

### **READY TO FILE**

- Total checks: **22**
- Passed: **22**
- Warnings: **0**
- Failed: **0**

All income lines match source documents. All math verified through Python scripts. Withholding matches W-2s. Cross-return consistency confirmed.

---

*Disclaimer: This audit assists with tax return preparation. It does not constitute tax advice. Verify all numbers against source documents. Consult a qualified tax professional for your specific situation.*
