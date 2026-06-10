---
name: tax-cheatsheet
description: "When the user is working on a specific tax form, generates a line-by-line cheat sheet explaining what each line means, where values come from, which rules apply, and whether each line is relevant to their situation. Also helps organize business expenses for Schedule C and rental property income/expenses for Schedule E (including single-member LLC and short/mid/long-term rentals). Triggers on: 'help me fill out [form name]', 'what goes on line X', 'cheat sheet for Schedule C', 'help with my rentals', 'Schedule E for my LLC', 'does this apply to me', 'explain this form', 'walk me through Form 1040', 'what is line 12a', 'help with Schedule A', 'how do I fill this out', or when user shares a screenshot of a form they're filling out."
---

# tax-cheatsheet

Form-filling companion — generates line-by-line cheat sheets for any tax form the user is working on. Explains what each line means, where the value comes from (referencing the `analysis/tax-doc-summary.csv` produced by `/tax-prep`), which tax rules apply (citing `reference/curated/` files), and whether each line is relevant to the user's situation. Also provides specialized help organizing business expenses for Schedule C.

## Session Handoff

Every conversation starts here:

1. Check if `analysis/tax-doc-summary.csv` exists
2. If it exists:
   - Count distinct documents and total rows
   - Report: "I have your extracted tax data (N documents, M values). Which form would you like help with?"
   - List the most common forms: Form 1040, Schedule A, Schedule B, Schedule C, Schedule D, Schedule 1, Schedule 2, Georgia Form 500
3. If it does NOT exist:
   - Tell the user: "No extracted tax data found. Run `/tax-prep` first to extract your document values, then come back here."
   - Stop — do not proceed without the CSV
4. If the user has already received a cheat sheet in this session, ask: "Would you like to continue with [previous form], or switch to a different form?"

## Supported Forms Table

Use this table to determine which curated reference files to read for each form, and which CSV document types contain the source values.

| Form / Schedule | Curated Reference File(s) | CSV Document Prefix |
|---|---|---|
| Form 1040 (Lines 1–8, Income) | `1040-line-by-line.md`, `investment-income.md` | W-2, 1099-INT, 1099-DIV, 1099-B |
| Form 1040 (Lines 9–11, AGI) | `1040-line-by-line.md`, `student-loan-interest.md` | All |
| Form 1040 (Lines 12–15, Deductions) | `1040-line-by-line.md`, `salt-deduction-2025.md`, `mortgage-interest.md`, `self-employment-qbi.md`, `schedule-1a-deductions.md` | 1098, W-2 |
| Form 1040 (Lines 16–24, Tax/Credits/Other) | `1040-line-by-line.md`, `2025-tax-numbers.md`, `additional-medicare-tax.md` | All |
| Form 1040 (Lines 25–38, Payments/Refund) | `1040-line-by-line.md` | W-2, 1099 |
| Schedule A (Itemized Deductions) | `salt-deduction-2025.md`, `mortgage-interest.md` | 1098, W-2 |
| Schedule B (Interest and Dividends) | `investment-income.md` | 1099-INT, 1099-DIV |
| Schedule C (Business Income) | `schedule-c-guide.md` | 1099-K, 1099-NEC |
| Schedule D / Form 8949 (Capital Gains) | `investment-income.md` | 1099-B, 1099-DIV |
| Schedule E (Rental Real Estate) | `schedule-e-guide.md`, `rental-depreciation.md`, `passive-activity-losses.md` | 1099-MISC, Rental, 1098 |
| Form 4562 (Depreciation) | `rental-depreciation.md` | Rental |
| Form 8582 (Passive Activity Losses) | `passive-activity-losses.md` | Rental |
| Schedule 1 (Additional Income/Adjustments) | `1040-line-by-line.md`, `schedule-c-guide.md`, `schedule-e-guide.md`, `student-loan-interest.md` | 1099-K, 1099-MISC, 1098-E |
| Schedule 1-A (OBBBA Deductions) | `schedule-1a-deductions.md` | W-2 |
| Schedule 2 (Additional Taxes) | `additional-medicare-tax.md`, `niit-form-8960.md`, `2025-tax-numbers.md` | W-2, 1099-INT, 1099-DIV, 1099-B |
| Form 8959 (Additional Medicare Tax) | `additional-medicare-tax.md`, `2025-tax-numbers.md` | W-2 |
| Form 8960 (NIIT) | `niit-form-8960.md`, `2025-tax-numbers.md` | 1099-INT, 1099-DIV, 1099-B, Schedule C result |
| Form 8995 (QBI Deduction) | `self-employment-qbi.md` | Schedule C result |
| Georgia Form 500 | `georgia-500-guide.md`, `2025-tax-numbers.md` | W-2, all |

## Cheat Sheet Generation Workflow

When the user asks about a form (by name, line number, or screenshot):

1. **Identify the form and section.** Parse the user's request to determine which form and which lines they need help with. If a screenshot is provided, read the image and identify the form name, page, and visible line numbers.

2. **Load the CSV.** Read `analysis/tax-doc-summary.csv`. Use `form_line_lookup.py` to pull relevant values.

3. **Consult the reference files.** Using the Supported Forms Table above, read the appropriate curated reference file(s) from `reference/curated/`.

3a. **Check prior-year carryovers.** If `analysis/prior-year-carryovers-*.json` exists, pull the values relevant to this form: QBI carryforward (Form 8995 Line 16 → this year's Line 3/16), capital loss carryforward (Schedule D Lines 6/14), suspended passive losses and depreciation (Schedule E), overpayment applied (1040 Line 26 / GA 500 Line 26), and whether the user itemized last year (state refund taxability, Schedule 1 Line 1). Cite `docs/PRIOR-YEAR-DATA.md` and remind the user to verify against the actual prior return.

4. **Generate the cheat sheet table.** For each line in the requested section, produce a row with these columns:

   | Column | Content |
   |--------|---------|
   | **Line** | The line number (bold if user needs to fill it) |
   | **What It Means** | Plain English explanation from the curated reference |
   | **Your Value** | The value from the CSV, or a calculation result from a script. If not available, show `[Not in CSV]` |
   | **Source Document** | Which CSV document and box provides this value (e.g., "W-2 Box 1") |
   | **Tax Rule** | Citation to the curated reference: *(Source: filename.md, section)* |
   | **Applies?** | **Yes**, **No — Leave blank**, or **Maybe — [explanation]** |

5. **Flag cross-references.** If a line pulls from another schedule or form (e.g., "from Schedule D, Line 16"), add a note below the table:
   > "Line X pulls from [Schedule Y]. Would you like a cheat sheet for that schedule?"

6. **Run scripts for computed values.** When a line requires calculation (not a direct CSV lookup), invoke the appropriate script and present the result. Never do arithmetic in natural language.

7. **Present the cheat sheet** using the output format below.

8. **Save the cheat sheet.** Write the cheat sheet to `analysis/cheatsheet-{form-name}.md` (e.g., `analysis/cheatsheet-schedule-c.md`, `analysis/cheatsheet-form-1040.md`). Use lowercase with hyphens. If the file already exists, overwrite it with the updated version. Tell the user: "Saved to `analysis/cheatsheet-{form-name}.md`."

## Cheat Sheet Output Format

Every cheat sheet follows this structure:

```
## Cheat Sheet: [Form Name] — [Section Name]

Based on your extracted data from `analysis/tax-doc-summary.csv` (N documents, M values).

| Line | What It Means | Your Value | Source Document | Tax Rule | Applies? |
|------|---------------|------------|-----------------|----------|----------|
| ... | ... | ... | ... | ... | ... |

### Cross-References
- Line X pulls from [Schedule Y]. Would you like a cheat sheet for that schedule?

### Notes
- [Any situation-specific observations, e.g., phase-outs that apply, elections to make]

---
*Disclaimer: This cheat sheet assists with tax return preparation. It does not constitute tax advice. Verify all numbers against source documents. Consult a qualified tax professional for your specific situation.*
```

## Standard vs. Itemized Comparison

When the user is working on Form 1040 Line 12a or Schedule A, automatically run the comparison:

1. Gather inputs from the CSV:
   - State/local income tax: Use `form_line_lookup.py` with document_filter "W-2", box_filter "Box 17" (state) and "Box 19" (local), operation "sum"
   - Real estate tax: Use `form_line_lookup.py` with document_filter "1098", box_filter "Box 4"
   - Mortgage interest: Use `form_line_lookup.py` with document_filter "1098", box_filter "Box 1"

2. Run `standard_vs_itemized.py` with the gathered values.

3. Present the comparison:

   | Path | Amount |
   |------|--------|
   | Standard Deduction | $X |
   | Itemized Deductions | $Y |
   | **Recommendation** | **[Standard/Itemized] by $Z** |

4. Show the itemized breakdown (SALT components, mortgage interest, charitable, medical) so the user understands each piece.

## Schedule C / Business Form Workflow

When the user asks about Schedule C or business-related forms, use this specialized workflow:

### Step 1 — Gather Business Records
- Check CSV for 1099-K and 1099-NEC documents
- Use `form_line_lookup.py` to pull gross receipts (1099-K Box 1a)
- Ask about refunds/returns, inventory, and expenses not captured in the CSV

### Step 2 — Reconcile Gross Receipts
- 1099-K gross includes refunds and platform-collected sales tax
- Ask user to confirm refund amounts
- Explain: "Sales tax collected by the platform is a pass-through — it doesn't appear on Schedule C" *(Source: schedule-c-guide.md, 1099-K Reconciliation)*

### Step 3 — Calculate COGS (Part III)
- Walk through Lines 35–42:
  - Line 35: Beginning inventory (year 1 = $0)
  - Line 36: Purchases (raw materials, items for resale)
  - Line 38: Materials and supplies (paint, stain, hardware)
  - Line 40: Other costs
  - Line 42: Ending inventory
- Run `schedule_c_calculator.py` with the COGS inputs

### Step 4 — Categorize Expenses (Part II)
- Present each expense category with what qualifies:
  - Line 9: Car/truck ($0.70/mile for 2025) *(Source: schedule-c-guide.md, Business Expenses)*
  - Line 10: Platform fees (transaction, processing, listing fees)
  - Line 22: Supplies (shipping materials, packaging)
  - Line 27: Other expenses (catch-all)
- Help the user assign their expenses to the correct lines

### Step 5 — Compute Net Profit/Loss
- Run `schedule_c_calculator.py` with all inputs
- Present the complete Schedule C summary:
  - Line 1 (gross) → Line 3 (net receipts) → Line 5 (gross profit) → Line 31 (net P/L)
- Flag downstream effects:
  - If net profit > $400: "SE tax applies — you'll need Schedule SE" *(Source: schedule-c-guide.md, SE Tax Threshold)*
  - If net loss: "No SE tax. Loss reduces AGI on Schedule 1, Line 3" *(Source: schedule-c-guide.md, SE Tax Threshold)*
  - QBI: Report deduction or carryforward *(Source: self-employment-qbi.md)*

### Step 6 — Hobby Loss Check
- If this is year 1 or the business has consecutive losses, note:
  > "Safe harbor: profit in 3 of 5 years. Keep documentation of profit intent." *(Source: schedule-c-guide.md, Hobby Loss Rules)*

### Step 7 — Home Office Assessment
- If the user asks about home office:
  > "Home office deduction cannot increase a net loss. If Schedule C shows a loss, the deduction is limited to $0." *(Source: schedule-c-guide.md, Home Office)*
- Recommend skipping Form 8829 if net loss year

## Schedule E / Rental Property Workflow

When the user asks about Schedule E, rental properties, or their rental LLCs, use this specialized workflow:

### Step 1 — Inventory Properties and Entities
- Check CSV for `Rental (...)` and `1099-MISC (...)` documents
- Check `analysis/prior-year-carryovers-*.json` (validated by `/tax-prep`) for each property's **suspended passive losses** (→ `prior_suspended_loss`) and **asset depreciation schedules** (basis, placed-in-service, prior accumulated depreciation → `schedule_e_calculator.py` inputs). See `docs/PRIOR-YEAR-DATA.md`.
- For each property, confirm: address, owning entity, classification (short-term / mid-term / long-term by average rental period), days rented vs. personal use
- **Single-member LLCs are disregarded** — each LLC's rentals go directly on the owner's Schedule E as if owned personally *(Source: schedule-e-guide.md, Single-Member LLCs)*

### Step 2 — Classify Each Property (this drives everything)
- **Substantial services provided** (regular cleaning, linen, maid service — hotel-like)? → **Schedule C, not E**, and SE tax applies *(Source: schedule-e-guide.md, Schedule C Boundary)*
- **Average rental period ≤ 7 days** (typical STR)? → Not a §469 rental activity: NO $25K allowance; passive unless material participation *(Source: passive-activity-losses.md, Exceptions)*
- **Average ≤ 30 days + significant personal services** (typical furnished MTR)? → Same exception applies *(Source: passive-activity-losses.md, Exceptions)*
- Otherwise → ordinary rental activity, $25K allowance possible with active participation
- Check vacation-home limits: personal use > greater of 14 days / 10% of rental days *(Source: schedule-e-guide.md, Personal Use)*; rented < 15 days → income not reported at all

### Step 3 — Reconcile Income
- Sum management-statement gross rents; reconcile against 1099-MISC Box 1 / platform 1099-K payouts
- All rents received go on Line 3 regardless of information returns

### Step 4 — Categorize Expenses (Lines 5–19)
- Repairs (Line 14) vs. improvements (capitalize → Line 18 depreciation) — triage every large item *(Source: schedule-e-guide.md, Repairs vs Improvements)*
- Mortgage interest Line 12 (from 1098), property taxes Line 16 (DeKalb County bill), management fees Line 11, cleaning Line 7

### Step 5 — Depreciation (Line 18)
- Building: 27.5-yr SL mid-month (residential); **39-yr if transient/hotel-like use** — check STR properties *(Source: rental-depreciation.md)*
- Land is never depreciated — split basis using county assessment ratio
- Run `schedule_e_calculator.py` with basis, placed-in-service date, recovery period
- **Georgia:** bonus depreciation claimed federally must be added back on GA Schedule 1 *(Source: georgia-500-guide.md, Key Structural Facts)*

### Step 6 — Compute and Apply Loss Limits
- Run `schedule_e_calculator.py` with all properties; it computes per-property Line 21, the simplified Form 8582 ($25K allowance with $100K–$150K MAGI phase-out), suspended carryforwards, and the GA addback
- Flag downstream forms: Form 4562 (first-year assets), Form 8582 (losses), Schedule 1 Line 5

### Step 7 — Downstream Flags
- Net rental income → NIIT exposure (Form 8960) *(Source: niit-form-8960.md)*
- No SE tax on Schedule E rentals *(Source: schedule-e-guide.md)*
- GA: flows through federal AGI to Form 500 Line 8 — no separate GA rental schedule *(Source: georgia-500-guide.md, Line 8)*

## "Does This Apply to Me?" Workflow

When the user asks whether a provision, credit, or deduction applies:

1. **Identify the provision.** Determine exactly which tax rule or line they're asking about.

2. **Look up eligibility criteria** in the relevant curated reference file.

3. **Cross-reference the user's data.** Use `form_line_lookup.py` to check income levels, document types present, and other relevant values from the CSV.

4. **Provide a clear answer:**
   - **Yes** — explain why it applies and what value to enter
   - **No** — explain why not (e.g., "Your MAGI of $X exceeds the $Y phase-out threshold")
   - **Maybe** — explain what additional information is needed to determine applicability

5. **Cite the source:** Always include *(Source: filename.md, section)*.

## Screenshot Handling

When the user shares a screenshot of a form they're filling out:

1. **Read the image** and identify:
   - Which form (Form 1040, Schedule A, etc.)
   - Which page/section is visible
   - Which line numbers are shown
2. **Confirm with the user:** "I see this is [Form X], Lines [Y–Z]. Is that correct?"
3. **Generate a cheat sheet** for exactly those lines (not the entire form).
4. **If values are already filled in** on the screenshot, compare them against the CSV data and flag any discrepancies: "Line X shows $A on your form but $B in your extracted data — please verify."

## Handling Partial Information

Not all lines will have data available. Handle gracefully:

- **Value not in CSV:** Show `[Not in CSV]` in the Your Value column and note: "Check if you have a document for this (e.g., Form 1099-R for retirement distributions)."
- **Value requires user input:** Show `[Ask user]` and pose the specific question (e.g., "Did you purchase a vehicle in 2025?")
- **Value requires another form first:** Show `[See Schedule X]` and offer to generate that schedule's cheat sheet.
- **Curated reference doesn't cover this rule:** Use the unverified disclaimer: "I cannot verify this from provided IRS materials — check IRS.gov before relying on this."
- **Partial completion:** Summarize what can be filled now vs. what's missing: "You can fill Lines 1–5 now. Line 6 needs your property tax bill — we'll come back to that."

## Mandatory Rules

> Full rule definitions are in CLAUDE.md. Skill-specific subset below.

1. **SSN PROTECTION** — Never attempt to reconstruct redacted SSNs from tax documents. If a document contains visible SSNs, do not include them in output.
2. **PYTHON-ONLY MATH** — All calculations run through scripts in `scripts/`. Never perform arithmetic in natural language. Use the scripts for any addition, subtraction, multiplication, division, or comparison of dollar values.
3. **CITATION REQUIRED** — Every tax rule must cite a file in `reference/curated/`. Format: *(Source: filename.md, section)*. If a curated reference file does not exist for a particular rule, say: "I cannot verify this from provided IRS materials — check IRS.gov before relying on this."
4. **UNVERIFIED RULES** — If a rule cannot be verified from reference files, say: "I cannot verify this from provided IRS materials — check IRS.gov before relying on this."
5. **BLANK SENSITIVE FIELDS** — Forms saved to `output/` must leave SSN, bank routing, account number, and signature fields BLANK.
6. **NO PII IN SKILL FILES** — No personal information in the SKILL.md or scripts.

## Script Invocation

Scripts live in `.claude/skills/tax-cheatsheet/scripts/`. Invoke via:

```bash
python .claude/skills/tax-cheatsheet/scripts/<script>.py '<json_input>'
```

Scripts accept a single CLI argument (JSON string) and print a JSON object to stdout. Parse that output — those are the authoritative results.

| Script | Purpose |
|--------|---------|
| `form_line_lookup.py` | Look up and sum values from the tax-doc-summary CSV by document type and box |
| `standard_vs_itemized.py` | Compare standard deduction vs. itemized, accounting for SALT cap and phase-out |
| `schedule_c_calculator.py` | Compute Schedule C lines: COGS, expenses, net profit/loss, SE tax flag, QBI |
| `schedule_e_calculator.py` | Compute Schedule E per-property lines, depreciation, passive-loss limits ($25K allowance), GA bonus addback |
| `salt_cap_calculator.py` | Compute effective SALT cap with MAGI phase-out |

## Related Skills

- `/tax-prep` — extract document values into CSV (run **before** this skill)
- `/tax-audit` — cross-check completed return against extracted source values (run **after** filling forms)
- `/tax-advisor` — next-year tax planning based on this year's data
