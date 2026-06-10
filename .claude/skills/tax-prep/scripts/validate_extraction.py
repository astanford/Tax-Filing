"""
validate_extraction.py — Tax document extraction validator.

Usage:
    python validate_extraction.py '{"csv_path": "analysis/tax-doc-summary.csv"}'

Reads the extracted tax document CSV and runs validation checks:
positive amounts, withholding present, Medicare wages consistency,
duplicate detection, and more.

All values read from the CSV — nothing hardcoded.
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP


def d(val):
    """Convert to Decimal. Returns 0 for non-numeric values."""
    if val is None:
        return Decimal("0")
    try:
        return Decimal(str(val).replace(",", "").strip())
    except Exception:
        return None


def cents(val):
    """Round to nearest cent."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def whole(val):
    """Round to nearest dollar."""
    return val.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def is_dollar_field(box_or_line):
    """Heuristic: most Box N fields are dollar amounts, except known text fields."""
    text_boxes = {"Box 7", "Box 12a", "Box 12b", "Box 12c", "Box 12d", "Box 14", "Box 15"}
    return box_or_line not in text_boxes


def parse_rows(csv_path):
    """Read the CSV and return a list of row dicts."""
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def check_valid_amounts(rows):
    """Check that dollar values parse as valid numbers."""
    invalid = []
    valid_count = 0
    for i, row in enumerate(rows):
        box = row.get("box_or_line", "")
        val_str = row.get("value", "")
        if val_str == "[REDACTED]" or not is_dollar_field(box):
            continue
        parsed = d(val_str)
        if parsed is None:
            invalid.append(f"Row {i+1}: {row.get('document', '?')} {box} = '{val_str}' is not a valid number")
        else:
            valid_count += 1

    if invalid:
        return {
            "check": "valid_amounts",
            "status": "warning",
            "detail": f"{len(invalid)} value(s) could not be parsed as numbers: {'; '.join(invalid[:5])}"
        }
    return {
        "check": "valid_amounts",
        "status": "pass",
        "detail": f"All {valid_count} dollar amounts are valid numbers"
    }


def check_positive_amounts(rows):
    """Check that income amounts are positive where expected."""
    positive_boxes = {
        "Box 1": "Wages",
        "Box 1a": "Total ordinary dividends",
        "Box 1b": "Qualified dividends",
    }
    issues = []
    for row in rows:
        box = row.get("box_or_line", "")
        if box in positive_boxes:
            val = d(row.get("value", "0"))
            if val is not None and val < 0:
                issues.append(f"{row.get('document', '?')} {box} ({positive_boxes[box]}) = {val}")

    if issues:
        return {
            "check": "positive_amounts",
            "status": "warning",
            "detail": f"Negative amounts where positive expected: {'; '.join(issues)}"
        }
    return {
        "check": "positive_amounts",
        "status": "pass",
        "detail": "All income amounts are positive where expected"
    }


def check_federal_withholding(rows):
    """At least one W-2 should have Box 2 (federal withholding) > 0."""
    w2_box2_values = []
    for row in rows:
        doc = row.get("document", "")
        box = row.get("box_or_line", "")
        if "W-2" in doc and box == "Box 2":
            val = d(row.get("value", "0"))
            if val is not None:
                w2_box2_values.append((doc, val))

    if not w2_box2_values:
        return {
            "check": "federal_withholding",
            "status": "warning",
            "detail": "No W-2 Box 2 (federal withholding) found in extraction"
        }

    total = sum(v for _, v in w2_box2_values)
    if total <= 0:
        details = "; ".join(f"{doc} = ${float(cents(val)):,.2f}" for doc, val in w2_box2_values)
        return {
            "check": "federal_withholding",
            "status": "warning",
            "detail": f"Total federal withholding is $0 across all W-2s ({details}) — verify this is correct"
        }

    return {
        "check": "federal_withholding",
        "status": "pass",
        "detail": f"Federal withholding total: ${float(cents(total)):,.2f} across {len(w2_box2_values)} W-2(s)"
    }


def check_medicare_vs_wages(rows):
    """For each W-2, Box 5 (Medicare wages) should be >= Box 1 (wages)."""
    w2_data = defaultdict(dict)
    for row in rows:
        doc = row.get("document", "")
        box = row.get("box_or_line", "")
        if "W-2" in doc and box in ("Box 1", "Box 5"):
            val = d(row.get("value", "0"))
            if val is not None:
                w2_data[doc][box] = val

    issues = []
    for doc, boxes in w2_data.items():
        wages = boxes.get("Box 1")
        medicare = boxes.get("Box 5")
        if wages is not None and medicare is not None and medicare < wages:
            issues.append(
                f"{doc}: Medicare wages (${float(cents(medicare)):,.2f}) < wages (${float(cents(wages)):,.2f})"
            )

    if issues:
        return {
            "check": "medicare_vs_wages",
            "status": "warning",
            "detail": f"Medicare wages below regular wages: {'; '.join(issues)}"
        }
    return {
        "check": "medicare_vs_wages",
        "status": "pass",
        "detail": "Medicare wages >= regular wages for all W-2s"
    }


def check_state_withholding(rows):
    """If W-2 state data exists (Box 15-17), withholding (Box 17) should be > 0."""
    w2_state_data = defaultdict(dict)
    for row in rows:
        doc = row.get("document", "")
        box = row.get("box_or_line", "")
        if "W-2" in doc and box in ("Box 15", "Box 16", "Box 17"):
            w2_state_data[doc][box] = row.get("value", "")

    issues = []
    for doc, boxes in w2_state_data.items():
        if "Box 15" in boxes or "Box 16" in boxes:
            box17_val = d(boxes.get("Box 17", "0"))
            if box17_val is not None and box17_val <= 0:
                issues.append(f"{doc}: has state info but Box 17 withholding is $0")

    if issues:
        return {
            "check": "state_withholding",
            "status": "warning",
            "detail": f"State withholding missing: {'; '.join(issues)}"
        }
    return {
        "check": "state_withholding",
        "status": "pass",
        "detail": "State withholding present for all W-2s with state data"
    }


def check_1099b_cost_basis(rows):
    """If 1099-B proceeds (Box 1d) exist, cost basis (Box 1e) should also exist."""
    docs_with_proceeds = set()
    docs_with_basis = set()
    for row in rows:
        doc = row.get("document", "")
        box = row.get("box_or_line", "")
        if "1099-B" in doc:
            if box == "Box 1d":
                docs_with_proceeds.add(doc)
            if box == "Box 1e":
                docs_with_basis.add(doc)

    missing = docs_with_proceeds - docs_with_basis
    if missing:
        return {
            "check": "1099b_cost_basis",
            "status": "warning",
            "detail": f"1099-B proceeds without cost basis: {'; '.join(missing)} — basis may need manual entry"
        }
    return {
        "check": "1099b_cost_basis",
        "status": "pass",
        "detail": "All 1099-B entries have both proceeds and cost basis"
    }


def check_duplicates(rows):
    """Flag duplicate document+box combinations."""
    keys = [(row.get("document", ""), row.get("box_or_line", "")) for row in rows]
    counts = Counter(keys)
    duplicates = [(doc, box, count) for (doc, box), count in counts.items() if count > 1]

    if duplicates:
        detail_parts = [f"{doc} {box} appears {count}x" for doc, box, count in duplicates[:5]]
        return {
            "check": "no_duplicates",
            "status": "warning",
            "detail": f"Duplicate entries found: {'; '.join(detail_parts)}"
        }
    return {
        "check": "no_duplicates",
        "status": "pass",
        "detail": f"No duplicate document+box combinations in {len(rows)} rows"
    }


def check_income_sanity(rows):
    """Sum of major income values should be positive and finite."""
    income_boxes = {"Box 1", "Box 1a"}
    total = Decimal("0")
    count = 0
    for row in rows:
        box = row.get("box_or_line", "")
        doc = row.get("document", "")
        if box in income_boxes and ("W-2" in doc or "1099" in doc):
            val = d(row.get("value", "0"))
            if val is not None:
                total += val
                count += 1

    if count == 0:
        return {
            "check": "income_sanity",
            "status": "warning",
            "detail": "No income values (W-2 Box 1 or 1099 Box 1a) found"
        }
    if total <= 0:
        return {
            "check": "income_sanity",
            "status": "warning",
            "detail": f"Total income across {count} entries is ${float(cents(total)):,.2f} — expected positive"
        }
    return {
        "check": "income_sanity",
        "status": "pass",
        "detail": f"Total income: ${float(cents(total)):,.2f} across {count} income entries"
    }


def check_mortgage_property_tax(rows):
    """If 1098 mortgage data exists, check for property tax (Box 4 or separate doc)."""
    has_1098 = False
    has_property_tax = False
    for row in rows:
        doc = row.get("document", "")
        box = row.get("box_or_line", "")
        desc = row.get("description", "").lower()
        if "1098" in doc and "1098-E" not in doc and "1098-T" not in doc:
            has_1098 = True
            if box == "Box 4" or "property tax" in desc:
                val = d(row.get("value", "0"))
                if val is not None and val > 0:
                    has_property_tax = True

    if has_1098 and not has_property_tax:
        return {
            "check": "mortgage_property_tax",
            "status": "warning",
            "detail": "1098 mortgage data found but no property tax value — property tax is often on a separate statement"
        }
    if not has_1098:
        return {
            "check": "mortgage_property_tax",
            "status": "pass",
            "detail": "No mortgage data — property tax check not applicable"
        }
    return {
        "check": "mortgage_property_tax",
        "status": "pass",
        "detail": "Mortgage data and property tax both present"
    }


def check_rental_completeness(rows):
    """Each 'Rental (...)' document should have rents (Line 3) and
    depreciation inputs (basis/placed-in-service rows).

    Depreciation is 'allowed or allowable' — a rental without basis data
    cannot compute Line 18 and will misstate income.
    (Source: rental-depreciation.md, Allowed or Allowable)
    """
    rentals = {}
    for row in rows:
        doc = row.get("document", "")
        if doc.upper().startswith("RENTAL"):
            info = rentals.setdefault(doc, {"has_rents": False, "has_basis": False})
            box = row.get("box_or_line", "")
            desc = row.get("description", "").lower()
            if box == "Line 3":
                info["has_rents"] = True
            if "basis" in desc or "placed in service" in desc:
                info["has_basis"] = True

    if not rentals:
        return {
            "check": "rental_completeness",
            "status": "pass",
            "detail": "No rental property records in extraction"
        }

    issues = []
    for doc, info in rentals.items():
        if not info["has_rents"]:
            issues.append(f"{doc}: no Line 3 (rents received) row")
        if not info["has_basis"]:
            issues.append(f"{doc}: no basis/placed-in-service rows — Line 18 depreciation cannot be computed")

    if issues:
        return {
            "check": "rental_completeness",
            "status": "warning",
            "detail": "; ".join(issues)
        }
    return {
        "check": "rental_completeness",
        "status": "pass",
        "detail": f"All {len(rentals)} rental record(s) have rents and depreciation inputs"
    }


def check_document_count(rows):
    """Report document count and warn if suspiciously low for a joint filer."""
    documents = set(row.get("document", "") for row in rows)
    count = len(documents)

    if count == 0:
        return {
            "check": "document_count",
            "status": "warning",
            "detail": "No documents found in extraction"
        }
    if count == 1:
        return {
            "check": "document_count",
            "status": "warning",
            "detail": f"Only 1 document extracted ({list(documents)[0]}). If filing jointly, check for spouse's documents."
        }
    return {
        "check": "document_count",
        "status": "pass",
        "detail": f"{count} distinct documents extracted"
    }


def build_document_inventory(rows):
    """Build a per-document summary of extracted boxes."""
    inventory = defaultdict(int)
    for row in rows:
        doc = row.get("document", "")
        inventory[doc] += 1
    return [{"document": doc, "boxes_extracted": count} for doc, count in sorted(inventory.items())]


def validate(data):
    """Run all validation checks on the extracted CSV."""
    csv_path = data.get("csv_path", "")

    if not csv_path or not os.path.exists(csv_path):
        return {"error": f"CSV file not found: {csv_path}"}

    rows = parse_rows(csv_path)
    if not rows:
        return {"error": "CSV file is empty or has no data rows"}

    results = [
        check_valid_amounts(rows),
        check_positive_amounts(rows),
        check_federal_withholding(rows),
        check_medicare_vs_wages(rows),
        check_state_withholding(rows),
        check_1099b_cost_basis(rows),
        check_duplicates(rows),
        check_income_sanity(rows),
        check_mortgage_property_tax(rows),
        check_rental_completeness(rows),
        check_document_count(rows),
    ]

    passed = sum(1 for r in results if r["status"] == "pass")
    warnings = sum(1 for r in results if r["status"] == "warning")
    failed = sum(1 for r in results if r["status"] == "fail")

    return {
        "validation_results": results,
        "summary": {
            "total_checks": len(results),
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "total_rows": len(rows),
            "unique_documents": len(set(row.get("document", "") for row in rows))
        },
        "document_inventory": build_document_inventory(rows)
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: validate_extraction.py '{\"csv_path\": \"analysis/tax-doc-summary.csv\"}' "}))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = validate(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
