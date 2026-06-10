# Prior-Year Return Data (2023, 2024)

How prior-year tax returns feed the current-year (2025) workflow without
PII entering the repo or the extracted datasets.

## Why Prior Years Matter

Carryover items that directly change the 2025 return:

| Carryover | From (prior-year form) | Used In (2025) |
|-----------|------------------------|----------------|
| Suspended passive losses (per property) | Form 8582 worksheets | `schedule_e_calculator.py` `prior_suspended_loss`; Schedule E Line 22 |
| Accumulated depreciation + placed-in-service dates (per asset) | Depreciation schedules / Form 4562 | `schedule_e_calculator.py` depreciation inputs; basis tracking |
| QBI loss carryforward | Form 8995 Line 16 | Form 8995; `what_if.py` `qbi_carryforward` |
| Capital loss carryforward | Schedule D / carryover worksheet | Schedule D Line 6/14 |
| Federal NOL carryforward | Prior 1040 records | Schedule 1; GA Schedule 1 addition |
| Georgia NOL carryforward | GA Form 500 Line 15b records | GA 500 Line 15b (80% limit) |
| GA depreciation differences (if bonus claimed federally) | Prior GA Schedule 1 addbacks | GA depreciation tracking *(Source: georgia-500-guide.md, Key Structural Facts)* |
| Overpayment applied to 2025 | 1040 Line 36 / GA 500 Line 31 | 1040 Line 26; GA 500 Line 26 |
| State refund received in 2025 + whether you itemized in 2024 | 1040 Schedule A (2024); 1099-G | Schedule 1 Line 1 taxability |
| IRA basis | Form 8606 | Form 8606 if distributions/conversions |
| Prior-year AGI | 1040 Line 11 | E-file identity verification |
| Prior-year total tax | 1040 Line 24; GA 500 Line 16 | 2025 estimated-tax safe harbor (110%/100% rules — verify on IRS.gov) |

Year-over-year comparison also powers `/tax-audit` sanity checks (income
swings, missing documents vs. last year) and gives `/tax-advisor` a real
baseline.

## File Locations and PII Policy

| What | Where | Committed? |
|------|-------|-----------|
| Prior-year return PDFs (full returns, contain PII) | `my-tax-docs/prior-years/` | **Never** (gitignored via `my-tax-docs/`) |
| Extracted carryover data (amounts only, no PII) | `analysis/prior-year-carryovers-<year>.json` | **Never** (gitignored via `analysis/`) |
| JSON schema + fictional example | `.claude/skills/tax-prep/templates/prior-year-carryovers-template.json` | Yes (no real data) |
| Hermes Agent extraction request | `.claude/skills/tax-prep/templates/hermes-extraction-request.md` | Yes (instructions only) |
| PII/schema validator | `.claude/skills/tax-prep/scripts/validate_prior_year.py` | Yes |

**The PII boundary:** PII (SSNs, bank/routing numbers, signatures, dates
of birth, full names) stays inside the source PDFs in `my-tax-docs/`.
Everything extracted from them — by Claude, by Hermes Agent, or typed in
by you — is restricted to **form-line dollar amounts, dates, statuses,
and property labels**. `validate_prior_year.py` enforces this: it
rejects files containing SSN patterns, 9+ digit account-like numbers,
or blocked field names before any skill consumes the data. Property
street labels (e.g., `Rental (456 Oak Ave - LLC B)`) are allowed — they
match the existing CSV convention and never leave gitignored `analysis/`.

## Three Ingestion Paths (any combination)

### Path A — Claude extracts directly (simplest)
1. Drop the 2023/2024 return PDFs in `my-tax-docs/prior-years/`
2. Run `/tax-prep` and say "ingest my prior-year returns"
3. Claude reads the PDFs, extracts ONLY the fields in the schema (never
   transcribing SSNs, bank numbers, or addresses beyond property labels),
   writes `analysis/prior-year-carryovers-<year>.json`, and runs the
   validator

### Path B — Hermes Agent extracts (keeps PDFs off this machine if desired)
1. Give your Hermes Agent the return PDFs plus
   `.claude/skills/tax-prep/templates/hermes-extraction-request.md`
   (it contains the exact field list, redaction rules, and output schema)
2. Hermes produces `prior-year-carryovers-<year>.json`
3. Drop the JSON in `analysis/`; Claude runs `validate_prior_year.py` —
   any PII pattern rejects the file with a list of offending paths so
   Hermes (or you) can fix and resubmit

### Path C — Manual entry
1. Run `/tax-prep` and say "enter prior-year data manually"
2. Claude walks through the schema field by field (you can skip unknowns)
3. Same validation applies

## Validation

```bash
python .claude/skills/tax-prep/scripts/validate_prior_year.py '{"json_path": "analysis/prior-year-carryovers-2024.json"}'
```

Checks: required fields present, amounts Decimal-parseable, tax_year
sane, **PII scan** (SSN patterns `xxx-xx-xxxx`, standalone 9–17 digit
account/routing-like numbers, blocked keys: ssn, social, routing,
account_number, bank, dob, birth, signature, phone, email), and
schema-shape checks for the rentals array. Verdict: `accepted` or
`rejected` with reasons.

## How the Data Is Used Downstream

- **/tax-prep** — after extraction, reports which carryovers were found
- **/tax-cheatsheet** — pulls `rentals[].suspended_passive_loss` and
  `rentals[].assets[]` into `schedule_e_calculator.py`; QBI carryforward
  into Form 8995 guidance; capital loss carryforward into Schedule D
- **/tax-audit** — verifies carryovers were applied (QBI, capital loss,
  suspended passive), checks the state-refund taxability question, and
  flags >30% year-over-year swings in wages/withholding/AGI for review
- **/tax-advisor** — uses prior-year totals as the comparison baseline
  and the estimated-tax safe harbor reference

## Disclaimer

Prior-year extraction assists with carryover tracking. Verify every
carryover against the actual prior-year forms before filing. Consult a
qualified tax professional for your specific situation.
