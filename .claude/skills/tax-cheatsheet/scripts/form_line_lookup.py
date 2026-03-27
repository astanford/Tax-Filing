"""
form_line_lookup.py — Look up values from the tax-doc-summary CSV.

Usage:
    python form_line_lookup.py '{"csv_path": "analysis/tax-doc-summary.csv", "document_filter": "W-2", "box_filter": "Box 1", "operation": "sum"}'

Filters CSV rows by document type and box/line, returns matching values
or their sum. Operations: "sum", "list", "first".
"""

import csv
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP


def d(val):
    """Convert to Decimal. Returns None for non-numeric values."""
    if val is None:
        return None
    try:
        return Decimal(str(val).replace(",", "").strip())
    except Exception:
        return None


def cents(val):
    """Round to nearest cent."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_rows(csv_path):
    """Read the CSV and return a list of row dicts."""
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def lookup(data):
    """Filter CSV rows by document type and box, return matches."""
    csv_path = data.get("csv_path", "")
    doc_filter = data.get("document_filter", "")
    box_filter = data.get("box_filter", "")
    operation = data.get("operation", "list")

    if not csv_path or not os.path.exists(csv_path):
        return {"error": f"CSV file not found: {csv_path}"}

    rows = parse_rows(csv_path)
    if not rows:
        return {"error": "CSV file is empty or has no data rows"}

    # Filter rows
    matches = []
    for row in rows:
        doc = row.get("document", "")
        box = row.get("box_or_line", "")

        doc_match = (not doc_filter) or (doc_filter.lower() in doc.lower())
        box_match = (not box_filter) or (box.strip().lower() == box_filter.strip().lower())

        if doc_match and box_match:
            matches.append({
                "document": doc,
                "box_or_line": box,
                "description": row.get("description", ""),
                "value": row.get("value", ""),
                "source_path": row.get("source_path", "")
            })

    # Compute sum of numeric values
    total = Decimal("0")
    numeric_count = 0
    for m in matches:
        val = d(m["value"])
        if val is not None:
            total += val
            numeric_count += 1

    result = {
        "matches": matches,
        "count": len(matches),
        "numeric_count": numeric_count,
        "sum": str(cents(total)) if numeric_count > 0 else "0.00",
        "operation": operation
    }

    if operation == "first" and matches:
        result["first"] = matches[0]
    elif operation == "first" and not matches:
        result["first"] = None

    return result


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: form_line_lookup.py \'{"csv_path": "...", "document_filter": "W-2", "box_filter": "Box 1", "operation": "sum"}\''
        }))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = lookup(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
