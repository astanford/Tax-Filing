"""
schedule_c_calculator.py — Compute Schedule C lines (COGS, expenses, net profit/loss).

Usage:
    python schedule_c_calculator.py '{"gross_receipts": 5000.00, "returns_allowances": 200.00, "beginning_inventory": 0, "purchases": 1500.00, "materials_supplies": 300.00, "other_cogs_costs": 0, "ending_inventory": 0, "expenses": {"line_10_commissions_fees": 150.00, "line_22_supplies": 400.00, "line_27_other": 100.00}}'

Schedule C line calculations (Source: schedule-c-guide.md):
- Line 1: Gross receipts (from 1099-K)
- Line 2: Returns and allowances
- Line 3: Net receipts (Line 1 - Line 2)
- Line 4: COGS (from Part III, Lines 35-42)
- Line 5: Gross profit (Line 3 - Line 4)
- Lines 8-27: Business expenses
- Line 28: Total expenses
- Line 31: Net profit or loss (Line 5 - Line 28)

SE tax threshold: net profit > $400 (Source: schedule-c-guide.md, SE Tax Threshold)
QBI: $0 if net loss; carryforward applies (Source: self-employment-qbi.md)
"""

import json
import sys
from decimal import Decimal, ROUND_HALF_UP


def d(val):
    """Convert to Decimal. Returns Decimal('0') for None."""
    if val is None:
        return Decimal("0")
    try:
        return Decimal(str(val).replace(",", "").strip())
    except Exception:
        return Decimal("0")


def cents(val):
    """Round to nearest cent."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# SE tax threshold (Source: schedule-c-guide.md, Self-Employment Tax Threshold)
SE_TAX_THRESHOLD = Decimal("400")


def calculate(data):
    """Compute Schedule C line values."""
    # Part I — Income
    gross_receipts = d(data.get("gross_receipts", 0))        # Line 1
    returns_allowances = d(data.get("returns_allowances", 0))  # Line 2
    net_receipts = gross_receipts - returns_allowances          # Line 3

    # Part III — Cost of Goods Sold
    beginning_inv = d(data.get("beginning_inventory", 0))      # Line 35
    purchases = d(data.get("purchases", 0))                    # Line 36
    materials = d(data.get("materials_supplies", 0))           # Line 38
    other_cogs = d(data.get("other_cogs_costs", 0))           # Line 40
    cogs_subtotal = beginning_inv + purchases + materials + other_cogs  # Line 41
    ending_inv = d(data.get("ending_inventory", 0))            # Line 42
    cogs = cogs_subtotal - ending_inv                           # Line 4 = Line 41 - Line 42

    # Line 5 — Gross profit
    gross_profit = net_receipts - cogs

    # Part II — Expenses
    expenses_input = data.get("expenses", {})
    expense_lines = {
        "line_8_advertising": d(expenses_input.get("line_8_advertising", 0)),
        "line_9_car_truck": d(expenses_input.get("line_9_car_truck", 0)),
        "line_10_commissions_fees": d(expenses_input.get("line_10_commissions_fees", 0)),
        "line_11_contract_labor": d(expenses_input.get("line_11_contract_labor", 0)),
        "line_12_depletion": d(expenses_input.get("line_12_depletion", 0)),
        "line_13_depreciation": d(expenses_input.get("line_13_depreciation", 0)),
        "line_14_employee_benefits": d(expenses_input.get("line_14_employee_benefits", 0)),
        "line_15_insurance": d(expenses_input.get("line_15_insurance", 0)),
        "line_16a_mortgage_interest": d(expenses_input.get("line_16a_mortgage_interest", 0)),
        "line_16b_other_interest": d(expenses_input.get("line_16b_other_interest", 0)),
        "line_17_legal_professional": d(expenses_input.get("line_17_legal_professional", 0)),
        "line_18_office_expense": d(expenses_input.get("line_18_office_expense", 0)),
        "line_19_pension_profit_sharing": d(expenses_input.get("line_19_pension_profit_sharing", 0)),
        "line_20a_vehicles": d(expenses_input.get("line_20a_vehicles", 0)),
        "line_20b_other_rental": d(expenses_input.get("line_20b_other_rental", 0)),
        "line_21_repairs": d(expenses_input.get("line_21_repairs", 0)),
        "line_22_supplies": d(expenses_input.get("line_22_supplies", 0)),
        "line_23_taxes_licenses": d(expenses_input.get("line_23_taxes_licenses", 0)),
        "line_24a_travel": d(expenses_input.get("line_24a_travel", 0)),
        "line_24b_meals": d(expenses_input.get("line_24b_meals", 0)),
        "line_25_utilities": d(expenses_input.get("line_25_utilities", 0)),
        "line_26_wages": d(expenses_input.get("line_26_wages", 0)),
        "line_27_other": d(expenses_input.get("line_27_other", 0)),
    }
    total_expenses = sum(expense_lines.values())  # Line 28

    # Line 31 — Net profit or (loss)
    net_profit_loss = gross_profit - total_expenses

    # SE tax flag (Source: schedule-c-guide.md)
    se_tax_required = net_profit_loss > SE_TAX_THRESHOLD

    # QBI (Source: self-employment-qbi.md)
    if net_profit_loss > Decimal("0"):
        qbi_deduction = cents(net_profit_loss * Decimal("0.20"))
        qbi_carryforward = Decimal("0")
    else:
        qbi_deduction = Decimal("0")
        qbi_carryforward = abs(net_profit_loss)

    return {
        "line_1_gross_receipts": str(cents(gross_receipts)),
        "line_2_returns": str(cents(returns_allowances)),
        "line_3_net_receipts": str(cents(net_receipts)),
        "line_4_cogs": str(cents(cogs)),
        "line_5_gross_profit": str(cents(gross_profit)),
        "line_28_total_expenses": str(cents(total_expenses)),
        "line_31_net_profit_loss": str(cents(net_profit_loss)),
        "se_tax_required": se_tax_required,
        "qbi_deduction": str(cents(qbi_deduction)),
        "qbi_carryforward": str(cents(qbi_carryforward)),
        "cogs_detail": {
            "line_35_beginning_inventory": str(cents(beginning_inv)),
            "line_36_purchases": str(cents(purchases)),
            "line_38_materials": str(cents(materials)),
            "line_40_other": str(cents(other_cogs)),
            "line_41_subtotal": str(cents(cogs_subtotal)),
            "line_42_ending_inventory": str(cents(ending_inv)),
        },
        "expense_detail": {k: str(cents(v)) for k, v in expense_lines.items() if v > 0},
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: schedule_c_calculator.py \'{"gross_receipts": 1242.50, ...}\''
        }))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = calculate(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
