"""Tests for schedule_c_calculator.py — Schedule C line math."""

from decimal import Decimal

import schedule_c_calculator as sc


def test_income_cogs_expenses_flow():
    """Docstring example: gross 5000, returns 200, COGS 1800, expenses 650."""
    result = sc.calculate({
        "gross_receipts": "5000.00",
        "returns_allowances": "200.00",
        "purchases": "1500.00",
        "materials_supplies": "300.00",
        "expenses": {
            "line_10_commissions_fees": "150.00",
            "line_22_supplies": "400.00",
            "line_27_other": "100.00",
        },
    })
    assert result["line_3_net_receipts"] == "4800.00"
    assert result["line_4_cogs"] == "1800.00"
    assert result["line_5_gross_profit"] == "3000.00"
    assert result["line_28_total_expenses"] == "650.00"
    assert result["line_31_net_profit_loss"] == "2350.00"
    assert result["se_tax_required"] is True
    # Simplified QBI: 20% of net profit
    assert result["qbi_deduction"] == "470.00"
    assert result["qbi_carryforward"] == "0.00"


def test_ending_inventory_reduces_cogs():
    result = sc.calculate({
        "gross_receipts": "10000",
        "purchases": "4000",
        "ending_inventory": "1000",
    })
    assert result["line_4_cogs"] == "3000.00"
    assert result["line_5_gross_profit"] == "7000.00"


def test_loss_yields_qbi_carryforward_no_se_tax():
    result = sc.calculate({
        "gross_receipts": "1000",
        "expenses": {"line_22_supplies": "3500"},
    })
    assert result["line_31_net_profit_loss"] == "-2500.00"
    assert result["se_tax_required"] is False
    assert result["qbi_deduction"] == "0.00"
    assert result["qbi_carryforward"] == "2500.00"


def test_net_profit_at_or_below_400_no_se_tax():
    """SE tax threshold is net profit > $400 (2025-tax-numbers.md)."""
    at_threshold = sc.calculate({"gross_receipts": "400"})
    assert at_threshold["se_tax_required"] is False
    above = sc.calculate({"gross_receipts": "401"})
    assert above["se_tax_required"] is True


def test_expense_detail_omits_zero_lines():
    result = sc.calculate({
        "gross_receipts": "1000",
        "expenses": {"line_8_advertising": "50", "line_25_utilities": "0"},
    })
    assert "line_8_advertising" in result["expense_detail"]
    assert "line_25_utilities" not in result["expense_detail"]


def test_all_expense_lines_summed():
    """Every Part II line contributes to Line 28."""
    expenses = {k: "10" for k in (
        "line_8_advertising", "line_9_car_truck", "line_10_commissions_fees",
        "line_11_contract_labor", "line_12_depletion", "line_13_depreciation",
        "line_14_employee_benefits", "line_15_insurance",
        "line_16a_mortgage_interest", "line_16b_other_interest",
        "line_17_legal_professional", "line_18_office_expense",
        "line_19_pension_profit_sharing", "line_20a_vehicles",
        "line_20b_other_rental", "line_21_repairs", "line_22_supplies",
        "line_23_taxes_licenses", "line_24a_travel", "line_24b_meals",
        "line_25_utilities", "line_26_wages", "line_27_other",
    )}
    result = sc.calculate({"gross_receipts": "1000", "expenses": expenses})
    assert result["line_28_total_expenses"] == "230.00"
