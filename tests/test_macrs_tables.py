"""Tests for engine/macrs_tables.py against Pub 946 Appendix A (pp. 73-74)."""

from decimal import Decimal

import pytest

from engine.macrs_tables import FINAL_TABLE_YEAR, macrs_sl_pct


@pytest.mark.parametrize("recovery", ["27.5", "39"])
@pytest.mark.parametrize("month", range(1, 13))
def test_every_column_sums_to_100_percent(recovery, month):
    """Each placement-month column of the printed table totals exactly 100%."""
    total = sum(macrs_sl_pct(recovery, y, month)
                for y in range(1, FINAL_TABLE_YEAR[recovery] + 1))
    assert total == Decimal("100"), f"{recovery}yr month {month}: {total}"


def test_a6_printed_cells():
    """Spot cells straight from the printed Table A-6 (p.73)."""
    assert macrs_sl_pct("27.5", 1, 1) == Decimal("3.485")
    assert macrs_sl_pct("27.5", 1, 12) == Decimal("0.152")
    assert macrs_sl_pct("27.5", 5, 3) == Decimal("3.636")
    # Alternation: year 10 months 1-6 = 3.637, months 7-12 = 3.636
    assert macrs_sl_pct("27.5", 10, 1) == Decimal("3.637")
    assert macrs_sl_pct("27.5", 10, 7) == Decimal("3.636")
    # Year 11 reverses
    assert macrs_sl_pct("27.5", 11, 1) == Decimal("3.636")
    assert macrs_sl_pct("27.5", 11, 7) == Decimal("3.637")
    # Year 27 (odd): months 7-12 get 3.637
    assert macrs_sl_pct("27.5", 27, 6) == Decimal("3.636")
    assert macrs_sl_pct("27.5", 27, 12) == Decimal("3.637")
    # Partial year 28
    assert macrs_sl_pct("27.5", 28, 1) == Decimal("1.970")
    assert macrs_sl_pct("27.5", 28, 6) == Decimal("3.485")
    assert macrs_sl_pct("27.5", 28, 7) == Decimal("3.636")
    # Year 29 exists only for Jul-Dec placements
    assert macrs_sl_pct("27.5", 29, 1) == Decimal("0")
    assert macrs_sl_pct("27.5", 29, 7) == Decimal("0.152")
    assert macrs_sl_pct("27.5", 29, 12) == Decimal("1.667")
    # Exhausted
    assert macrs_sl_pct("27.5", 30, 12) == Decimal("0")


def test_a7a_printed_cells():
    """Spot cells straight from the printed Table A-7a (p.74)."""
    assert macrs_sl_pct("39", 1, 1) == Decimal("2.461")
    assert macrs_sl_pct("39", 1, 12) == Decimal("0.107")
    assert macrs_sl_pct("39", 20, 5) == Decimal("2.564")
    assert macrs_sl_pct("39", 40, 1) == Decimal("0.107")
    assert macrs_sl_pct("39", 40, 12) == Decimal("2.461")
    assert macrs_sl_pct("39", 41, 6) == Decimal("0")


def test_bad_inputs():
    with pytest.raises(KeyError):
        macrs_sl_pct("15", 1, 1)
    with pytest.raises(ValueError):
        macrs_sl_pct("27.5", 1, 13)
    assert macrs_sl_pct("27.5", 0, 1) == Decimal("0")
