"""
cross_check.py — Federal/state consistency, withholding match, AGI math,
and tax bracket verification.

Usage:
    python cross_check.py '{"csv_path": "analysis/tax-doc-summary.csv", "federal_values": {"line_1_wages": "85000.00", "line_2b_interest": "200.00", "line_3b_dividends": "350.00", "line_7_capital_gain": "0.00", "line_8_other_income": "0.00", "line_9_total_income": "85550.00", "line_10_adjustments": "0.00", "line_11_agi": "85550.00", "line_12a_deduction": "31500.00", "line_13a_qbi": "0.00", "line_13b_sched1a": "0.00", "line_14_total_deductions": "31500.00", "line_15_taxable_income": "54050.00", "line_16_tax": "6197.00", "line_25a_w2_withholding": "9500.00"}, "state_values": {"line_1_agi": "85550.00", "line_40_withholding": "5200.00"}, "filing_status": "MFJ"}'

Reads the extracted tax document CSV and the user's completed form values,
then runs 10 cross-checks comparing source documents to form entries.

Tolerance: $1.00 for rounding (IRS rounds to whole dollars on forms).

Constants from reference/curated/2025-tax-numbers.md.
"""

import csv
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Helpers (matching validate_extraction.py pattern)
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


def whole(val):
    """Round to nearest dollar."""
    return val.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def fmt(val):
    """Format a Decimal as a dollar string for display."""
    return f"${float(cents(val)):,.2f}"


TOLERANCE = Decimal("1.00")


def compare(expected, actual):
    """Return status based on difference vs tolerance."""
    diff = abs(expected - actual)
    if diff <= TOLERANCE:
        return "pass"
    return "fail"


# ---------------------------------------------------------------------------
# Federal Income Tax Brackets — 2025
# (Source: 2025-tax-numbers.md, Federal Income Tax Brackets)
#
# Each tuple: (upper_bound, rate, base_tax_at_lower_bound)
# upper_bound=None means no ceiling (top bracket).
# ---------------------------------------------------------------------------

FEDERAL_BRACKETS = {
    "MFJ": [
        (Decimal("23850"),  Decimal("0.10"), Decimal("0")),
        (Decimal("96950"),  Decimal("0.12"), Decimal("2385")),
        (Decimal("206700"), Decimal("0.22"), Decimal("11157")),
        (Decimal("394600"), Decimal("0.24"), Decimal("35302")),
        (Decimal("501050"), Decimal("0.32"), Decimal("80398")),
        (Decimal("751600"), Decimal("0.35"), Decimal("114462")),
        (None,              Decimal("0.37"), Decimal("188770")),
    ],
    # Single and HoH brackets can be added here when needed.
    # For now, MFJ is the primary use case.
}

# Alias: MFS uses half the MFJ bracket widths, but for a first pass we only
# support MFJ. Other statuses will produce a warning, not a failure.


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


def sum_csv(rows, doc_filter, box_filter):
    """Sum numeric values from CSV rows matching document and box filters.

    doc_filter: case-insensitive substring match on 'document' column.
    box_filter: exact match on 'box_or_line' column.
    """
    total = Decimal("0")
    count = 0
    for row in rows:
        doc = row.get("document", "")
        box = row.get("box_or_line", "")
        if doc_filter.lower() in doc.lower() and box == box_filter:
            val = d(row.get("value", "0"))
            total += val
            count += 1
    return total, count


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_wages_match(rows, fv):
    """Check 1: 1040 Line 1 vs sum of W-2 Box 1 from CSV."""
    csv_sum, count = sum_csv(rows, "W-2", "Box 1")
    form_val = d(fv.get("line_1_wages"))
    status = compare(csv_sum, form_val)
    return {
        "check_name": "wages_match",
        "category": "Internal Consistency",
        "status": status,
        "expected": str(cents(csv_sum)),
        "actual": str(cents(form_val)),
        "difference": str(cents(abs(csv_sum - form_val))),
        "detail": f"1040 Line 1 ({fmt(form_val)}) vs sum of {count} W-2 Box 1 ({fmt(csv_sum)})"
    }


def check_interest_match(rows, fv):
    """Check 2: 1040 Line 2b vs sum of 1099-INT Box 1 from CSV."""
    csv_sum, count = sum_csv(rows, "1099-INT", "Box 1")
    form_val = d(fv.get("line_2b_interest"))
    status = compare(csv_sum, form_val)
    return {
        "check_name": "interest_match",
        "category": "Internal Consistency",
        "status": status,
        "expected": str(cents(csv_sum)),
        "actual": str(cents(form_val)),
        "difference": str(cents(abs(csv_sum - form_val))),
        "detail": f"1040 Line 2b ({fmt(form_val)}) vs sum of {count} 1099-INT Box 1 ({fmt(csv_sum)})"
    }


def check_dividends_match(rows, fv):
    """Check 3: 1040 Line 3b vs sum of 1099-DIV Box 1a from CSV."""
    csv_sum, count = sum_csv(rows, "1099-DIV", "Box 1a")
    form_val = d(fv.get("line_3b_dividends"))
    status = compare(csv_sum, form_val)
    return {
        "check_name": "dividends_match",
        "category": "Internal Consistency",
        "status": status,
        "expected": str(cents(csv_sum)),
        "actual": str(cents(form_val)),
        "difference": str(cents(abs(csv_sum - form_val))),
        "detail": f"1040 Line 3b ({fmt(form_val)}) vs sum of {count} 1099-DIV Box 1a ({fmt(csv_sum)})"
    }


def check_total_income(fv):
    """Check 4: Line 9 = Line 1 + 2b + 3b + 7 + 8."""
    line_1 = d(fv.get("line_1_wages"))
    line_2b = d(fv.get("line_2b_interest"))
    line_3b = d(fv.get("line_3b_dividends"))
    line_7 = d(fv.get("line_7_capital_gain"))
    line_8 = d(fv.get("line_8_other_income"))
    expected = line_1 + line_2b + line_3b + line_7 + line_8
    actual = d(fv.get("line_9_total_income"))
    status = compare(expected, actual)
    return {
        "check_name": "total_income",
        "category": "Math Verification",
        "status": status,
        "expected": str(cents(expected)),
        "actual": str(cents(actual)),
        "difference": str(cents(abs(expected - actual))),
        "detail": f"Line 9 should be {fmt(expected)} (sum of Lines 1+2b+3b+7+8), entered as {fmt(actual)}"
    }


def check_agi(fv):
    """Check 5: Line 11 = Line 9 - Line 10."""
    line_9 = d(fv.get("line_9_total_income"))
    line_10 = d(fv.get("line_10_adjustments"))
    expected = line_9 - line_10
    actual = d(fv.get("line_11_agi"))
    status = compare(expected, actual)
    return {
        "check_name": "agi_calculation",
        "category": "Math Verification",
        "status": status,
        "expected": str(cents(expected)),
        "actual": str(cents(actual)),
        "difference": str(cents(abs(expected - actual))),
        "detail": f"Line 11 (AGI) should be {fmt(expected)} (Line 9 {fmt(line_9)} - Line 10 {fmt(line_10)}), entered as {fmt(actual)}"
    }


def check_taxable_income(fv):
    """Check 6: Line 15 = Line 11 - Line 14; Line 14 = 12a + 13a + 13b."""
    line_12a = d(fv.get("line_12a_deduction"))
    line_13a = d(fv.get("line_13a_qbi"))
    line_13b = d(fv.get("line_13b_sched1a"))
    expected_14 = line_12a + line_13a + line_13b
    actual_14 = d(fv.get("line_14_total_deductions"))

    line_11 = d(fv.get("line_11_agi"))
    expected_15 = max(line_11 - actual_14, Decimal("0"))
    actual_15 = d(fv.get("line_15_taxable_income"))

    # Check both Line 14 and Line 15
    issues = []
    if abs(expected_14 - actual_14) > TOLERANCE:
        issues.append(
            f"Line 14 should be {fmt(expected_14)} (12a+13a+13b), entered as {fmt(actual_14)}"
        )
    if abs(expected_15 - actual_15) > TOLERANCE:
        issues.append(
            f"Line 15 should be {fmt(expected_15)} (Line 11 - Line 14), entered as {fmt(actual_15)}"
        )

    status = "fail" if issues else "pass"
    detail = "; ".join(issues) if issues else (
        f"Line 14 = {fmt(actual_14)}, Line 15 = {fmt(actual_15)} — both correct"
    )

    return {
        "check_name": "taxable_income",
        "category": "Math Verification",
        "status": status,
        "expected": str(cents(expected_15)),
        "actual": str(cents(actual_15)),
        "difference": str(cents(abs(expected_15 - actual_15))),
        "detail": detail
    }


def check_federal_withholding(rows, fv):
    """Check 7: 1040 Line 25a vs sum of W-2 Box 2 from CSV."""
    csv_sum, count = sum_csv(rows, "W-2", "Box 2")
    form_val = d(fv.get("line_25a_w2_withholding"))
    status = compare(csv_sum, form_val)
    return {
        "check_name": "federal_withholding",
        "category": "Withholding Match",
        "status": status,
        "expected": str(cents(csv_sum)),
        "actual": str(cents(form_val)),
        "difference": str(cents(abs(csv_sum - form_val))),
        "detail": f"1040 Line 25a ({fmt(form_val)}) vs sum of {count} W-2 Box 2 ({fmt(csv_sum)})"
    }


def check_state_withholding(rows, sv):
    """Check 8: MD 502 Line 40 vs sum of W-2 Box 17 from CSV."""
    csv_sum, count = sum_csv(rows, "W-2", "Box 17")
    form_val = d(sv.get("line_40_withholding"))
    status = compare(csv_sum, form_val)
    return {
        "check_name": "state_withholding",
        "category": "Withholding Match",
        "status": status,
        "expected": str(cents(csv_sum)),
        "actual": str(cents(form_val)),
        "difference": str(cents(abs(csv_sum - form_val))),
        "detail": f"MD 502 Line 40 ({fmt(form_val)}) vs sum of {count} W-2 Box 17 ({fmt(csv_sum)})"
    }


def check_fed_state_agi_match(fv, sv):
    """Check 9: 1040 Line 11 = MD 502 Line 1."""
    fed_agi = d(fv.get("line_11_agi"))
    state_agi = d(sv.get("line_1_agi"))
    status = compare(fed_agi, state_agi)
    return {
        "check_name": "fed_state_agi_match",
        "category": "Cross-Return Consistency",
        "status": status,
        "expected": str(cents(fed_agi)),
        "actual": str(cents(state_agi)),
        "difference": str(cents(abs(fed_agi - state_agi))),
        "detail": f"Federal AGI ({fmt(fed_agi)}) vs MD 502 Line 1 ({fmt(state_agi)})"
    }


def compute_ordinary_tax(taxable_income, filing_status):
    """Compute ordinary income tax using 2025 federal brackets.

    (Source: 2025-tax-numbers.md, Federal Income Tax Brackets)
    """
    brackets = FEDERAL_BRACKETS.get(filing_status)
    if brackets is None:
        return None  # Unsupported filing status

    for i, (ceiling, rate, base_tax) in enumerate(brackets):
        if ceiling is None or taxable_income <= ceiling:
            if i == 0:
                return cents(taxable_income * rate)
            prev_ceiling = brackets[i - 1][0]
            return cents(base_tax + (taxable_income - prev_ceiling) * rate)
    return Decimal("0")


def check_tax_bracket(fv, filing_status):
    """Check 10: Verify Line 16 tax against bracket computation.

    If the user has qualified dividends or long-term capital gains,
    Line 16 should be LESS than or equal to the ordinary tax (QDCG
    rates are lower). If Line 16 exceeds ordinary tax, that's a fail.

    (Source: 2025-tax-numbers.md, Federal Income Tax Brackets and
    Qualified Dividends and Capital Gain Tax Rates)
    """
    taxable_income = d(fv.get("line_15_taxable_income"))
    form_tax = d(fv.get("line_16_tax"))

    ordinary_tax = compute_ordinary_tax(taxable_income, filing_status)

    if ordinary_tax is None:
        return {
            "check_name": "tax_bracket_verify",
            "category": "Math Verification",
            "status": "warning",
            "expected": "N/A",
            "actual": str(cents(form_tax)),
            "difference": "N/A",
            "detail": f"Tax bracket verification not available for filing status '{filing_status}' — only MFJ supported. Verify manually."
        }

    diff = form_tax - ordinary_tax

    if diff > TOLERANCE:
        # Tax is HIGHER than ordinary — something is wrong
        return {
            "check_name": "tax_bracket_verify",
            "category": "Math Verification",
            "status": "fail",
            "expected": str(cents(ordinary_tax)),
            "actual": str(cents(form_tax)),
            "difference": str(cents(abs(diff))),
            "detail": f"Line 16 ({fmt(form_tax)}) exceeds ordinary tax ({fmt(ordinary_tax)}) by {fmt(abs(diff))}. Tax should never exceed ordinary rates."
        }

    if abs(diff) <= TOLERANCE:
        # Exact match — no QDCG adjustment or no preferential income
        return {
            "check_name": "tax_bracket_verify",
            "category": "Math Verification",
            "status": "pass",
            "expected": str(cents(ordinary_tax)),
            "actual": str(cents(form_tax)),
            "difference": str(cents(abs(diff))),
            "detail": f"Line 16 ({fmt(form_tax)}) matches ordinary tax computation ({fmt(ordinary_tax)})"
        }

    # Tax is less than ordinary — QDCG rates applied (expected)
    return {
        "check_name": "tax_bracket_verify",
        "category": "Math Verification",
        "status": "pass",
        "expected": str(cents(ordinary_tax)),
        "actual": str(cents(form_tax)),
        "difference": str(cents(abs(diff))),
        "detail": f"Line 16 ({fmt(form_tax)}) is {fmt(abs(diff))} less than ordinary tax ({fmt(ordinary_tax)}) — consistent with QDCG preferential rates"
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def cross_check(data):
    """Run all cross-checks and return results."""
    csv_path = data.get("csv_path", "")
    fv = data.get("federal_values", {})
    sv = data.get("state_values", {})
    filing_status = data.get("filing_status", "MFJ")

    if not csv_path or not os.path.exists(csv_path):
        return {"error": f"CSV file not found: {csv_path}"}

    rows = parse_rows(csv_path)
    if not rows:
        return {"error": "CSV file is empty or has no data rows"}

    checks = [
        check_wages_match(rows, fv),
        check_interest_match(rows, fv),
        check_dividends_match(rows, fv),
        check_total_income(fv),
        check_agi(fv),
        check_taxable_income(fv),
        check_federal_withholding(rows, fv),
        check_state_withholding(rows, sv),
        check_fed_state_agi_match(fv, sv),
        check_tax_bracket(fv, filing_status),
    ]

    passed = sum(1 for c in checks if c["status"] == "pass")
    warnings = sum(1 for c in checks if c["status"] == "warning")
    failed = sum(1 for c in checks if c["status"] == "fail")

    return {
        "checks": checks,
        "summary": {
            "total": len(checks),
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
        }
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: cross_check.py \'{"csv_path": "...", "federal_values": {...}, "state_values": {...}, "filing_status": "MFJ"}\''
        }))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = cross_check(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
