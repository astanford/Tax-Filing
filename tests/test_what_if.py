"""Tests for what_if.py — the planning engine's core computations.

Bracket expectations from Rev. Proc. 2024-40 (reference/Raw/rp-24-40.pdf);
SE tax from self-employment-qbi.md; GA flow from georgia-500-guide.md.
"""

from decimal import Decimal

import what_if as wi
from engine.constants_2025 import FEDERAL_BRACKETS


def test_apply_brackets_mfj_simple():
    """$168,500 MFJ: 11157 + 22% * (168500-96950) = 26898."""
    tax = wi.apply_brackets(Decimal("168500"), FEDERAL_BRACKETS["MFJ"])
    assert tax == Decimal("26898.00")


def test_apply_brackets_mfs_top_bracket():
    """$400K MFS: 101077.25 + 37% * (400000-375800) = 110031.25.
    The old Single-alias table gave 109547.25 — understated by $484."""
    tax = wi.apply_brackets(Decimal("400000"), FEDERAL_BRACKETS["MFS"])
    assert tax == Decimal("110031.25")


def test_apply_brackets_zero_and_negative():
    assert wi.apply_brackets(Decimal("0"), FEDERAL_BRACKETS["MFJ"]) == Decimal("0")
    assert wi.apply_brackets(Decimal("-5"), FEDERAL_BRACKETS["MFJ"]) == Decimal("0")


def test_compute_se_tax():
    """$100K Schedule C, no wages: 92.35% net; 12.4% SS + 2.9% Medicare."""
    se_tax, half = wi.compute_se_tax(Decimal("100000"), Decimal("0"))
    assert se_tax == Decimal("14129.55")
    assert half == Decimal("7064.78")


def test_se_tax_respects_ss_wage_base():
    """Wages already at the $176,100 SS base: only the 2.9% Medicare part."""
    se_tax, _ = wi.compute_se_tax(Decimal("100000"), Decimal("176100"))
    assert se_tax == Decimal("2678.15")   # 92350 * 2.9%


def test_se_tax_zero_at_or_below_400():
    assert wi.compute_se_tax(Decimal("400"), Decimal("0")) == (Decimal("0"), Decimal("0"))


def test_compute_total_tax_mfj_standard_deduction():
    result = wi.compute_total_tax({
        "filing_status": "MFJ",
        "wages_primary": "200000",
    })
    assert result["agi"] == "200000.00"
    assert result["deduction_type"] == "standard"
    assert result["taxable_income"] == "168500.00"
    assert result["federal_tax"] == "26898.00"
    # GA: 200000 - 24000 std = 176000 * 5.19% = 9134.40
    assert result["ga_taxable_income"] == "176000.00"
    assert result["ga_state_tax"] == "9134.40"
    assert result["additional_medicare_tax"] == "0.00"
    assert result["total_tax"] == "36032.40"


def test_additional_medicare_above_threshold():
    result = wi.compute_total_tax({
        "filing_status": "MFJ",
        "wages_primary": "300000",
    })
    # (300000 - 250000) * 0.9% = 450
    assert result["additional_medicare_tax"] == "450.00"


def test_ga_itemizer_credit_mfj():
    """Itemizing MFJ couple gets up to $300/taxpayer off GA tax."""
    result = wi.compute_total_tax({
        "filing_status": "MFJ",
        "wages_primary": "200000",
        "mortgage_interest": "20000",
        "state_local_tax": "15000",
    })
    assert result["deduction_type"] == "itemized"
    assert result["deduction_amount"] == "35000.00"
    assert result["ga_itemizer_credit"] == "600.00"
    # GA: 200000 - 35000 = 165000 * 5.19% = 8563.50, minus 600 credit
    assert result["ga_state_tax"] == "7963.50"


def test_ira_deductibility_phaseout_mfj():
    assert wi.compute_ira_deductibility(Decimal("126000"), Decimal("7000"), "MFJ") == Decimal("7000")
    assert wi.compute_ira_deductibility(Decimal("146000"), Decimal("7000"), "MFJ") == Decimal("0")
    assert wi.compute_ira_deductibility(Decimal("136000"), Decimal("7000"), "MFJ") == Decimal("3500")


def test_max_hsa_scenario_saves_tax():
    result = wi.what_if({
        "baseline": {"filing_status": "MFJ", "wages_primary": "200000"},
        "scenario": {"name": "max_hsa"},
    })
    baseline_total = Decimal(result["baseline"]["total_tax"])
    modified_total = Decimal(result["modified"]["total_tax"])
    savings = Decimal(result["savings"]["total_tax"])
    assert savings == baseline_total - modified_total
    assert savings > 0
    # HSA advisory notes must carry the verify-against-IRS.gov warning
    assert any("verify against IRS.gov" in n for n in result["notes"])


def test_schedule_e_net_flows_into_agi_without_se_tax():
    result = wi.compute_total_tax({
        "filing_status": "MFJ",
        "wages_primary": "100000",
        "schedule_e_net": "12000",
    })
    assert result["agi"] == "112000.00"
    assert result["se_tax"] == "0.00"
