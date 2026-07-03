"""Tests for k1_passthrough_calculator.py — the §704(d)/§1366(d) → §465 →
§469 limitation cascade, PTP segregation, and the combined Form 8582.

Rules from reference/curated/passthrough-loss-limitations.md and
k1-guide.md; raw sources i1065sk1.pdf, i1120ssk.pdf, i8582.pdf, p925.pdf.
"""

from decimal import Decimal

import k1_passthrough_calculator as k1


def _entity(**overrides):
    ent = {
        "name": "Acme Partners LP",
        "entity_type": "partnership",
        "is_ptp": False,
        "materially_participates": False,
        "k1": {"box1_ordinary_business": "-12000"},
        "basis_available": "100000",
        "at_risk_available": "100000",
        "carryovers": {
            "basis_carryforward_704d_1366d": "0",
            "at_risk_carryforward_465": "0",
            "suspended_passive_loss_form_8582": "0",
        },
    }
    ent.update(overrides)
    return ent


def _run(entities, **kw):
    data = {"tax_year": 2025, "filing_status": "MFJ", "magi": "90000",
            "entities": entities}
    data.update(kw)
    return k1.compute(data)


# --- Cascade order: basis → at-risk → passive ------------------------------

def test_basis_limits_first():
    """$12K loss, $5K basis: $5K proceeds, $7K suspended by basis."""
    result = _run([_entity(basis_available="5000", at_risk_available="5000")])
    co = result["next_year_carryovers_passthrough"][0]
    assert co["basis_carryforward_704d_1366d"] == "7000.00"
    assert co["at_risk_carryforward_465"] == "0.00"


def test_at_risk_limits_second():
    """$12K loss, $12K basis but only $4K at risk: $8K at-risk suspended,
    Line 28 column (f) checked."""
    result = _run([_entity(basis_available="12000", at_risk_available="4000")])
    co = result["next_year_carryovers_passthrough"][0]
    assert co["basis_carryforward_704d_1366d"] == "0.00"
    assert co["at_risk_carryforward_465"] == "8000.00"
    assert result["schedule_e_part_2"]["rows"][0]["col_f_not_at_risk"] is True


def test_passive_limits_third_no_passive_income():
    """Loss clears basis and at-risk but is passive with no passive income
    and no allowance eligibility (not rental RE): fully suspended on 8582."""
    result = _run([_entity()])
    co = result["next_year_carryovers_passthrough"][0]
    assert co["suspended_passive_loss_form_8582"] == "12000.00"
    assert result["schedule_e_part_2"]["line_32_total"] == "0.00"


def test_prior_basis_carryforward_retests():
    """Prior basis-suspended $3K joins this year's $12K loss against basis."""
    ent = _entity(basis_available="20000")
    ent["carryovers"]["basis_carryforward_704d_1366d"] = "3000"
    result = _run([ent])
    # 15000 total clears basis and at-risk, all passive-suspended
    co = result["next_year_carryovers_passthrough"][0]
    assert co["basis_carryforward_704d_1366d"] == "0.00"
    assert co["suspended_passive_loss_form_8582"] == "15000.00"


def test_missing_basis_blocks_entity():
    ent = _entity()
    del ent["basis_available"]
    result = _run([ent])
    assert result["blocked_entities"] == ["Acme Partners LP"]
    assert any("basis_available" in n for n in result["notes"])


# --- Passive vs nonpassive -------------------------------------------------

def test_material_participation_is_nonpassive():
    """Materially participating: loss fully deductible in column (i)."""
    result = _run([_entity(materially_participates=True)])
    row = result["schedule_e_part_2"]["rows"][0]
    assert row["col_i_nonpassive_loss"] == "12000.00"
    assert result["schedule_e_part_2"]["line_32_total"] == "-12000.00"


def test_passive_income_entity_reports_col_h():
    result = _run([_entity(k1={"box1_ordinary_business": "9000"})])
    row = result["schedule_e_part_2"]["rows"][0]
    assert row["col_h_passive_income"] == "9000.00"
    assert result["schedule_e_part_2"]["line_32_total"] == "9000.00"


def test_passive_income_absorbs_passive_loss_across_entities():
    """$9K passive income + $12K passive loss: $9K absorbed, $3K suspended
    (no allowance for non-rental trade/business)."""
    result = _run([
        _entity(name="Winner LP", k1={"box1_ordinary_business": "9000"}),
        _entity(name="Loser LP"),
    ])
    f = result["combined_form_8582"]
    assert f["allowed_loss_total"] == "9000.00"
    assert f["suspended_total"] == "3000.00"
    # Line 32 = 9000 income - 9000 allowed loss = 0
    assert result["schedule_e_part_2"]["line_32_total"] == "0.00"


def test_k1_rental_re_active_participation_gets_allowance():
    """K-1 box 2 rental RE loss with active participation qualifies for the
    $25K allowance (bucket 1 / Form 8582 line 1d)."""
    result = _run([_entity(
        k1={"box2_net_rental_re": "-10000"},
        active_participation_rental=True,
    )])
    f = result["combined_form_8582"]
    assert f["line_1d_rental_net"] == "-10000.00"
    assert f["allowed_by_allowance"] == "10000.00"
    assert f["suspended_total"] == "0.00"
    assert result["schedule_e_part_2"]["line_32_total"] == "-10000.00"


def test_guaranteed_payments_always_nonpassive_income():
    result = _run([_entity(
        k1={"box1_ordinary_business": "0", "box4_guaranteed_payments": "30000"},
    )])
    row = result["schedule_e_part_2"]["rows"][0]
    assert row["col_k_nonpassive_income"] == "30000.00"
    assert result["schedule_e_part_2"]["line_32_total"] == "30000.00"


# --- PTP segregation --------------------------------------------------------

def test_ptp_loss_never_on_8582():
    result = _run([_entity(name="Pipeline PTP", is_ptp=True)])
    f = result["combined_form_8582"]
    assert f["line_2d_other_passive_net"] == "0.00"
    assert result["ptp"][0]["suspended_passive_loss_form_8582"] == "12000.00"
    assert any("NEVER entered on Form 8582" in n for n in result["notes"])


def test_ptp_income_nets_against_own_suspended_loss():
    ent = _entity(name="Pipeline PTP", is_ptp=True,
                  k1={"box1_ordinary_business": "5000"})
    ent["carryovers"]["suspended_passive_loss_form_8582"] = "3000"
    result = _run([ent])
    ptp = result["ptp"][0]
    assert ptp["ptp_loss_allowed"] == "3000.00"
    assert ptp["ptp_income_reported"] == "2000.00"
    assert ptp["suspended_passive_loss_form_8582"] == "0.00"
    # Part II shows full income (col h) and allowed loss (col g): net $2,000
    row = result["schedule_e_part_2"]["rows"][0]
    assert row["col_h_passive_income"] == "5000.00"
    assert row["col_g_passive_loss_allowed"] == "3000.00"
    assert result["schedule_e_part_2"]["line_32_total"] == "2000.00"


def test_ptp_full_absorption_nets_to_zero_on_line_32():
    ent = _entity(name="Pipeline PTP", is_ptp=True,
                  k1={"box1_ordinary_business": "2500"})
    ent["carryovers"]["suspended_passive_loss_form_8582"] = "4000"
    result = _run([ent])
    assert result["schedule_e_part_2"]["line_32_total"] == "0.00"
    assert result["ptp"][0]["suspended_passive_loss_form_8582"] == "1500.00"


# --- Combined 8582 with Part I rentals --------------------------------------

def test_combined_8582_with_part1_rentals():
    """Part I rental loss (allowance-eligible) + K-1 passive loss share one
    form: allowance covers only the rental (line 1d) side."""
    result = _run(
        [_entity()],   # $12K passive K-1 loss, bucket 2
        part1_buckets={
            "rental_activity_income": "0",
            "rental_activity_losses": "2099",
            "nonrental_passive_income": "0",
            "nonrental_passive_losses": "0",
            "prior_suspended": "0",
        },
        active_participation=True,
    )
    f = result["combined_form_8582"]
    assert f["line_1d_rental_net"] == "-2099.00"
    assert f["line_2d_other_passive_net"] == "-12000.00"
    # Allowance limited to the line 1d loss (Form 8582 line 4)
    assert f["allowed_by_allowance"] == "2099.00"
    assert f["suspended_total"] == "12000.00"
    # Part I's share of the suspension (2099/14099 of 12000, Decimal-computed)
    assert Decimal(f["part1_rentals_share_of_suspended"]) == Decimal("1786.51")


# --- Part III (estates/trusts) ----------------------------------------------

def test_trust_reports_on_part_3():
    result = _run([_entity(
        name="Family Trust", entity_type="estate_trust",
        k1={"box1_ordinary_business": "4000"},
    )])
    assert result["schedule_e_part_2"]["rows"] == []
    row = result["schedule_e_part_3"]["rows"][0]
    assert row["col_d_passive_income"] == "4000.00"
    assert result["schedule_e_part_3"]["line_37_total"] == "4000.00"


# --- S-corp specifics ---------------------------------------------------------

def test_s_corp_loss_requires_form_7203():
    result = _run([_entity(entity_type="s_corp", materially_participates=True)])
    row = result["schedule_e_part_2"]["rows"][0]
    assert row["col_b_type"] == "S"
    assert row["col_e_basis_computation_required"] is True


def test_sec179_splits_into_col_j_for_nonpassive():
    result = _run([_entity(
        materially_participates=True,
        k1={"box1_ordinary_business": "-9000", "section_179": "3000"},
    )])
    row = result["schedule_e_part_2"]["rows"][0]
    assert row["col_j_section_179"] == "3000.00"
    assert row["col_i_nonpassive_loss"] == "9000.00"
    assert result["schedule_e_part_2"]["line_31_loss_cols_g_i_j"] == "12000.00"


# --- SE + QBI info -----------------------------------------------------------

def test_se_earnings_totaled():
    result = _run([_entity(
        materially_participates=True,
        k1={"box1_ordinary_business": "50000", "box14a_se_earnings": "50000"},
    )])
    assert result["se_earnings_box_14a_total"] == "50000.00"


def test_limited_qbi_loss_flagged():
    result = _run([_entity(
        basis_available="5000", at_risk_available="5000",
        k1={"box1_ordinary_business": "-12000", "qbi_income": "-12000"},
    )])
    assert result["qbi_passthrough"][0]["loss_limited"] is True
    assert any("QBI" in n and "ALLOWED" in n for n in result["notes"])


def test_unknown_entity_type_is_error():
    assert "error" in _run([_entity(entity_type="c_corp")])
