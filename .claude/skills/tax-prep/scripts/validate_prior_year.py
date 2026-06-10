"""
validate_prior_year.py — Schema and PII validation for prior-year
carryover data before any skill consumes it.

Usage:
    python validate_prior_year.py '{"json_path": "analysis/prior-year-carryovers-2024.json"}'

Validates a prior-year carryover JSON (produced by Claude extraction,
the user's Hermes Agent, or manual entry — see docs/PRIOR-YEAR-DATA.md):

1. PII scan (hard reject): SSN patterns, standalone 9-17 digit
   account/routing-like numbers, blocked key names (ssn, routing,
   account_number, dob, ...). PII must never leave the source PDFs in
   my-tax-docs/ (per CLAUDE.md rules).
2. Schema: required fields, Decimal-parseable amounts, sane tax_year,
   rentals array shape (matches schedule_e_calculator.py inputs).

Output: JSON with verdict "accepted" or "rejected" plus per-check detail.

All arithmetic uses Decimal — no float math (per CLAUDE.md rules).
"""

import json
import os
import re
import sys
from decimal import Decimal


# ---------------------------------------------------------------------------
# PII rules
# ---------------------------------------------------------------------------

# Key names that must not appear anywhere in the JSON (case-insensitive,
# substring match on each key)
BLOCKED_KEY_FRAGMENTS = [
    "ssn", "social_security", "socialsecurity", "routing", "account_number",
    "accountnumber", "bank", "dob", "birth", "signature", "phone", "email",
    "itin", "ein",
]

# Value patterns that indicate PII leaked into the data
SSN_DASHED = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# Standalone long digit runs (9-17 digits): routing numbers are 9 digits,
# bank accounts 8-17. Dollar amounts in this schema are strings with a
# decimal point and at most 2 decimal places, so a bare 9+ digit integer
# is suspicious. Allow digits adjacent to a '.' (cents) to pass.
LONG_DIGIT_RUN = re.compile(r"(?<![\d.])\d{9,17}(?![\d.])")

AMOUNT_OK = re.compile(r"^-?[\d,]+(\.\d{1,2})?$")

MAX_PLAUSIBLE_AMOUNT = Decimal("100000000")  # $100M sanity ceiling


def d(val):
    """Convert to Decimal. Returns None for non-numeric."""
    if val is None:
        return None
    try:
        return Decimal(str(val).replace(",", "").strip())
    except Exception:
        return None


def walk(node, path="$"):
    """Yield (path, key, value) for every entry in nested JSON —
    including list elements (a string inside an array must be scanned
    the same as a dict value)."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield (f"{path}.{k}", k, v)
            yield from walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield (f"{path}[{i}]", "", v)
            yield from walk(v, f"{path}[{i}]")


def pii_scan(data):
    """Return a list of PII findings (empty = clean)."""
    findings = []
    for path, key, value in walk(data):
        key_lower = str(key).lower()
        for frag in BLOCKED_KEY_FRAGMENTS:
            if frag in key_lower:
                findings.append(f"Blocked key name at {path} (contains '{frag}')")
                break
        # JSON numbers: amounts must be strings per the schema, so any
        # 9+ digit bare integer is account/routing-like, not money
        if isinstance(value, int) and not isinstance(value, bool):
            if len(str(abs(value))) >= 9:
                findings.append(f"Account/routing-like bare integer in value at {path}")
        if isinstance(value, str):
            if SSN_DASHED.search(value):
                findings.append(f"SSN-like pattern (xxx-xx-xxxx) in value at {path}")
            if LONG_DIGIT_RUN.search(value):
                amt = d(value)
                # A parseable amount under the sanity ceiling is money, not
                # an account number
                if amt is None or abs(amt) > MAX_PLAUSIBLE_AMOUNT or "." not in value:
                    findings.append(f"Account/routing-like digit run in value at {path}")
    return findings


# ---------------------------------------------------------------------------
# Schema checks
# ---------------------------------------------------------------------------

REQUIRED_TOP_LEVEL = ["tax_year", "filing_status", "federal"]
VALID_FILING_STATUS = {"MFJ", "Single", "MFS", "HoH", "QSS"}
VALID_CLASSIFICATIONS = {"long_term", "mid_term", "short_term"}


def schema_check(data):
    """Return (errors, warnings) lists."""
    errors = []
    warnings = []

    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    tax_year = data.get("tax_year")
    if not isinstance(tax_year, int) or not 2015 <= tax_year <= 2025:
        errors.append(f"tax_year must be an integer between 2015 and 2025, got: {tax_year!r}")

    if data.get("filing_status") not in VALID_FILING_STATUS:
        errors.append(f"filing_status must be one of {sorted(VALID_FILING_STATUS)}, got: {data.get('filing_status')!r}")

    # Every leaf under federal/georgia that isn't a bool must be a
    # Decimal-parseable amount or null
    for section in ("federal", "georgia"):
        sec = data.get(section)
        if sec is None:
            continue
        if not isinstance(sec, dict):
            errors.append(f"{section} must be an object")
            continue
        for key, value in sec.items():
            if value is None or isinstance(value, bool):
                continue
            if d(value) is None:
                errors.append(f"{section}.{key} is not a parseable amount: {value!r}")

    rentals = data.get("rentals", [])
    if not isinstance(rentals, list):
        errors.append("rentals must be an array")
        rentals = []
    for i, r in enumerate(rentals):
        label = r.get("property_label")
        if not label:
            errors.append(f"rentals[{i}]: missing property_label")
        if r.get("classification") not in VALID_CLASSIFICATIONS:
            warnings.append(f"rentals[{i}]: classification should be one of {sorted(VALID_CLASSIFICATIONS)} (got {r.get('classification')!r})")
        if d(r.get("suspended_passive_loss_form_8582")) is None:
            warnings.append(f"rentals[{i}]: suspended_passive_loss_form_8582 missing or unparseable — confirm against prior Form 8582")
        assets = r.get("assets", [])
        if not assets:
            warnings.append(f"rentals[{i}]: no assets[] — depreciation cannot carry forward without basis and placed-in-service data")
        for j, a in enumerate(assets):
            for req in ("description", "placed_in_service", "cost_basis"):
                if not a.get(req):
                    errors.append(f"rentals[{i}].assets[{j}]: missing {req}")
            if a.get("cost_basis") is not None and d(a.get("cost_basis")) is None:
                errors.append(f"rentals[{i}].assets[{j}]: cost_basis not parseable")

    if "georgia" not in data:
        warnings.append("No georgia section — GA carryovers (NOL, depreciation differences, overpayment applied) will be unavailable")

    return errors, warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate(params):
    json_path = params.get("json_path", "")
    if not json_path or not os.path.exists(json_path):
        return {"error": f"File not found: {json_path}"}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {"verdict": "rejected", "pii_findings": [], "schema_errors": [f"Invalid JSON: {e}"], "schema_warnings": []}

    pii = pii_scan(data)
    errors, warnings = schema_check(data)

    verdict = "accepted" if not pii and not errors else "rejected"
    summary = {
        "tax_year": data.get("tax_year"),
        "source": data.get("source", "unspecified"),
        "rental_properties": len(data.get("rentals", []) or []),
        "has_georgia_section": "georgia" in data,
    }

    return {
        "verdict": verdict,
        "pii_findings": pii,
        "schema_errors": errors,
        "schema_warnings": warnings,
        "summary": summary,
        "note": "PII findings must be fixed at the source (re-extract without the offending values) — never edit PII into a redacted form by hand inside analysis/." if pii else "Validation passed — data is safe for downstream skills.",
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: validate_prior_year.py \'{"json_path": "analysis/prior-year-carryovers-2024.json"}\''
        }))
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = validate(params)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
