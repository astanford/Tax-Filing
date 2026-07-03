"""Tests for engine/constants_2025.py.

The bracket tables must be internally consistent: within a progressive rate
schedule, the base tax at each bracket's lower bound MUST equal the
cumulative tax on all income below it. This property caught the original
MFJ top-bracket error ($188,770 instead of $202,154.50).

Exact values verified against Rev. Proc. 2024-40 (reference/Raw/rp-24-40.pdf).
"""

from decimal import Decimal

import pytest

from engine.constants_2025 import (
    FEDERAL_BRACKETS,
    FILING_STATUSES,
    GA_STANDARD_DEDUCTION,
    GA_TAX_RATE,
    QDCG_THRESHOLDS,
    SALT_CAP,
    STANDARD_DEDUCTION,
)


@pytest.mark.parametrize("status", FILING_STATUSES)
def test_bracket_continuity(status):
    """base_tax[i] must equal cumulative tax below bracket i's lower bound."""
    brackets = FEDERAL_BRACKETS[status]
    cumulative = Decimal("0")
    prev_ceiling = Decimal("0")
    for ceiling, rate, base_tax in brackets:
        assert base_tax == cumulative, (
            f"{status}: base at lower bound {prev_ceiling} is {base_tax}, "
            f"but cumulative tax below is {cumulative}"
        )
        if ceiling is not None:
            cumulative += rate * (ceiling - prev_ceiling)
            prev_ceiling = ceiling


@pytest.mark.parametrize("status", FILING_STATUSES)
def test_bracket_shape(status):
    """Rates ascend 10%→37%; ceilings strictly increase; top is unbounded."""
    brackets = FEDERAL_BRACKETS[status]
    rates = [b[1] for b in brackets]
    assert rates == [Decimal(r) for r in
                     ("0.10", "0.12", "0.22", "0.24", "0.32", "0.35", "0.37")]
    ceilings = [b[0] for b in brackets]
    assert ceilings[-1] is None
    finite = ceilings[:-1]
    assert all(a < b for a, b in zip(finite, finite[1:]))


# Top-bracket (start, base) per Rev. Proc. 2024-40 §2.01 Tables 1-4.
TOP_BRACKETS = {
    "MFJ": (Decimal("751600"), Decimal("202154.50")),
    "HoH": (Decimal("626350"), Decimal("187031.50")),
    "Single": (Decimal("626350"), Decimal("188769.75")),
    "MFS": (Decimal("375800"), Decimal("101077.25")),
}


@pytest.mark.parametrize("status", FILING_STATUSES)
def test_top_bracket_matches_rev_proc(status):
    brackets = FEDERAL_BRACKETS[status]
    start, base = TOP_BRACKETS[status]
    assert brackets[-2][0] == start
    assert brackets[-1][2] == base


def test_mfs_is_not_single_alias():
    """MFS has its own 37% boundary at $375,800 (half of MFJ's $751,600)."""
    assert FEDERAL_BRACKETS["MFS"][-2][0] == Decimal("375800")
    assert FEDERAL_BRACKETS["MFS"][-2][0] == FEDERAL_BRACKETS["MFJ"][-2][0] / 2
    assert FEDERAL_BRACKETS["MFS"] is not FEDERAL_BRACKETS["Single"]


def test_qdcg_thresholds_match_rev_proc():
    """Rev. Proc. 2024-40 §2.03 zero/15% maximum amounts."""
    assert QDCG_THRESHOLDS["MFJ"] == {"zero_max": Decimal("96700"), "fifteen_max": Decimal("600050")}
    assert QDCG_THRESHOLDS["MFS"] == {"zero_max": Decimal("48350"), "fifteen_max": Decimal("300000")}
    assert QDCG_THRESHOLDS["HoH"] == {"zero_max": Decimal("64750"), "fifteen_max": Decimal("566700")}
    assert QDCG_THRESHOLDS["Single"] == {"zero_max": Decimal("48350"), "fifteen_max": Decimal("533400")}


def test_standard_deductions():
    """2025-tax-numbers.md, Standard Deduction."""
    assert STANDARD_DEDUCTION == {
        "MFJ": Decimal("31500"),
        "Single": Decimal("15750"),
        "MFS": Decimal("15750"),
        "HoH": Decimal("23625"),
    }


def test_salt_cap_mfs_is_half():
    for key in ("base", "floor", "threshold"):
        assert SALT_CAP["MFS"][key] * 2 == SALT_CAP["MFJ"][key]


def test_georgia_numbers():
    """georgia-500-guide.md / 2025-tax-numbers.md Georgia sections."""
    assert GA_TAX_RATE == Decimal("0.0519")
    assert GA_STANDARD_DEDUCTION["MFJ"] == Decimal("24000")
    assert GA_STANDARD_DEDUCTION["Single"] == Decimal("12000")


@pytest.mark.parametrize("status", FILING_STATUSES)
def test_every_status_in_every_table(status):
    for table in (FEDERAL_BRACKETS, QDCG_THRESHOLDS, STANDARD_DEDUCTION,
                  SALT_CAP, GA_STANDARD_DEDUCTION):
        assert status in table
