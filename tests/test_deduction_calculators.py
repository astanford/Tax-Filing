"""Tests for standard_vs_itemized.py and salt_cap_calculator.py."""

import salt_cap_calculator as salt
import standard_vs_itemized as svi


# --- standard_vs_itemized -------------------------------------------------

def test_itemized_wins_for_single_with_mortgage():
    result = svi.compare({
        "filing_status": "Single", "magi": 120000,
        "state_local_income_tax": 5000, "real_estate_tax": 4500,
        "mortgage_interest": 12000,
    })
    assert result["itemized_total"] == "21500.00"
    assert result["standard_deduction"] == "15750.00"
    assert result["recommendation"] == "itemized"
    assert result["advantage"] == "5750.00"


def test_standard_wins_when_itemized_small():
    result = svi.compare({
        "filing_status": "MFJ", "magi": 100000,
        "state_local_income_tax": 4000, "mortgage_interest": 6000,
    })
    assert result["recommendation"] == "standard"
    assert result["standard_deduction"] == "31500.00"


def test_salt_capped_within_itemized():
    """SALT above the effective cap is truncated before comparison."""
    result = svi.compare({
        "filing_status": "MFJ", "magi": 200000,
        "state_local_income_tax": 30000, "real_estate_tax": 15000,
    })
    b = result["itemized_breakdown"]
    assert b["salt_before_cap"] == "45000.00"
    assert b["salt_after_cap"] == "40000.00"
    assert b["salt_lost_to_cap"] == "5000.00"


def test_medical_floor_7_5_percent():
    result = svi.compare({
        "filing_status": "MFJ", "magi": 100000,
        "medical_expenses": 10000,
    })
    b = result["itemized_breakdown"]
    assert b["medical_floor_7_5_pct"] == "7500.00"
    assert b["medical_deduction"] == "2500.00"


def test_unknown_status_is_error():
    assert "error" in svi.compare({"filing_status": "QSS"})


# --- salt_cap_calculator --------------------------------------------------

def test_no_phaseout_below_threshold():
    result = salt.calculate({
        "filing_status": "MFJ", "magi": 400000,
        "state_income_tax": 25000, "real_estate_tax": 10000,
    })
    assert result["phase_out_applies"] is False
    assert result["effective_cap"] == "40000.00"
    assert result["deductible_salt"] == "35000.00"


def test_phaseout_reduces_cap():
    """MAGI $550K: cap = 40000 - 30%*50000 = $25,000."""
    result = salt.calculate({
        "filing_status": "MFJ", "magi": 550000,
        "state_income_tax": 30000, "real_estate_tax": 15000,
    })
    assert result["phase_out_applies"] is True
    assert result["effective_cap"] == "25000.00"
    assert result["deductible_salt"] == "25000.00"
    assert result["salt_lost_to_cap"] == "20000.00"


def test_floor_holds_at_high_magi():
    result = salt.calculate({
        "filing_status": "MFJ", "magi": 700000,
        "state_income_tax": 30000,
    })
    assert result["effective_cap"] == "10000.00"


def test_mfs_uses_half_parameters():
    result = salt.calculate({
        "filing_status": "MFS", "magi": 300000,
        "state_income_tax": 25000,
    })
    # cap = 20000 - 30%*50000 = 5000 floor
    assert result["effective_cap"] == "5000.00"


def test_unknown_status_error():
    assert "error" in salt.calculate({"filing_status": "widow"})
