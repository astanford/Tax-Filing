"""Tests for completeness_check.py — document coverage and required forms.

Covers the gaps found in the 2026-09-30 review: K-1s, HSA forms, supporting
records, Georgia return detection without W-2s, rental 1098s, Form 8995 and
Form 4562 requirements for rental filers.
"""

import csv

import completeness_check as cc

HEADER = ["document", "box_or_line", "description", "value", "source_path"]


def _csv(tmp_path, rows):
    path = tmp_path / "c.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    return str(path)


def _row(doc, box="Box 1", value="100.00"):
    return (doc, box, "x", value, "src")


def _run(tmp_path, rows, forms=(), **extra):
    return cc.completeness_check({"csv_path": _csv(tmp_path, rows), "forms_filed": list(forms),
                                  "filing_status": "MFJ", **extra})


def _cov(result, doc):
    return next(c for c in result["document_coverage"] if c["document"] == doc)


def _req(result, form):
    return next((r for r in result["required_forms"] if r["form"] == form), None)


# --- document recognition ------------------------------------------------------

def test_k1_is_recognized_and_needs_schedule_e(tmp_path):
    doc = "K-1 1065 (Gatsby Homes LLC - Partner)"
    filed = _run(tmp_path, [_row(doc, "Box 2", "22270.00")], ["Schedule E"])
    assert _cov(filed, doc)["status"] == "mapped"
    assert _cov(filed, doc)["type"] == "K-1"
    missing = _run(tmp_path, [_row(doc, "Box 2", "22270.00")], ["1040"])
    assert _cov(missing, doc)["status"] == "unmapped"


def test_k1_requires_schedule_e_and_schedule_1(tmp_path):
    doc = "K-1 1065 (Gatsby Homes LLC - Partner)"
    result = _run(tmp_path, [_row(doc, "Box 2", "22270.00")], [])
    assert _req(result, "Schedule E")["status"] == "required"
    assert _req(result, "Schedule 1")["status"] == "required"


def test_5498_sa_is_informational(tmp_path):
    doc = "5498-SA (2025 HSA)"
    result = _run(tmp_path, [_row(doc, "Box 5", "5638.02")])
    assert _cov(result, doc)["status"] == "mapped"
    assert _cov(result, doc)["maps_to"] == ["Reference only"]


def test_1099_sa_maps_to_form_8889(tmp_path):
    doc = "1099-SA (HSA custodian)"
    assert _cov(_run(tmp_path, [_row(doc)], ["1040"]), doc)["status"] == "unmapped"
    assert _cov(_run(tmp_path, [_row(doc)], ["Form 8889"]), doc)["status"] == "mapped"


def test_supporting_records_are_not_orphans(tmp_path):
    docs = ["IRS Account Transcript (2025 Form 1040)", "Stripe Payout Reconciliation (X LLC)",
            "Mileage Log (Tacoma - MileIQ 2025, corrected)", "Home Office (X LLC - user reported)",
            "Capital Additions 2025 (Landon Ct - X LLC)", "Property Tax Bills (Landon Ct parcels)"]
    result = _run(tmp_path, [_row(d) for d in docs])
    for d in docs:
        assert _cov(result, d)["status"] == "supporting", d
    assert result["summary"]["orphaned"] == 0


def test_unknown_document_is_orphaned(tmp_path):
    result = _run(tmp_path, [_row("Mystery Letter")])
    assert _cov(result, "Mystery Letter")["status"] == "orphaned"


def test_rental_1098_maps_to_schedule_e_personal_1098_to_schedule_a(tmp_path):
    rental = "1098 (First National Community Bank - Cloudbase Holdings LLC, Landon Ct)"
    personal = "1098 (PNC mortgage)"
    result = _run(tmp_path, [_row(rental), _row(personal)], ["Schedule E", "Schedule A"])
    assert _cov(result, rental)["maps_to"] == ["Schedule E"]
    assert _cov(result, personal)["maps_to"] == ["Schedule A"]


# --- required forms ---------------------------------------------------------------

def test_ga_500_required_for_georgia_rentals_without_w2(tmp_path):
    rows = [_row("Rental (186-188 Landon Ct, Calhoun GA - Cloudbase Holdings LLC)", "Line 3", "5000.00")]
    result = _run(tmp_path, rows, ["1040", "Schedule E"])
    assert _req(result, "GA 500")["status"] == "required"
    assert result["verdict"] == "incomplete"


def test_ga_500_required_when_resident_flag_set(tmp_path):
    result = _run(tmp_path, [_row("1099-INT (Bank)", "Box 1", "50.00")], ["1040"], ga_resident=True)
    assert _req(result, "GA 500")["status"] == "required"


def test_ga_500_not_required_without_georgia_signal(tmp_path):
    result = _run(tmp_path, [_row("1099-INT (Bank)", "Box 1", "50.00")], ["1040"])
    assert _req(result, "GA 500") is None


def test_form_8995_recommended_for_rentals_required_when_qbi_claimed(tmp_path):
    rows = [_row("Rental (A, Calhoun GA - X LLC)", "Line 3", "5000.00")]
    assert _req(_run(tmp_path, rows), "Form 8995")["status"] == "recommended"
    assert _req(_run(tmp_path, rows, qbi_claimed=True), "Form 8995")["status"] == "required"


def test_form_4562_required_with_capital_additions_or_mileage(tmp_path):
    rows = [_row("Rental (A, Calhoun GA - X LLC)", "Line 3", "5000.00")]
    assert _req(_run(tmp_path, rows), "Form 4562")["status"] == "recommended"
    with_add = rows + [_row("Capital Additions 2025 (Landon Ct - X LLC)", "Asset", "5692.50")]
    assert _req(_run(tmp_path, with_add), "Form 4562")["status"] == "required"
    with_miles = rows + [_row("Mileage Log (Tacoma - MileIQ 2025)", "Miles", "10706.90")]
    assert _req(_run(tmp_path, with_miles), "Form 4562")["status"] == "required"


# --- regression: original behavior ---------------------------------------------

def test_schedule_b_required_over_1500(tmp_path):
    result = _run(tmp_path, [_row("1099-INT (Bank)", "Box 1", "1600.00")], ["1040"])
    assert _req(result, "Schedule B")["status"] == "required"
    under = _run(tmp_path, [_row("1099-INT (Bank)", "Box 1", "1500.00")], ["1040"])
    assert _req(under, "Schedule B") is None


def test_form_8959_over_threshold(tmp_path):
    result = _run(tmp_path, [_row("W-2 (Acme)", "Box 5", "260000.00")], ["1040"])
    assert _req(result, "Form 8959")["status"] == "required"


def test_complete_for_no_w2_rental_k1_return(tmp_path):
    docs = [_row("K-1 1065 (Gatsby Homes LLC)", "Box 2", "22270.00"),
            _row("Rental (A Landon Ct, Calhoun GA - Cloudbase Holdings LLC)", "Line 3", "30000.00"),
            _row("1098 (PNC mortgage)"), _row("5498-SA (2025 HSA)", "Box 5", "5638.02"),
            _row("Mileage Log (Tacoma - MileIQ 2025)", "Miles", "10706.90")]
    forms = ["1040", "Schedule 1", "Schedule A", "Schedule E", "Form 8582", "Form 4562",
             "Form 8995", "GA 500"]
    result = _run(tmp_path, docs, forms, qbi_claimed=True)
    assert result["verdict"] == "complete", result["required_forms"]


# --- found on the first real run (2026-09-30) ------------------------------------

def test_home_1098_is_optional_when_schedule_a_not_filed(tmp_path):
    """Taking the standard deduction: a personal 1098 legitimately feeds no
    filed form. It must not make the verdict 'incomplete'."""
    doc = "1098 (PNC mortgage)"
    result = _run(tmp_path, [_row(doc)], ["1040"])
    assert _cov(result, doc)["status"] == "optional"
    assert result["summary"]["unmapped"] == 0
    assert result["verdict"] == "warning"      # Schedule A is still recommended
    itemizing = _run(tmp_path, [_row(doc)], ["1040", "Schedule A"])
    assert _cov(itemizing, doc)["status"] == "mapped"


def test_real_estate_professional_record_is_supporting(tmp_path):
    doc = "Real Estate Professional (primary taxpayer - user claim)"
    assert _cov(_run(tmp_path, [_row(doc, "Claim", "Claimed")]), doc)["status"] == "supporting"
