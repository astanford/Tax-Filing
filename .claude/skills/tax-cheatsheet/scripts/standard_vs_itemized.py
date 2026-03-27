"""
standard_vs_itemized.py — Compare standard deduction vs. itemized deductions.

Usage:
    python standard_vs_itemized.py '{"filing_status": "MFJ", "magi": 120000.00, "state_local_income_tax": 5000.00, "real_estate_tax": 4500.00, "personal_property_tax": 0.00, "mortgage_interest": 12000.00, "charitable_cash": 500.00, "charitable_noncash": 0.00, "medical_expenses": 0.00, "other_itemized": 0.00}'

2025 standard deduction amounts (Source: 2025-tax-numbers.md, Standard Deduction):
- MFJ: $31,500
- Single: $15,750
- MFS: $15,750
- HoH: $23,625

SALT cap rules (Source: salt-deduction-2025.md, Overall SALT Cap):
- Base cap: $40,000 MFJ / $20,000 MFS
- Phase-out at MAGI > $500,000 MFJ
- Floor: $10,000 MFJ

Medical expense threshold: 7.5% of AGI (Source: 2025-tax-numbers.md)
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


# 2025 standard deduction (Source: 2025-tax-numbers.md)
STANDARD_DEDUCTION = {
    "MFJ": Decimal("31500"),
    "Single": Decimal("15750"),
    "MFS": Decimal("15750"),
    "HoH": Decimal("23625"),
}

# SALT cap parameters (Source: salt-deduction-2025.md)
SALT_CAP = {
    "MFJ":    {"base": Decimal("40000"), "floor": Decimal("10000"), "threshold": Decimal("500000")},
    "Single": {"base": Decimal("40000"), "floor": Decimal("10000"), "threshold": Decimal("500000")},
    "HoH":    {"base": Decimal("40000"), "floor": Decimal("10000"), "threshold": Decimal("500000")},
    "MFS":    {"base": Decimal("20000"), "floor": Decimal("5000"),  "threshold": Decimal("250000")},
}

# Medical expense threshold (Source: 2025-tax-numbers.md)
MEDICAL_THRESHOLD_RATE = Decimal("0.075")

PHASE_OUT_RATE = Decimal("0.30")


def compare(data):
    """Compare standard vs. itemized deductions."""
    filing_status = data.get("filing_status", "MFJ")
    magi = d(data.get("magi", 0))

    if filing_status not in STANDARD_DEDUCTION:
        return {"error": f"Unknown filing status: {filing_status}. Use MFJ, MFS, Single, or HoH."}

    # Standard deduction
    standard = STANDARD_DEDUCTION[filing_status]

    # SALT computation
    state_local = d(data.get("state_local_income_tax", 0))
    real_estate = d(data.get("real_estate_tax", 0))
    personal_property = d(data.get("personal_property_tax", 0))
    total_salt = state_local + real_estate + personal_property

    cap_params = SALT_CAP[filing_status]
    base_cap = cap_params["base"]
    floor_cap = cap_params["floor"]
    threshold = cap_params["threshold"]

    if magi > threshold:
        excess = magi - threshold
        reduction = PHASE_OUT_RATE * excess
        effective_cap = max(floor_cap, base_cap - reduction)
    else:
        effective_cap = base_cap

    salt_after_cap = min(total_salt, effective_cap)

    # Mortgage interest (Source: mortgage-interest.md)
    mortgage_interest = d(data.get("mortgage_interest", 0))

    # Charitable contributions
    charitable_cash = d(data.get("charitable_cash", 0))
    charitable_noncash = d(data.get("charitable_noncash", 0))
    charitable_total = charitable_cash + charitable_noncash

    # Medical expenses (7.5% AGI floor)
    medical_gross = d(data.get("medical_expenses", 0))
    medical_floor = MEDICAL_THRESHOLD_RATE * magi
    medical_deduction = max(Decimal("0"), medical_gross - medical_floor)

    # Other itemized
    other = d(data.get("other_itemized", 0))

    # Total itemized
    itemized_total = salt_after_cap + mortgage_interest + charitable_total + medical_deduction + other

    # Recommendation
    if itemized_total > standard:
        recommendation = "itemized"
        advantage = itemized_total - standard
    elif itemized_total < standard:
        recommendation = "standard"
        advantage = standard - itemized_total
    else:
        recommendation = "either"
        advantage = Decimal("0")

    return {
        "standard_deduction": str(cents(standard)),
        "itemized_total": str(cents(itemized_total)),
        "recommendation": recommendation,
        "advantage": str(cents(advantage)),
        "itemized_breakdown": {
            "salt_before_cap": str(cents(total_salt)),
            "salt_cap": str(cents(effective_cap)),
            "salt_after_cap": str(cents(salt_after_cap)),
            "salt_lost_to_cap": str(cents(total_salt - salt_after_cap)),
            "mortgage_interest": str(cents(mortgage_interest)),
            "charitable_cash": str(cents(charitable_cash)),
            "charitable_noncash": str(cents(charitable_noncash)),
            "charitable_total": str(cents(charitable_total)),
            "medical_gross": str(cents(medical_gross)),
            "medical_floor_7_5_pct": str(cents(medical_floor)),
            "medical_deduction": str(cents(medical_deduction)),
            "other_itemized": str(cents(other)),
        },
        "detail": (
            f"{'Itemized' if recommendation == 'itemized' else 'Standard'} deductions "
            f"({'$' + str(cents(itemized_total)) if recommendation == 'itemized' else '$' + str(cents(standard))}) "
            f"exceed {'standard' if recommendation == 'itemized' else 'itemized'} "
            f"({'$' + str(cents(standard)) if recommendation == 'itemized' else '$' + str(cents(itemized_total))}) "
            f"by ${str(cents(advantage))}."
        ),
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: standard_vs_itemized.py \'{"filing_status": "MFJ", "magi": 120000, ...}\''
        }))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = compare(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
