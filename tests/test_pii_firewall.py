"""Adversarial PII-firewall tests. ALL data fabricated (Rule 4)."""
import json

import validate_prior_year as v


def clean_minimal():
    """A minimal, PII-free, schema-valid carryover dict."""
    return {
        "tax_year": 2024,
        "source": "test",
        "filing_status": "MFJ",
        "federal": {"agi_line_11": "185000.00"},
    }


def test_clean_data_has_no_pii_findings():
    assert v.pii_scan(clean_minimal()) == []


def test_dashed_ssn_in_value_is_caught():
    data = clean_minimal()
    data["notes"] = ["Taxpayer SSN 000-00-0000 on page 1"]
    findings = v.pii_scan(data)
    assert any("SSN-like" in f for f in findings)


def test_bare_account_like_integer_is_caught():
    data = clean_minimal()
    data["federal"]["agi_line_11"] = 123456789  # 9-digit bare int = account-like
    findings = v.pii_scan(data)
    assert any("Account/routing-like bare number" in f for f in findings)


def test_long_digit_run_string_is_caught():
    data = clean_minimal()
    data["notes"] = ["Routing 021000021 on the 1099"]
    findings = v.pii_scan(data)
    assert any("Account/routing-like digit run" in f for f in findings)


def test_legit_money_string_is_not_flagged_as_account():
    data = clean_minimal()
    data["federal"]["agi_line_11"] = "12345678.90"  # ~$12.3M, has decimal
    assert v.pii_scan(data) == []


def test_each_blocked_key_fragment_is_caught():
    for frag in v.BLOCKED_KEY_FRAGMENTS:
        data = clean_minimal()
        # build a key that contains the blocked fragment
        data[f"x_{frag}_field"] = "whatever"
        findings = v.pii_scan(data)
        assert any(frag in f for f in findings), f"fragment not caught: {frag}"


def test_pii_nested_in_array_is_caught():
    data = clean_minimal()
    data["rentals"] = [{"property_label": "Rental (1 A St)", "dob": "1980-01-01"}]
    findings = v.pii_scan(data)
    assert any("dob" in f for f in findings)


def test_name_fragment_key_is_caught():
    # "taxpayer_name" is a classic PII key — must be blocked even if the
    # schema never uses it, closing the defense-in-depth gap noted in Task 3.
    data = clean_minimal()
    data["taxpayer_name"] = "Jane Fabricated"
    findings = v.pii_scan(data)
    assert any("taxpayer" in f or "name" in f for f in findings)


def test_validate_rejects_file_with_pii(tmp_path):
    data = clean_minimal()
    data["notes"] = ["SSN 000-00-0000"]
    p = tmp_path / "cy.json"
    p.write_text(json.dumps(data))
    result = v.validate({"json_path": str(p)})
    assert result["verdict"] == "rejected"
    assert result["pii_findings"]
