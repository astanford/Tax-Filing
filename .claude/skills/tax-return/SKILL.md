---
name: tax-return
description: "Produces the accountant-ready deliverable: fills the official IRS/GA form PDFs from the computed return manifest (with read-back verification), and generates the accountant review package (memo, blocked items, citations, prior-year comparison). Run AFTER /tax-interview converges the return. Triggers on: 'fill my forms', 'generate my return', 'make the PDFs', 'accountant package', 'finalize my return', 'produce the return', 'print my 1040'."
---

# tax-return

Turns the converged return manifest into the deliverable: filled official
PDFs in `output/` plus `output/accountant-package.md`.

## Prerequisites
- `/tax-interview` has converged: `python engine/return_engine.py --file
  analysis/return-inputs.json` reports `missing_count: 0`. If not, stop and
  route the user to `/tax-interview`.
- The repo venv exists (`python3 -m venv .venv && .venv/bin/pip install -r
  engine/requirements.txt`) — pypdf is quarantined there; core skills stay
  stdlib-only.

## Workflow

### Step 1 — Compute and save the manifest
`python engine/return_engine.py --file analysis/return-inputs.json > analysis/return-manifest.json`

### Step 2 — Fill the forms (venv)
`.venv/bin/python engine/fill_return.py '{"manifest_path": "analysis/return-manifest.json", "forms": ["f1040"], "out_dir": "output"}'`
- Only forms with a curated map in `engine/field_maps/` can be filled;
  `f1040.json` is visually verified. For an unmapped form, curate a map
  first (Step 4), or include the manifest table for that form in the
  package instead — never guess field names.
- The script's read-back diff MUST be empty; a mismatch means the map or the
  PDF changed — stop and re-verify.
- SSN, bank, and signature fields are never written (Rule 5) — the script
  hard-guards this and the accountant adds identity at filing.

### Step 3 — Visual verification (mandatory gate)
- `pdftoppm -png -r 100 output/f1040-filled.pdf /tmp/check` and READ the
  images: confirm each value sits on the right printed line and identity
  fields are blank. This is the plan's field-map audit — do not skip it.

### Step 4 — Curating a new field map (when needed)
1. `.venv/bin/python engine/dump_fields.py reference/Raw/<form>.pdf sentinel.pdf`
2. `pdftoppm -png -r 100 sentinel.pdf page` and read the images — each field
   shows its own field-name digits on the printed form.
3. Record `pdf_field` ↔ `manifest_form`/`manifest_line` pairs in
   `engine/field_maps/<form>.json` (format: see `f1040.json`). Include a
   `label`. NEVER map SSN/bank/signature/PIN fields.
4. Re-run Steps 2–3 for that form.

### Step 5 — Accountant package
`python engine/accountant_package.py '{"manifest_path": "analysis/return-manifest.json", "carryovers_path": "analysis/prior-year-carryovers-<year>.json", "out_path": "output/accountant-package.md"}'`
- Present the memo to the user; every engine-BLOCKED item appears under
  "Items for your review" — these are expected handoffs (8995-A, AMT,
  penalty computation, entities without basis records), not errors.

### Step 6 — Hand off to /tax-audit
Run `/tax-audit` for the three-way cross-check (source CSV ↔ manifest ↔
filled PDFs) before anything goes to the accountant.

## Mandatory Rules
> Full definitions in CLAUDE.md. Citations (Rule 1); unverifiable →
> disclaim (Rule 2); Python-only math (Rule 3); no PII in skill files
> (Rule 4); **forms in output/ leave SSN, bank, and signature fields BLANK
> (Rule 5)** — output/ and analysis/ are gitignored.

## Related Skills
- `/tax-interview` (before): converges the inputs
- `/tax-audit` (after): three-way verification
- `/tax-advisor` (after filing): next-year planning
