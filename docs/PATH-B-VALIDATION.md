# Path B Validation Findings

*Date: 2026-06-22*

Validation of Claude Fable's prior-year ingestion artifacts before building
the `ingest/` subsystem. Verdicts: **GO** (sound as-is), **FIX** (gap found
and corrected here), **NO-GO** (needs redesign). All test fixtures use
fabricated data per Rule 4.

## PII firewall — `validate_prior_year.py` (`pii_scan`)

**Verdict:** GO

Covered by `tests/test_pii_firewall.py`: clean data passes; dashed SSNs,
bare 9+ digit account-like integers, long digit runs, every blocked key
fragment, and array-nested PII are all rejected; legitimate money strings
are not false-flagged.

## Carryover schema — `prior-year-carryovers-template.json` + `schema_check`

**Verdict:** GO

Behavior covered by `tests/test_schema_check.py`: required fields, tax_year
bounds, filing_status enum, amount parseability, rentals/assets shape, and
the georgia-section warning. All 8 tests passed on the first run against the
existing `schema_check` implementation — no fixes needed.

Field-name/line audit vs `docs/PRIOR-YEAR-DATA.md` and curated refs:

**Federal fields (`federal.*`):**
- `agi_line_11` — 1040 Line 11 = AGI. VERIFIED. [1040-line-by-line.md, "Total Income and AGI (Lines 9–11)"]
- `taxable_income_line_15` — 1040 Line 15 = Taxable income. VERIFIED. [1040-line-by-line.md, "Deductions (Lines 12–15)"]
- `total_tax_line_24` — 1040 Line 24 = Total tax. VERIFIED. [1040-line-by-line.md, "Other Taxes (Lines 23–24)"]
- `withholding_line_25` — 1040 Line 25d = Total federal tax withheld. MINOR NOTE: the actual
  summary line on the form is 25d (not a bare line 25); the field name suffix `_line_25` is
  slightly imprecise but semantically correct. VERIFIED. [1040-line-by-line.md, "Payments (Lines 25–33)"]
- `estimated_payments_line_26` — 1040 Line 26 = Estimated tax payments. VERIFIED. [1040-line-by-line.md, "Payments (Lines 25–33)"]
- `refund_line_34` — 1040 Line 34 = Overpayment. VERIFIED. [1040-line-by-line.md, "Refund or Amount Owed (Lines 34–37)"]
- `balance_due_line_37` — 1040 Line 37 = Amount owed. VERIFIED. [1040-line-by-line.md, "Refund or Amount Owed (Lines 34–37)"]
- `overpayment_applied_to_next_year_line_36` — 1040 Line 36 = Applied to next year's estimated tax. VERIFIED. [1040-line-by-line.md, "Refund or Amount Owed (Lines 34–37)"]
- `qbi_carryforward_form_8995_line_16` — Form 8995 Line 16 = QBI loss carryforward. VERIFIED. [self-employment-qbi.md, "QBI Loss Carryforward Mechanics"]
- `salt_deducted_schedule_a_line_5e` — Schedule A Line 5e. NOT VERIFIABLE from the four cited
  refs (1040-line-by-line.md covers only Form 1040 + Schedule 1/2; Schedule A line enumeration
  is in salt-deduction-2025.md which is outside scope here). No mismatch found; check against
  `reference/curated/salt-deduction-2025.md` when auditing Schedule A fields.
- `itemized`, `itemized_total_schedule_a`, `capital_loss_carryforward`, `nol_carryforward`,
  `charitable_carryforward`, `ira_basis_form_8606` — no form-line numbers embedded in names;
  pass as description-only fields. All carryover types confirmed as valid from
  `docs/PRIOR-YEAR-DATA.md` carryover table.

**Georgia fields (`georgia.*`):**
- `ga_taxable_income_line_15c` — GA Form 500 Line 15c = Georgia taxable income after NOL
  (Line 15a − Line 15b). VERIFIED. [georgia-500-guide.md, "Tax Computation", Lines 15a–b–c]
- `ga_tax_line_16` — GA Form 500 Line 16 = Tax at 5.19% of Line 15c. VERIFIED. [georgia-500-guide.md, "Tax Computation", Line 16]
- `ga_withholding_line_24` — GA Form 500 Line 24 = Georgia income tax withheld. VERIFIED. [georgia-500-guide.md, "Payments and Balance Due", Line 24]
- `ga_estimated_payments_line_26` — GA Form 500 Line 26 = Estimated tax payments. VERIFIED. [georgia-500-guide.md, "Payments and Balance Due", Line 26]
- `ga_overpayment_applied_to_next_year_line_31` — GA Form 500 Line 31 = Amount credited to
  next year's estimated tax. VERIFIED. [georgia-500-guide.md, "Payments and Balance Due", Line 31]
- `ga_refund_line_46` — GA Form 500 Line 46/46a = Refund and direct deposit. VERIFIED. [georgia-500-guide.md, "Payments and Balance Due", Line 46/46a]
- `ga_nol_carryforward`, `ga_depreciation_difference_tracking` — no line numbers in names;
  pass as description-only fields. GA NOL confirmed at GA Form 500 Lines 15b and Schedule 1
  Additions #6; depreciation differences confirmed at GA Schedule 1 Additions #4–5.
  [georgia-500-guide.md, "Line-by-Line Reference" and "Schedule 1 — Additions"]

**Rental fields (`rentals[].`):**
- `suspended_passive_loss_form_8582` — no line number in name; refers to Form 8582 worksheets.
  Confirmed valid carryover source. [schedule-e-guide.md, Lines 20–22; docs/PRIOR-YEAR-DATA.md
  carryover table row "Suspended passive losses"]
- `assets[].cost_basis`, `assets[].placed_in_service`, `assets[].prior_accumulated_depreciation`,
  `assets[].federal_bonus_claimed`, `assets[].land_value_excluded`, `assets[].method_recovery`
  — no form-line numbers in names; all confirmed as valid depreciation-tracking fields.
  [schedule-e-guide.md, "Depreciation Basics"; georgia-500-guide.md, "Schedule 1 — Additions"]

**Summary:** All line-number references in field names match the actual form lines.
`withholding_line_25` has a cosmetic imprecision (should strictly be `_line_25d`) but no
substantive mismatch. `salt_deducted_schedule_a_line_5e` cannot be verified from the four
cited refs; flag for audit against `salt-deduction-2025.md`.

## Extraction prompt — `hermes-extraction-request.md`

**Verdict:** GO

Field-by-field source map vs schema + curated refs: all 33 fields in the prompt exist in
`prior-year-carryovers-template.json` with identical keys. All line-number claims verified
against curated refs — `salt_deducted_schedule_a_line_5e` confirmed against
`reference/curated/salt-deduction-2025.md` (present in curated; gap noted in Task 2 is
resolved). `ira_basis_form_8606` has no dedicated curated guide but the key encodes the source
form unambiguously. Redaction rules vs firewall coverage: the prompt's Rule 1 covers every PII
category blocked by `BLOCKED_KEY_FRAGMENTS` and the SSN/LONG_DIGIT_RUN value patterns, with one
defense-in-depth gap: `BLOCKED_KEY_FRAGMENTS` omits `name`/`taxpayer`/`dependent` fragments.
The schema contains no name-bearing keys, so a schema-compliant extraction cannot leak names;
a non-compliant extraction would pass the validator unchallenged. Low risk; recommend adding
`"name"` to `BLOCKED_KEY_FRAGMENTS` as a hardening step in a later task.

## Downstream wiring — skills + schedule_e_calculator.py

**Verdict:** GO

Keys consumed by the skills and confirmed present in the schema: `federal.capital_loss_carryforward`
(consumed by tax-cheatsheet/SKILL.md and tax-audit/SKILL.md at concept level), `federal.qbi_carryforward_form_8995_line_16`
(consumed by tax-cheatsheet/SKILL.md and tax-audit/SKILL.md; mapped implicitly to `what_if.py`
baseline param `qbi_carryforward` — no SKILL.md sentence names both the JSON key and the script
param together), `rentals[].suspended_passive_loss_form_8582` (consumed with explicit `→ prior_suspended_loss`
mapping in tax-cheatsheet/SKILL.md and tax-audit/SKILL.md), `federal.overpayment_applied_to_next_year_line_36`
and `georgia.ga_overpayment_applied_to_next_year_line_31` (consumed by tax-audit/SKILL.md),
`state_refund_received_during_current_year` (consumed by tax-cheatsheet/SKILL.md and tax-audit/SKILL.md).
Orphans (consumed but not produced): none found — every schema key that appears in a script param
or SKILL.md instruction maps to a key that exists in the schema. Produced but not yet consumed:
`federal.nol_carryforward`, `federal.charitable_carryforward`, `federal.ira_basis_form_8606`,
`georgia.ga_nol_carryforward`, `georgia.ga_depreciation_difference_tracking` — stored for
future skill use; expected at Phase 0. `rentals[].assets[].prior_accumulated_depreciation` is
referenced in tax-cheatsheet/SKILL.md as a "schedule_e_calculator.py input" but the script
does not have a param by that name — it is stored for audit/recapture reference only; SKILL.md
wording is loose but not broken.
