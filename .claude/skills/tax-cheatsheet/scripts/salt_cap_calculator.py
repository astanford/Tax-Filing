"""
salt_cap_calculator.py — Compute effective SALT deduction with cap and phase-out.

Usage:
    python salt_cap_calculator.py '{"filing_status": "MFJ", "magi": 120000.00, "state_income_tax": 5000.00, "local_income_tax": 3000.00, "real_estate_tax": 4500.00, "personal_property_tax": 0.00}'

Implements the OBBBA SALT cap rules for 2025:
- Base cap: $40,000 MFJ / $20,000 MFS
  (Source: salt-deduction-2025.md, Overall SALT Cap)
- Phase-out: 30% of MAGI over $500,000 MFJ / $250,000 MFS
  (Source: salt-deduction-2025.md, MAGI Phase-Out)
- Floor: $10,000 MFJ / $5,000 MFS
  (Source: salt-deduction-2025.md, MAGI Phase-Out)
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


# 2025 SALT cap parameters (Source: salt-deduction-2025.md)
SALT_PARAMS = {
    "MFJ": {
        "base_cap": Decimal("40000"),
        "floor": Decimal("10000"),
        "phase_out_threshold": Decimal("500000"),
        "phase_out_rate": Decimal("0.30"),
    },
    "MFS": {
        "base_cap": Decimal("20000"),
        "floor": Decimal("5000"),
        "phase_out_threshold": Decimal("250000"),
        "phase_out_rate": Decimal("0.30"),
    },
    "Single": {
        "base_cap": Decimal("40000"),
        "floor": Decimal("10000"),
        "phase_out_threshold": Decimal("500000"),
        "phase_out_rate": Decimal("0.30"),
    },
    "HoH": {
        "base_cap": Decimal("40000"),
        "floor": Decimal("10000"),
        "phase_out_threshold": Decimal("500000"),
        "phase_out_rate": Decimal("0.30"),
    },
}


def calculate(data):
    """Compute effective SALT cap and deductible amount."""
    filing_status = data.get("filing_status", "MFJ")
    magi = d(data.get("magi", 0))

    state_income = d(data.get("state_income_tax", 0))
    local_income = d(data.get("local_income_tax", 0))
    real_estate = d(data.get("real_estate_tax", 0))
    personal_property = d(data.get("personal_property_tax", 0))

    if filing_status not in SALT_PARAMS:
        return {"error": f"Unknown filing status: {filing_status}. Use MFJ, MFS, Single, or HoH."}

    params = SALT_PARAMS[filing_status]
    base_cap = params["base_cap"]
    floor = params["floor"]
    threshold = params["phase_out_threshold"]
    rate = params["phase_out_rate"]

    # Total SALT before cap
    total_salt = state_income + local_income + real_estate + personal_property

    # Effective cap with phase-out
    phase_out_applies = magi > threshold
    if phase_out_applies:
        excess = magi - threshold
        reduction = rate * excess
        effective_cap = max(floor, base_cap - reduction)
    else:
        effective_cap = base_cap

    # Deductible SALT = min(total, effective cap)
    deductible_salt = min(total_salt, effective_cap)
    salt_lost = total_salt - deductible_salt

    # Build detail message
    if not phase_out_applies:
        detail = (
            f"Total SALT ${float(cents(total_salt)):,.2f} is "
            f"{'under' if total_salt <= effective_cap else 'over'} the "
            f"${float(cents(effective_cap)):,.0f} cap. "
            f"No phase-out (MAGI ${float(cents(magi)):,.0f} < "
            f"${float(cents(threshold)):,.0f} threshold)."
        )
    else:
        detail = (
            f"Total SALT ${float(cents(total_salt)):,.2f}. "
            f"MAGI ${float(cents(magi)):,.0f} exceeds ${float(cents(threshold)):,.0f} by "
            f"${float(cents(magi - threshold)):,.0f}. "
            f"Cap reduced from ${float(cents(base_cap)):,.0f} to "
            f"${float(cents(effective_cap)):,.0f}."
        )

    return {
        "total_salt": str(cents(total_salt)),
        "base_cap": str(cents(base_cap)),
        "effective_cap": str(cents(effective_cap)),
        "phase_out_applies": phase_out_applies,
        "deductible_salt": str(cents(deductible_salt)),
        "salt_lost_to_cap": str(cents(salt_lost)),
        "components": {
            "state_income_tax": str(cents(state_income)),
            "local_income_tax": str(cents(local_income)),
            "real_estate_tax": str(cents(real_estate)),
            "personal_property_tax": str(cents(personal_property)),
        },
        "detail": detail,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: salt_cap_calculator.py \'{"filing_status": "MFJ", "magi": 120000, ...}\''
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
