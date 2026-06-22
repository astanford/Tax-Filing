"""Passthrough/K-1 carryover schema tests. Fabricated data."""
import json

import validate_prior_year as v


def with_passthrough(entry):
    return {
        "tax_year": 2024,
        "source": "test",
        "filing_status": "MFJ",
        "federal": {"agi_line_11": "185000.00"},
        "passthrough": [entry],
    }


def valid_entry():
    return {
        "entity_label": "Partnership (Acme Partners LP)",
        "entity_type": "partnership",
        "is_ptp": False,
        "basis_carryforward_704d_1366d": "12000.00",
        "at_risk_carryforward_465": "8000.00",
        "suspended_passive_loss_form_8582": "5000.00",
        "qbi_passthrough_form_8995": "0.00",
    }


def test_valid_passthrough_has_no_errors():
    errors, _ = v.schema_check(with_passthrough(valid_entry()))
    assert errors == []


def test_passthrough_must_be_array():
    data = with_passthrough(valid_entry())
    data["passthrough"] = {"not": "a list"}
    errors, _ = v.schema_check(data)
    assert any("passthrough must be an array" in e for e in errors)


def test_passthrough_missing_entity_label_errors():
    e = valid_entry()
    e["entity_label"] = ""
    errors, _ = v.schema_check(with_passthrough(e))
    assert any("entity_label" in err for err in errors)


def test_passthrough_bad_entity_type_errors():
    e = valid_entry()
    e["entity_type"] = "llc"
    errors, _ = v.schema_check(with_passthrough(e))
    assert any("entity_type" in err for err in errors)


def test_passthrough_non_bool_is_ptp_errors():
    e = valid_entry()
    e["is_ptp"] = "yes"
    errors, _ = v.schema_check(with_passthrough(e))
    assert any("is_ptp" in err for err in errors)


def test_passthrough_unparseable_amount_errors():
    e = valid_entry()
    e["at_risk_carryforward_465"] = "lots"
    errors, _ = v.schema_check(with_passthrough(e))
    assert any("at_risk_carryforward_465" in err for err in errors)


def test_passthrough_count_in_summary(tmp_path):
    p = tmp_path / "cy.json"
    p.write_text(json.dumps(with_passthrough(valid_entry())))
    result = v.validate({"json_path": str(p)})
    assert result["verdict"] == "accepted"
    assert result["summary"]["passthrough_entities"] == 1


def test_passthrough_entity_label_is_not_pii():
    # Entity labels are allowed, like property labels — must not be flagged.
    assert v.pii_scan(with_passthrough(valid_entry())) == []
