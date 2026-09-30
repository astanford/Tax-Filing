"""Tests for cross_check.py — CSV↔form checks and bracket verification.

Bracket expectations computed from Rev. Proc. 2024-40 §2.01 tables
(reference/Raw/rp-24-40.pdf), matching engine/constants_2025.py.
"""

import csv
from decimal import Decimal

import pytest

import cross_check as cc


# Ordinary tax on $500,000 of taxable income, per status (hand-derived from
# the Rev. Proc. tables: base + rate * excess over bracket start).
TAX_ON_500K = {
    "MFJ": Decimal("114126.00"),      # 80398 + 32% * (500000-394600)
    "Single": Decimal("144547.25"),   # 57231 + 35% * (500000-250525)
    "HoH": Decimal("142809.00"),      # 55484 + 35% * (500000-250500)
    "MFS": Decimal("147031.25"),      # 101077.25 + 37% * (500000-375800)
}


@pytest.mark.parametrize("status,expected", sorted(TAX_ON_500K.items()))
def test_ordinary_tax_all_statuses(status, expected):
    assert cc.compute_ordinary_tax(Decimal("500000"), status) == expected


def test_mfj_top_bracket_regression():
    """$800K MFJ: 202154.50 + 37% * 48400 = 220062.50. The old table's
    188770 base understated this by $13,384.50."""
    assert cc.compute_ordinary_tax(Decimal("800000"), "MFJ") == Decimal("220062.50")


def test_unknown_status_returns_none():
    assert cc.compute_ordinary_tax(Decimal("100000"), "QSS") is None


def test_tax_bracket_check_warns_on_unknown_status():
    result = cc.check_tax_bracket({"line_15_taxable_income": "100000",
                                   "line_16_tax": "10000"}, "QSS")
    assert result["status"] == "warning"


def test_tax_bracket_check_fails_when_tax_exceeds_ordinary():
    result = cc.check_tax_bracket({"line_15_taxable_income": "54050",
                                   "line_16_tax": "9999"}, "MFJ")
    assert result["status"] == "fail"


def test_tax_bracket_check_passes_below_ordinary_only_with_preferential_income():
    """Tax below the ordinary amount is only plausible when qualified
    dividends or capital gain are present. (The old check accepted any lower
    tax, including zero.)"""
    with_qd = cc.check_tax_bracket({"line_15_taxable_income": "54050",
                                    "line_3a_qualified_dividends": "10000",
                                    "line_16_tax": "5000"}, "MFJ")
    assert with_qd["status"] == "pass"
    without = cc.check_tax_bracket({"line_15_taxable_income": "54050",
                                   "line_16_tax": "5000"}, "MFJ")
    assert without["status"] == "fail"


# --- end-to-end with a fabricated CSV --------------------------------------

CSV_ROWS = [
    # document, box_or_line, description, value, source_path
    ("W-2 Employer A", "Box 1", "Wages", "85000.00", "w2a.pdf"),
    ("W-2 Employer A", "Box 2", "Federal withholding", "9500.00", "w2a.pdf"),
    ("W-2 Employer A", "Box 17", "State withholding", "4400.00", "w2a.pdf"),
    ("1099-INT Bank X", "Box 1", "Interest income", "200.00", "int.pdf"),
    ("1099-DIV Broker Y", "Box 1a", "Ordinary dividends", "350.00", "div.pdf"),
]


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "tax-doc-summary.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["document", "box_or_line", "description", "value", "source_path"])
        writer.writerows(CSV_ROWS)
    return str(path)


def _consistent_federal_values():
    # taxable = 85550 - 31500 = 54050. Under $100,000 the IRS Tax Table
    # applies: row 54,050-54,100 (midpoint 54,075) -> 6012 (the exact rate
    # formula at 54,050 would give 6009).
    return {
        "line_1_wages": "85000.00",
        "line_2b_interest": "200.00",
        "line_3b_dividends": "350.00",
        "line_7_capital_gain": "0.00",
        "line_8_other_income": "0.00",
        "line_9_total_income": "85550.00",
        "line_10_adjustments": "0.00",
        "line_11_agi": "85550.00",
        "line_12a_deduction": "31500.00",
        "line_13a_qbi": "0.00",
        "line_13b_sched1a": "0.00",
        "line_14_total_deductions": "31500.00",
        "line_15_taxable_income": "54050.00",
        "line_16_tax": "6012.00",
        "line_25a_w2_withholding": "9500.00",
    }


def test_consistent_return_all_pass(csv_path):
    result = cc.cross_check({
        "csv_path": csv_path,
        "federal_values": _consistent_federal_values(),
        "state_values": {"line_8_fagi": "85550.00", "line_24_withholding": "4400.00"},
        "filing_status": "MFJ",
    })
    assert result["summary"]["failed"] == 0
    assert result["summary"]["warnings"] == 0
    statuses = {c["check_name"]: c["status"] for c in result["checks"]}
    # The ten original checks all pass; optional checks have nothing to verify.
    for name in ("wages_match", "interest_match", "dividends_match", "total_income",
                 "agi_calculation", "taxable_income", "federal_withholding",
                 "state_withholding", "fed_state_agi_match", "tax_bracket_verify"):
        assert statuses[name] == "pass", name


def test_wage_mismatch_fails(csv_path):
    fv = _consistent_federal_values()
    fv["line_1_wages"] = "80000.00"
    result = cc.cross_check({
        "csv_path": csv_path,
        "federal_values": fv,
        "state_values": {"line_8_fagi": "85550.00", "line_24_withholding": "4400.00"},
        "filing_status": "MFJ",
    })
    names_failed = {c["check_name"] for c in result["checks"] if c["status"] == "fail"}
    assert "wages_match" in names_failed


def test_missing_csv_is_error():
    assert "error" in cc.cross_check({"csv_path": "/nonexistent.csv"})


# --- tolerance ($100, user-directed) ----------------------------------------

def test_tolerance_is_100():
    assert cc.TOLERANCE == Decimal("100")


def test_compare_boundary():
    assert cc.compare(Decimal("1000"), Decimal("1100")) == "pass"
    assert cc.compare(Decimal("1000"), Decimal("1100.01")) == "fail"


# --- tax bracket check: Tax Table, two-sided --------------------------------

def test_tax_bracket_uses_tax_table_under_100k():
    """$51,704.06 MFJ: Tax Table row 51,700-51,750 -> $5,730. The exact
    formula gives $5,727.49; the old check failed the correct return."""
    result = cc.check_tax_bracket({"line_15_taxable_income": "51704.06",
                                   "line_16_tax": "5730"}, "MFJ")
    assert result["status"] == "pass"
    assert result["expected"] == "5730.00"


def test_tax_bracket_fails_zero_tax():
    """The old one-sided check passed any tax below the ordinary amount."""
    result = cc.check_tax_bracket({"line_15_taxable_income": "51704.06",
                                   "line_16_tax": "0"}, "MFJ")
    assert result["status"] == "fail"


def test_tax_bracket_low_tax_outside_tolerance_fails():
    result = cc.check_tax_bracket({"line_15_taxable_income": "51704.06",
                                   "line_16_tax": "5600"}, "MFJ")
    assert result["status"] == "fail"      # 130 below the table amount
    ok = cc.check_tax_bracket({"line_15_taxable_income": "51704.06",
                               "line_16_tax": "5650"}, "MFJ")
    assert ok["status"] == "pass"          # 80 below, inside $100


def test_tax_bracket_preferential_income_allows_lower_tax():
    """Qualified dividends of 20,000 in taxable income 60,000: tax may be as
    low as the Tax Table amount on the 40,000 ordinary part."""
    fv = {"line_15_taxable_income": "60000", "line_3a_qualified_dividends": "20000"}
    floor = cc.check_tax_bracket({**fv, "line_16_tax": "4300"}, "MFJ")
    assert floor["status"] == "pass"       # 40,000 ordinary -> 4,326 table
    assert cc.check_tax_bracket({**fv, "line_16_tax": "4000"}, "MFJ")["status"] == "fail"
    assert cc.check_tax_bracket({**fv, "line_16_tax": "0"}, "MFJ")["status"] == "fail"
    assert cc.check_tax_bracket({**fv, "line_16_tax": "9000"}, "MFJ")["status"] == "fail"


def test_tax_bracket_missing_inputs_skipped():
    assert cc.check_tax_bracket({}, "MFJ")["status"] == "skipped"


# --- vacuous passes and missing entries --------------------------------------

def _run(csv_path, fv, sv=None, **extra):
    return cc.cross_check({"csv_path": csv_path, "federal_values": fv,
                           "state_values": sv or {}, "filing_status": "MFJ", **extra})


def _status(result, name):
    return next(c["status"] for c in result["checks"] if c["check_name"] == name)


def test_no_documents_and_zero_entered_is_not_applicable(tmp_path):
    path = tmp_path / "t.csv"
    path.write_text("document,box_or_line,description,value,source_path\n"
                    "Rental (A),Line 3,rents,1000.00,x\n")
    result = _run(str(path), {"line_1_wages": "0"})
    assert _status(result, "wages_match") == "not_applicable"
    assert _status(result, "federal_withholding") == "not_applicable"


def test_documents_present_but_entry_missing_fails(csv_path):
    fv = _consistent_federal_values()
    del fv["line_1_wages"]
    assert _status(_run(csv_path, fv), "wages_match") == "fail"


# --- Schedule E pairing (line 41, not line 26) --------------------------------

def test_schedule_e_total_includes_part_2(csv_path):
    fv = _consistent_federal_values()
    fv.update({"schedule_e_line_26": "75522.00", "schedule_e_part2_line_32": "20321.08",
               "schedule_1_line_5": "95843.08"})
    assert _status(_run(csv_path, fv), "schedule_e_match") == "pass"


def test_schedule_e_line_26_alone_does_not_match_when_part_2_present(csv_path):
    fv = _consistent_federal_values()
    fv.update({"schedule_e_line_26": "75522.00", "schedule_e_part2_line_32": "20321.08",
               "schedule_1_line_5": "75522.00"})
    assert _status(_run(csv_path, fv), "schedule_e_match") == "fail"


def test_schedule_e_explicit_line_41(csv_path):
    fv = _consistent_federal_values()
    fv.update({"schedule_e_line_41": "95843.08", "schedule_1_line_5": "95843.08"})
    assert _status(_run(csv_path, fv), "schedule_e_match") == "pass"


def test_schedule_e_legacy_line_26_only(csv_path):
    fv = _consistent_federal_values()
    fv.update({"schedule_e_line_26": "5000", "schedule_1_line_5": "5000"})
    assert _status(_run(csv_path, fv), "schedule_e_match") == "pass"


# --- new CSV-tied checks ------------------------------------------------------

def _csv_with(tmp_path, extra_rows):
    path = tmp_path / "t2.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["document", "box_or_line", "description", "value", "source_path"])
        w.writerows(extra_rows)
    return str(path)


def test_k1_to_schedule_e_part_2(tmp_path):
    rows = [("K-1 1065 (Gatsby Homes LLC)", "Box 1", "ordinary", "-76.00", "k1.pdf"),
            ("K-1 1065 (Gatsby Homes LLC)", "Box 2", "rental", "22270.00", "k1.pdf")]
    path = _csv_with(tmp_path, rows)
    good = _run(path, {"schedule_e_part2_line_32": "20320.31", "schedule_e_part2_upe": "1873.69"})
    assert _status(good, "k1_schedule_e_part2") == "pass"
    bad = _run(path, {"schedule_e_part2_line_32": "20320.31"})   # UPE not declared
    assert _status(bad, "k1_schedule_e_part2") == "fail"


def test_estimated_payments_match_transcript(tmp_path):
    rows = [("IRS Account Transcript (2025 Form 1040)", "Code 670", "payment", "7510.00", "t.pdf")]
    path = _csv_with(tmp_path, rows)
    assert _status(_run(path, {"line_26_estimated_payments": "7510"}), "estimated_payments_match") == "pass"
    assert _status(_run(path, {"line_26_estimated_payments": "0"}), "estimated_payments_match") == "fail"


def test_rents_match_rental_documents(tmp_path):
    rows = [("Rental (A Landon Ct)", "Line 3", "rents", "30000.00", "p.csv"),
            ("Rental (B Landon Ct)", "Line 3", "rents", "20000.00", "p.csv")]
    path = _csv_with(tmp_path, rows)
    assert _status(_run(path, {"schedule_e_line_23a_rents": "50000"}), "rents_match") == "pass"
    assert _status(_run(path, {"schedule_e_line_23a_rents": "40000"}), "rents_match") == "fail"


def test_total_income_includes_pension_and_ira_lines(csv_path):
    fv = _consistent_federal_values()
    fv.update({"line_5b_pensions": "1000.00", "line_9_total_income": "86550.00",
               "line_11_agi": "86550.00", "line_15_taxable_income": "55050.00",
               "line_16_tax": "6132.00"})
    fv["line_5b_pensions"] = "1000.00"
    result = _run(csv_path, fv, {"line_8_fagi": "86550.00", "line_24_withholding": "4400.00"})
    assert _status(result, "total_income") == "pass"


# --- engine adapter -------------------------------------------------------------

def test_cross_check_accepts_engine_output(tmp_path):
    from engine.return_engine import compute_return
    inputs = {
        "tax_year": 2025, "filing_status": "MFJ",
        "income": {"schedule_e_line_26": "75522.00", "schedule_e_part2_line_32": "20321.08",
                   "k1_box14a_se_earnings": "-76"},
        "itemized": {"mortgage_interest": "7867.26", "real_estate_tax": "8308.93"},
        "qbi": {"qbi_net": "75446.00"},
        "payments": {"federal_estimated_payments": "7510.00", "prior_year_total_tax": "18350",
                     "prior_year_agi": "174306"},
    }
    engine = compute_return(inputs)
    rows = [("IRS Account Transcript (2025 Form 1040)", "Code 670", "payment", "7510.00", "t.pdf")]
    result = cc.cross_check({"csv_path": _csv_with(tmp_path, rows), "engine_result": engine,
                             "filing_status": "MFJ"})
    assert result["summary"]["failed"] == 0, result["checks"]
    statuses = {c["check_name"]: c["status"] for c in result["checks"]}
    assert statuses["tax_bracket_verify"] == "pass"
    assert statuses["estimated_payments_match"] == "pass"
    assert statuses["total_income"] == "pass"


# --- K-1 interest and dividends count toward lines 2b and 3b -------------------

def test_interest_includes_k1_box_5(tmp_path):
    rows = [("1099-INT (Bank)", "Box 1", "interest", "200.00", "b.pdf"),
            ("K-1 1065 (Gatsby Homes LLC)", "Box 5", "interest", "287.00", "k1.pdf")]
    path = _csv_with(tmp_path, rows)
    assert _status(_run(path, {"line_2b_interest": "487"}), "interest_match") == "pass"
    assert _status(_run(path, {"line_2b_interest": "200"}), "interest_match") == "fail"   # omits the K-1's 287


def test_dividends_include_k1_box_6a(tmp_path):
    rows = [("K-1 1065 (Gatsby Homes LLC)", "Box 6a", "ordinary dividends", "500.00", "k1.pdf")]
    path = _csv_with(tmp_path, rows)
    assert _status(_run(path, {"line_3b_dividends": "500"}), "dividends_match") == "pass"
    assert _status(_run(path, {"line_3b_dividends": "0"}), "dividends_match") == "fail"
