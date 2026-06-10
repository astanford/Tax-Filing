"""
schedule_e_calculator.py — Schedule E Part I (rental real estate) computation.

Computes per-property net income/loss, straight-line MACRS depreciation for
the building, Schedule E totals (Lines 23a-26), and a simplified Form 8582
passive-loss limitation with the $25,000 special allowance and MAGI
phase-out. Handles short-term / mid-term rental classification under the
section 469 "not a rental activity" exceptions.

Usage:
    python schedule_e_calculator.py '{"tax_year": 2025, "magi": "120000", "filing_status": "MFJ", "active_participation": true, "prior_suspended_loss": "0", "properties": [{"name": "LLC A - 123 Main St", "classification": "long_term", "rents_received": "24000", "expenses": {"insurance": "1200", "management_fees": "2400", "mortgage_interest": "8000", "repairs": "1500", "taxes": "3000"}, "depreciation": {"building_basis": "275000", "placed_in_service_month": 5, "placed_in_service_year": 2022, "recovery_years": "27.5", "additional_assets_depreciation": "0", "bonus_depreciation_claimed": "0"}}]}'

Property classification:
  - "long_term"   — ordinary rental activity (avg rental period > 30 days)
  - "mid_term"    — avg rental period <= 30 days; if significant_services is
                    true, NOT a rental activity for section 469
  - "short_term"  — avg rental period <= 7 days; NOT a rental activity for
                    section 469 (no $25K allowance; material participation
                    decides passive vs nonpassive)
  - substantial_services: true on any property means it belongs on
    Schedule C (hotel-like services) — it is EXCLUDED from Schedule E
    totals here and flagged.

Constants sourced from:
  - reference/curated/schedule-e-guide.md (line structure, Schedule C boundary)
  - reference/curated/rental-depreciation.md (27.5/39-year SL, mid-month convention)
  - reference/curated/passive-activity-losses.md ($25K allowance, MAGI phase-out,
    7-day/30-day exceptions, material participation)
  - reference/curated/georgia-500-guide.md (GA bonus depreciation addback)

All arithmetic uses Decimal — no float math (per CLAUDE.md rules).
"""

import json
import sys
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Helpers (matching schedule_c_calculator.py pattern)
# ---------------------------------------------------------------------------

def d(val):
    """Convert to Decimal. Returns Decimal('0') for None or non-numeric."""
    if val is None:
        return Decimal("0")
    try:
        return Decimal(str(val).replace(",", "").strip())
    except Exception:
        return Decimal("0")


def cents(val):
    """Round to nearest cent."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt(val):
    """Format a Decimal as a dollar string for display."""
    return f"${float(cents(val)):,.2f}"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Special $25,000 allowance and MAGI phase-out
# (Source: passive-activity-losses.md, Special $25,000 Allowance)
ALLOWANCE_MAX = Decimal("25000")
ALLOWANCE_PHASEOUT_START = Decimal("100000")
ALLOWANCE_PHASEOUT_END = Decimal("150000")
ALLOWANCE_PHASEOUT_RATE = Decimal("0.50")

# Schedule E Part I expense lines
# (Source: schedule-e-guide.md, Line-by-Line Reference)
EXPENSE_LINES = [
    ("advertising", "Line 5", "Advertising"),
    ("auto_travel", "Line 6", "Auto and travel"),
    ("cleaning_maintenance", "Line 7", "Cleaning and maintenance"),
    ("commissions", "Line 8", "Commissions"),
    ("insurance", "Line 9", "Insurance"),
    ("legal_professional", "Line 10", "Legal and other professional fees"),
    ("management_fees", "Line 11", "Management fees"),
    ("mortgage_interest", "Line 12", "Mortgage interest paid to banks, etc."),
    ("other_interest", "Line 13", "Other interest"),
    ("repairs", "Line 14", "Repairs"),
    ("supplies", "Line 15", "Supplies"),
    ("taxes", "Line 16", "Taxes"),
    ("utilities", "Line 17", "Utilities"),
    ("other", "Line 19", "Other expenses"),
]


# ---------------------------------------------------------------------------
# Depreciation — straight line, mid-month convention, using the printed
# MACRS percentage tables (the IRS tables round slightly differently than
# the raw formula, especially Table A-7a).
# (Source: rental-depreciation.md, MACRS Percentage Tables —
#  Pub 946 (2025), Appendix A, Tables A-6 and A-7a)
# ---------------------------------------------------------------------------

# Year-1 percentage by placed-in-service month (Jan..Dec)
YEAR1_PCT = {
    "27.5": [Decimal(p) for p in (
        "3.485", "3.182", "2.879", "2.576", "2.273", "1.970",
        "1.667", "1.364", "1.061", "0.758", "0.455", "0.152")],
    "39": [Decimal(p) for p in (
        "2.461", "2.247", "2.033", "1.819", "1.605", "1.391",
        "1.177", "0.963", "0.749", "0.535", "0.321", "0.107")],
}

# Steady-state (full-year) percentage; Table A-6 alternates 3.636/3.637 in
# years 10-27 — 3.636 is used here, within the repo's $1 audit tolerance.
STEADY_PCT = {"27.5": Decimal("3.636"), "39": Decimal("2.564")}


def compute_building_depreciation(dep, tax_year, notes):
    """Straight-line MACRS for the building: 27.5-year residential or
    39-year nonresidential (transient/hotel-like use), mid-month convention,
    via the Pub 946 Appendix A percentage tables.
    """
    basis = d(dep.get("building_basis"))
    recovery_key = str(dep.get("recovery_years", "27.5")).strip()
    pis_year = int(dep.get("placed_in_service_year", tax_year))
    pis_month = int(dep.get("placed_in_service_month", 1))

    if basis <= 0:
        return Decimal("0"), False
    if recovery_key not in YEAR1_PCT:
        notes.append(f"Unsupported recovery period '{recovery_key}' — use '27.5' or '39'. No depreciation computed.")
        return Decimal("0"), False
    if not 1 <= pis_month <= 12:
        notes.append(f"Invalid placed-in-service month {pis_month} — no depreciation computed.")
        return Decimal("0"), False

    years_elapsed = tax_year - pis_year
    placed_this_year = years_elapsed == 0

    if years_elapsed < 0:
        notes.append("Building placed in service after the tax year — no depreciation.")
        return Decimal("0"), False

    if placed_this_year:
        pct = YEAR1_PCT[recovery_key][pis_month - 1]
        return cents(basis * pct / Decimal("100")), True

    # Recovery period exhausted (approximate check; the final year is a
    # partial mid-month year — verify against the Pub 946 table)
    if Decimal(str(years_elapsed)) > Decimal(recovery_key):
        notes.append(
            f"Building recovery period (~{recovery_key} yrs) appears exhausted — verify final-year proration against rental-depreciation.md table."
        )
        return Decimal("0"), False

    return cents(basis * STEADY_PCT[recovery_key] / Decimal("100")), False


# ---------------------------------------------------------------------------
# Section 469 classification
# (Source: passive-activity-losses.md, Activities That Are Not Rental Activities)
# ---------------------------------------------------------------------------

def classify_469(prop, notes):
    """Return one of: 'schedule_c', 'rental_activity', 'nonrental_passive',
    'nonrental_nonpassive' for a property dict."""
    name = prop.get("name", "property")
    classification = prop.get("classification", "long_term")
    substantial_services = bool(prop.get("substantial_services", False))
    significant_services = bool(prop.get("significant_services", False))
    material_participation = bool(prop.get("material_participation", False))

    if substantial_services:
        notes.append(
            f"{name}: substantial services provided — report on SCHEDULE C (SE tax applies), excluded from Schedule E totals. (Source: schedule-e-guide.md, Schedule C Boundary)"
        )
        return "schedule_c"

    not_rental = classification == "short_term" or (
        classification == "mid_term" and significant_services
    )
    if not_rental:
        rule = "avg rental period <= 7 days" if classification == "short_term" \
            else "avg rental period <= 30 days with significant personal services"
        if material_participation:
            notes.append(
                f"{name}: {rule} — NOT a rental activity under section 469; taxpayer materially participates, so income/loss is NONPASSIVE (loss fully deductible, no $25K allowance needed). (Source: passive-activity-losses.md, Exceptions)"
            )
            return "nonrental_nonpassive"
        notes.append(
            f"{name}: {rule} — NOT a rental activity under section 469 and NO material participation: loss gets NO $25,000 allowance and only offsets passive income. (Source: passive-activity-losses.md, Exceptions)"
        )
        return "nonrental_passive"

    return "rental_activity"


def compute_allowance(magi, filing_status, active_participation, notes):
    """$25,000 special allowance with 50% phase-out from $100K to $150K MAGI.

    (Source: passive-activity-losses.md, Special $25,000 Allowance)
    """
    if not active_participation:
        notes.append("No active participation — $25,000 special allowance unavailable. (Source: passive-activity-losses.md)")
        return Decimal("0")
    if filing_status == "MFS":
        notes.append("MFS: special allowance is $0 unless you lived apart from your spouse all year ($12,500/$50K-$75K phase-out) — verify in passive-activity-losses.md.")
        return Decimal("0")
    if magi <= ALLOWANCE_PHASEOUT_START:
        return ALLOWANCE_MAX
    if magi >= ALLOWANCE_PHASEOUT_END:
        notes.append(f"MAGI {fmt(magi)} >= {fmt(ALLOWANCE_PHASEOUT_END)} — special allowance fully phased out; rental losses suspended on Form 8582.")
        return Decimal("0")
    reduced = ALLOWANCE_MAX - ALLOWANCE_PHASEOUT_RATE * (magi - ALLOWANCE_PHASEOUT_START)
    return cents(max(Decimal("0"), reduced))


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------

def schedule_e(data):
    tax_year = int(data.get("tax_year", 2025))
    magi = d(data.get("magi"))
    filing_status = data.get("filing_status", "MFJ")
    active_participation = bool(data.get("active_participation", True))
    prior_suspended = d(data.get("prior_suspended_loss"))
    properties = data.get("properties", [])

    if not properties:
        return {"error": "No properties provided"}

    notes = []
    prop_results = []
    total_rents = Decimal("0")
    total_expenses_all = Decimal("0")
    total_depreciation = Decimal("0")
    total_bonus_claimed = Decimal("0")
    form_4562_needed = False

    # Buckets for the simplified Form 8582
    rental_income = Decimal("0")        # rental activities with net income
    rental_losses = Decimal("0")        # rental activities with net loss (positive number)
    nonrental_passive_income = Decimal("0")
    nonrental_passive_losses = Decimal("0")
    nonpassive_net = Decimal("0")
    schedule_c_excluded = []

    for prop in properties:
        name = prop.get("name", "property")
        bucket = classify_469(prop, notes)

        rents = d(prop.get("rents_received"))
        expenses = prop.get("expenses", {}) or {}

        lines = {"Line 3 (Rents received)": str(cents(rents))}
        expense_total = Decimal("0")
        for key, line_no, label in EXPENSE_LINES:
            val = d(expenses.get(key))
            expense_total += val
            if val != 0:
                lines[f"{line_no} ({label})"] = str(cents(val))

        # Depreciation (Line 18)
        dep = prop.get("depreciation", {}) or {}
        building_dep, placed_this_year = compute_building_depreciation(dep, tax_year, notes)
        other_assets_dep = d(dep.get("additional_assets_depreciation"))
        bonus = d(dep.get("bonus_depreciation_claimed"))
        line_18 = building_dep + other_assets_dep + bonus
        if line_18 != 0:
            lines["Line 18 (Depreciation)"] = str(cents(line_18))
        if placed_this_year or bonus > 0:
            form_4562_needed = True
        if bonus > 0:
            total_bonus_claimed += bonus
        if d(dep.get("building_basis")) > 0 and line_18 == 0:
            notes.append(f"{name}: no depreciation claimed despite building basis — depreciation is 'allowed or allowable' and reduces basis either way. (Source: rental-depreciation.md, Allowed or Allowable)")

        expense_total += line_18
        net = rents - expense_total
        lines["Line 20 (Total expenses)"] = str(cents(expense_total))
        lines["Line 21 (Income or loss)"] = str(cents(net))

        if bucket == "schedule_c":
            schedule_c_excluded.append(name)
        else:
            total_rents += rents
            total_expenses_all += expense_total
            total_depreciation += line_18
            if bucket == "rental_activity":
                if net >= 0:
                    rental_income += net
                else:
                    rental_losses += -net
            elif bucket == "nonrental_passive":
                if net >= 0:
                    nonrental_passive_income += net
                else:
                    nonrental_passive_losses += -net
            else:  # nonrental_nonpassive
                nonpassive_net += net

        prop_results.append({
            "name": name,
            "classification": prop.get("classification", "long_term"),
            "section_469_bucket": bucket,
            "lines": lines,
            "net_income_or_loss": str(cents(net)),
        })

    # --- Simplified Form 8582 ---
    # Passive income first absorbs passive losses; the $25K allowance applies
    # only to rental-activity losses (active participation).
    # (Source: passive-activity-losses.md, Form 8582 Flow)
    passive_income = rental_income + nonrental_passive_income
    passive_losses = rental_losses + nonrental_passive_losses + prior_suspended

    absorbed = min(passive_income, passive_losses)
    remaining_loss = passive_losses - absorbed

    # Allowance applies to the rental-activity share of the remaining loss
    rental_share_remaining = min(remaining_loss, rental_losses + prior_suspended)
    allowance = compute_allowance(magi, filing_status, active_participation, notes)
    allowed_by_allowance = min(rental_share_remaining, allowance)

    suspended = remaining_loss - allowed_by_allowance
    allowed_loss_total = absorbed + allowed_by_allowance

    # Schedule E net result (Line 26): passive income kept + allowed losses
    # against it + nonpassive net
    schedule_e_net = passive_income - allowed_loss_total + nonpassive_net

    form_8582_needed = suspended > 0 or prior_suspended > 0 or (
        rental_losses > 0 and (magi > ALLOWANCE_PHASEOUT_START or not active_participation)
    )

    if schedule_e_net > 0:
        notes.append(f"Net rental income {fmt(schedule_e_net)} is investment income for the 3.8% NIIT if MAGI exceeds the threshold. (Source: niit-form-8960.md)")
    if total_bonus_claimed > 0:
        notes.append(f"Federal bonus depreciation of {fmt(total_bonus_claimed)} claimed — Georgia has NOT adopted section 168(k): add it back on GA Form 500 Schedule 1 and maintain separate GA depreciation. (Source: georgia-500-guide.md, Key Structural Facts)")
    if form_4562_needed:
        notes.append("Form 4562 required (property placed in service this year and/or bonus depreciation claimed). (Source: rental-depreciation.md, Form 4562)")
    notes.append("Rental income here is NOT subject to SE tax. (Source: schedule-e-guide.md)")

    return {
        "properties": prop_results,
        "schedule_c_excluded_properties": schedule_c_excluded,
        "totals": {
            "line_23a_total_rents": str(cents(total_rents)),
            "line_20_total_expenses": str(cents(total_expenses_all)),
            "total_depreciation_line_18": str(cents(total_depreciation)),
        },
        "form_8582": {
            "passive_income": str(cents(passive_income)),
            "passive_losses_incl_prior_suspended": str(cents(passive_losses)),
            "special_allowance_available": str(cents(allowance)),
            "allowed_loss_total": str(cents(allowed_loss_total)),
            "suspended_loss_carryforward": str(cents(suspended)),
            "form_8582_needed": form_8582_needed,
        },
        "line_26_total_rental_income_or_loss": str(cents(schedule_e_net)),
        "flows_to": "Schedule 1, Line 5 -> Form 1040 Line 8; included in federal AGI -> GA Form 500 Line 8",
        "ga_bonus_depreciation_addback": str(cents(total_bonus_claimed)),
        "notes": notes,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: schedule_e_calculator.py \'{"tax_year": 2025, "magi": "...", "filing_status": "MFJ", "active_participation": true, "properties": [...]}\''
        }))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = schedule_e(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
