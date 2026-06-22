"""Schema-validation tests for validate_prior_year.schema_check. Fabricated data."""
import validate_prior_year as v


def valid_full():
    return {
        "tax_year": 2024,
        "source": "test",
        "filing_status": "MFJ",
        "federal": {"agi_line_11": "185000.00", "itemized": True},
        "georgia": {"ga_tax_line_16": "7977.00"},
        "rentals": [{
            "property_label": "Rental (1 A St - A LLC)",
            "classification": "long_term",
            "suspended_passive_loss_form_8582": "3400.00",
            "assets": [{
                "description": "Building",
                "placed_in_service": "2022-05",
                "cost_basis": "275000.00",
            }],
        }],
    }


def test_valid_data_has_no_errors():
    errors, _ = v.schema_check(valid_full())
    assert errors == []


def test_missing_required_top_level_field_errors():
    data = valid_full()
    del data["federal"]
    errors, _ = v.schema_check(data)
    assert any("federal" in e for e in errors)


def test_out_of_range_tax_year_errors():
    data = valid_full()
    data["tax_year"] = 1999
    errors, _ = v.schema_check(data)
    assert any("tax_year" in e for e in errors)


def test_bad_filing_status_errors():
    data = valid_full()
    data["filing_status"] = "married"
    errors, _ = v.schema_check(data)
    assert any("filing_status" in e for e in errors)


def test_unparseable_federal_amount_errors():
    data = valid_full()
    data["federal"]["agi_line_11"] = "one hundred"
    errors, _ = v.schema_check(data)
    assert any("agi_line_11" in e for e in errors)


def test_rental_missing_label_errors():
    data = valid_full()
    data["rentals"][0]["property_label"] = ""
    errors, _ = v.schema_check(data)
    assert any("property_label" in e for e in errors)


def test_rental_asset_missing_cost_basis_errors():
    data = valid_full()
    del data["rentals"][0]["assets"][0]["cost_basis"]
    errors, _ = v.schema_check(data)
    assert any("cost_basis" in e for e in errors)


def test_missing_georgia_section_warns_not_errors():
    data = valid_full()
    del data["georgia"]
    errors, warnings = v.schema_check(data)
    assert errors == []
    assert any("georgia" in w.lower() for w in warnings)
