"""
macrs_tables.py — Complete MACRS straight-line percentage tables for real
property (mid-month convention).

Source: Pub 946 (2025), Appendix A (reference/Raw/p946.pdf, pp. 73-74;
curated: reference/curated/rental-depreciation.md):
  - Table A-6:  Residential Rental Property, SL 27.5 years
  - Table A-7a: Nonresidential Real Property, SL 39 years

These are the tables as PRINTED, including the parts the earlier simplified
implementation got wrong (validated 2026-07-03):
  - A-6 years 10-27 alternate 3.637/3.636 by month half and year parity.
  - A-6 year 28 is a partial year for Jan-Jun placements; year 29 exists
    only for Jul-Dec placements.
  - A-7a year 40 is a month-dependent final partial year.

Invariant (tested): every placement-month column sums to exactly 100%.

All values Decimal (Rule 3). `table_year` below is the printed table's
"Year" column: 1 = the placed-in-service year (tax_year - pis_year + 1).
"""

from decimal import Decimal


def _row(*vals):
    return [Decimal(v) for v in vals]


# Table A-6 — 27.5-year residential rental (Pub 946 p.73)
A6_YEAR_1 = _row("3.485", "3.182", "2.879", "2.576", "2.273", "1.970",
                 "1.667", "1.364", "1.061", "0.758", "0.455", "0.152")
A6_STEADY = Decimal("3.636")            # years 2-9, all months
A6_HIGH = Decimal("3.637")              # the alternation partner, years 10-27
A6_YEAR_28 = _row("1.970", "2.273", "2.576", "2.879", "3.182", "3.485",
                  "3.636", "3.636", "3.636", "3.636", "3.636", "3.636")
A6_YEAR_29 = _row("0", "0", "0", "0", "0", "0",
                  "0.152", "0.455", "0.758", "1.061", "1.364", "1.667")

# Table A-7a — 39-year nonresidential (Pub 946 p.74)
A7A_YEAR_1 = _row("2.461", "2.247", "2.033", "1.819", "1.605", "1.391",
                  "1.177", "0.963", "0.749", "0.535", "0.321", "0.107")
A7A_STEADY = Decimal("2.564")           # years 2-39, all months
A7A_YEAR_40 = _row("0.107", "0.321", "0.535", "0.749", "0.963", "1.177",
                   "1.391", "1.605", "1.819", "2.033", "2.247", "2.461")

FINAL_TABLE_YEAR = {"27.5": 29, "39": 40}


def macrs_sl_pct(recovery, table_year, month):
    """Percentage (as printed, e.g. Decimal('3.636')) for the given recovery
    period ('27.5' or '39'), table year (1-based; 1 = placed-in-service
    year), and placement month (1-12).

    Returns Decimal('0') once the recovery period is exhausted for that
    placement month. Raises KeyError for an unsupported recovery period and
    ValueError for an out-of-range month.
    """
    if recovery not in FINAL_TABLE_YEAR:
        raise KeyError(f"Unsupported recovery period {recovery!r} — use '27.5' or '39'")
    if not 1 <= month <= 12:
        raise ValueError(f"month must be 1-12, got {month}")
    if table_year < 1:
        return Decimal("0")

    m = month - 1

    if recovery == "27.5":
        if table_year == 1:
            return A6_YEAR_1[m]
        if 2 <= table_year <= 9:
            return A6_STEADY
        if 10 <= table_year <= 27:
            # Pub 946 Table A-6: months 1-6 get 3.637 in EVEN years,
            # months 7-12 get 3.637 in ODD years (p.73).
            even_year = table_year % 2 == 0
            first_half = month <= 6
            return A6_HIGH if (even_year == first_half) else A6_STEADY
        if table_year == 28:
            return A6_YEAR_28[m]
        if table_year == 29:
            return A6_YEAR_29[m]
        return Decimal("0")

    # recovery == "39"
    if table_year == 1:
        return A7A_YEAR_1[m]
    if 2 <= table_year <= 39:
        return A7A_STEADY
    if table_year == 40:
        return A7A_YEAR_40[m]
    return Decimal("0")
