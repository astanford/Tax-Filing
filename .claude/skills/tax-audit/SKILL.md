---
name: tax-audit
description: "After all forms are filled, performs a comprehensive cross-check of the entire tax return against source documents before submission. Catches cross-form errors, math mistakes, withholding mismatches, and missing documents that session-by-session filing misses. Triggers on: 'audit my return', 'final check', 'am I ready to file', 'check everything', 'cross-check my forms', 'verify my return', 'pre-filing review', 'review before I file', 'double check my taxes', 'did I miss anything'."
---

# tax-audit

Comprehensive pre-filing audit — cross-checks the entire completed tax return against source documents in `analysis/tax-doc-summary.csv`. Verifies all math through Python scripts, checks for missing forms and common pitfalls. This should be the **last step before filing**, run after all forms are filled using `/tax-cheatsheet`.

## Session Handoff

Every conversation starts here:

1. Check if `analysis/tax-doc-summary.csv` exists
2. If it exists:
   - Count distinct documents and total rows
   - Report: "I have your extracted tax data (N documents, M values). Ready to audit your completed return."
3. If it does NOT exist:
   - Tell the user: "No extracted tax data found. Run `/tax-prep` first to extract your document values, then fill your forms with `/tax-cheatsheet`, and come back here for the final audit."
   - Stop — do not proceed without the CSV
4. Collect the user's completed form values. Accept them in any of these ways:
   - The user provides values directly — for example:
     ```
     1040 Line 1 wages: $85,000
     1040 Line 2b interest: $1,200
     1040 Line 11 AGI: $98,500
     1040 Line 15 taxable income: $67,000
     1040 Line 16 tax: $7,582
     1040 Line 25a withholding: $12,400
     GA 500 Line 8: $98,500
     GA 500 Line 24: $3,200
     ```
   - The user references completed form files
   - The user reads values from their filled forms
5. Ask for **filing status** if not already known (MFJ, Single, MFS, HoH)
6. Ask which **forms they have completed** (list of form names, e.g., "1040, Schedule A, Schedule D, GA 500")
7. Build the `federal_values` and `state_values` dicts from the user's input (see Input Schema Reference below)

## Audit Checks Table

| # | Category | What It Verifies | Script | Reference File(s) |
|---|----------|-----------------|--------|--------------------|
| 1 | Internal Consistency | Wages, interest, dividends match source docs | `cross_check.py` | `1040-line-by-line.md` |
| 2 | Internal Consistency | Total income = sum of income lines | `cross_check.py` | `1040-line-by-line.md` |
| 3 | Internal Consistency | AGI = total income - adjustments | `cross_check.py` | `1040-line-by-line.md` |
| 4 | Internal Consistency | Taxable income = AGI - deductions | `cross_check.py` | `1040-line-by-line.md` |
| 5 | Math Verification | Tax computed correctly for bracket and filing status | `cross_check.py` | `2025-tax-numbers.md` |
| 6 | Withholding Match | Federal withholding on 1040 = sum of W-2 Box 2 | `cross_check.py` | `1040-line-by-line.md` |
| 7 | Withholding Match | State withholding on GA 500 Line 24 = sum of W-2 Box 17 | `cross_check.py` | `georgia-500-guide.md` |
| 8 | Cross-Return Consistency | Federal AGI matches GA 500 Line 8 | `cross_check.py` | `georgia-500-guide.md` |
| 8a | Cross-Form Consistency | Schedule E Line 26 matches Schedule 1 Line 5 (when rentals present) | `cross_check.py` | `schedule-e-guide.md` |
| 9 | Document Completeness | Every CSV document reflected in filed forms | `completeness_check.py` | All |
| 10 | Missing Forms | Required schedules filed based on income types | `completeness_check.py` | `investment-income.md`, `schedule-c-guide.md`, `additional-medicare-tax.md` |
| 11 | Common Mistakes | 14 known pitfalls verified | Manual review | `docs/KNOWN-PITFALLS.md` |
| 12 | Estimated Payments | Entered amounts match actual payments | Manual review | `1040-line-by-line.md` |

## Audit Workflow

### Step 1 — Gather Inputs

Load `analysis/tax-doc-summary.csv` and count documents. Collect the user's federal form values (`federal_values` dict), state form values (`state_values` dict), filing status, and list of completed forms. See Input Schema Reference for the exact keys needed.

### Step 2 — Run Cross-Check Script

Invoke `cross_check.py` to verify internal consistency, withholding match, cross-return consistency, and tax bracket verification.

```bash
python .claude/skills/tax-audit/scripts/cross_check.py '{"csv_path": "analysis/tax-doc-summary.csv", "federal_values": {...}, "state_values": {...}, "filing_status": "MFJ"}'
```

Parse the JSON output. Each check returns: `check_name`, `status` (pass/fail/warning), `expected`, `actual`, `difference`, and `detail`.

### Step 3 — Run Completeness Check Script

Invoke `completeness_check.py` to verify document coverage and required forms.

```bash
python .claude/skills/tax-audit/scripts/completeness_check.py '{"csv_path": "analysis/tax-doc-summary.csv", "forms_filed": ["1040", "Schedule A", ...], "filing_status": "MFJ"}'
```

Parse the JSON output. Check `document_coverage` for unmapped documents, `required_forms` for missing schedules, and `orphaned_documents` for unrecognized types.

### Step 4 — Manual Pitfall Review

Read `docs/KNOWN-PITFALLS.md` and walk through each of the 14 pitfalls against the user's values:

1. **AGI includes ALL income** — Verify AGI accounts for wages + interest + dividends + capital gains + Schedule C, not just W-2 wages. *(Source: 1040-line-by-line.md, Income Section)*
2. **Math verified through Python** — Confirm all computed values came from script output, not manual arithmetic. *(Source: CLAUDE.md, Rules)*
3. **State rules differ from federal** — Confirm the GA deduction type matches the federal return (itemize both or standard both), and that GA itemized (Line 12c) = federal Schedule A minus other states' income taxes — Georgia income tax is NOT backed out. *(Source: georgia-500-guide.md, Deduction Section)*
4. **Cross-form references match** — Verify 1040 Line 7 matches Schedule D Line 21, 1040 Line 8 matches Schedule 1 Line 10, etc. *(Source: 1040-line-by-line.md, Income Section)*
5. **W-2 Box 5 >= Box 1** — For each W-2 in CSV, confirm Medicare wages >= regular wages. *(Source: additional-medicare-tax.md, Form 8959 Line-by-Line)*
6. **SALT cap on Schedule A only** — Confirm SALT cap ($40K MFJ) applied to federal Schedule A. GA Line 12a starts from the post-cap federal total. *(Source: salt-deduction-2025.md, Overall SALT Cap; georgia-500-guide.md, Lines 12a–c)*
7. **GA 500 Line 8 = federal AGI** — Already checked by `cross_check.py` (check `fed_state_agi_match`). Line 8 must be federal AGI, NOT federal taxable income. *(Source: georgia-500-guide.md, Line 8)*
8. **Student loan interest phase-out** — If 1098-E exists but MAGI >= $200K (MFJ), deduction must be $0. *(Source: student-loan-interest.md, MAGI Phase-Out)*
9. **QBI = $0 if Schedule C loss** — If Schedule C Line 31 is negative, Form 8995 Line 15 must be $0. *(Source: self-employment-qbi.md, QBI Loss Carryforward)*
10. **Additional Medicare Tax threshold** — Combined W-2 Box 5 > $250K (MFJ) triggers Form 8959 even if neither spouse individually exceeds $200K. *(Source: additional-medicare-tax.md, How Employer Withholding Works)*
11. **Depreciation claimed on every rental** — Depreciation is "allowed or allowable": basis is reduced (and §1250 recapture applies at sale) whether or not it was claimed. Every rental property with a building basis must show Line 18 depreciation. *(Source: rental-depreciation.md, Allowed or Allowable)*
12. **Rental losses vs. MAGI** — If MAGI ≥ $150,000, the $25,000 special allowance is fully phased out: rental-activity losses must be suspended on Form 8582, not deducted. Short-term rentals (avg ≤ 7 days) get NO allowance at any income — material participation decides. *(Source: passive-activity-losses.md, Special $25,000 Allowance; Exceptions)*
13. **STR on the right schedule and recovery period** — Substantial services → Schedule C (with SE tax), not Schedule E. Transient/hotel-like use → 39-year depreciation, not 27.5. *(Source: schedule-e-guide.md, Schedule C Boundary; rental-depreciation.md)*
14. **GA bonus depreciation addback** — If bonus depreciation was claimed federally on rental assets, confirm the GA Form 500 Schedule 1 addition is present (Georgia has not adopted §168(k)). *(Source: georgia-500-guide.md, Key Structural Facts)*

For each pitfall, determine: **PASS** (verified correct), **WARNING** (could not verify — needs user confirmation), or **FAIL** (confirmed incorrect).

### Step 4a — Prior-Year Carryover Review (when prior-year data exists)

If `analysis/prior-year-carryovers-*.json` exists (see `docs/PRIOR-YEAR-DATA.md`), verify each carryover was applied on the current return:

- **QBI carryforward** (prior Form 8995 Line 16) appears on this year's Form 8995
- **Capital loss carryforward** appears on Schedule D Line 6/14
- **Suspended passive losses** per property entered as `prior_suspended_loss` in the Schedule E computation (Form 8582)
- **Depreciation continuity** — each prior-year asset still depreciating this year (no asset silently dropped)
- **Overpayment applied** (prior 1040 Line 36 / GA 500 Line 31) included in this year's 1040 Line 26 / GA 500 Line 26
- **State refund taxability** — if the user itemized last year and received a GA refund, confirm Schedule 1 Line 1 treatment
- **Year-over-year sanity** — flag swings > 30% in wages, withholding, or AGI vs. prior year as WARNING for user confirmation (legitimate changes pass with explanation)

### Step 5 — Estimated Payments Check

Ask the user: "Did you make estimated tax payments during the year?"

- If **no**: Mark this section as N/A
- If **yes**: Ask for the amounts paid and compare to:
  - 1040 Line 26 (federal estimated payments)
  - GA 500 Line 26 (state estimated payments + Form IT-560 extension payments, if applicable)
  - Flag any discrepancy as WARNING

### Step 6 — Compile Results

Merge all results from Steps 2–5 into the output format below. Apply the verdict logic:

- Any **FAIL** anywhere → **STOP — DO NOT FILE**
- Any **WARNING** (no FAILs) → **REVIEW THESE ITEMS**
- All **PASS** → **READY TO FILE**

## Output Template

Present the audit results in this format:

```markdown
## Tax Audit Report

Audited against `analysis/tax-doc-summary.csv` (N documents, M values).
Filing status: [status]. Forms reviewed: [list].

### 1. Internal Consistency

| Check | Status | Expected | Actual | Diff | Detail |
|-------|--------|----------|--------|------|--------|
| Wages match W-2 | PASS/FAIL | $X | $Y | $Z | ... |
| Interest match 1099-INT | ... | ... | ... | ... | ... |
| Dividends match 1099-DIV | ... | ... | ... | ... | ... |
| Total income sum | ... | ... | ... | ... | ... |
| AGI calculation | ... | ... | ... | ... | ... |
| Taxable income | ... | ... | ... | ... | ... |

### 2. Math Verification

| Check | Status | Expected | Actual | Diff | Detail |
|-------|--------|----------|--------|------|--------|
| Tax bracket verify | PASS/FAIL/WARN | $X | $Y | $Z | ... |

### 3. Withholding Match

| Check | Status | Expected | Actual | Diff | Detail |
|-------|--------|----------|--------|------|--------|
| Federal withholding | ... | ... | ... | ... | ... |
| State withholding | ... | ... | ... | ... | ... |

### 4. Cross-Return Consistency

| Check | Status | Expected | Actual | Diff | Detail |
|-------|--------|----------|--------|------|--------|
| Federal AGI = State AGI | ... | ... | ... | ... | ... |

### 5. Document Completeness

| Document | Type | Status | Maps To |
|----------|------|--------|---------|
| W-2 (Name - Employer) | W-2 | Mapped | 1040, Schedule A |
| ... | ... | ... | ... |

### 6. Missing Forms

| Form | Status | Reason | Filed? |
|------|--------|--------|--------|
| Schedule B | Required | Interest > $1,500 | Yes/No |
| ... | ... | ... | ... |

### 7. Common Mistakes Review

| # | Pitfall | Status | Detail |
|---|---------|--------|--------|
| 1 | AGI includes all income | PASS | Verified: AGI = wages + interest + dividends + ... |
| ... | ... | ... | ... |

### 8. Estimated Payments

| Check | Status | Detail |
|-------|--------|--------|
| Federal estimated (Line 26) | PASS/N/A | ... |
| State estimated (Line 41) | PASS/N/A | ... |

---

### Verdict

**[VERDICT]**

[Summary paragraph]

- Total checks: N
- Passed: N
- Warnings: N
- Failed: N

---
*Disclaimer: This audit assists with tax return preparation. It does not constitute tax advice. Verify all results against source documents. Consult a qualified tax professional for your specific situation.*
```

**Verdict values:**
- **READY TO FILE** — All checks passed. Return appears consistent and complete.
- **REVIEW THESE ITEMS** — N items need review before filing. See WARNING items above.
- **STOP — DO NOT FILE** — N critical errors found. Do NOT file until resolved.

## Input Schema Reference

### federal_values

Collect these key 1040 line values from the user:

| Key | Form Line | Description |
|-----|-----------|-------------|
| `line_1_wages` | 1040 Line 1 | Total wages from all W-2s |
| `line_2b_interest` | 1040 Line 2b | Taxable interest |
| `line_3b_dividends` | 1040 Line 3b | Ordinary dividends |
| `line_7_capital_gain` | 1040 Line 7 | Capital gain or loss |
| `line_8_other_income` | 1040 Line 8 | Other income (Schedule 1) |
| `line_9_total_income` | 1040 Line 9 | Total income |
| `line_10_adjustments` | 1040 Line 10 | Adjustments to income |
| `line_11_agi` | 1040 Line 11 | Adjusted gross income |
| `line_12a_deduction` | 1040 Line 12a | Standard or itemized deduction |
| `line_13a_qbi` | 1040 Line 13a | QBI deduction |
| `line_13b_sched1a` | 1040 Line 13b | Schedule 1-A deductions |
| `line_14_total_deductions` | 1040 Line 14 | Total deductions |
| `line_15_taxable_income` | 1040 Line 15 | Taxable income |
| `line_16_tax` | 1040 Line 16 | Tax |
| `line_25a_w2_withholding` | 1040 Line 25a | W-2 withholding |
| `schedule_e_line_26` | Schedule E Line 26 | Total rental income/(loss) — optional, when rentals present |
| `schedule_1_line_5` | Schedule 1 Line 5 | Rental real estate income from Schedule E — optional |

### state_values

Collect these key GA Form 500 line values:

| Key | Form Line | Description |
|-----|-----------|-------------|
| `line_8_fagi` | GA 500 Line 8 | Federal adjusted gross income |
| `line_24_withholding` | GA 500 Line 24 | Georgia tax withheld (W-2s/1099s) |

Additional state values are helpful but not required for the core checks.

### forms_filed

A list of form names the user has completed. Common values:

`["1040", "Schedule A", "Schedule B", "Schedule C", "Schedule D", "Form 8949", "Schedule 1", "Schedule 1-A", "Schedule 2", "Form 8959", "Form 8995", "GA 500"]`

## Mandatory Rules

1. **Never** attempt to reconstruct redacted SSNs or other PII
2. **All calculations** run through Python scripts — never do arithmetic in natural language
3. Every tax rule **must cite** a file in `reference/curated/` — format: *(Source: filename.md, section)*
4. If a rule cannot be verified from curated references: "I cannot verify this from provided IRS materials — check IRS.gov"
5. Any saved forms must leave SSN, bank routing, account number, and signature fields **blank**
6. No personal information stored in skill files

## Script Reference

| Script | Purpose | Location |
|--------|---------|----------|
| `cross_check.py` | Federal vs state, withholding vs W-2, AGI math, tax bracket verification | `.claude/skills/tax-audit/scripts/` |
| `completeness_check.py` | Document coverage, required forms, orphaned documents | `.claude/skills/tax-audit/scripts/` |

Also available from `/tax-cheatsheet` (do not modify):

| Script | Purpose | Location |
|--------|---------|----------|
| `form_line_lookup.py` | Query CSV by document type and box | `.claude/skills/tax-cheatsheet/scripts/` |
| `standard_vs_itemized.py` | Compare standard vs itemized deduction | `.claude/skills/tax-cheatsheet/scripts/` |
| `schedule_e_calculator.py` | Recompute Schedule E lines, depreciation, passive-loss limits to verify entered values | `.claude/skills/tax-cheatsheet/scripts/` |
| `salt_cap_calculator.py` | SALT cap with MAGI phase-out | `.claude/skills/tax-cheatsheet/scripts/` |

## Related Skills

- `/tax-prep` — Extract document values into CSV (run **first**)
- `/tax-cheatsheet` — Line-by-line form filling help (run **before** this skill)
- `/tax-advisor` — Next-year tax planning based on this year's data (run **after** filing)
