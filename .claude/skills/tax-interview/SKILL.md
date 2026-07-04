---
name: tax-interview
description: "Gap-driven interview that converges the return: builds engine inputs from the extracted CSV and prior-year carryovers, runs the return engine, asks the user for every MISSING input the engine reports, and repeats until the return computes cleanly or only accountant-flagged items remain. Triggers on: 'finish my return', 'what do you still need from me', 'interview me', 'complete my tax inputs', 'what questions do you have', 'compute my return', 'run the engine', 'what's missing'."
---

# tax-interview

Converges `analysis/return-inputs.json` until `engine/return_engine.py`
computes a full federal + Georgia return with no missing inputs. The engine
never guesses: every gap becomes a question here, every out-of-scope item a
flagged accountant note.

## Workflow

### Step 1 — Build or load the inputs file
- If `analysis/return-inputs.json` does not exist, build it:
  `python engine/inputs_from_csv.py '{"csv_path": "analysis/tax-doc-summary.csv", "carryovers_path": "analysis/prior-year-carryovers-<year>.json", "filing_status": "<status>", "out_path": "analysis/return-inputs.json"}'`
  (requires `/tax-prep` to have run first — stop and say so if the CSV is missing).
- Report the builder's `unmapped_rows` to the user: every CSV value that
  didn't map automatically is either irrelevant (confirm) or needs a home
  (ask).

### Step 2 — Run the engine
- `python engine/return_engine.py --file analysis/return-inputs.json`
- Read three result sections: `missing_inputs`, `blocked_for_accountant`,
  and `summary`.

### Step 3 — Ask the user (batched, cited)
- Group `missing_inputs` and the calculator prerequisites into ONE batch of
  questions (use the AskUserQuestion tool where options are enumerable,
  free-text otherwise). Always include WHY, citing the curated reference the
  engine cited.
- Standing question sets to check even if the engine hasn't reached them yet:
  - **Rentals:** the per-property checklist in `docs/SCHEDULE-E-PLAN.md` §5
    (basis/land split, placed-in-service, days rented, services, suspended
    losses) → run `schedule_e_calculator.py`, put its Line 26 and
    `form_8582.buckets` into the inputs file.
  - **K-1s:** entity list with type/PTP/participation, box values, and
    `basis_available` / `at_risk_available` (Form 7203 or basis worksheet —
    if the user doesn't have them, leave null; the entity BLOCKS to the
    accountant) → run `k1_passthrough_calculator.py`, put line 32 / line 37 /
    SE box 14A into the inputs file.
  - **1099-B category totals** (proceeds/basis/adjustments per 8949 box A-F)
    from the broker's summary page.
  - **MileIQ annual totals** per activity (dollar amounts) *(Source:
    docs/FULL-RETURN-PLAN.md scope decisions)*.
  - **State refund taxability** if the prior year itemized (`_prior_year_itemized`
    true): confirm the refund amount to include *(Source: 1040-line-by-line.md)*.
  - **Capital-loss carryover split** (short vs long) from the prior Schedule D
    if `capital_loss_carryforward_combined` is nonzero.
- Record each answer into `analysis/return-inputs.json` (Edit tool). NO
  arithmetic in prose — any derived number goes through a script.

### Step 4 — Validate and loop
- PII check the inputs file: it must contain amounts and labels only — no
  SSNs, account numbers, or names beyond entity/property labels (same policy
  as `validate_prior_year.py`; see docs/PRIVATE-DATA.md).
- Re-run Step 2. Repeat until `missing_count == 0`.
- Then present: the `summary` block, every `blocked_for_accountant` item
  (these go in the accountant memo — they are NOT errors), and offer
  `/tax-audit` for the cross-check and `/tax-return` for form output.

## Mandatory Rules
> Full definitions in CLAUDE.md. Citations (Rule 1), unverifiable
> disclaimer (Rule 2), Python-only math (Rule 3), no PII in skill files
> (Rule 4), SSN/bank/signature fields stay blank (Rule 5).
> `analysis/` is gitignored — never commit it.

## Related Skills
- `/tax-prep` (before): extracts the CSV this skill builds from
- `/tax-cheatsheet` (any time): line-by-line explanations
- `/tax-audit` (after): cross-checks the computed return
- `/tax-advisor` (after filing): next-year planning
