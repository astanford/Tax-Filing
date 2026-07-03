"""Tests for the Phase 3 return engine (engine/return_engine.py + modules).

Golden values Decimal-derived from the curated references: bracket tables
(rp-24-40.pdf via constants), QDCG thresholds, SALT cap, GA flow.
"""

from decimal import Decimal

from engine.income import qdcg_worksheet
from engine.manifest import Manifest
from engine.other_taxes import form_8959, form_8960, form_8995
from engine.return_engine import compute_return


def _mfj_inputs(**overrides):
    inputs = {
        "tax_year": 2025,
        "filing_status": "MFJ",
        "num_dependents": 0,
        "income": {
            "interest": [{"payer": "Bank X", "amount": "2000"}],
            "dividends_ordinary": [{"payer": "Broker Y", "amount": "10000"}],
            "dividends_qualified": "8000",
            "form_1099b": {
                "short_a": {"proceeds": "50000", "basis": "48000", "adjustments": "0"},
                "long_d": {"proceeds": "120000", "basis": "95000", "adjustments": "0"},
            },
            "schedule_e_line_26": "-2099",
            "schedule_e_part2_line_32": "30000",
            "k1_box14a_se_earnings": "0",
        },
        "adjustments": {},
        "itemized": {
            "state_local_income_tax": "9000",
            "real_estate_tax": "8000",
            "mortgage_interest": "16000",
        },
        "qbi": {"qbi_net": "30000"},
        "carryovers": {},
        "payments": {
            "federal_withholding": "0",
            "federal_estimated_payments": "40000",
            "prior_year_total_tax": "38000",
            "prior_year_agi": "300000",
        },
        "georgia": {
            "us_obligation_interest": "0",
            "ga_withholding": "0",
            "ga_estimated_payments": "9000",
        },
    }
    inputs.update(overrides)
    return inputs


def test_full_return_no_w2_profile():
    """End-to-end fabricated MFJ return mirroring the owner's profile:
    no W-2; interest + dividends + capital gains + rentals + K-1."""
    result = compute_return(_mfj_inputs())
    f1040 = result["forms"]["Form 1040"]

    # Income: 0 wages + 2000 int + 10000 div + 27000 cap gain + 27901 Sch1
    assert f1040["line_7_capital_gain"]["value"] == "27000.00"
    assert f1040["line_9_total_income"]["value"] == "66901.00"
    assert f1040["line_11_agi"]["value"] == "66901.00"
    # Itemized 33000 (SALT 17000 under cap + 16000 mortgage) > std 31500
    assert f1040["line_12_deduction"]["value"] == "33000.00"
    # QBI income limit binds: net capital gain (25000) + qualified div (8000)
    # leaves only 901 of non-preferential taxable income; 20% * 901 = 180.20
    # (self-employment-qbi.md, QBI Deduction Rules — income limit)
    assert f1040["line_13_qbi_deduction"]["value"] == "180.20"
    assert f1040["line_15_taxable_income"]["value"] == "33720.80"
    # Every line carries source + citation
    for line in f1040.values():
        assert line["citation"]

    # GA: agi 66901 - itemized 33000 = 33901 * 5.19% = 1759.46, minus $600
    ga = result["forms"]["GA Form 500"]
    assert ga["line_15c_ga_taxable_income"]["value"] == "33901.00"
    assert ga["line_19_itemizer_credit"]["value"] == "600.00"
    assert ga["line_22_tax_after_credits"]["value"] == "1159.46"


def test_qdcg_worksheet_zero_bracket():
    """MFJ taxable 27,901 with 35,000 preferential income: ordinary part is
    0 (income below preferential), everything preferential fits under the
    $96,700 0% max — tax = ordinary tax on line 6 only."""
    m = Manifest(2025, "MFJ")
    tax = qdcg_worksheet(m, Decimal("27901"), Decimal("8000"),
                         Decimal("27000"), Decimal("27000"), "MFJ")
    # line 5 = 35000 > line 1 -> line 6 = 0 -> all taxed at 0/15/20 within
    # thresholds; at 27,901 total it's all in the 0% band
    assert m.get("QDCG Worksheet", "taxed_at_0pct") == Decimal("27901")
    assert tax == Decimal("0")


def test_qdcg_worksheet_15_pct_band():
    """MFJ: 200,000 taxable, 50,000 preferential. Ordinary 150,000 fills the
    0% band; all 50,000 preferential taxed at 15% = 7,500. Ordinary tax on
    150,000 = 11157 + 22% * 53050 = 22,828. Total 30,328."""
    m = Manifest(2025, "MFJ")
    tax = qdcg_worksheet(m, Decimal("200000"), Decimal("20000"),
                         Decimal("30000"), Decimal("30000"), "MFJ")
    assert m.get("QDCG Worksheet", "taxed_at_0pct") == Decimal("0")
    assert m.get("QDCG Worksheet", "taxed_at_15pct") == Decimal("50000")
    assert tax == Decimal("30328.00")


def test_qdcg_worksheet_20_pct_band():
    """MFJ 700,000 taxable, 150,000 preferential: 550,000 ordinary fills past
    the $600,050 15% max; 50,050 of preferential at 15%, 99,950 at 20%."""
    m = Manifest(2025, "MFJ")
    tax = qdcg_worksheet(m, Decimal("700000"), Decimal("150000"),
                         Decimal("0"), Decimal("0"), "MFJ")
    assert m.get("QDCG Worksheet", "taxed_at_15pct") == Decimal("50050")
    assert m.get("QDCG Worksheet", "taxed_at_20pct") == Decimal("99950")
    # ordinary tax on 550,000 = 114462 + 35% * (550000-501050) = 131,594.50
    # + 15% * 50050 (7507.50) + 20% * 99950 (19990) = 159,092
    assert tax == Decimal("159092.00")


def test_qdcg_never_exceeds_ordinary():
    m = Manifest(2025, "MFJ")
    tax = qdcg_worksheet(m, Decimal("100000"), Decimal("0"),
                         Decimal("0"), Decimal("0"), "MFJ")
    # No preferential income -> equals ordinary bracket tax
    # 11157 + 22% * (100000-96950) = 11,828
    assert tax == Decimal("11828.00")


def test_capital_loss_limited_and_carried():
    inputs = _mfj_inputs()
    inputs["income"]["form_1099b"] = {
        "short_a": {"proceeds": "10000", "basis": "18000", "adjustments": "0"},
    }
    result = compute_return(inputs)
    sd = result["forms"]["Schedule D"]
    assert sd["line_16_total"]["value"] == "-8000.00"
    assert sd["line_21_allowed_loss"]["value"] == "-3000.00"
    assert sd["next_year_carryover_short"]["value"] == "5000.00"
    assert result["forms"]["Form 1040"]["line_7_capital_gain"]["value"] == "-3000.00"


def test_unrecaptured_1250_blocks():
    inputs = _mfj_inputs()
    inputs["income"]["unrecaptured_1250_gain"] = "5000"
    result = compute_return(inputs)
    assert any("1250" in b["item"] for b in result["blocked_for_accountant"])


def test_qbi_over_threshold_blocks_to_8995a():
    inputs = _mfj_inputs()
    inputs["income"]["schedule_e_part2_line_32"] = "500000"
    result = compute_return(inputs)
    assert any(b["form"] == "Form 8995" for b in result["blocked_for_accountant"])
    assert result["forms"]["Form 1040"]["line_13_qbi_deduction"]["value"] == "0.00"


def test_se_tax_from_k1_box14a():
    inputs = _mfj_inputs()
    inputs["income"]["k1_box14a_se_earnings"] = "100000"
    result = compute_return(inputs)
    se = result["forms"]["Schedule SE"]
    assert se["line_12_se_tax"]["value"] == "14129.55"
    assert se["line_13_deduction_half"]["value"] == "7064.78"


def test_safe_harbor_missed_blocks_2210():
    inputs = _mfj_inputs()
    inputs["income"]["schedule_e_part2_line_32"] = "300000"
    inputs["payments"]["federal_estimated_payments"] = "10000"
    result = compute_return(inputs)
    f2210 = result["forms"]["Form 2210"]
    # prior AGI 300000 > 150000 -> 110% of 38000 = 41800 vs 90% of current
    assert f2210["underpayment_exposure"]["value"] is True
    assert any(b["form"] == "Form 2210" for b in result["blocked_for_accountant"])


def test_safe_harbor_met_no_block():
    result = compute_return(_mfj_inputs())
    f2210 = result["forms"]["Form 2210"]
    assert f2210["underpayment_exposure"]["value"] is False


def test_missing_prior_year_tax_is_missing_input():
    inputs = _mfj_inputs()
    del inputs["payments"]["prior_year_total_tax"]
    result = compute_return(inputs)
    assert any(x["field"] == "payments.prior_year_tax" for x in result["missing_inputs"])


# --- module-level unit checks ------------------------------------------------

def test_form_8959_wage_and_se_stack():
    m = Manifest(2025, "MFJ")
    total = form_8959(m, Decimal("200000"), Decimal("100000"), "MFJ")
    # SE income 92,350; threshold left = 50,000; excess 42,350 * 0.9% = 381.15
    assert total == Decimal("381.15")


def test_form_8960_niit():
    m = Manifest(2025, "MFJ")
    niit = form_8960(m, Decimal("300000"), Decimal("40000"), Decimal("0"), "MFJ")
    # min(40000, 50000) * 3.8% = 1520
    assert niit == Decimal("1520.00")


def test_form_8995_loss_carries_forward():
    m = Manifest(2025, "MFJ")
    ded, carry, _ = form_8995(m, Decimal("-5000"), Decimal("2000"),
                              Decimal("0"), Decimal("100000"), Decimal("0"), "MFJ")
    assert ded == Decimal("0")
    assert carry == Decimal("7000")


def test_unknown_filing_status_is_error():
    assert "error" in compute_return({"filing_status": "QSS"})
