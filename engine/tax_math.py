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


def tax_from_table_or_schedule(taxable_income, brackets):
    """The tax the FORM requires: under $100,000 the IRS Tax Table (a $25/
    $50-row lookup whose cell = the rate schedule applied to the row
    MIDPOINT, rounded to the dollar); at $100,000+ the Tax Computation
    Worksheet (the exact rate schedule).

    Row structure and midpoint rule verified against printed cells of the
    2025 table, e.g. 3,000-3,050 -> 303 (all statuses); 95,000-95,050 ->
    15,820/10,926/15,820/14,081; 99,950-100,000 MFJ -> 11,823.
    (Source: 2025-tax-numbers.md, Tax Table Mechanics; raw source
    reference/Raw/i1040gi.pdf, 2025 Tax Table)
    """
    if taxable_income <= ZERO:
        return ZERO
    if taxable_income >= Decimal("100000"):
        return apply_brackets(taxable_income, brackets)

    if taxable_income < 5:
        return ZERO
    if taxable_income < 25:
        lower = Decimal("5") if taxable_income < 15 else Decimal("15")
        midpoint = lower + Decimal("5")
    elif taxable_income < 3000:
        lower = (taxable_income / Decimal("25")).to_integral_value(rounding="ROUND_FLOOR") * Decimal("25")
        midpoint = lower + Decimal("12.50")
    else:
        lower = (taxable_income / Decimal("50")).to_integral_value(rounding="ROUND_FLOOR") * Decimal("50")
        midpoint = lower + Decimal("25")
    return whole(apply_brackets(midpoint, brackets))
