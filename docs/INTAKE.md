# Getting ready for tax year 2025

You can start with the documents you have. `/tax-prep` supports adding
documents to an existing extraction. Resolve missing records before
finalizing the return; a passing engine run alone does not prove completeness.

## Private folders

- `my-tax-docs/`: current-year forms and supporting records
- `my-tax-docs/prior-years/`: prior returns and depreciation/carryover schedules
- `analysis/`: extracted values, interview answers, and computed manifest
- `output/`: filled forms and review package

These paths are gitignored. Keep real tax data out of issues, commits, and
examples. Redact SSNs, bank account numbers, and routing numbers from copies
provided for extraction; those fields are not needed by this workflow.

## Gather as available

- W-2s and income statements from banks, brokerages, retirement providers,
  payment platforms, and other payers
- Mortgage statements and supporting deduction records
- Health coverage statements, including Form 1095-A if applicable
- Estimated-payment records and prior-year returns with supporting schedules
- Business income and expense records, if applicable
- Rental income and expenses per property, purchase/closing records,
  land/building allocation, placed-in-service dates, prior depreciation
  schedules, improvement/asset records, rental/personal-use days, and service
  descriptions; see [the rental checklist](SCHEDULE-E-PLAN.md)
- K-1s and accompanying basis, at-risk, and carryover worksheets, if applicable

This is a document-intake list, not a determination of tax treatment. The
interview and audit must establish which records and forms apply.

## Workflow

1. `/tax-prep`: inventory available documents, extract the CSV, validate it,
   and identify missing records. Do not create an empty CSV to imply intake
   has completed.
2. `/tax-cheatsheet`: explain supported form lines from the extracted values.
3. `/tax-interview`: resolve unmapped values and missing inputs, run the
   calculators, and review all engine-blocked items.
4. `/tax-return`: create supported PDFs and the review package.
5. `/tax-audit`: reconcile documents, manifest, and available PDFs before filing.
6. `/tax-advisor`: planning after the return is finalized.

In Codex, the local skill instructions are under `.claude/skills/`; an agent
can read and follow them even when the slash command is not registered.

## PDF prerequisites

The current field map is `engine/field_maps/f1040.json` and expects the
official **2025** Form 1040 at `reference/Raw/f1040.pdf`. Obtain the 2025
edition from IRS.gov and verify the printed year before using it. The file
is intentionally ignored. A current-year PDF with changed fields is not a
safe substitute.

Install the pinned dependencies using the README's local verification
commands. PDF generation also requires read-back and visual verification
as specified by `/tax-return`. Other forms currently need a verified field
map or must be represented by their manifest tables in the review package.

This repository assists with preparation and review; it does not submit
returns. Verify figures against records and obtain qualified review for
unresolved or unsupported items.
