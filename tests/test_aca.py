"""Tests for engine/aca.py — Form 8962 annual method.

Golden values from aca-premium-tax-credit.md (i8962 2025: Table 1-1 FPL,
Table 2 applicable figures incl. verified anchor rows, Table 5 repayment
caps) and rp-24-40 §2.07.
"""

from decimal import Decimal

from engine.aca import applicable_figure, form_8962, fpl_for_household
from engine.manifest import Manifest
from engine.return_engine import compute_return


def _aca(**overrides):
    aca = {
        "household_size": 2,
        "form_1095a": {"annual_premiums": "9600", "annual_slcsp": "9000",
                       "annual_aptc": "8400"},
        "full_year_unchanged_coverage": True,
    }
    aca.update(overrides)
    return aca


def test_fpl_matches_printed_table():
    """Table 1-1, 48 states (2024 guidelines for 2025 coverage)."""
    assert fpl_for_household(1) == Decimal("15060")
    assert fpl_for_household(2) == Decimal("20440")
    assert fpl_for_household(3) == Decimal("25820")
    assert fpl_for_household(4) == Decimal("31200")
    assert fpl_for_household(5) == Decimal("36580")


def test_applicable_figure_anchor_rows():
    """Verified Table 2 rows from the curated extraction."""
    assert applicable_figure(Decimal("133")) == Decimal("0.0000")
    assert applicable_figure(Decimal("150")) == Decimal("0.0000")
    assert applicable_figure(Decimal("151")) == Decimal("0.0004")
    assert applicable_figure(Decimal("176")) == Decimal("0.0104")
    assert applicable_figure(Decimal("199")) == Decimal("0.0196")
    assert applicable_figure(Decimal("200")) == Decimal("0.0200")
    assert applicable_figure(Decimal("251")) == Decimal("0.0404")
    assert applicable_figure(Decimal("300")) == Decimal("0.0600")
    assert applicable_figure(Decimal("301")) == Decimal("0.0603")
    assert applicable_figure(Decimal("302")) == Decimal("0.0605")
    assert applicable_figure(Decimal("353")) == Decimal("0.0733")
    assert applicable_figure(Decimal("400")) == Decimal("0.0850")
    assert applicable_figure(Decimal("401")) == Decimal("0.0850")


def test_owner_scenario_net_ptc():
    """MFJ, household of 2, $36,000 MAGI: 176% FPL, figure 0.0104,
    contribution $374; PTC = min(9600, 9000-374) = 8626; APTC 8400 ->
    net PTC $226 to Schedule 3."""
    m = Manifest(2025, "MFJ")
    net_ptc, repay = form_8962(m, _aca(), Decimal("36000"), Decimal("0"), "MFJ")
    assert m.get("Form 8962", "line_5_pct_of_fpl") == Decimal("176")
    assert m.get("Form 8962", "line_8a_annual_contribution") == Decimal("374")
    assert net_ptc == Decimal("226.00")
    assert repay == Decimal("0")


def test_excess_aptc_capped_by_table_5():
    """Same scenario but APTC 9,600: excess 974, cap $750 at <200% FPL
    (other-than-single)."""
    aca = _aca()
    aca["form_1095a"]["annual_aptc"] = "9600"
    m = Manifest(2025, "MFJ")
    net_ptc, repay = form_8962(m, aca, Decimal("36000"), Decimal("0"), "MFJ")
    assert net_ptc == Decimal("0")
    assert m.get("Form 8962", "line_27_excess_aptc") == Decimal("974")
    assert repay == Decimal("750.00")


def test_single_gets_half_caps():
    aca = _aca(household_size=1)
    aca["form_1095a"]["annual_aptc"] = "9600"
    m = Manifest(2025, "Single")
    # 36000/15060 = 239% -> figure band 200-300; contribution larger
    net_ptc, repay = form_8962(m, aca, Decimal("36000"), Decimal("0"), "Single")
    assert m.get("Form 8962", "line_5_pct_of_fpl") == Decimal("239")
    assert repay <= Decimal("975")   # single cap in the 200-<300 band


def test_above_400_pct_uncapped_but_85_pct_figure():
    aca = _aca()
    aca["form_1095a"]["annual_aptc"] = "9600"
    m = Manifest(2025, "MFJ")
    net_ptc, repay = form_8962(m, aca, Decimal("100000"), Decimal("0"), "MFJ")
    assert m.get("Form 8962", "line_5_pct_of_fpl") == Decimal("401")
    # contribution = 100000 * 0.085 = 8500 > SLCSP 9000-8500=500 -> PTC 500
    assert repay == Decimal("9100.00")   # uncapped: 9600 - 500


def test_below_100_pct_blocks():
    m = Manifest(2025, "MFJ")
    net_ptc, repay = form_8962(m, _aca(), Decimal("18000"), Decimal("0"), "MFJ")
    assert (net_ptc, repay) == (Decimal("0"), Decimal("0"))
    assert any("100%" in b["item"] or "100%" in b["reason"] for b in m.blocked)


def test_mfs_blocks():
    m = Manifest(2025, "MFS")
    net_ptc, repay = form_8962(m, _aca(), Decimal("36000"), Decimal("0"), "MFS")
    assert (net_ptc, repay) == (Decimal("0"), Decimal("0"))
    assert m.blocked


def test_mid_year_change_blocks_to_monthly():
    m = Manifest(2025, "MFJ")
    aca = _aca(full_year_unchanged_coverage=False)
    net_ptc, repay = form_8962(m, aca, Decimal("36000"), Decimal("0"), "MFJ")
    assert m.blocked


def test_tax_exempt_interest_raises_magi():
    """MAGI includes tax-exempt interest — can change the FPL band."""
    m = Manifest(2025, "MFJ")
    form_8962(m, _aca(), Decimal("36000"), Decimal("5000"), "MFJ")
    # (36000+5000)/20440 = 200.5 -> 200
    assert m.get("Form 8962", "line_5_pct_of_fpl") == Decimal("200")


def test_integration_net_ptc_flows_to_payments():
    """End-to-end: net PTC lands on Schedule 3 line 9 and in total payments."""
    inputs = {
        "tax_year": 2025, "filing_status": "MFJ",
        "income": {
            "interest": [{"payer": "Bank", "amount": "1000"}],
            "schedule_e_part2_line_32": "35000",
        },
        "itemized": {}, "qbi": {}, "carryovers": {},
        "payments": {"federal_withholding": "0",
                     "federal_estimated_payments": "3000",
                     "prior_year_total_tax": "1000", "prior_year_agi": "40000"},
        "georgia": {},
        "aca": _aca(),
    }
    result = compute_return(inputs)
    sched3 = result["forms"]["Schedule 3"]
    assert Decimal(sched3["line_9_net_premium_tax_credit"]["value"]) > 0
    f1040 = result["forms"]["Form 1040"]
    assert "line_31_schedule_3_line_13" in f1040
    assert Decimal(f1040["line_33_total_payments"]["value"]) > Decimal("3000")


def test_integration_repayment_raises_total_tax():
    inputs = {
        "tax_year": 2025, "filing_status": "MFJ",
        "income": {"schedule_e_part2_line_32": "36000"},
        "itemized": {}, "qbi": {}, "carryovers": {},
        "payments": {"federal_withholding": "0",
                     "federal_estimated_payments": "3000",
                     "prior_year_total_tax": "1000", "prior_year_agi": "40000"},
        "georgia": {},
        "aca": _aca(),
    }
    inputs["aca"]["form_1095a"]["annual_aptc"] = "9600"
    result = compute_return(inputs)
    f1040 = result["forms"]["Form 1040"]
    assert f1040["line_17_schedule_2_line_3"]["value"] == "750.00"
    # line 24 = line 22 (16 + repayment) + line 23
    line_22 = Decimal(f1040["line_22_tax_after_credits"]["value"])
    line_16 = Decimal(f1040["line_16_tax"]["value"])
    assert line_22 - line_16 == Decimal("750.00")
