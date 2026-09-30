"""
cross_check.py — Federal/state consistency, withholding match, AGI math,
and tax bracket verification.

Usage:
    python cross_check.py '{"csv_path": "analysis/tax-doc-summary.csv", "federal_values": {"line_1_wages": "85000.00", "line_2b_interest": "200.00", "line_3b_dividends": "350.00", "line_7_capital_gain": "0.00", "line_8_other_income": "0.00", "line_9_total_income": "85550.00", "line_10_adjustments": "0.00", "line_11_agi": "85550.00", "line_12a_deduction": "31500.00", "line_13a_qbi": "0.00", "line_13b_sched1a": "0.00", "line_14_total_deductions": "31500.00", "line_15_taxable_income": "54050.00", "line_16_tax": "6197.00", "line_25a_w2_withholding": "9500.00"}, "state_values": {"line_8_fagi": "85550.00", "line_24_withholding": "4400.00"}, "filing_status": "MFJ"}'

Reads the extracted tax document CSV and the user's completed form values,
then runs 10 core cross-checks (plus optional Schedule E, K-1, payments and rents checks)
comparing source documents to form entries. Also accepts engine/return_engine.py
output via "engine_result" / "engine_result_path".

Tolerance: $100.00 (user-directed; was $1.00). See TOLERANCE below.

Constants from reference/curated/2025-tax-numbers.md.
"""

import csv
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

# Shared 2025 constants live at the repo root (engine/constants_2025.py).
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.constants_2025 import FEDERAL_BRACKETS
from engine.tax_math import tax_from_table_or_schedule


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


# Tolerance for comparisons. Raised from $1.00 to $100.00 at the user's
# direction (2026-09-30): the return is prepared to "close enough," and the
# value still catches a missing or mistyped entry, which is the point of these
# checks. Note it does not catch small errors, and it applies to every
# comparison in this file.
TOLERANCE = Decimal("100.00")


def compare(expected, actual):
    """Return status based on difference vs tolerance."""
    diff = abs(expected - actual)
    if diff <= TOLERANCE:
        return "pass"
    return "fail"


# Federal brackets for all four filing statuses come from
# engine/constants_2025.py (Source: 2025-tax-numbers.md, Federal Income Tax
# Brackets; raw source reference/Raw/rp-24-40.pdf).


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


def sum_csv(rows, doc_filter, box_filter, prefix=False):
    """Sum numeric values from CSV rows matching document and box filters.

    doc_filter: case-insensitive substring match on 'document' column (or a
    prefix match when prefix=True).
    box_filter: exact match on 'box_or_line' column.
    """
    total = Decimal("0")
    count = 0
    for row in rows:
        doc = row.get("document", "").lower()
        box = row.get("box_or_line", "")
        needle = doc_filter.lower()
        hit = doc.startswith(needle) if prefix else needle in doc
        if hit and box == box_filter:
            total += d(row.get("value", "0"))
            count += 1
    return total, count


# ---------------------------------------------------------------------------
# Result builders
# ---------------------------------------------------------------------------

def _result(name, category, status, expected, actual, detail):
    diff = "N/A"
    if isinstance(expected, Decimal) and isinstance(actual, Decimal):
        diff = str(cents(abs(expected - actual)))
    return {
        "check_name": name,
        "category": category,
        "status": status,
        "expected": str(cents(expected)) if isinstance(expected, Decimal) else str(expected),
        "actual": str(cents(actual)) if isinstance(actual, Decimal) else str(actual),
        "difference": diff,
        "detail": detail,
    }


def _skipped(name, category, missing):
    return _result(name, category, "skipped", "N/A", "N/A",
                   "Not evaluated: missing input(s) " + ", ".join(missing))


def _missing(fv, keys):
    return [k for k in keys if k not in fv]


def _csv_vs_form(name, category, csv_sum, count, fv, key, form_label, csv_label):
    """Compare a CSV total to an entered form value.

    - nothing in the documents and nothing (or $0) entered: not_applicable
      (a 0 = 0 comparison verifies nothing, so it is not counted as a pass);
    - documents present but no entry provided: fail (an omitted line);
    - otherwise compare within TOLERANCE.
    """
    if key not in fv:
        if csv_sum == 0 and count == 0:
            return _result(name, category, "not_applicable", Decimal("0"), Decimal("0"),
                           f"{form_label} not provided and no {csv_label} in the documents")
        return _result(name, category, "fail", csv_sum, Decimal("0"),
                       f"{form_label} not provided, but {csv_label} total {fmt(csv_sum)} "
                       f"({count} rows)")
    form_val = d(fv[key])
    if count == 0 and form_val == 0:
        return _result(name, category, "not_applicable", csv_sum, form_val,
                       f"No {csv_label} in the documents and {form_label} is $0 — nothing to verify")
    return _result(name, category, compare(csv_sum, form_val), csv_sum, form_val,
                   f"{form_label} ({fmt(form_val)}) vs sum of {count} {csv_label} ({fmt(csv_sum)})")


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_wages_match(rows, fv):
    """Check 1: 1040 Line 1 vs sum of W-2 Box 1 from CSV."""
    s, n = sum_csv(rows, "W-2", "Box 1")
    return _csv_vs_form("wages_match", "Internal Consistency", s, n, fv,
                        "line_1_wages", "1040 Line 1", "W-2 Box 1")


def check_interest_match(rows, fv):
    """Check 2: 1040 Line 2b vs 1099-INT Box 1 plus K-1 Box 5 from the CSV."""
    s, n = sum_csv(rows, "1099-INT", "Box 1")
    k, kn = sum_csv(rows, "K-1", "Box 5", prefix=True)
    return _csv_vs_form("interest_match", "Internal Consistency", s + k, n + kn, fv,
                        "line_2b_interest", "1040 Line 2b", "1099-INT Box 1 and K-1 Box 5")


def check_dividends_match(rows, fv):
    """Check 3: 1040 Line 3b vs 1099-DIV Box 1a plus K-1 Box 6a from the CSV."""
    s, n = sum_csv(rows, "1099-DIV", "Box 1a")
    k, kn = sum_csv(rows, "K-1", "Box 6a", prefix=True)
    return _csv_vs_form("dividends_match", "Internal Consistency", s + k, n + kn, fv,
                        "line_3b_dividends", "1040 Line 3b", "1099-DIV Box 1a and K-1 Box 6a")


def check_total_income(fv):
    """Check 4: Line 9 = Lines 1 + 2b + 3b + 4b + 5b + 6b + 7 + 8."""
    name, cat = "total_income", "Math Verification"
    miss = _missing(fv, ["line_9_total_income"])
    if miss:
        return _skipped(name, cat, miss)
    keys = ("line_1_wages", "line_2b_interest", "line_3b_dividends", "line_4b_ira",
            "line_5b_pensions", "line_6b_social_security", "line_7_capital_gain",
            "line_8_other_income")
    expected = sum((d(fv.get(k)) for k in keys), Decimal("0"))
    actual = d(fv.get("line_9_total_income"))
    return _result(name, cat, compare(expected, actual), expected, actual,
                   f"Line 9 should be {fmt(expected)} (sum of Lines 1+2b+3b+4b+5b+6b+7+8), "
                   f"entered as {fmt(actual)}")


def check_agi(fv):
    """Check 5: Line 11 = Line 9 - Line 10."""
    name, cat = "agi_calculation", "Math Verification"
    miss = _missing(fv, ["line_9_total_income", "line_11_agi"])
    if miss:
        return _skipped(name, cat, miss)
    line_9 = d(fv.get("line_9_total_income"))
    line_10 = d(fv.get("line_10_adjustments"))
    expected = line_9 - line_10
    actual = d(fv.get("line_11_agi"))
    return _result(name, cat, compare(expected, actual), expected, actual,
                   f"Line 11 (AGI) should be {fmt(expected)} (Line 9 {fmt(line_9)} - "
                   f"Line 10 {fmt(line_10)}), entered as {fmt(actual)}")


def check_taxable_income(fv):
    """Check 6: Line 15 = Line 11 - Line 14; Line 14 = 12a + 13a + 13b."""
    name, cat = "taxable_income", "Math Verification"
    miss = _missing(fv, ["line_11_agi", "line_14_total_deductions", "line_15_taxable_income"])
    if miss:
        return _skipped(name, cat, miss)
    expected_14 = d(fv.get("line_12a_deduction")) + d(fv.get("line_13a_qbi")) + d(fv.get("line_13b_sched1a"))
    actual_14 = d(fv.get("line_14_total_deductions"))
    expected_15 = max(d(fv.get("line_11_agi")) - actual_14, Decimal("0"))
    actual_15 = d(fv.get("line_15_taxable_income"))

    issues = []
    if abs(expected_14 - actual_14) > TOLERANCE:
        issues.append(f"Line 14 should be {fmt(expected_14)} (12a+13a+13b), entered as {fmt(actual_14)}")
    if abs(expected_15 - actual_15) > TOLERANCE:
        issues.append(f"Line 15 should be {fmt(expected_15)} (Line 11 - Line 14), entered as {fmt(actual_15)}")
    detail = "; ".join(issues) if issues else (
        f"Line 14 = {fmt(actual_14)}, Line 15 = {fmt(actual_15)} — both correct")
    return _result(name, cat, "fail" if issues else "pass", expected_15, actual_15, detail)


def check_federal_withholding(rows, fv):
    """Check 7: 1040 Line 25a vs sum of W-2 Box 2 from CSV."""
    s, n = sum_csv(rows, "W-2", "Box 2")
    return _csv_vs_form("federal_withholding", "Withholding Match", s, n, fv,
                        "line_25a_w2_withholding", "1040 Line 25a", "W-2 Box 2")


def check_state_withholding(rows, sv):
    """Check 8: GA Form 500 Line 24 vs sum of W-2 Box 17 from CSV.

    (Source: georgia-500-guide.md, Payments and Balance Due, Line 24)
    """
    s, n = sum_csv(rows, "W-2", "Box 17")
    return _csv_vs_form("state_withholding", "Withholding Match", s, n, sv,
                        "line_24_withholding", "GA 500 Line 24", "W-2 Box 17")


def check_fed_state_agi_match(fv, sv):
    """Check 9: 1040 Line 11 = GA Form 500 Line 8.

    (Source: georgia-500-guide.md, Income Section, Line 8)
    """
    name, cat = "fed_state_agi_match", "Cross-Return Consistency"
    if "line_11_agi" not in fv or "line_8_fagi" not in sv:
        return _skipped(name, cat, [k for k, src in (("line_11_agi", fv), ("line_8_fagi", sv)) if k not in src])
    fed_agi = d(fv.get("line_11_agi"))
    state_agi = d(sv.get("line_8_fagi"))
    return _result(name, cat, compare(fed_agi, state_agi), fed_agi, state_agi,
                   f"Federal AGI ({fmt(fed_agi)}) vs GA 500 Line 8 ({fmt(state_agi)})")


def _schedule_e_total(fv):
    """Schedule E line 41 (Part V) — the amount Schedule 1 line 5 carries.

    Preferred: schedule_e_line_41. Otherwise Part I line 26 + Part II line 32
    + Part III line 37. (Source: schedule-e-guide.md, Totals — line 26 carries
    to Part V line 41, which feeds Schedule 1 line 5 and the 1040.)
    """
    if "schedule_e_line_41" in fv:
        return d(fv.get("schedule_e_line_41"))
    if "schedule_e_line_26" in fv:
        return (d(fv.get("schedule_e_line_26")) + d(fv.get("schedule_e_part2_line_32"))
                + d(fv.get("schedule_e_part3_line_37")))
    return None


def check_schedule_e_match(fv):
    """Optional: Schedule 1 Line 5 = Schedule E Line 41 (total of Parts I-IV).

    Returns None when neither form value is provided.
    """
    name, cat = "schedule_e_match", "Cross-Form Consistency"
    sch_e = _schedule_e_total(fv)
    if sch_e is None and "schedule_1_line_5" not in fv:
        return None
    if sch_e is None or "schedule_1_line_5" not in fv:
        return _skipped(name, cat, ["schedule_e_line_41 (or line_26)" if sch_e is None else "schedule_1_line_5"])
    sch_1 = d(fv.get("schedule_1_line_5"))
    return _result(name, cat, compare(sch_e, sch_1), sch_e, sch_1,
                   f"Schedule E Line 41 ({fmt(sch_e)}) vs Schedule 1 Line 5 ({fmt(sch_1)})")


def check_k1_schedule_e_part2(rows, fv):
    """Optional: Schedule E Part II net = K-1 boxes 1 + 2 + 3 less declared UPE.

    Runs when K-1 rows exist or a Part II line 32 is provided.
    (Source: k1-guide.md, Part III box-by-box)
    """
    name, cat = "k1_schedule_e_part2", "Cross-Form Consistency"
    s1, n1 = sum_csv(rows, "K-1", "Box 1", prefix=True)
    s2, n2 = sum_csv(rows, "K-1", "Box 2", prefix=True)
    s3, n3 = sum_csv(rows, "K-1", "Box 3", prefix=True)
    count = n1 + n2 + n3
    if count == 0 and "schedule_e_part2_line_32" not in fv:
        return None
    if "schedule_e_part2_line_32" not in fv:
        return _skipped(name, cat, ["schedule_e_part2_line_32"])
    upe = d(fv.get("schedule_e_part2_upe"))
    expected = s1 + s2 + s3 - upe
    actual = d(fv.get("schedule_e_part2_line_32"))
    return _result(name, cat, compare(expected, actual), expected, actual,
                   f"Schedule E Part II net ({fmt(actual)}) vs K-1 boxes 1+2+3 ({fmt(s1 + s2 + s3)}) "
                   f"less unreimbursed partnership expenses ({fmt(upe)})")


def check_estimated_payments(rows, fv):
    """Optional: 1040 Line 26 vs IRS account transcript payments (code 670)."""
    s, n = sum_csv(rows, "IRS Account Transcript", "Code 670", prefix=True)
    if n == 0 and "line_26_estimated_payments" not in fv:
        return None
    return _csv_vs_form("estimated_payments_match", "Withholding Match", s, n, fv,
                        "line_26_estimated_payments", "1040 Line 26", "IRS transcript payments (code 670)")


def check_rents_match(rows, fv):
    """Optional: Schedule E line 23a total rents vs rental documents' Line 3."""
    s, n = sum_csv(rows, "Rental (", "Line 3", prefix=True)
    if n == 0 and "schedule_e_line_23a_rents" not in fv:
        return None
    return _csv_vs_form("rents_match", "Cross-Form Consistency", s, n, fv,
                        "schedule_e_line_23a_rents", "Schedule E line 23a", "rental Line 3 rows")


def compute_ordinary_tax(taxable_income, filing_status):
    """Compute ordinary income tax using the 2025 rate schedule (exact formula).

    Kept for reference. The bracket check uses the IRS Tax Table under
    $100,000 (see check_tax_bracket). (Source: 2025-tax-numbers.md)
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
    """Check 10: Verify Line 16 tax against the IRS Tax Table / rate schedule.

    Under $100,000 of taxable income the form requires the Tax Table (the rate
    schedule applied to the row midpoint); at $100,000+ the exact schedule.
    Two-sided: the tax must not exceed that amount by more than TOLERANCE, and
    must not fall below the amount on the ORDINARY part of taxable income
    (taxable income less qualified dividends and capital gain) by more than
    TOLERANCE. With no qualified dividends or capital gain, the tax must
    match. (Source: 2025-tax-numbers.md, Tax Table Mechanics; Qualified
    Dividends and Capital Gain Tax Rates)
    """
    name, cat = "tax_bracket_verify", "Math Verification"
    miss = _missing(fv, ["line_15_taxable_income", "line_16_tax"])
    if miss:
        return _skipped(name, cat, miss)
    taxable_income = d(fv.get("line_15_taxable_income"))
    form_tax = d(fv.get("line_16_tax"))

    brackets = FEDERAL_BRACKETS.get(filing_status)
    if brackets is None:
        return _result(name, cat, "warning", "N/A", form_tax,
                       f"Unknown filing status '{filing_status}' — use MFJ, Single, HoH, or MFS. Verify manually.")

    expected = Decimal(tax_from_table_or_schedule(taxable_income, brackets))
    preferential = min(taxable_income,
                       d(fv.get("line_3a_qualified_dividends")) + max(d(fv.get("line_7_capital_gain")), Decimal("0")))
    floor = expected
    if preferential > 0:
        floor = Decimal(tax_from_table_or_schedule(taxable_income - preferential, brackets))

    if form_tax > expected + TOLERANCE:
        return _result(name, cat, "fail", expected, form_tax,
                       f"Line 16 ({fmt(form_tax)}) exceeds the tax on Line 15 ({fmt(expected)}) "
                       f"by more than {fmt(TOLERANCE)}. Tax should never exceed ordinary rates.")
    if form_tax < floor - TOLERANCE:
        why = ("even with qualified dividends/capital gain taxed at 0%"
               if preferential > 0 else "and no qualified dividends or capital gain explain a lower amount")
        return _result(name, cat, "fail", floor, form_tax,
                       f"Line 16 ({fmt(form_tax)}) is below the minimum tax of {fmt(floor)} "
                       f"{why}.")
    return _result(name, cat, "pass", expected, form_tax,
                   f"Line 16 ({fmt(form_tax)}) is within {fmt(TOLERANCE)} of the expected tax ({fmt(expected)})"
                   + (" (lower amounts allowed for preferential income)" if preferential > 0 else ""))


# ---------------------------------------------------------------------------
# Engine adapter
# ---------------------------------------------------------------------------

_ENGINE_1040_MAP = {
    "line_1_wages": "line_1_wages",
    "line_2b_interest": "line_2b_interest",
    "line_3a_qualified_dividends": "line_3a_qualified_dividends",
    "line_3b_dividends": "line_3b_dividends",
    "line_7_capital_gain": "line_7_capital_gain",
    "line_8_other_income": "line_8_schedule_1_income",
    "line_9_total_income": "line_9_total_income",
    "line_10_adjustments": "line_10_adjustments",
    "line_11_agi": "line_11_agi",
    "line_12a_deduction": "line_12_deduction",
    "line_13a_qbi": "line_13_qbi_deduction",
    "line_14_total_deductions": "line_14_deductions_total",
    "line_15_taxable_income": "line_15_taxable_income",
    "line_16_tax": "line_16_tax",
    "line_25a_w2_withholding": "line_25_withholding",
    "line_26_estimated_payments": "line_26_estimated_payments",
}


def _engine_value(forms, form, key):
    item = (forms.get(form) or {}).get(key)
    if item is None:
        return None
    return str(item["value"] if isinstance(item, dict) else item)


def values_from_engine(engine_result):
    """Translate engine/return_engine.py output into (federal_values, state_values).

    Engine line keys differ from the keys this script uses (for example
    line_12_deduction -> line_12a_deduction), so they are mapped here.
    """
    forms = engine_result.get("forms", {})
    fv, sv = {}, {}
    for ours, theirs in _ENGINE_1040_MAP.items():
        v = _engine_value(forms, "Form 1040", theirs)
        if v is not None:
            fv[ours] = v
    v = _engine_value(forms, "Schedule E", "line_41_total")
    if v is not None:
        fv["schedule_e_line_41"] = v
    for ours, theirs in (("line_8_fagi", "line_8_federal_agi"), ("line_24_withholding", "line_24_withholding")):
        v = _engine_value(forms, "GA Form 500", theirs)
        if v is not None:
            sv[ours] = v
    return fv, sv


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def cross_check(data):
    """Run all cross-checks and return results.

    Inputs: csv_path; federal_values / state_values (form lines as entered);
    optionally engine_result (dict from engine/return_engine.py) or
    engine_result_path, whose lines are used unless overridden by the explicit
    values; filing_status.
    """
    csv_path = data.get("csv_path", "")
    fv = dict(data.get("federal_values", {}) or {})
    sv = dict(data.get("state_values", {}) or {})
    filing_status = data.get("filing_status", "MFJ")

    engine_result = data.get("engine_result")
    if engine_result is None and data.get("engine_result_path"):
        with open(data["engine_result_path"], encoding="utf-8") as f:
            engine_result = json.load(f)
    if engine_result is not None:
        efv, esv = values_from_engine(engine_result)
        fv = {**efv, **fv}
        sv = {**esv, **sv}

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
    for optional in (check_schedule_e_match(fv), check_k1_schedule_e_part2(rows, fv),
                     check_estimated_payments(rows, fv), check_rents_match(rows, fv)):
        if optional is not None:
            checks.append(optional)

    count = lambda status: sum(1 for c in checks if c["status"] == status)
    return {
        "checks": checks,
        "summary": {
            "total": len(checks),
            "passed": count("pass"),
            "warnings": count("warning"),
            "failed": count("fail"),
            "skipped": count("skipped"),
            "not_applicable": count("not_applicable"),
            "tolerance": str(TOLERANCE),
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
