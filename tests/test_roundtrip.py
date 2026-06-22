"""End-to-end: a fabricated full return (rentals + passthrough) validates clean."""
import json

import validate_prior_year as v


def fabricated_full_return():
    return {
        "tax_year": 2024,
        "source": "test",
        "filing_status": "MFJ",
        "federal": {
            "agi_line_11": "185000.00",
            "total_tax_line_24": "24500.00",
            "qbi_carryforward_form_8995_line_16": "0.00",
            "capital_loss_carryforward": "1200.00",
            "itemized": True,
        },
        "georgia": {"ga_tax_line_16": "7977.00", "ga_nol_carryforward": "0.00"},
        "state_refund_received_during_current_year": "223.00",
        "rentals": [{
            "property_label": "Rental (456 Oak Ave - Oak LLC)",
            "classification": "short_term",
            "suspended_passive_loss_form_8582": "3400.00",
            "assets": [{
                "description": "Building",
                "placed_in_service": "2022-05",
                "cost_basis": "275000.00",
            }],
        }],
        "passthrough": [{
            "entity_label": "Partnership (Acme Partners LP)",
            "entity_type": "partnership",
            "is_ptp": False,
            "basis_carryforward_704d_1366d": "12000.00",
            "at_risk_carryforward_465": "8000.00",
            "suspended_passive_loss_form_8582": "5000.00",
            "qbi_passthrough_form_8995": "0.00",
        }],
        "notes": ["Itemized in 2024; 2025 GA refund may be federally taxable."],
    }


def test_full_return_validates_clean(tmp_path):
    p = tmp_path / "carryovers-2024.json"
    p.write_text(json.dumps(fabricated_full_return()))
    result = v.validate({"json_path": str(p)})
    assert result["verdict"] == "accepted", result
    assert result["pii_findings"] == []
    assert result["schema_errors"] == []
    assert result["summary"]["rental_properties"] == 1
    assert result["summary"]["passthrough_entities"] == 1
