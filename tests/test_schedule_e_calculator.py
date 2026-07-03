"""Tests for schedule_e_calculator.py — Schedule E Part I + simplified 8582.

Depreciation percentages from Pub 946 Appendix A Tables A-6/A-7a
(rental-depreciation.md). Allowance rules from passive-activity-losses.md.
"""

from decimal import Decimal

import schedule_e_calculator as se


def _long_term_property(**overrides):
    prop = {
        "name": "123 Main St",
        "classification": "long_term",
        "rents_received": "24000",
        "expenses": {
            "insurance": "1200",
            "management_fees": "2400",
            "mortgage_interest": "8000",
            "repairs": "1500",
            "taxes": "3000",
        },
        "depreciation": {
            "building_basis": "275000",
            "placed_in_service_month": 5,
            "placed_in_service_year": 2022,
            "recovery_years": "27.5",
        },
    }
    prop.update(overrides)
    return prop


def test_steady_state_depreciation_27_5():
    """Year 4 of 27.5-yr SL: 3.636% of $275,000 = $9,999.00 (Table A-6)."""
    result = se.schedule_e({
        "tax_year": 2025, "magi": "120000", "filing_status": "MFJ",
        "active_participation": True,
        "properties": [_long_term_property()],
    })
    assert result["totals"]["line_23d_total_depreciation"] == "9999.00"
    # Net: 24000 - (16100 + 9999) = -2099
    assert result["properties"][0]["net_income_or_loss"] == "-2099.00"


def test_year1_mid_month_depreciation():
    """Placed in service May of the tax year: 2.273% (Table A-6, month 5)."""
    prop = _long_term_property()
    prop["depreciation"]["placed_in_service_year"] = 2025
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "properties": [prop],
    })
    # 275000 * 2.273% = 6250.75
    assert result["totals"]["line_23d_total_depreciation"] == "6250.75"
    # First-year placement requires Form 4562
    assert any("Form 4562" in n for n in result["notes"])


def test_allowance_phaseout_partial():
    """MAGI $120K: allowance = 25000 - 50%*(120000-100000) = $15,000; a
    $2,099 rental loss is fully allowed."""
    result = se.schedule_e({
        "tax_year": 2025, "magi": "120000", "filing_status": "MFJ",
        "active_participation": True,
        "properties": [_long_term_property()],
    })
    f = result["form_8582"]
    assert f["special_allowance_available"] == "15000.00"
    assert f["allowed_loss_total"] == "2099.00"
    assert f["suspended_loss_carryforward"] == "0.00"
    assert result["line_26_total_rental_income_or_loss"] == "-2099.00"


def test_allowance_fully_phased_out_suspends_loss():
    result = se.schedule_e({
        "tax_year": 2025, "magi": "200000", "filing_status": "MFJ",
        "active_participation": True,
        "properties": [_long_term_property()],
    })
    f = result["form_8582"]
    assert f["special_allowance_available"] == "0.00"
    assert f["suspended_loss_carryforward"] == "2099.00"
    assert result["line_26_total_rental_income_or_loss"] == "0.00"
    assert f["form_8582_needed"] is True


def test_prior_suspended_loss_added_to_passive_losses():
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "active_participation": True, "prior_suspended_loss": "5000",
        "properties": [_long_term_property()],
    })
    f = result["form_8582"]
    # 2099 current + 5000 prior, all within the full $25K allowance
    assert f["passive_losses_incl_prior_suspended"] == "7099.00"
    assert f["allowed_loss_total"] == "7099.00"
    assert result["line_26_total_rental_income_or_loss"] == "-7099.00"


def test_mfs_living_together_gets_no_allowance():
    result = se.schedule_e({
        "tax_year": 2025, "magi": "40000", "filing_status": "MFS",
        "active_participation": True, "mfs_lived_apart_all_year": False,
        "properties": [_long_term_property()],
    })
    assert result["form_8582"]["special_allowance_available"] == "0.00"


def test_mfs_apart_gets_half_allowance():
    result = se.schedule_e({
        "tax_year": 2025, "magi": "40000", "filing_status": "MFS",
        "active_participation": True, "mfs_lived_apart_all_year": True,
        "properties": [_long_term_property()],
    })
    assert result["form_8582"]["special_allowance_available"] == "12500.00"


def test_short_term_no_material_participation_no_allowance():
    """Avg <=7 days is NOT a rental activity under §469 — no $25K allowance."""
    prop = _long_term_property(classification="short_term")
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "active_participation": True,
        "properties": [prop],
    })
    assert result["properties"][0]["section_469_bucket"] == "nonrental_passive"
    assert result["form_8582"]["suspended_loss_carryforward"] == "2099.00"
    assert result["line_26_total_rental_income_or_loss"] == "0.00"


def test_short_term_with_material_participation_is_nonpassive():
    prop = _long_term_property(classification="short_term",
                               material_participation=True)
    result = se.schedule_e({
        "tax_year": 2025, "magi": "200000", "filing_status": "MFJ",
        "properties": [prop],
    })
    assert result["properties"][0]["section_469_bucket"] == "nonrental_nonpassive"
    # Nonpassive loss fully deductible despite high MAGI
    assert result["line_26_total_rental_income_or_loss"] == "-2099.00"


def test_substantial_services_excluded_to_schedule_c():
    prop = _long_term_property(substantial_services=True)
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "properties": [prop],
    })
    assert result["schedule_c_excluded_properties"] == ["123 Main St"]
    assert result["totals"]["line_23a_total_rents"] == "0.00"
    assert result["line_26_total_rental_income_or_loss"] == "0.00"


def test_ga_bonus_depreciation_addback_flagged():
    prop = _long_term_property()
    prop["depreciation"]["bonus_depreciation_claimed"] = "10000"
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "properties": [prop],
    })
    assert result["ga_bonus_depreciation_addback"] == "10000.00"
    assert any("Georgia" in n and "168(k)" in n for n in result["notes"])


def test_39_year_steady_state():
    prop = _long_term_property()
    prop["depreciation"]["recovery_years"] = "39"
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "properties": [prop],
    })
    # 275000 * 2.564% = 7051.00
    assert result["totals"]["line_23d_total_depreciation"] == "7051.00"


def test_passive_income_absorbs_passive_losses_first():
    winner = _long_term_property(name="Winner", rents_received="30000")
    loser = _long_term_property(name="Loser", rents_received="10000")
    result = se.schedule_e({
        "tax_year": 2025, "magi": "200000", "filing_status": "MFJ",
        "active_participation": True,
        "properties": [winner, loser],
    })
    # Winner: 30000 - 26099 = +3901; Loser: 10000 - 26099 = -16099.
    # Allowance is $0 at 200K MAGI, but income absorbs 3901 of the loss.
    f = result["form_8582"]
    assert f["passive_income"] == "3901.00"
    assert f["allowed_loss_total"] == "3901.00"
    assert f["suspended_loss_carryforward"] == "12198.00"
    assert result["line_26_total_rental_income_or_loss"] == "0.00"


# --- Regression tests from the Part I validation (2026-07-03) --------------
# docs/SCHEDULE-E-PART1-VALIDATION.md

def test_year_28_partial_depreciation_january():
    """Table A-6 year 28 (Jan placement) = 1.970%, not the flat 3.636%.
    Old code overstated by ~$4,581 on a $275K basis."""
    prop = _long_term_property()
    prop["depreciation"]["placed_in_service_year"] = 1998
    prop["depreciation"]["placed_in_service_month"] = 1
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "properties": [prop],
    })
    # 275000 * 1.970% = 5417.50
    assert result["totals"]["line_23d_total_depreciation"] == "5417.50"


def test_year_29_december_placement_still_depreciates():
    """Table A-6 year 29 exists for Jul-Dec placements (Dec = 1.667%).
    Old code returned $0 with a wrong 'exhausted' note."""
    prop = _long_term_property()
    prop["depreciation"]["placed_in_service_year"] = 1997
    prop["depreciation"]["placed_in_service_month"] = 12
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "properties": [prop],
    })
    # 275000 * 1.667% = 4584.25
    assert result["totals"]["line_23d_total_depreciation"] == "4584.25"


def test_fully_depreciated_after_table_ends():
    prop = _long_term_property()
    prop["depreciation"]["placed_in_service_year"] = 1990
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "properties": [prop],
    })
    assert result["totals"]["line_23d_total_depreciation"] == "0.00"
    assert any("fully depreciated" in n for n in result["notes"])


def test_year_40_partial_for_39_year_property():
    """Table A-7a year 40 (Jan placement) = 0.107%, not 2.564%."""
    prop = _long_term_property()
    prop["depreciation"]["recovery_years"] = "39"
    prop["depreciation"]["placed_in_service_year"] = 1986
    prop["depreciation"]["placed_in_service_month"] = 1
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "properties": [prop],
    })
    # 275000 * 0.107% = 294.25
    assert result["totals"]["line_23d_total_depreciation"] == "294.25"


def test_alternating_year_uses_3637():
    """Table A-6 year 10 (Jan placement) = 3.637%, not 3.636%."""
    prop = _long_term_property()
    prop["depreciation"]["placed_in_service_year"] = 2016
    prop["depreciation"]["placed_in_service_month"] = 1
    result = se.schedule_e({
        "tax_year": 2025, "magi": "50000", "filing_status": "MFJ",
        "properties": [prop],
    })
    # 275000 * 3.637% = 10001.75
    assert result["totals"]["line_23d_total_depreciation"] == "10001.75"


def test_allowance_base_nets_rental_income_form_8582_line_4():
    """Form 8582 line 4 = smaller of the line 1d NET rental loss or the
    line 3 loss. Profitable rental + other-passive loss must not inflate
    the allowance base (i8582 pp.10-11 worked example pattern).

    Rental A +$2,000, Rental B -$3,000, short-term (no material
    participation) -$5,000, MAGI $90K MFJ:
    line 1d = -1000; allowance = 1000; allowed = 2000 absorbed + 1000;
    suspended = 5000; Schedule E net = -1000."""
    rental_a = _long_term_property(name="Rental A", rents_received="28099")
    rental_b = _long_term_property(name="Rental B", rents_received="23099")
    st = _long_term_property(name="Beach Cottage", classification="short_term",
                             rents_received="21099")
    result = se.schedule_e({
        "tax_year": 2025, "magi": "90000", "filing_status": "MFJ",
        "active_participation": True,
        "properties": [rental_a, rental_b, st],
    })
    # Each property's expenses total 26099 (16100 + 9999 depreciation):
    # A = +2000, B = -3000, ST = -5000
    f = result["form_8582"]
    assert f["passive_income"] == "2000.00"
    assert f["allowed_loss_total"] == "3000.00"
    assert f["suspended_loss_carryforward"] == "5000.00"
    assert result["line_26_total_rental_income_or_loss"] == "-1000.00"
