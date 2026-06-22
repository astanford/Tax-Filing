# Prior-Year Ingestion — Phase 0 (Validate Path B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate Claude Fable's existing prior-year "Path B" artifacts (PII firewall, carryover schema, extraction prompt, downstream wiring) and extend the schema to be passthrough/K-1 aware, producing a standalone `docs/PATH-B-VALIDATION.md` with a per-artifact GO/FIX/NO-GO verdict — the hard gate before any Phase 1 build.

**Architecture:** Phase 0 is a *validation* phase, not a greenfield build. The implementation under test (`validate_prior_year.py`) already exists. Each task writes tests asserting the *required* behavior, runs them, and treats any failure as a finding: GO if it already passes, FIX if a test reveals a gap (then fix red→green). Tests use only fabricated data. The audit of line-number claims is recorded in the findings doc with citations to `reference/curated/`.

**Tech Stack:** Python 3 (stdlib only for the validator, per repo rules), `pytest` as a test-only dev dependency, JSON.

## Global Constraints

Copied verbatim from `CLAUDE.md` Rules and the spec — every task implicitly includes these:

- Every tax rule / line-number claim must cite a file in `reference/curated/` (Rule 1).
- If unverifiable: "I cannot verify this — check IRS.gov" (Rule 2).
- All math via Python — no LLM arithmetic; validator uses `Decimal`, never float (Rule 3).
- No personal information stored in committed files (Rule 4). All test fixtures use **obviously fabricated** data — SSN `000-00-0000`, names like "Jane Testfiler".
- Forms leave SSN, bank, signature fields blank (Rule 5).
- The PII validator and carryover schema are the **single source of truth**; nothing is duplicated. They live under `.claude/skills/tax-prep/`.
- Validator stays **stdlib-only** at runtime; `pytest` is test-tooling, declared in `requirements-dev.txt`, never imported by the validator.

---

## File Structure

- `requirements-dev.txt` (create) — test-only deps (`pytest`).
- `tests/conftest.py` (create) — puts the scripts dir on `sys.path` so tests can `import validate_prior_year`.
- `tests/test_pii_firewall.py` (create) — adversarial PII tests (Task 1).
- `tests/test_schema_check.py` (create) — schema-validation tests (Task 2).
- `tests/test_passthrough.py` (create) — passthrough/K-1 schema tests (Task 4).
- `tests/test_roundtrip.py` (create) — end-to-end fabricated-return test (Task 5).
- `.claude/skills/tax-prep/scripts/validate_prior_year.py` (modify, Task 4) — add passthrough schema checks.
- `.claude/skills/tax-prep/templates/prior-year-carryovers-template.json` (modify, Task 4) — add fabricated `passthrough` example.
- `.claude/skills/tax-prep/templates/hermes-extraction-request.md` (modify, Task 4) — add `passthrough` section to the schema map.
- `docs/PATH-B-VALIDATION.md` (create, Tasks 1–5) — the findings deliverable.

---

## Task 1: PII firewall validation (the crown jewel)

**Files:**
- Create: `requirements-dev.txt`
- Create: `tests/conftest.py`
- Create: `tests/test_pii_firewall.py`
- Create: `docs/PATH-B-VALIDATION.md`
- Under test: `.claude/skills/tax-prep/scripts/validate_prior_year.py` (`pii_scan`, `validate`)

**Interfaces:**
- Consumes: `validate_prior_year.pii_scan(data: dict) -> list[str]`; `validate_prior_year.validate(params: dict) -> dict` where `params={"json_path": str}` and the result has keys `verdict` ("accepted"|"rejected"), `pii_findings`, `schema_errors`, `schema_warnings`, `summary`.
- Produces: a runnable `tests/` harness and the `## PII firewall` section of `docs/PATH-B-VALIDATION.md`. No code is exported to later tasks.

- [ ] **Step 1: Create the dev-dependency file**

`requirements-dev.txt`:
```
# Test-only tooling. NOT runtime deps — the skills/validator stay stdlib-only.
pytest==8.3.4
```

- [ ] **Step 2: Install pytest**

Run: `python -m pip install -r requirements-dev.txt`
Expected: pytest installs (or "Requirement already satisfied").

- [ ] **Step 3: Create the test harness so tests can import the validator**

`tests/conftest.py`:
```python
import pathlib
import sys

# validate_prior_year.py lives under the tax-prep skill, not on the path.
# tests/ is at the repo root, so parent.parent is the repo root.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / ".claude" / "skills" / "tax-prep" / "scripts"
sys.path.insert(0, str(SCRIPTS))
```

- [ ] **Step 4: Write the failing PII tests**

`tests/test_pii_firewall.py`:
```python
"""Adversarial PII-firewall tests. ALL data fabricated (Rule 4)."""
import json

import validate_prior_year as v


def clean_minimal():
    """A minimal, PII-free, schema-valid carryover dict."""
    return {
        "tax_year": 2024,
        "source": "test",
        "filing_status": "MFJ",
        "federal": {"agi_line_11": "185000.00"},
    }


def test_clean_data_has_no_pii_findings():
    assert v.pii_scan(clean_minimal()) == []


def test_dashed_ssn_in_value_is_caught():
    data = clean_minimal()
    data["notes"] = ["Taxpayer SSN 000-00-0000 on page 1"]
    findings = v.pii_scan(data)
    assert any("SSN-like" in f for f in findings)


def test_bare_account_like_integer_is_caught():
    data = clean_minimal()
    data["federal"]["agi_line_11"] = 123456789  # 9-digit bare int = account-like
    findings = v.pii_scan(data)
    assert any("Account/routing-like bare number" in f for f in findings)


def test_long_digit_run_string_is_caught():
    data = clean_minimal()
    data["notes"] = ["Routing 021000021 on the 1099"]
    findings = v.pii_scan(data)
    assert any("Account/routing-like digit run" in f for f in findings)


def test_legit_money_string_is_not_flagged_as_account():
    data = clean_minimal()
    data["federal"]["agi_line_11"] = "12345678.90"  # ~$12.3M, has decimal
    assert v.pii_scan(data) == []


def test_each_blocked_key_fragment_is_caught():
    for frag in v.BLOCKED_KEY_FRAGMENTS:
        data = clean_minimal()
        # build a key that contains the blocked fragment
        data[f"x_{frag}_field"] = "whatever"
        findings = v.pii_scan(data)
        assert any(frag in f for f in findings), f"fragment not caught: {frag}"


def test_pii_nested_in_array_is_caught():
    data = clean_minimal()
    data["rentals"] = [{"property_label": "Rental (1 A St)", "dob": "1980-01-01"}]
    findings = v.pii_scan(data)
    assert any("dob" in f for f in findings)


def test_validate_rejects_file_with_pii(tmp_path):
    data = clean_minimal()
    data["notes"] = ["SSN 000-00-0000"]
    p = tmp_path / "cy.json"
    p.write_text(json.dumps(data))
    result = v.validate({"json_path": str(p)})
    assert result["verdict"] == "rejected"
    assert result["pii_findings"]
```

- [ ] **Step 5: Run the tests — observe results**

Run: `python -m pytest tests/test_pii_firewall.py -v`
Expected: All PASS → PII firewall is **GO**. Any FAIL → a real gap in `validate_prior_year.py` → record as **FIX** and proceed to Step 6. (Based on reading the validator, these are expected to pass.)

- [ ] **Step 6: If any test failed, fix the validator**

Only if Step 5 surfaced a failure: edit `pii_scan`/the regexes in `validate_prior_year.py` to close the gap, then re-run Step 5 until green. If all passed, skip.

- [ ] **Step 7: Record the verdict in the findings doc**

Create `docs/PATH-B-VALIDATION.md`:
```markdown
# Path B Validation Findings

*Date: 2026-06-22*

Validation of Claude Fable's prior-year ingestion artifacts before building
the `ingest/` subsystem. Verdicts: **GO** (sound as-is), **FIX** (gap found
and corrected here), **NO-GO** (needs redesign). All test fixtures use
fabricated data per Rule 4.

## PII firewall — `validate_prior_year.py` (`pii_scan`)

**Verdict:** <GO|FIX>

Covered by `tests/test_pii_firewall.py`: clean data passes; dashed SSNs,
bare 9+ digit account-like integers, long digit runs, every blocked key
fragment, and array-nested PII are all rejected; legitimate money strings
are not false-flagged. <If FIX: describe the gap and the change made.>
```

- [ ] **Step 8: Commit**

```bash
git add requirements-dev.txt tests/conftest.py tests/test_pii_firewall.py docs/PATH-B-VALIDATION.md
git commit -m "test: validate PII firewall (Phase 0); start PATH-B-VALIDATION findings"
```

---

## Task 2: Schema-check validation

**Files:**
- Create: `tests/test_schema_check.py`
- Modify: `docs/PATH-B-VALIDATION.md` (append schema section)
- Under test: `.claude/skills/tax-prep/scripts/validate_prior_year.py` (`schema_check`)

**Interfaces:**
- Consumes: `validate_prior_year.schema_check(data: dict) -> tuple[list[str], list[str]]` returning `(errors, warnings)`.
- Produces: the `## Carryover schema` section of `docs/PATH-B-VALIDATION.md`. No code exported.

- [ ] **Step 1: Write the failing schema tests**

`tests/test_schema_check.py`:
```python
"""Schema-validation tests for validate_prior_year.schema_check. Fabricated data."""
import validate_prior_year as v


def valid_full():
    return {
        "tax_year": 2024,
        "source": "test",
        "filing_status": "MFJ",
        "federal": {"agi_line_11": "185000.00", "itemized": True},
        "georgia": {"ga_tax_line_16": "7977.00"},
        "rentals": [{
            "property_label": "Rental (1 A St - A LLC)",
            "classification": "long_term",
            "suspended_passive_loss_form_8582": "3400.00",
            "assets": [{
                "description": "Building",
                "placed_in_service": "2022-05",
                "cost_basis": "275000.00",
            }],
        }],
    }


def test_valid_data_has_no_errors():
    errors, _ = v.schema_check(valid_full())
    assert errors == []


def test_missing_required_top_level_field_errors():
    data = valid_full()
    del data["federal"]
    errors, _ = v.schema_check(data)
    assert any("federal" in e for e in errors)


def test_out_of_range_tax_year_errors():
    data = valid_full()
    data["tax_year"] = 1999
    errors, _ = v.schema_check(data)
    assert any("tax_year" in e for e in errors)


def test_bad_filing_status_errors():
    data = valid_full()
    data["filing_status"] = "married"
    errors, _ = v.schema_check(data)
    assert any("filing_status" in e for e in errors)


def test_unparseable_federal_amount_errors():
    data = valid_full()
    data["federal"]["agi_line_11"] = "one hundred"
    errors, _ = v.schema_check(data)
    assert any("agi_line_11" in e for e in errors)


def test_rental_missing_label_errors():
    data = valid_full()
    data["rentals"][0]["property_label"] = ""
    errors, _ = v.schema_check(data)
    assert any("property_label" in e for e in errors)


def test_rental_asset_missing_cost_basis_errors():
    data = valid_full()
    del data["rentals"][0]["assets"][0]["cost_basis"]
    errors, _ = v.schema_check(data)
    assert any("cost_basis" in e for e in errors)


def test_missing_georgia_section_warns_not_errors():
    data = valid_full()
    del data["georgia"]
    errors, warnings = v.schema_check(data)
    assert errors == []
    assert any("georgia" in w.lower() for w in warnings)
```

- [ ] **Step 2: Run the tests — observe results**

Run: `python -m pytest tests/test_schema_check.py -v`
Expected: All PASS → schema validator is **GO**. Any FAIL → **FIX** (fix `schema_check`, re-run green).

- [ ] **Step 3: Audit schema field names against the carryover map**

Cross-check each field in `prior-year-carryovers-template.json` against the
carryover table in `docs/PRIOR-YEAR-DATA.md` and the cited curated refs
(`georgia-500-guide.md`, `1040-line-by-line.md`, `schedule-e-guide.md`,
`self-employment-qbi.md`). For each field, confirm the form-line in its name
matches the actual line (Rule 1). Note any mismatch or orphan field.

- [ ] **Step 4: Record the verdict in the findings doc**

Append to `docs/PATH-B-VALIDATION.md`:
```markdown
## Carryover schema — `prior-year-carryovers-template.json` + `schema_check`

**Verdict:** <GO|FIX>

Behavior covered by `tests/test_schema_check.py`: required fields, tax_year
bounds, filing_status enum, amount parseability, rentals/assets shape, and
the georgia-section warning. Field-name/line audit vs `docs/PRIOR-YEAR-DATA.md`
and curated refs: <list each field checked + citation; note mismatches or
"all line references verified">.
```

- [ ] **Step 5: Commit**

```bash
git add tests/test_schema_check.py docs/PATH-B-VALIDATION.md
git commit -m "test: validate carryover schema_check (Phase 0); audit field lines"
```

---

## Task 3: Extraction-prompt + downstream-wiring audit

**Files:**
- Modify: `docs/PATH-B-VALIDATION.md` (append two sections)
- Reviewed: `.claude/skills/tax-prep/templates/hermes-extraction-request.md`; the four skills + `schedule_e_calculator.py`

**Interfaces:**
- Consumes: nothing (pure audit).
- Produces: the `## Extraction prompt` and `## Downstream wiring` sections of the findings doc. No code.

- [ ] **Step 1: Audit the extraction prompt's source map**

For each field in `hermes-extraction-request.md`, confirm (a) it exists in
`prior-year-carryovers-template.json` with the same key, and (b) its stated
source line matches the curated refs (Rule 1). Confirm the redaction rules
cover every PII category the firewall blocks (`BLOCKED_KEY_FRAGMENTS` +
SSN/account patterns). Note gaps.

- [ ] **Step 2: Audit downstream consumption**

Grep the skills and `schedule_e_calculator.py` for every carryover key they
read, and confirm each exists in the schema with a matching name (no
consumed-but-never-produced field).

Run: `grep -rn "suspended_passive_loss_form_8582\|qbi_carryforward\|capital_loss_carryforward\|prior_accumulated_depreciation\|overpayment_applied" .claude/skills/`
Expected: every hit maps to a schema key. Record any orphan.

- [ ] **Step 3: Record both verdicts in the findings doc**

Append to `docs/PATH-B-VALIDATION.md`:
```markdown
## Extraction prompt — `hermes-extraction-request.md`

**Verdict:** <GO|FIX>

Field-by-field source map vs schema + curated refs: <result>. Redaction
rules vs firewall coverage: <result>.

## Downstream wiring — skills + schedule_e_calculator.py

**Verdict:** <GO|FIX>

Keys consumed by the skills and confirmed present in the schema: <list>.
Orphans (consumed but not produced, or produced but never consumed): <list
or "none">.
```

- [ ] **Step 4: Commit**

```bash
git add docs/PATH-B-VALIDATION.md
git commit -m "docs: audit extraction prompt + downstream wiring (Phase 0)"
```

---

## Task 4: Passthrough/K-1 carryover schema extension

**Files:**
- Modify: `.claude/skills/tax-prep/scripts/validate_prior_year.py`
- Modify: `.claude/skills/tax-prep/templates/prior-year-carryovers-template.json`
- Modify: `.claude/skills/tax-prep/templates/hermes-extraction-request.md`
- Create: `tests/test_passthrough.py`
- Modify: `docs/PATH-B-VALIDATION.md` (append section)

**Interfaces:**
- Consumes: `validate_prior_year.schema_check`, `validate_prior_year.d`.
- Produces: a validated top-level `passthrough` array. Each entry:
  `entity_label: str`, `entity_type: "partnership"|"s_corp"|"trust"`,
  `is_ptp: bool`, and amount strings `basis_carryforward_704d_1366d`,
  `at_risk_carryforward_465`, `suspended_passive_loss_form_8582`,
  `qbi_passthrough_form_8995`. `validate()`'s `summary` gains
  `passthrough_entities: int`.

- [ ] **Step 1: Write the failing passthrough tests**

`tests/test_passthrough.py`:
```python
"""Passthrough/K-1 carryover schema tests. Fabricated data."""
import json

import validate_prior_year as v


def with_passthrough(entry):
    return {
        "tax_year": 2024,
        "source": "test",
        "filing_status": "MFJ",
        "federal": {"agi_line_11": "185000.00"},
        "passthrough": [entry],
    }


def valid_entry():
    return {
        "entity_label": "Partnership (Acme Partners LP)",
        "entity_type": "partnership",
        "is_ptp": False,
        "basis_carryforward_704d_1366d": "12000.00",
        "at_risk_carryforward_465": "8000.00",
        "suspended_passive_loss_form_8582": "5000.00",
        "qbi_passthrough_form_8995": "0.00",
    }


def test_valid_passthrough_has_no_errors():
    errors, _ = v.schema_check(with_passthrough(valid_entry()))
    assert errors == []


def test_passthrough_must_be_array():
    data = with_passthrough(valid_entry())
    data["passthrough"] = {"not": "a list"}
    errors, _ = v.schema_check(data)
    assert any("passthrough must be an array" in e for e in errors)


def test_passthrough_missing_entity_label_errors():
    e = valid_entry()
    e["entity_label"] = ""
    errors, _ = v.schema_check(with_passthrough(e))
    assert any("entity_label" in err for err in errors)


def test_passthrough_bad_entity_type_errors():
    e = valid_entry()
    e["entity_type"] = "llc"
    errors, _ = v.schema_check(with_passthrough(e))
    assert any("entity_type" in err for err in errors)


def test_passthrough_non_bool_is_ptp_errors():
    e = valid_entry()
    e["is_ptp"] = "yes"
    errors, _ = v.schema_check(with_passthrough(e))
    assert any("is_ptp" in err for err in errors)


def test_passthrough_unparseable_amount_errors():
    e = valid_entry()
    e["at_risk_carryforward_465"] = "lots"
    errors, _ = v.schema_check(with_passthrough(e))
    assert any("at_risk_carryforward_465" in err for err in errors)


def test_passthrough_count_in_summary(tmp_path):
    p = tmp_path / "cy.json"
    p.write_text(json.dumps(with_passthrough(valid_entry())))
    result = v.validate({"json_path": str(p)})
    assert result["verdict"] == "accepted"
    assert result["summary"]["passthrough_entities"] == 1


def test_passthrough_entity_label_is_not_pii():
    # Entity labels are allowed, like property labels — must not be flagged.
    assert v.pii_scan(with_passthrough(valid_entry())) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_passthrough.py -v`
Expected: FAIL — `passthrough` is not yet validated and `summary` lacks `passthrough_entities`.

- [ ] **Step 3: Add the passthrough constant**

In `validate_prior_year.py`, after the line `VALID_CLASSIFICATIONS = {"long_term", "mid_term", "short_term"}`, add:
```python
VALID_ENTITY_TYPES = {"partnership", "s_corp", "trust"}
```

- [ ] **Step 4: Add passthrough schema checks**

In `validate_prior_year.py`, inside `schema_check`, immediately before the
`if "georgia" not in data:` block, add:
```python
    passthrough = data.get("passthrough", [])
    if not isinstance(passthrough, list):
        errors.append("passthrough must be an array")
        passthrough = []
    for i, p in enumerate(passthrough):
        if not p.get("entity_label"):
            errors.append(f"passthrough[{i}]: missing entity_label")
        if p.get("entity_type") not in VALID_ENTITY_TYPES:
            errors.append(f"passthrough[{i}]: entity_type must be one of {sorted(VALID_ENTITY_TYPES)} (got {p.get('entity_type')!r})")
        if not isinstance(p.get("is_ptp", False), bool):
            errors.append(f"passthrough[{i}]: is_ptp must be a boolean")
        for amt_field in (
            "basis_carryforward_704d_1366d",
            "at_risk_carryforward_465",
            "suspended_passive_loss_form_8582",
            "qbi_passthrough_form_8995",
        ):
            val = p.get(amt_field)
            if val is not None and d(val) is None:
                errors.append(f"passthrough[{i}].{amt_field} not parseable: {val!r}")
```

- [ ] **Step 5: Add passthrough count to the summary**

In `validate_prior_year.py`, in `validate()`, change the `summary` dict to add one key. Replace:
```python
        "rental_properties": len(data.get("rentals", []) or []),
```
with:
```python
        "rental_properties": len(data.get("rentals", []) or []),
        "passthrough_entities": len(data.get("passthrough", []) or []),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_passthrough.py -v`
Expected: PASS. Then run the whole suite to confirm no regressions:
Run: `python -m pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 7: Add the fabricated passthrough example to the template**

In `prior-year-carryovers-template.json`, after the `rentals` array (before
`notes`), add a `passthrough` key:
```json
  "passthrough": [
    {
      "entity_label": "Partnership (Acme Partners LP)",
      "entity_type": "partnership",
      "is_ptp": false,
      "basis_carryforward_704d_1366d": "12000.00",
      "at_risk_carryforward_465": "8000.00",
      "suspended_passive_loss_form_8582": "5000.00",
      "qbi_passthrough_form_8995": "0.00"
    }
  ],
```

- [ ] **Step 8: Document passthrough in the extraction prompt**

In `hermes-extraction-request.md`, after the `rentals` section, add a
`passthrough` section describing each field and its source form line, with a
citation note to verify K-1 line meanings on IRS.gov until a curated K-1
reference exists (Rule 2):
```markdown
### `passthrough` — one entry per K-1 (Schedule E Part II)
- `entity_label` — entity name + type only, e.g. `"Partnership (Acme Partners LP)"`; no EIN, no PII
- `entity_type` — `"partnership" | "s_corp" | "trust"`
- `is_ptp` — true if a publicly traded partnership
- `basis_carryforward_704d_1366d` — remaining outside basis carried forward (§704(d) partnership / §1366(d) S-corp)
- `at_risk_carryforward_465` — suspended at-risk amount (Form 6198)
- `suspended_passive_loss_form_8582` — this entity's unallowed passive loss (Form 8582 worksheets)
- `qbi_passthrough_form_8995` — QBI from this entity (Form 8995/8995-A)

*Source K-1 line meanings vary by form (1065 vs 1120-S vs 1041); a curated
reference does not yet exist — verify on IRS.gov (Rule 2).*
```

- [ ] **Step 9: Run the validator CLI against the updated template as a smoke test**

Run: `python .claude/skills/tax-prep/scripts/validate_prior_year.py '{"json_path": ".claude/skills/tax-prep/templates/prior-year-carryovers-template.json"}'`
Expected: JSON output with `"verdict": "accepted"` and `summary.passthrough_entities` = 1. (The template has no PII and is schema-valid.)

- [ ] **Step 10: Record the verdict in the findings doc**

Append to `docs/PATH-B-VALIDATION.md`:
```markdown
## Passthrough/K-1 carryover extension

**Verdict:** ADDED

Schema, validator, template, and extraction prompt extended with a
`passthrough` array (basis §704(d)/§1366(d), at-risk §465, suspended passive,
PTP flag, passthrough QBI). Covered by `tests/test_passthrough.py`. This is
the *ingestion* side only; current-year computation is the follow-on design.
K-1 line meanings flagged for IRS.gov verification pending a curated ref.
```

- [ ] **Step 11: Commit**

```bash
git add .claude/skills/tax-prep/scripts/validate_prior_year.py .claude/skills/tax-prep/templates/prior-year-carryovers-template.json .claude/skills/tax-prep/templates/hermes-extraction-request.md tests/test_passthrough.py docs/PATH-B-VALIDATION.md
git commit -m "feat: make prior-year carryover schema passthrough/K-1 aware (Phase 0)"
```

---

## Task 5: End-to-end round-trip + findings summary (the gate)

**Files:**
- Create: `tests/test_roundtrip.py`
- Modify: `docs/PATH-B-VALIDATION.md` (add summary verdict table)

**Interfaces:**
- Consumes: `validate_prior_year.validate`.
- Produces: the final GO/FIX/NO-GO summary table — the Phase 0 → Phase 1 gate.

- [ ] **Step 1: Write the round-trip test**

`tests/test_roundtrip.py`:
```python
"""End-to-end: a fabricated full return (rentals + passthrough) validates clean."""
import json

import validate_prior_year as v


def fabricated_full_return():
    return {
        "tax_year": 2024,
        "source": "test",
        "filing_status": "MFJ",
        "federal": {
            "agi_line_11": "185000.00",
            "total_tax_line_24": "24500.00",
            "qbi_carryforward_form_8995_line_16": "0.00",
            "capital_loss_carryforward": "1200.00",
            "itemized": True,
        },
        "georgia": {"ga_tax_line_16": "7977.00", "ga_nol_carryforward": "0.00"},
        "state_refund_received_during_current_year": "223.00",
        "rentals": [{
            "property_label": "Rental (456 Oak Ave - Oak LLC)",
            "classification": "short_term",
            "suspended_passive_loss_form_8582": "3400.00",
            "assets": [{
                "description": "Building",
                "placed_in_service": "2022-05",
                "cost_basis": "275000.00",
            }],
        }],
        "passthrough": [{
            "entity_label": "Partnership (Acme Partners LP)",
            "entity_type": "partnership",
            "is_ptp": False,
            "basis_carryforward_704d_1366d": "12000.00",
            "at_risk_carryforward_465": "8000.00",
            "suspended_passive_loss_form_8582": "5000.00",
            "qbi_passthrough_form_8995": "0.00",
        }],
        "notes": ["Itemized in 2024; 2025 GA refund may be federally taxable."],
    }


def test_full_return_validates_clean(tmp_path):
    p = tmp_path / "carryovers-2024.json"
    p.write_text(json.dumps(fabricated_full_return()))
    result = v.validate({"json_path": str(p)})
    assert result["verdict"] == "accepted", result
    assert result["pii_findings"] == []
    assert result["schema_errors"] == []
    assert result["summary"]["rental_properties"] == 1
    assert result["summary"]["passthrough_entities"] == 1
```

- [ ] **Step 2: Run the full test suite**

Run: `python -m pytest tests/ -v`
Expected: all tests PASS (PII, schema, passthrough, round-trip).

- [ ] **Step 3: Add the summary verdict table to the findings doc**

Append to `docs/PATH-B-VALIDATION.md`:
```markdown
## Summary — Phase 0 gate

| Artifact | Verdict |
|---|---|
| PII firewall (`pii_scan`) | <GO/FIX> |
| Carryover schema (`schema_check` + template) | <GO/FIX> |
| Extraction prompt (`hermes-extraction-request.md`) | <GO/FIX> |
| Downstream wiring (skills + calculator) | <GO/FIX> |
| Passthrough/K-1 extension | ADDED |
| End-to-end round-trip | <GO/FIX> |

**Gate decision:** <PROCEED to Phase 1 / fixes required>.

Test coverage: `tests/` (run `python -m pytest tests/`). All fixtures
fabricated per Rule 4.
```

- [ ] **Step 4: Commit**

```bash
git add tests/test_roundtrip.py docs/PATH-B-VALIDATION.md
git commit -m "test: end-to-end round-trip + Phase 0 gate summary"
```

---

## Self-Review (completed by plan author)

**Spec coverage** — Phase 0 spec items mapped to tasks:
- Validate `prior-year-carryovers-template.json` schema → Task 2 (+ audit Step 3).
- Validate `hermes-extraction-request.md` → Task 3 Step 1.
- Validate `validate_prior_year.py` PII firewall → Task 1.
- Validate downstream wiring → Task 3 Step 2.
- Round-trip fixture → Task 5.
- Fabricated PII fixtures → enforced in every test task (Rule 4 in Global Constraints).
- Standalone `docs/PATH-B-VALIDATION.md` → built across Tasks 1–5.
- Passthrough/K-1 carryover ingestion → Task 4.
- Gate before Phase 1 → Task 5 Step 3 summary table.

**Placeholder scan** — the `<GO|FIX>` / `<result>` markers in the *findings
doc* are intentional verdict slots filled at execution from test outcomes,
not code placeholders; all *code* steps contain complete, runnable content.

**Type consistency** — `pii_scan`/`schema_check`/`validate`/`d` signatures
and the `summary` keys (`rental_properties`, `passthrough_entities`) are used
consistently across Tasks 1–5 and match the actual source in
`validate_prior_year.py`.

## Out of scope for this plan

Phase 1 (`ingest/` subsystem + Hermes orchestration) and Phase 2 (analysis
layer) get their own plans, authored at the Phase 0 → Phase 1 boundary once
these findings exist and the exact Hermes invocation is pinned by reading
Hermes' `AGENTS.md`/`README` (a spec "open item"). The K-1 / Schedule E
Part II *computation* follow-on is a separate design entirely.
```
