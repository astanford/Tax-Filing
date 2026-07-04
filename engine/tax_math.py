"""
tax_math.py — Shared Decimal helpers and bracket math for the return engine.

All arithmetic uses Decimal (Rule 3 — no float math).
"""

from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0")


def d(val):
    """Convert to Decimal. Returns Decimal('0') for None or non-numeric."""
    if val is None:
        return ZERO
    try:
        return Decimal(str(val).replace(",", "").strip())
    except Exception:
        return ZERO


def cents(val):
    """Round to nearest cent."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def whole(val):
    """Round to nearest dollar (IRS forms use whole dollars)."""
    return val.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def apply_brackets(taxable_income, brackets):
    """Compute tax from a (ceiling, rate, base_tax) bracket table.

    (Source: 2025-tax-numbers.md, Federal Income Tax Brackets;
     raw source reference/Raw/rp-24-40.pdf)
    """
    if taxable_income <= ZERO:
        return ZERO
    for i, (ceiling, rate, base_tax) in enumerate(brackets):
        if ceiling is None or taxable_income <= ceiling:
            if i == 0:
                return cents(taxable_income * rate)
            prev_ceiling = brackets[i - 1][0]
            return cents(base_tax + (taxable_income - prev_ceiling) * rate)
    return ZERO
