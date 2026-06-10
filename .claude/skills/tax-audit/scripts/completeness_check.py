"""
completeness_check.py — Document coverage, required forms detection,
and orphaned document identification.

Usage:
    python completeness_check.py '{"csv_path": "analysis/tax-doc-summary.csv", "forms_filed": ["1040", "Schedule A", "Schedule B", "Schedule D", "GA 500"], "filing_status": "MFJ"}'

Reads the extracted tax document CSV and checks:
1. Every document is mapped to at least one filed form
2. All required schedules/forms are filed based on income types
3. No orphaned (unrecognized) documents exist

Thresholds from reference/curated/2025-tax-numbers.md and
reference/curated/additional-medicare-tax.md.
"""

import csv
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def d(val):
    """Convert to Decimal. Returns Decimal('0') for None or non-numeric."""
    if val is None:
        return Decimal("0")
    try:
        return Decimal(str(val).replace(",", "").strip())
    except Exception:
        return Decimal("0")


def cents(val):
    """Round to nearest cent."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt(val):
    """Format a Decimal as a dollar string for display."""
    return f"${float(cents(val)):,.2f}"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Schedule B threshold (Source: 2025-tax-numbers.md, Other Key Federal Numbers)
SCHEDULE_B_THRESHOLD = Decimal("1500")

# Additional Medicare Tax thresholds (Source: additional-medicare-tax.md)
MEDICARE_THRESHOLD = {
    "MFJ": Decimal("250000"),
    "Single": Decimal("200000"),
    "MFS": Decimal("125000"),
    "HoH": Decimal("200000"),
}

# SE tax threshold (Source: 2025-tax-numbers.md, Other Key Federal Numbers)
SE_TAX_THRESHOLD = Decimal("400")

# Document type to forms mapping
# Each key is a document type prefix (case-insensitive match).
# Each value is a list of forms that this document feeds into.
DOC_TO_FORMS = {
    "W-2": ["1040", "Schedule A"],
    "1099-INT": ["1040", "Schedule B"],
    "1099-DIV": ["1040", "Schedule B", "Schedule D"],
    "1099-B": ["Schedule D", "Form 8949"],
    "1099-K": ["Schedule C"],
    "1098-E": ["Schedule 1"],
    "1098-T": ["1040"],
    "1098": ["Schedule A"],
    "1099-NEC": ["Schedule C"],
    "1099-R": ["1040"],
    "1099-G": ["Schedule 1", "1040"],
    "1099-SA": ["1040"],
    "1099-MISC": ["Schedule E"],
    "1095-C": [],
    "W-2G": ["1040", "Schedule 1"],
    # Rental property records (property manager statements, expense logs)
    # use document labels like "Rental (123 Main St)" — see tax-prep SKILL.md
    "RENTAL": ["Schedule E"],
}

# Known document type prefixes for detection
DOC_TYPE_ORDER = [
    "1099-INT", "1099-DIV", "1099-NEC", "1099-SA", "1099-B", "1099-K",
    "1099-MISC", "1099-R", "1099-G", "1098-E", "1098-T", "1098", "1095-C",
    "W-2G", "W-2", "RENTAL",
]


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

def parse_rows(csv_path):
    """Read the CSV and return a list of row dicts."""
    rows = []
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def detect_doc_type(doc_name):
    """Detect document type from the document name.

    Checks longer prefixes first to avoid '1098' matching '1098-E'.
    """
    upper = doc_name.upper()
    for prefix in DOC_TYPE_ORDER:
        if prefix.upper() in upper:
            return prefix
    return None


def normalize_form(form_name):
    """Normalize form name for comparison (case-insensitive, strip whitespace)."""
    return form_name.strip().lower()


def form_filed(forms_filed, form_name):
    """Check if a form appears in the filed forms list (case-insensitive)."""
    target = normalize_form(form_name)
    return any(normalize_form(f) == target for f in forms_filed)


# ---------------------------------------------------------------------------
# Check A: Document coverage
# ---------------------------------------------------------------------------

def check_document_coverage(rows, forms_filed):
    """For each distinct document in CSV, check if its expected forms are filed."""
    documents = {}
    for row in rows:
        doc = row.get("document", "")
        if doc and doc not in documents:
            documents[doc] = detect_doc_type(doc)

    coverage = []
    for doc, doc_type in documents.items():
        if doc_type is None:
            coverage.append({
                "document": doc,
                "type": "unknown",
                "status": "orphaned",
                "maps_to": [],
                "detail": "Unrecognized document type"
            })
            continue

        expected_forms = DOC_TO_FORMS.get(doc_type, [])
        if not expected_forms:
            # Document type recognized but has no form mapping (e.g., 1095-C)
            coverage.append({
                "document": doc,
                "type": doc_type,
                "status": "mapped",
                "maps_to": ["Reference only"],
                "detail": f"{doc_type} is informational — no form lines required"
            })
            continue

        # Check if at least one expected form is filed
        filed_matches = [f for f in expected_forms if form_filed(forms_filed, f)]
        if filed_matches:
            coverage.append({
                "document": doc,
                "type": doc_type,
                "status": "mapped",
                "maps_to": filed_matches,
                "detail": f"{doc_type} feeds into {', '.join(filed_matches)}"
            })
        else:
            coverage.append({
                "document": doc,
                "type": doc_type,
                "status": "unmapped",
                "maps_to": expected_forms,
                "detail": f"{doc_type} expects {', '.join(expected_forms)} but none are filed"
            })

    return coverage


# ---------------------------------------------------------------------------
# Check B: Required forms
# ---------------------------------------------------------------------------

def check_required_forms(rows, forms_filed, filing_status):
    """Determine which forms/schedules are required based on CSV content."""
    required = []

    # --- 1040 is always required ---
    required.append({
        "form": "1040",
        "status": "required",
        "reason": "Primary federal return — always required",
        "filed": form_filed(forms_filed, "1040")
    })

    # --- Schedule B: interest or dividends > $1,500 ---
    # (Source: 2025-tax-numbers.md, Other Key Federal Numbers)
    interest_total = Decimal("0")
    dividend_total = Decimal("0")
    for row in rows:
        doc = row.get("document", "").upper()
        box = row.get("box_or_line", "")
        val = d(row.get("value", "0"))
        if "1099-INT" in doc and box == "Box 1":
            interest_total += val
        if "1099-DIV" in doc and box == "Box 1a":
            dividend_total += val

    if interest_total > SCHEDULE_B_THRESHOLD or dividend_total > SCHEDULE_B_THRESHOLD:
        amounts = []
        if interest_total > SCHEDULE_B_THRESHOLD:
            amounts.append(f"interest {fmt(interest_total)}")
        if dividend_total > SCHEDULE_B_THRESHOLD:
            amounts.append(f"dividends {fmt(dividend_total)}")
        required.append({
            "form": "Schedule B",
            "status": "required",
            "reason": f"Taxable {' and '.join(amounts)} exceeds $1,500 threshold",
            "filed": form_filed(forms_filed, "Schedule B")
        })

    # --- Schedule C: 1099-K or 1099-NEC present ---
    has_1099k = any("1099-K" in row.get("document", "").upper() for row in rows)
    has_1099nec = any("1099-NEC" in row.get("document", "").upper() for row in rows)
    if has_1099k or has_1099nec:
        sources = []
        if has_1099k:
            sources.append("1099-K")
        if has_1099nec:
            sources.append("1099-NEC")
        required.append({
            "form": "Schedule C",
            "status": "required",
            "reason": f"Business income documents present: {', '.join(sources)}",
            "filed": form_filed(forms_filed, "Schedule C")
        })

    # --- Schedule E: 1099-MISC rents or rental property records ---
    # (Source: schedule-e-guide.md)
    has_1099misc = any("1099-MISC" in row.get("document", "").upper() for row in rows)
    has_rental = any(row.get("document", "").upper().startswith("RENTAL") for row in rows)
    if has_1099misc or has_rental:
        sources = []
        if has_1099misc:
            sources.append("1099-MISC")
        if has_rental:
            sources.append("rental property records")
        required.append({
            "form": "Schedule E",
            "status": "required",
            "reason": f"Rental income documents present: {', '.join(sources)}",
            "filed": form_filed(forms_filed, "Schedule E")
        })
        required.append({
            "form": "Form 8582",
            "status": "recommended",
            "reason": "Rental activity present — required if there is a rental loss or prior suspended passive losses (see passive-activity-losses.md for the exception conditions)",
            "filed": form_filed(forms_filed, "Form 8582")
        })
        required.append({
            "form": "Form 4562",
            "status": "recommended",
            "reason": "Required if property/assets were placed in service this year or bonus depreciation is claimed (see rental-depreciation.md)",
            "filed": form_filed(forms_filed, "Form 4562")
        })

    # --- Schedule D: 1099-B or capital gain distributions ---
    has_1099b = any("1099-B" in row.get("document", "").upper() for row in rows)
    has_cap_gain_dist = False
    for row in rows:
        if "1099-DIV" in row.get("document", "").upper() and row.get("box_or_line", "") == "Box 2a":
            val = d(row.get("value", "0"))
            if val > 0:
                has_cap_gain_dist = True
                break
    if has_1099b or has_cap_gain_dist:
        sources = []
        if has_1099b:
            sources.append("1099-B")
        if has_cap_gain_dist:
            sources.append("1099-DIV Box 2a (capital gain distributions)")
        required.append({
            "form": "Schedule D",
            "status": "required",
            "reason": f"Capital gains/losses: {', '.join(sources)}",
            "filed": form_filed(forms_filed, "Schedule D")
        })

    # --- Schedule 1: if Schedule C is present, or 1098-E, or 1099-G ---
    has_sched_c = has_1099k or has_1099nec
    has_sched_e = has_1099misc or has_rental
    has_1098e = any("1098-E" in row.get("document", "").upper() for row in rows)
    has_1099g = any("1099-G" in row.get("document", "").upper() for row in rows)
    if has_sched_c or has_sched_e or has_1098e or has_1099g:
        reasons = []
        if has_sched_c:
            reasons.append("Schedule C flows through Schedule 1 Line 3")
        if has_sched_e:
            reasons.append("Schedule E flows through Schedule 1 Line 5")
        if has_1098e:
            reasons.append("Student loan interest on Schedule 1 Line 21")
        if has_1099g:
            reasons.append("State refund/unemployment on Schedule 1")
        required.append({
            "form": "Schedule 1",
            "status": "required",
            "reason": "; ".join(reasons),
            "filed": form_filed(forms_filed, "Schedule 1")
        })

    # --- Form 8959 + Schedule 2: Medicare wages > threshold ---
    # (Source: additional-medicare-tax.md, Tax Rate and Thresholds)
    medicare_total = Decimal("0")
    for row in rows:
        if "W-2" in row.get("document", "").upper() and row.get("box_or_line", "") == "Box 5":
            medicare_total += d(row.get("value", "0"))

    threshold = MEDICARE_THRESHOLD.get(filing_status, Decimal("200000"))
    if medicare_total > threshold:
        excess = medicare_total - threshold
        required.append({
            "form": "Form 8959",
            "status": "required",
            "reason": f"Medicare wages ({fmt(medicare_total)}) exceed {filing_status} threshold ({fmt(threshold)}) by {fmt(excess)}",
            "filed": form_filed(forms_filed, "Form 8959")
        })
        required.append({
            "form": "Schedule 2",
            "status": "required",
            "reason": "Form 8959 Additional Medicare Tax flows to Schedule 2 Line 11",
            "filed": form_filed(forms_filed, "Schedule 2")
        })

    # --- Form 8995 (QBI): recommended if Schedule C present ---
    # (Source: self-employment-qbi.md, QBI Deduction)
    if has_sched_c:
        required.append({
            "form": "Form 8995",
            "status": "recommended",
            "reason": "Schedule C business income — file Form 8995 for QBI deduction (or to establish loss carryforward)",
            "filed": form_filed(forms_filed, "Form 8995")
        })

    # --- GA 500: if any W-2 has Georgia state data ---
    has_ga = False
    for row in rows:
        doc = row.get("document", "").upper()
        box = row.get("box_or_line", "")
        val = row.get("value", "").upper()
        if "W-2" in doc and box == "Box 15" and "GA" in val:
            has_ga = True
            break
        # Also check if Box 16 or 17 exist for W-2s (some CSVs may not have Box 15)
        if "W-2" in doc and box in ("Box 16", "Box 17"):
            has_ga = True

    if has_ga:
        required.append({
            "form": "GA 500",
            "status": "required",
            "reason": "W-2 contains Georgia state wage/withholding data",
            "filed": form_filed(forms_filed, "GA 500")
        })

    # --- Schedule A: if itemizing (check for 1098 mortgage data) ---
    has_1098 = any(
        "1098" in row.get("document", "").upper()
        and "1098-E" not in row.get("document", "").upper()
        and "1098-T" not in row.get("document", "").upper()
        for row in rows
    )
    if has_1098:
        required.append({
            "form": "Schedule A",
            "status": "recommended",
            "reason": "1098 mortgage data present — may benefit from itemizing",
            "filed": form_filed(forms_filed, "Schedule A")
        })

    return required


# ---------------------------------------------------------------------------
# Check C: Orphaned documents
# ---------------------------------------------------------------------------

def find_orphaned(coverage):
    """Extract orphaned documents from coverage results."""
    return [c for c in coverage if c["status"] == "orphaned"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def completeness_check(data):
    """Run all completeness checks and return results."""
    csv_path = data.get("csv_path", "")
    forms_filed = data.get("forms_filed", [])
    filing_status = data.get("filing_status", "MFJ")

    if not csv_path or not os.path.exists(csv_path):
        return {"error": f"CSV file not found: {csv_path}"}

    rows = parse_rows(csv_path)
    if not rows:
        return {"error": "CSV file is empty or has no data rows"}

    # Run checks
    coverage = check_document_coverage(rows, forms_filed)
    required = check_required_forms(rows, forms_filed, filing_status)
    orphaned = find_orphaned(coverage)

    # Compute summary
    total_docs = len(coverage)
    mapped = sum(1 for c in coverage if c["status"] == "mapped")
    unmapped = sum(1 for c in coverage if c["status"] == "unmapped")
    orphaned_count = len(orphaned)

    forms_required = sum(1 for r in required if r["status"] == "required")
    forms_recommended = sum(1 for r in required if r["status"] == "recommended")
    forms_required_filed = sum(1 for r in required if r["status"] == "required" and r["filed"])
    forms_required_missing = forms_required - forms_required_filed

    # Verdict
    if unmapped > 0 or forms_required_missing > 0:
        verdict = "incomplete"
    elif orphaned_count > 0 or any(r["status"] == "recommended" and not r["filed"] for r in required):
        verdict = "warning"
    else:
        verdict = "complete"

    return {
        "document_coverage": coverage,
        "required_forms": required,
        "orphaned_documents": orphaned,
        "summary": {
            "total_documents": total_docs,
            "mapped": mapped,
            "unmapped": unmapped,
            "orphaned": orphaned_count,
            "forms_required": forms_required,
            "forms_required_filed": forms_required_filed,
            "forms_required_missing": forms_required_missing,
            "forms_recommended": forms_recommended,
        },
        "verdict": verdict,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: completeness_check.py \'{"csv_path": "...", "forms_filed": [...], "filing_status": "MFJ"}\''
        }))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = completeness_check(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
