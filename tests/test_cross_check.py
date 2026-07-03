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


def test_tax_bracket_check_passes_below_ordinary_qdcg():
    """Tax below ordinary is consistent with QDCG preferential rates."""
    result = cc.check_tax_bracket({"line_15_taxable_income": "54050",
                                   "line_16_tax": "5000"}, "MFJ")
    assert result["status"] == "pass"


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
    # taxable = 85550 - 31500 = 54050;
    # MFJ tax = 2385 + 12% * (54050 - 23850) = 6009
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
        "line_16_tax": "6009.00",
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
    assert result["summary"]["passed"] == result["summary"]["total"]


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
