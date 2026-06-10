---
name: tax-prep
description: "Extract every relevant line value from all user-provided tax documents (W-2s, 1099s, 1098s, 1099-K, etc.) into a structured CSV summary. Runs once at the start of tax filing to build a complete inventory of document values. Triggers on: 'extract my tax docs', 'prepare my tax files', 'let's start my taxes', 'create a tax summary', 'read my W-2s', 'scan my tax documents', 'what do my tax forms say', 'I have my tax docs ready', 'start tax prep', 'pull values from my forms'. Use this skill whenever the user provides tax documents and wants values extracted, or at the beginning of any tax filing workflow — even if they just say something like 'I got my W-2' or 'here are my tax docs'."
---

# tax-prep

Document extraction and inventory — the data intake phase that runs **before** `/tax-cheatsheet`. Reads every tax document the user provides, extracts each box/line value, and produces a single CSV at `analysis/tax-doc-summary.csv` that downstream skills reference.

## Session Handoff

Every conversation starts here:

0. Check if `analysis/prior-year-carryovers-*.json` files exist — if so, mention which prior years are on file; if not and this is a new session, ask whether the user has 2023/2024 returns to ingest (see Prior-Year Returns Workflow below)
1. Check if `analysis/tax-doc-summary.csv` already exists
2. If it exists:
   - Count distinct documents and total rows
   - Report: "You have N documents with M extracted values. Here's what's on file:" followed by a summary table of documents and row counts
   - Ask: "Do you have new documents to add, or shall we move to `/tax-cheatsheet`?"
3. If it does not exist:
   - Tell the user: "No extraction file found. Let's build one. Please share your tax documents (W-2s, 1099s, 1098s, etc.) or point me to a folder."
4. If no documents have been provided yet, wait for the user to share them before proceeding

## Supported Document Types

When extracting, consult this table to know which boxes matter for each form. Extract **every populated box** — the table below highlights the most important ones and their downstream use.

| Form | Key Boxes | Description | Downstream Use |
|------|-----------|-------------|----------------|
| **W-2** | 1, 2, 3, 4, 5, 6, 12a–12d, 14, 15–20 | Wages, withholding, Medicare, state/local | 1040 Lines 1a, 25a; Schedule A (SALT); Form 8959 |
| **1099-INT** | 1, 3, 8, 13 | Interest income (taxable, savings bond, tax-exempt, FATCA) | 1040 Lines 2a, 2b; Schedule B |
| **1099-DIV** | 1a, 1b, 2a, 2b, 5, 7, 12, 13 | Dividends, capital gain distributions, exempt interest | 1040 Lines 3a, 3b; Schedule B; Schedule D |
| **1099-B** | 1d, 1e, 1f, 1g | Proceeds, cost basis, accrued market discount, wash sale adj | Schedule D; Form 8949 |
| **1099-K** | 1a, 5a–5l | Gross payment amount, monthly breakdown | Schedule C Line 1 |
| **1098** | 1, 2, 4, 5, 6 | Mortgage interest, points, PMI, property tax, acquisition debt | Schedule A Lines 8a–10 |
| **1098-E** | 1 | Student loan interest paid | Schedule 1 Line 21 |
| **1098-T** | 1, 2, 5 | Tuition, amounts billed, scholarships | Education credits |
| **1099-R** | 1, 2a, 2b, 4, 7 | Retirement distributions, taxable amount, distribution code | 1040 Lines 4a–5b |
| **1099-G** | 1, 5 | State tax refund, unemployment compensation | Schedule 1 Lines 1, 7 |
| **1099-NEC** | 1, 4 | Non-employee compensation, federal tax withheld | Schedule C; 1040 Line 25a |
| **1099-MISC** | 1, 2, 4 | Rents (from property managers), royalties, withholding | Schedule E Line 3 |
| **1099-SA** | 1, 2, 3 | HSA/MSA distributions, earnings, gross distribution | Form 8889 |
| **1095-C** | 14–16 | Health coverage verification | ACA compliance (reference only) |
| **W-2G** | 1, 4, 7 | Gambling winnings, withholding, state winnings | Schedule 1; 1040 Line 25a |

For **1099-B statements with many transactions** (e.g., dozens of stock trades), extract aggregate totals per category (short-term covered, long-term covered, etc.) rather than individual transactions. Record one summary row per category with total proceeds, total basis, and total gain/loss.

### Rental Property Records (Schedule E)

Most rental data does NOT arrive on IRS forms. For each rental property (including those held in single-member LLCs — disregarded entities report on the owner's return), extract from property-manager annual statements, mortgage 1098s, county property tax bills, and the user's expense log:

- **Document label:** `Rental (address - LLC name if any)`, e.g., `Rental (456 Oak Ave - Oak LLC)` — the `Rental` prefix is what `completeness_check.py` keys on
- **box_or_line:** the Schedule E line the value belongs to (`Line 3` rents received, `Line 7` cleaning/maintenance, `Line 9` insurance, `Line 11` management fees, `Line 12` mortgage interest, `Line 14` repairs, `Line 16` taxes, `Line 17` utilities, `Line 19` other)
- Also record per property (as text-value rows): date placed in service, building cost basis, land value, prior accumulated depreciation, fair rental days, personal use days, average rental period (short/mid/long-term classification), and whether substantial services are provided
- A 1099-MISC from a property manager records under its own `1099-MISC (...)` label; reconcile its Box 1 against the management statement gross rents

*(Source: schedule-e-guide.md; rental-depreciation.md)*

## Extraction Workflow

For each document the user provides:

1. **Identify the form type** — Read the document header/title to determine which IRS form it is (W-2, 1099-INT, etc.)
2. **Consult the Supported Document Types table** above for which boxes to extract
3. **Extract every populated box** — Read each box value carefully. For dollar amounts, preserve cents (e.g., `12345.67`). For text fields (distribution codes, checkboxes), record the text value.
4. **Record to CSV** — Add one row per box value to `analysis/tax-doc-summary.csv` using the format below. Use RFC 4180 quoting for descriptions that contain commas.
5. **Label the document** — Use format: `FormType (Name - Payer)` e.g., `W-2 (Jane Doe - Acme Corp)` or `1099-INT (First National Bank)`. If the name is redacted, use the payer/institution name alone.
6. **Repeat** for all documents provided
7. **Run validation** — After all documents are processed, run `validate_extraction.py` (see Validation below)
8. **Present results** — Show the user a summary table: document name, number of values extracted, any validation warnings
9. **Ask**: "Are there any other tax documents you haven't shared yet? (W-2s from other employers, 1099s from banks/brokerages, 1098 mortgage forms, K-1s, etc.)"

### Handling Unreadable Documents

If a document cannot be read (low-quality scan, password-protected PDF, unsupported format):
- Tell the user: "I can't read [filename] — it appears to be [reason]. Could you provide a clearer copy, or enter the values manually?"
- Offer a template: "Here are the boxes I'd need for a [form type]:" followed by the relevant rows from the Supported Document Types table

## Prior-Year Returns Workflow (2023 / 2024)

When the user provides prior-year returns or asks to "ingest prior years" (full design: `docs/PRIOR-YEAR-DATA.md`):

1. **Locate the returns.** Look in `my-tax-docs/prior-years/` for federal 1040 + GA 500 PDFs, or accept a pre-extracted `prior-year-carryovers-<year>.json` produced by the user's local Hermes Agent (request template: `templates/hermes-extraction-request.md`).
2. **Extract ONLY schema fields** (template: `templates/prior-year-carryovers-template.json`): carryovers (QBI, capital loss, NOL, suspended passive losses per property), depreciation schedules per asset, amounts applied to the next year, itemized status, GA Form 500 values. **NEVER transcribe SSNs, ITINs/EINs, bank/routing numbers, dates of birth, names, or full addresses** — property street labels only. Amounts as strings with cents.
3. **Write** `analysis/prior-year-carryovers-<year>.json` (gitignored).
4. **Validate** — mandatory before any downstream use:
   ```bash
   python .claude/skills/tax-prep/scripts/validate_prior_year.py '{"json_path": "analysis/prior-year-carryovers-2024.json"}'
   ```
   If `verdict` is `rejected`, report the PII findings/schema errors. For Hermes-produced files, return the offending JSON paths to the user so Hermes can re-extract — never hand-redact PII inside `analysis/`.
5. **Report** which carryovers were found and which downstream skills will use them (suspended passive losses and depreciation → `/tax-cheatsheet` Schedule E; QBI/capital loss → Form 8995/Schedule D; prior-year tax → estimated-tax safe harbor; YoY comparison → `/tax-audit`).
6. **Manual fallback:** if no PDFs and no Hermes file, walk the user through the template field by field (skipping unknowns), then validate the same way.

## CSV Output Format

Output file: `analysis/tax-doc-summary.csv`

| Column | Description | Example |
|--------|-------------|---------|
| `document` | Form type with name/payer | `W-2 (Jane Doe - Acme Corp)` |
| `box_or_line` | Box or line number | `Box 1` |
| `description` | Human-readable label | `Wages, tips, other compensation` |
| `value` | Dollar amount or text value | `125000.00` |
| `source_path` | Relative path to source file | `my-tax-docs/w2-acme-2025.pdf` |

See `templates/tax-doc-summary-template.csv` for a complete example with sample data.

## Validation

After extraction is complete, run the validation script to flag anomalies:

```bash
python .claude/skills/tax-prep/scripts/validate_extraction.py '{"csv_path": "analysis/tax-doc-summary.csv"}'
```

The script checks for common issues: zero withholding, Medicare wages below regular wages, missing cost basis on 1099-B, duplicate entries, and more. It outputs JSON with:
- `validation_results[]` — each check with pass/warning/fail status and detail
- `summary` — counts of checks passed, warnings, and failures
- `document_inventory[]` — per-document count of extracted boxes

**Interpret the results:**
- **All checks passed** — Tell the user: "Extraction looks clean. No anomalies detected."
- **Warnings** — Present each warning and ask the user to confirm the value is correct (e.g., "Your W-2 from Acme shows $0 federal withholding — is that right?")
- **Failures** — Present the issue and ask the user to provide the correct value

## Mandatory Rules

> Full rule definitions are in CLAUDE.md. Skill-specific subset below.

1. **SSN PROTECTION** — Never attempt to reconstruct redacted SSNs from tax documents. If a document contains visible SSNs, do not include them in the CSV.
2. **PYTHON-ONLY MATH** — All calculations run through scripts in `scripts/`. Never perform arithmetic in natural language.
3. **CITATION REQUIRED** — Every tax rule must cite a file in `reference/curated/`. Format: *(Source: filename.md, section)*. If a curated reference file does not exist yet, say: "I cannot verify this from provided IRS materials — check IRS.gov before relying on this."
4. **UNVERIFIED RULES** — If a rule cannot be verified from reference files, say: "I cannot verify this from provided IRS materials — check IRS.gov before relying on this."
5. **BLANK SENSITIVE FIELDS** — Forms saved to `output/` must leave SSN, bank routing, account number, and signature fields BLANK.
6. **NO PII IN CSV** — The CSV must not contain SSNs, account numbers, routing numbers, or other personally identifiable information. If a box contains such data, replace the value with `[REDACTED]` and note it in the description.

## Script Invocation

Scripts live in `.claude/skills/tax-prep/scripts/`. Invoke via:

```bash
python .claude/skills/tax-prep/scripts/<script>.py '<json_input>'
```

Scripts accept a single CLI argument (JSON string) and print a JSON object to stdout. Parse that output — those are the authoritative results.

| Script | Purpose |
|--------|---------|
| `validate_extraction.py` | Validate extracted CSV for anomalies and completeness |
| `validate_prior_year.py` | Validate prior-year carryover JSON: schema + PII scan (rejects SSNs, account-like numbers, blocked keys) |

## Related Skills

- `/tax-cheatsheet` — line-by-line form guidance using the extracted values (run after this skill)
- `/tax-audit` — cross-check completed return against extracted source values
- `/tax-advisor` — next-year tax planning based on this year's data
