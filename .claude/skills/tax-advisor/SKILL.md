---
name: tax-advisor
description: "After filing, analyzes the completed return and recommends actions to reduce tax liability for the next year. Runs what-if scenarios showing the dollar impact of each recommendation on federal and Georgia state taxes. Triggers on: 'what should I do differently next year', 'how to reduce my taxes', 'tax planning', 'what if I maxed my 401k', 'tax optimization', 'next year tax strategy', 'reduce my tax bill', 'tax savings opportunities', 'should I change my withholding', 'how much would I save'."
---

# tax-advisor

Post-filing tax planning — analyzes this year's completed return and models what-if scenarios to quantify the dollar impact of tax-saving strategies. This is the **last skill in the workflow**, run after filing to plan for next year. Uses data from `analysis/tax-doc-summary.csv` and the user's filed return values to feed `what_if.py`.

## Session Handoff

Every conversation starts here:

1. Check if `analysis/tax-doc-summary.csv` exists
2. If it exists:
   - Count distinct documents and total rows
   - Report: "I have your extracted tax data (N documents, M values). Ready to run tax planning scenarios."
3. If it does NOT exist:
   - Tell the user: "No extracted tax data found. Run `/tax-prep` first to extract your document values, then file your return with `/tax-cheatsheet` and `/tax-audit`, and come back here for planning."
   - Stop — do not proceed without the CSV
4. If the user has already run `/tax-audit`, offer to reuse those filed return values as the baseline. If `analysis/prior-year-carryovers-*.json` exists, also use it for year-over-year comparison and the estimated-tax safe-harbor reference (prior-year total tax — verify the 100%/110% safe-harbor rules on IRS.gov; not yet in a curated file)
5. Otherwise, collect the baseline data from the user:
   - Filing status
   - Wages (primary and spouse, both W-2 Box 1 and Box 5 Medicare wages)
   - Interest, dividends (ordinary and qualified), capital gains
   - Schedule C net profit/loss
   - Deduction components (mortgage interest, state/local tax, real estate tax, charitable)
   - Retirement contributions already made (401k, IRA, HSA)
   - Number of dependents (for the GA $4,000/dependent exemption)
   - US obligation interest (GA Schedule 1 subtraction)
   - QBI carryforward from current year (if any)
6. Ask which scenarios to explore, or offer to run all scenarios

## Scenario Table

| # | Scenario | What It Models | Script Parameter | Timing | Reference File(s) |
|---|----------|---------------|------------------|--------|-------------------|
| 1 | Max 401(k) primary | Primary spouse contributes $23,500 pre-tax | `max_401k` | Plan for next year | `retirement-hsa-limits.md` |
| 2 | Max 401(k) spouse | Spouse contributes $23,500 pre-tax | `max_401k_spouse` | Plan for next year | `retirement-hsa-limits.md` |
| 3 | Max 401(k) both | Both spouses max out 401(k) | `max_401k_both` | Plan for next year | `retirement-hsa-limits.md` |
| 4 | Traditional IRA | $7,000 IRA contribution (checks deductibility) | `add_ira` | Before deadline (Apr 15) | `retirement-hsa-limits.md` |
| 5 | Traditional IRA spouse | Spouse $7,000 IRA contribution | `add_ira_spouse` | Before deadline (Apr 15) | `retirement-hsa-limits.md` |
| 6 | Max HSA (family) | $8,550 family HSA contribution | `max_hsa` | Before deadline (Apr 15) | `retirement-hsa-limits.md` |
| 7 | Increase charitable | $10,000 charitable contributions | `increase_charitable` | Plan for next year | `2025-tax-numbers.md` |
| 8 | Donor-advised fund | Large one-time $25,000 DAF contribution | `charitable_daf` | Plan for next year | `2025-tax-numbers.md` |
| 9 | Adjust withholding | Target $0 refund/balance due | `adjust_withholding` | Plan for next year | `2025-tax-numbers.md` |
| 10 | Increase Schedule C revenue | Model business becoming profitable | `increase_schedule_c_revenue` | Plan for next year | `schedule-c-guide.md`, `self-employment-qbi.md` |
| 11 | Add Schedule C expenses | Additional business deductions | `add_schedule_c_expenses` | Plan for next year | `schedule-c-guide.md` |

## Advisor Workflow

### Step 1 — Build Baseline

Reconstruct the baseline from the user's filed return. Use `form_line_lookup.py` from `/tax-cheatsheet` to pull values from the CSV where possible:

```bash
python .claude/skills/tax-cheatsheet/scripts/form_line_lookup.py '{"csv_path": "analysis/tax-doc-summary.csv", "document_filter": "W-2", "box_filter": "Box 1", "operation": "sum"}'
```

Build the baseline JSON dict with all fields from the Input Schema Reference below. Key extraction mappings:

| Baseline Field | CSV Source | Script Query |
|---------------|-----------|-------------|
| `wages_primary` | W-2 Box 1 (primary) | `document_filter: "W-2 (primary name)"`, `box_filter: "Box 1"` |
| `wages_spouse` | W-2 Box 1 (spouse) | Same with spouse name |
| `medicare_wages_primary` | W-2 Box 5 (primary) | `box_filter: "Box 5"` |
| `medicare_wages_spouse` | W-2 Box 5 (spouse) | Same with spouse name |
| `interest` | 1099-INT Box 1 | `document_filter: "1099-INT"`, `box_filter: "Box 1"`, `operation: "sum"` |
| `dividends_ordinary` | 1099-DIV Box 1a | `document_filter: "1099-DIV"`, `box_filter: "Box 1a"`, `operation: "sum"` |
| `capital_gain` | User's filed 1040 Line 7 | Ask user (Schedule D result) |
| `schedule_c_net` | User's filed Schedule C Line 31 | Ask user |
| `mortgage_interest` | 1098 Box 1 | `document_filter: "1098"`, `box_filter: "Box 1"`, `operation: "sum"` |
| `state_local_tax` | W-2 Box 17 (all) | `document_filter: "W-2"`, `box_filter: "Box 17"`, `operation: "sum"` |
| `real_estate_tax` | 1098 Box 4 | `document_filter: "1098"`, `box_filter: "Box 4"` |

### Step 2 — Run Scenarios

For each scenario the user wants to explore, invoke `what_if.py`:

```bash
python .claude/skills/tax-advisor/scripts/what_if.py '{"baseline": {...}, "scenario": {"name": "max_401k_both", "retirement_contributions_primary": "23500", "retirement_contributions_spouse": "23500"}}'
```

Parse the JSON output. Each result contains `baseline`, `modified`, `savings`, and `notes`.

### Step 3 — Prioritize Results

Sort all scenario results by `savings.total_tax` (descending — largest savings first). Group into:
1. **Actionable before filing deadline** — IRA contributions, HSA contributions (can still be made for prior tax year before April 15)
2. **Plan for next year** — 401(k) enrollment, charitable strategy, withholding adjustment, business optimization

### Step 4 — Present Results

Use the Output Template below. For each scenario:
1. Explain what it is and who it applies to, citing the relevant curated reference file
2. Show the dollar impact from the script output
3. Note any phase-outs or limitations at the user's income level (from the `notes` array)
4. Clearly mark timing: "Still do before April 15" vs "Plan for next year"

### Step 5 — Combined Analysis

If the user wants to see the combined impact of multiple strategies, run a single combined scenario through `what_if.py` (not a sum of individual savings — tax is nonlinear):

```bash
python .claude/skills/tax-advisor/scripts/what_if.py '{"baseline": {...}, "scenario": {"name": "custom", "retirement_contributions_primary": "23500", "retirement_contributions_spouse": "23500", "hsa_contributions": "8550", "charitable": "10000"}}'
```

## Input Schema Reference

### baseline

Collect these values from the user's filed return and extracted CSV:

| Key | Source | Description |
|-----|--------|-------------|
| `filing_status` | User input | `MFJ`, `Single`, `MFS`, or `HoH` |
| `wages_primary` | W-2 Box 1 (primary) | W-2 wages after any existing 401(k) |
| `wages_spouse` | W-2 Box 1 (spouse) | Spouse W-2 wages |
| `medicare_wages_primary` | W-2 Box 5 (primary) | Medicare wages (before 401(k) reduction) |
| `medicare_wages_spouse` | W-2 Box 5 (spouse) | Spouse Medicare wages |
| `interest` | 1099-INT Box 1 sum | Total taxable interest |
| `dividends_ordinary` | 1099-DIV Box 1a sum | Total ordinary dividends |
| `dividends_qualified` | 1099-DIV Box 1b sum | Qualified dividends (for reference) |
| `capital_gain` | 1040 Line 7 | Net capital gain or loss |
| `schedule_c_net` | Schedule C Line 31 | Net business profit or loss |
| `schedule_e_net` | Schedule E Line 26 | Allowed rental income/(loss) after Form 8582 limits (from `schedule_e_calculator.py`); no SE tax applies |
| `other_income` | 1040 Line 8 | Other income (Schedule 1) |
| `adjustments` | Other adjustments | Other Schedule 1 adjustments |
| `retirement_contributions_primary` | Current 401(k) | Primary current 401(k) contribution |
| `retirement_contributions_spouse` | Current 401(k) | Spouse current 401(k) contribution |
| `hsa_contributions` | Current HSA | Current HSA contribution |
| `mortgage_interest` | 1098 Box 1 | Mortgage interest paid |
| `state_local_tax` | W-2 Box 17 sum | State/local income tax paid |
| `real_estate_tax` | 1098 Box 4 | Property tax paid |
| `charitable` | Schedule A Line 12 | Charitable contributions |
| `medical_expenses` | Schedule A Line 1 | Gross medical expenses |
| `other_itemized` | Schedule A other | Other itemized deductions |
| `us_obligation_interest` | 1099-INT Box 3 | U.S. obligation interest (GA Schedule 1 subtraction) |
| `qbi_carryforward` | Form 8995 Line 16 | QBI loss carryforward from current year |
| `num_dependents` | User input | Number of dependents (GA Line 7c — $4,000 each; default: 0) |

### scenario

| Key | Description |
|-----|-------------|
| `name` | Scenario identifier (see Scenario Table) |
| Additional fields | Override values specific to the scenario |

## Output Template

Present the planning results in this format:

```markdown
## Tax Planning Report

Based on your 2025 filed return (filing status: [status], AGI: $[amount]).

### Still Do Before April 15

| # | Strategy | Federal Savings | State Savings | Total Savings | Note |
|---|----------|-----------------|---------------|---------------|------|
| 1 | [Strategy name] | $X | $Y | $Z | [Key note] |

*If any before-deadline strategies show $0 savings, explain why (e.g., "IRA not deductible at your income level").*

### Plan for Next Year

| # | Strategy | Current → Proposed | Federal Savings | GA State Savings | Total Savings |
|---|----------|-------------------|-----------------|----------------------|---------------|
| 1 | Max 401(k) both | $0 → $47,000 | $X | $Y | $Z |
| ... | ... | ... | ... | ... | ... |

*Ranked by total savings (largest first).*

### Scenario Details

For each scenario:

#### [Scenario Name]

**What:** [One-line explanation]
**Who it applies to:** [Eligibility check at user's income level]
**Impact:**
- Current total tax: $X
- Modified total tax: $Y
- **Annual savings: $Z** (effective rate: X% → Y%)
**Notes:**
- [Phase-out or limitation notes from script output]
- *(Source: [reference-file.md], [section])*

### Combined Impact

If you implemented [list of recommended strategies]:
- Current total tax: $X
- Projected total tax: $Y
- **Total annual savings: $Z**
- Effective rate: X% → Y%

*Note: Combined savings account for interaction effects — they differ from summing individual scenarios.*

---
*Disclaimer: This analysis assists with tax planning. It does not constitute tax advice. Retirement contribution limits, IRA deductibility phase-outs, and HSA limits should be verified against IRS.gov (see retirement-hsa-limits.md). Consult a qualified tax professional for your specific situation.*
```

**Important output rules:**
- Always show both federal AND state impact — GA's flat 5.19% adds meaningful savings to every AGI-reducing strategy (no local income tax in Georgia)
- When a scenario shows $0 savings, explain why (phase-out, not eligible, etc.)
- When retirement/HSA limits are used, include the verification warning from the script's `notes` array
- Round dollar amounts to whole dollars in the summary table; cents in detail sections
- The combined scenario must be run as a single `what_if.py` invocation, not summed

## Mandatory Rules

1. **Never** attempt to reconstruct redacted SSNs or other PII
2. **All calculations** run through `what_if.py` — never do arithmetic in natural language
3. Every tax rule **must cite** a file in `reference/curated/` — format: *(Source: filename.md, section)*
4. If a rule cannot be verified from curated references: "I cannot verify this from provided IRS materials — check IRS.gov"
5. Any saved forms must leave SSN, bank routing, account number, and signature fields **blank**
6. No personal information stored in skill files
7. **Retirement and HSA limits** ($23,500 for 401k, $7,000 for IRA, $8,550 for HSA) are sourced from `retirement-hsa-limits.md`. Every mention must include: "verify against IRS.gov" *(Source: retirement-hsa-limits.md, Verification note)*

## Script Reference

| Script | Purpose | Location |
|--------|---------|----------|
| `what_if.py` | Model tax scenarios, compute dollar savings for federal + GA state | `.claude/skills/tax-advisor/scripts/` |

Also available from other skills (do not modify):

| Script | Purpose | Location |
|--------|---------|----------|
| `form_line_lookup.py` | Query CSV by document type and box | `.claude/skills/tax-cheatsheet/scripts/` |
| `standard_vs_itemized.py` | Compare standard vs itemized deduction | `.claude/skills/tax-cheatsheet/scripts/` |
| `salt_cap_calculator.py` | SALT cap with MAGI phase-out | `.claude/skills/tax-cheatsheet/scripts/` |
| `cross_check.py` | Federal vs state consistency, tax bracket verification | `.claude/skills/tax-audit/scripts/` |

## Related Skills

- `/tax-prep` — Extract document values into CSV (run **first**)
- `/tax-cheatsheet` — Line-by-line form filling help (run **second**)
- `/tax-audit` — Cross-check before filing (run **third**, before this skill)
