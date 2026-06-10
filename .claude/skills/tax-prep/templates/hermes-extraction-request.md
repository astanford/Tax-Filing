# Extraction Request: Prior-Year Tax Return → Carryover JSON

*Hand this file (plus one tax-year's return PDFs) to the local extraction
agent (e.g., Hermes Agent). Its output is consumed by an automated
validator — follow the format exactly.*

## Task

Read the attached federal Form 1040 return (with schedules) and Georgia
Form 500 return for ONE tax year. Produce a single JSON document with the
fields below. Output ONLY the JSON — no prose, no markdown fences.

## Redaction Rules (hard requirements — output is machine-rejected on violation)

1. **NEVER include:** Social Security Numbers or ITINs/EINs (any format),
   bank account or routing numbers, dates of birth, phone numbers, email
   addresses, signatures, or taxpayer/spouse/dependent names.
2. Dollar amounts must be strings with cents, e.g., `"185000.00"` —
   never bare integers (a 9+ digit integer is auto-rejected as an
   account-like number).
3. Rental properties are identified ONLY by street label + LLC name,
   e.g., `"Rental (456 Oak Ave - Oak LLC)"` — no city/state/ZIP.
4. If a field is not on the return, use `null` or omit it. Never guess.

## Output Schema

Follow `prior-year-carryovers-template.json` (provided alongside this
request). Field-by-field source map:

### Top level
- `tax_year` — integer, the year of the return being read
- `source` — `"hermes-agent"`
- `filing_status` — `"MFJ" | "Single" | "MFS" | "HoH" | "QSS"` (1040 checkbox)

### `federal` (from Form 1040 and schedules)
- `agi_line_11` — 1040 Line 11
- `taxable_income_line_15` — 1040 Line 15
- `total_tax_line_24` — 1040 Line 24
- `withholding_line_25` — 1040 Line 25d
- `estimated_payments_line_26` — 1040 Line 26
- `refund_line_34` / `balance_due_line_37` — 1040 Lines 34 / 37
- `overpayment_applied_to_next_year_line_36` — 1040 Line 36
- `itemized` — true if Schedule A was filed
- `itemized_total_schedule_a` — Schedule A total (if itemized)
- `salt_deducted_schedule_a_line_5e` — Schedule A Line 5e (if itemized)
- `qbi_carryforward_form_8995_line_16` — Form 8995 Line 16
- `capital_loss_carryforward` — Schedule D capital loss carryover to next
  year (from the carryover worksheet if attached; else null)
- `nol_carryforward`, `charitable_carryforward`, `ira_basis_form_8606` —
  if present on attached statements/Form 8606; else null

### `georgia` (from GA Form 500)
- `ga_taxable_income_line_15c` — Line 15c
- `ga_tax_line_16` — Line 16
- `ga_withholding_line_24` — Line 24
- `ga_estimated_payments_line_26` — Line 26
- `ga_overpayment_applied_to_next_year_line_31` — Line 31
- `ga_refund_line_46` — Line 46
- `ga_nol_carryforward` — remaining GA NOL after Line 15b usage, if shown
- `ga_depreciation_difference_tracking` — net GA/federal depreciation
  difference being tracked (GA Schedule 1 addbacks), if shown

### `state_refund_received_during_current_year`
The state refund actually received (matches what a 1099-G would show).

### `rentals` — one entry per property on Schedule E Part I
- `property_label` — per redaction rule 3
- `classification` — `"long_term" | "mid_term" | "short_term"` (judge from
  the return context; if unknown, use `"long_term"` and note it)
- `suspended_passive_loss_form_8582` — that property's unallowed loss
  from the Form 8582 worksheets (Worksheet 5/6/7); `"0.00"` if none
- `assets[]` — one per line on the depreciation schedule/Form 4562:
  - `description` (e.g., `"Building"`, `"HVAC replacement"`)
  - `placed_in_service` — `"YYYY-MM"`
  - `cost_basis` — depreciable basis
  - `land_value_excluded` — land portion excluded from basis (buildings)
  - `method_recovery` — e.g., `"SL/27.5 MM"`, `"200DB/5"`
  - `prior_accumulated_depreciation` — through the END of this return's year
  - `federal_bonus_claimed` — bonus depreciation taken on this asset (any year)

### `notes`
Array of short free-text strings for anything material that doesn't fit
the schema (e.g., "Form 8582 shows $0 allowed due to MAGI"). No PII.

## Delivery

Name the file `prior-year-carryovers-<tax_year>.json`. It will be placed
in the repo's gitignored `analysis/` folder and validated by
`validate_prior_year.py`; PII or schema violations are returned with
exact JSON paths for correction.
