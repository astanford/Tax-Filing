"""
what_if.py — Tax planning what-if scenario engine.

Models hypothetical changes to a filed return and computes the dollar impact
on federal, Maryland state, and local taxes.

Usage:
    python what_if.py '{"baseline": {"filing_status": "MFJ", "wages_primary": 162025, ...}, "scenario": {"name": "max_401k_both", "retirement_contributions_primary": 23500, "retirement_contributions_spouse": 23500}}'

Constants sourced from:
  - reference/curated/2025-tax-numbers.md (federal brackets, standard deduction, SALT cap, AMT, Medicare)
  - reference/curated/maryland-502-guide.md (MD brackets, MD deductions, exemptions, local rates)
  - reference/curated/salt-deduction-2025.md (SALT cap mechanics)
  - reference/curated/retirement-hsa-limits.md (401k, IRA, HSA limits — verify against IRS.gov)
  - reference/curated/self-employment-qbi.md (SE tax, QBI deduction)
  - reference/curated/additional-medicare-tax.md (0.9% Additional Medicare Tax)

All arithmetic uses Decimal — no float math (per CLAUDE.md rules).
"""

import json
import sys
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------------------------------------------------------
# Helpers (matching cross_check.py / standard_vs_itemized.py pattern)
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


def whole(val):
    """Round to nearest dollar."""
    return val.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def fmt(val):
    """Format a Decimal as a dollar string for display."""
    return f"${float(cents(val)):,.2f}"


def pct(val):
    """Format a Decimal as a percentage string."""
    return f"{float(cents(val * Decimal('100')))}%"


# ---------------------------------------------------------------------------
# Federal Income Tax Brackets — 2025 MFJ
# (Source: 2025-tax-numbers.md, Federal Income Tax Brackets)
# Each tuple: (upper_bound, rate, base_tax_at_lower_bound)
# upper_bound=None means no ceiling (top bracket).
# ---------------------------------------------------------------------------

FEDERAL_BRACKETS = {
    "MFJ": [
        (Decimal("23850"),  Decimal("0.10"), Decimal("0")),
        (Decimal("96950"),  Decimal("0.12"), Decimal("2385")),
        (Decimal("206700"), Decimal("0.22"), Decimal("11157")),
        (Decimal("394600"), Decimal("0.24"), Decimal("35302")),
        (Decimal("501050"), Decimal("0.32"), Decimal("80398")),
        (Decimal("751600"), Decimal("0.35"), Decimal("114462")),
        (None,              Decimal("0.37"), Decimal("188770")),
    ],
    "Single": [
        (Decimal("11925"),  Decimal("0.10"), Decimal("0")),
        (Decimal("48475"),  Decimal("0.12"), Decimal("1192.50")),
        (Decimal("103350"), Decimal("0.22"), Decimal("5578.50")),
        (Decimal("197300"), Decimal("0.24"), Decimal("17651.50")),
        (Decimal("250525"), Decimal("0.32"), Decimal("40199.50")),
        (Decimal("626350"), Decimal("0.35"), Decimal("57231.50")),
        (None,              Decimal("0.37"), Decimal("188769.75")),
    ],
    "HoH": [
        (Decimal("17000"),  Decimal("0.10"), Decimal("0")),
        (Decimal("64850"),  Decimal("0.12"), Decimal("1700")),
        (Decimal("103350"), Decimal("0.22"), Decimal("7442")),
        (Decimal("197300"), Decimal("0.24"), Decimal("15912")),
        (Decimal("250500"), Decimal("0.32"), Decimal("38460")),
        (Decimal("626350"), Decimal("0.35"), Decimal("55484")),
        (None,              Decimal("0.37"), Decimal("187032")),
    ],
}
# MFS uses half the MFJ bracket widths — approximated via Single brackets.
FEDERAL_BRACKETS["MFS"] = FEDERAL_BRACKETS["Single"]


# ---------------------------------------------------------------------------
# Maryland State Income Tax Brackets — 2025 MFJ / HoH / QSS
# (Source: 2025-tax-numbers.md, Maryland State Income Tax Brackets)
# ---------------------------------------------------------------------------

MD_BRACKETS = {
    "MFJ": [
        (Decimal("1000"),    Decimal("0.02"),   Decimal("0")),
        (Decimal("2000"),    Decimal("0.03"),   Decimal("20")),
        (Decimal("3000"),    Decimal("0.04"),   Decimal("50")),
        (Decimal("150000"),  Decimal("0.0475"), Decimal("90")),
        (Decimal("175000"),  Decimal("0.05"),   Decimal("7072.50")),
        (Decimal("225000"),  Decimal("0.0525"), Decimal("8322.50")),
        (Decimal("300000"),  Decimal("0.055"),  Decimal("10947.50")),
        (Decimal("600000"),  Decimal("0.0575"), Decimal("15072.50")),
        (Decimal("1200000"), Decimal("0.0625"), Decimal("32322.50")),
        (None,               Decimal("0.065"),  Decimal("69822.50")),
    ],
}
# Alias: same brackets used for HoH and QSS
MD_BRACKETS["HoH"] = MD_BRACKETS["MFJ"]
MD_BRACKETS["Single"] = MD_BRACKETS["MFJ"]  # MD uses same brackets for all statuses
MD_BRACKETS["MFS"] = MD_BRACKETS["MFJ"]


# ---------------------------------------------------------------------------
# Standard Deductions (Source: 2025-tax-numbers.md, Standard Deduction)
# ---------------------------------------------------------------------------

STANDARD_DEDUCTION = {
    "MFJ": Decimal("31500"),
    "Single": Decimal("15750"),
    "MFS": Decimal("15750"),
    "HoH": Decimal("23625"),
}


# ---------------------------------------------------------------------------
# SALT Cap Parameters (Source: salt-deduction-2025.md, Overall SALT Cap)
# ---------------------------------------------------------------------------

SALT_CAP = {
    "MFJ":    {"base": Decimal("40000"), "floor": Decimal("10000"), "threshold": Decimal("500000")},
    "Single": {"base": Decimal("40000"), "floor": Decimal("10000"), "threshold": Decimal("500000")},
    "HoH":    {"base": Decimal("40000"), "floor": Decimal("10000"), "threshold": Decimal("500000")},
    "MFS":    {"base": Decimal("20000"), "floor": Decimal("5000"),  "threshold": Decimal("250000")},
}

SALT_PHASE_OUT_RATE = Decimal("0.30")


# ---------------------------------------------------------------------------
# Maryland Deduction Parameters (Source: maryland-502-guide.md)
# ---------------------------------------------------------------------------

MD_STANDARD_DEDUCTION = {
    "MFJ": Decimal("6700"),
    "Single": Decimal("3350"),
    "MFS": Decimal("3350"),
    "HoH": Decimal("6700"),
}

# Itemized deduction phase-out: 7.5% of FAGI over threshold
# (Source: maryland-502-guide.md, Itemized Deduction Phase-Out)
MD_ITEMIZED_PHASEOUT = {
    "MFJ":    {"threshold": Decimal("200000"), "rate": Decimal("0.075")},
    "Single": {"threshold": Decimal("200000"), "rate": Decimal("0.075")},
    "HoH":    {"threshold": Decimal("200000"), "rate": Decimal("0.075")},
    "MFS":    {"threshold": Decimal("100000"), "rate": Decimal("0.075")},
}

# Personal exemption: $3,200/person, phased out at high income
# (Source: maryland-502-guide.md, Exemptions)
MD_EXEMPTION_TIERS = {
    "MFJ": [
        (Decimal("150000"), Decimal("3200")),   # up to $150K: full $3,200/person
        (Decimal("175000"), Decimal("1600")),   # $150K-$175K: $1,600/person
        (Decimal("200000"), Decimal("800")),    # $175K-$200K: $800/person
        (None,              Decimal("0")),      # over $200K: $0
    ],
}
MD_EXEMPTION_TIERS["Single"] = MD_EXEMPTION_TIERS["MFJ"]
MD_EXEMPTION_TIERS["HoH"] = MD_EXEMPTION_TIERS["MFJ"]
MD_EXEMPTION_TIERS["MFS"] = MD_EXEMPTION_TIERS["MFJ"]

# Two-income married subtraction (Source: maryland-502-guide.md, Two-Income Subtraction)
MD_TWO_INCOME_SUBTRACTION_MAX = Decimal("1200")

# Maryland local tax rates (Source: 2025-tax-numbers.md, Maryland Local Tax Rates)
MD_LOCAL_RATES = {
    "Montgomery": Decimal("0.032"),
    "Baltimore City": Decimal("0.032"),
    "Howard": Decimal("0.032"),
    "Dorchester": Decimal("0.033"),
    # Default for other counties — user should verify
    "default": Decimal("0.032"),
}

# Capital gains surtax (Source: maryland-502-guide.md, Capital Gains Surtax)
MD_CAP_GAINS_SURTAX_THRESHOLD = Decimal("350000")
MD_CAP_GAINS_SURTAX_RATE = Decimal("0.02")


# ---------------------------------------------------------------------------
# Additional Medicare Tax (Source: additional-medicare-tax.md)
# ---------------------------------------------------------------------------

MEDICARE_TAX_THRESHOLD = {
    "MFJ": Decimal("250000"),
    "Single": Decimal("200000"),
    "HoH": Decimal("200000"),
    "MFS": Decimal("125000"),
}

ADDITIONAL_MEDICARE_RATE = Decimal("0.009")


# ---------------------------------------------------------------------------
# Self-Employment Tax (Source: self-employment-qbi.md)
# ---------------------------------------------------------------------------

SE_TAX_THRESHOLD = Decimal("400")
SE_TAX_RATE = Decimal("0.153")        # 12.4% SS + 2.9% Medicare
SE_NET_FACTOR = Decimal("0.9235")     # 92.35% adjustment
SS_WAGE_BASE = Decimal("176100")      # (Source: 2025-tax-numbers.md)
SS_RATE = Decimal("0.124")
MEDICARE_SE_RATE = Decimal("0.029")


# ---------------------------------------------------------------------------
# Medical Expense Threshold (Source: 2025-tax-numbers.md)
# ---------------------------------------------------------------------------

MEDICAL_THRESHOLD_RATE = Decimal("0.075")


# ---------------------------------------------------------------------------
# Retirement / HSA Limits (Source: retirement-hsa-limits.md)
# VERIFY AGAINST IRS.GOV — raw sources not yet curated.
# ---------------------------------------------------------------------------

RETIREMENT_401K_LIMIT = Decimal("23500")
IRA_LIMIT = Decimal("7000")
HSA_FAMILY_LIMIT = Decimal("8550")
HSA_SELF_LIMIT = Decimal("4300")

# IRA deductibility phase-out for MFJ with employer plan
# (Source: retirement-hsa-limits.md, Traditional IRA Deductibility)
IRA_DEDUCTIBILITY_PHASEOUT = {
    "MFJ": {"lower": Decimal("126000"), "upper": Decimal("146000")},
    "Single": {"lower": Decimal("79000"), "upper": Decimal("89000")},
    "HoH": {"lower": Decimal("79000"), "upper": Decimal("89000")},
    "MFS": {"lower": Decimal("0"), "upper": Decimal("10000")},
}


# ---------------------------------------------------------------------------
# Core Computation Functions
# ---------------------------------------------------------------------------

def apply_brackets(taxable_income, brackets):
    """Compute tax from a bracket table.

    brackets: list of (upper_bound, rate, base_tax) tuples.
    (Source: 2025-tax-numbers.md for federal, maryland-502-guide.md for MD)
    """
    if taxable_income <= Decimal("0"):
        return Decimal("0")

    for i, (ceiling, rate, base_tax) in enumerate(brackets):
        if ceiling is None or taxable_income <= ceiling:
            if i == 0:
                return cents(taxable_income * rate)
            prev_ceiling = brackets[i - 1][0]
            return cents(base_tax + (taxable_income - prev_ceiling) * rate)
    return Decimal("0")


def compute_salt_cap(magi, filing_status):
    """Compute effective SALT cap after MAGI phase-out.

    (Source: salt-deduction-2025.md, Overall SALT Cap)
    """
    params = SALT_CAP.get(filing_status, SALT_CAP["MFJ"])
    base_cap = params["base"]
    floor_cap = params["floor"]
    threshold = params["threshold"]

    if magi > threshold:
        excess = magi - threshold
        reduction = SALT_PHASE_OUT_RATE * excess
        return max(floor_cap, base_cap - reduction)
    return base_cap


def compute_federal_deduction(agi, itemized_components, filing_status):
    """Compare standard vs itemized deductions and return the better option.

    (Source: 2025-tax-numbers.md, Standard Deduction;
     salt-deduction-2025.md, Overall SALT Cap;
     mortgage-interest.md)
    """
    standard = STANDARD_DEDUCTION.get(filing_status, STANDARD_DEDUCTION["MFJ"])

    # SALT computation
    state_local = d(itemized_components.get("state_local_tax"))
    real_estate = d(itemized_components.get("real_estate_tax"))
    personal_property = d(itemized_components.get("personal_property_tax"))
    total_salt = state_local + real_estate + personal_property

    effective_cap = compute_salt_cap(agi, filing_status)
    salt_after_cap = min(total_salt, effective_cap)

    # Mortgage interest (Source: mortgage-interest.md)
    mortgage_interest = d(itemized_components.get("mortgage_interest"))

    # Charitable contributions
    charitable = d(itemized_components.get("charitable"))

    # Medical expenses (7.5% AGI floor)
    medical_gross = d(itemized_components.get("medical_expenses"))
    medical_floor = MEDICAL_THRESHOLD_RATE * agi
    medical_deduction = max(Decimal("0"), medical_gross - medical_floor)

    # Other itemized
    other = d(itemized_components.get("other_itemized"))

    # Total itemized
    itemized_total = salt_after_cap + mortgage_interest + charitable + medical_deduction + other

    if itemized_total > standard:
        return {"type": "itemized", "amount": cents(itemized_total), "salt_after_cap": cents(salt_after_cap)}
    else:
        return {"type": "standard", "amount": cents(standard), "salt_after_cap": cents(salt_after_cap)}


def compute_md_deduction(fagi, itemized_components, filing_status):
    """Compute Maryland deduction (standard vs itemized with phase-out).

    MD itemized = federal itemized components MINUS state/local income taxes.
    Then apply 7.5% phase-out on FAGI excess over $200K.
    (Source: maryland-502-guide.md, Itemized Deduction for Maryland;
     maryland-502-guide.md, Itemized Deduction Phase-Out)
    """
    md_standard = MD_STANDARD_DEDUCTION.get(filing_status, MD_STANDARD_DEDUCTION["MFJ"])

    # MD itemized: federal itemized minus state/local income taxes
    mortgage_interest = d(itemized_components.get("mortgage_interest"))
    charitable = d(itemized_components.get("charitable"))
    real_estate = d(itemized_components.get("real_estate_tax"))
    personal_property = d(itemized_components.get("personal_property_tax"))
    medical_gross = d(itemized_components.get("medical_expenses"))
    medical_floor = MEDICAL_THRESHOLD_RATE * fagi
    medical_deduction = max(Decimal("0"), medical_gross - medical_floor)
    other = d(itemized_components.get("other_itemized"))

    # Note: real_estate and personal_property ARE included in MD itemized
    # (they are property taxes, not state/local income taxes)
    md_itemized_before_phaseout = (
        mortgage_interest + charitable + real_estate + personal_property
        + medical_deduction + other
    )

    # Apply 7.5% phase-out
    phaseout = MD_ITEMIZED_PHASEOUT.get(filing_status, MD_ITEMIZED_PHASEOUT["MFJ"])
    if fagi > phaseout["threshold"]:
        excess = fagi - phaseout["threshold"]
        reduction = phaseout["rate"] * excess
        md_itemized_after_phaseout = max(Decimal("0"), md_itemized_before_phaseout - reduction)
    else:
        md_itemized_after_phaseout = md_itemized_before_phaseout

    if md_itemized_after_phaseout > md_standard:
        return {"type": "itemized", "amount": cents(md_itemized_after_phaseout)}
    else:
        return {"type": "standard", "amount": cents(md_standard)}


def compute_md_exemption(fagi, filing_status, num_exemptions=2):
    """Compute Maryland personal exemption amount.

    (Source: maryland-502-guide.md, Exemptions)
    """
    tiers = MD_EXEMPTION_TIERS.get(filing_status, MD_EXEMPTION_TIERS["MFJ"])
    per_person = Decimal("0")
    for ceiling, amount in tiers:
        if ceiling is None or fagi <= ceiling:
            per_person = amount
            break
    return cents(per_person * Decimal(str(num_exemptions)))


def compute_se_tax(schedule_c_net, total_wages):
    """Compute self-employment tax if Schedule C net profit > $400.

    (Source: self-employment-qbi.md, SE Tax Calculation)
    Returns (se_tax, deductible_half).
    """
    if schedule_c_net <= SE_TAX_THRESHOLD:
        return Decimal("0"), Decimal("0")

    net_se_earnings = schedule_c_net * SE_NET_FACTOR

    # SS portion: only on amount up to wage base minus W-2 wages
    ss_remaining = max(Decimal("0"), SS_WAGE_BASE - total_wages)
    ss_subject = min(net_se_earnings, ss_remaining)
    ss_tax = ss_subject * SS_RATE

    # Medicare portion: all net SE earnings
    medicare_tax = net_se_earnings * MEDICARE_SE_RATE

    se_tax = cents(ss_tax + medicare_tax)
    deductible_half = cents(se_tax / Decimal("2"))

    return se_tax, deductible_half


def compute_qbi_deduction(schedule_c_net, taxable_income_before_qbi, qbi_carryforward, filing_status):
    """Compute QBI deduction (20% of qualified business income).

    (Source: self-employment-qbi.md, QBI Deduction Rules)
    """
    qbi = schedule_c_net - qbi_carryforward
    if qbi <= Decimal("0"):
        return Decimal("0"), max(Decimal("0"), abs(qbi) if schedule_c_net < Decimal("0") else qbi_carryforward - schedule_c_net)

    qbi_deduction = Decimal("0.20") * qbi
    taxable_limit = Decimal("0.20") * taxable_income_before_qbi
    deduction = min(qbi_deduction, taxable_limit)

    return cents(max(Decimal("0"), deduction)), Decimal("0")


def compute_ira_deductibility(magi, ira_amount, filing_status, has_employer_plan=True):
    """Compute deductible portion of traditional IRA contribution.

    (Source: retirement-hsa-limits.md, Traditional IRA Deductibility Phase-Out)
    If covered by employer plan and MAGI exceeds phase-out, deduction is $0.
    """
    if not has_employer_plan:
        return min(ira_amount, IRA_LIMIT)

    phaseout = IRA_DEDUCTIBILITY_PHASEOUT.get(filing_status, IRA_DEDUCTIBILITY_PHASEOUT["MFJ"])
    lower = phaseout["lower"]
    upper = phaseout["upper"]

    if magi <= lower:
        return min(ira_amount, IRA_LIMIT)
    elif magi >= upper:
        return Decimal("0")
    else:
        # Partial deduction: reduce proportionally
        range_width = upper - lower
        excess = magi - lower
        reduction_pct = excess / range_width
        max_deduction = IRA_LIMIT * (Decimal("1") - reduction_pct)
        # Round up to next $10
        rounded = (max_deduction / Decimal("10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("10")
        return min(ira_amount, max(Decimal("0"), rounded))


# ---------------------------------------------------------------------------
# Unified Tax Computation
# ---------------------------------------------------------------------------

def compute_total_tax(params):
    """Compute full federal + MD state + local tax from input parameters.

    Returns a dict with all intermediate values for comparison.
    """
    filing_status = params.get("filing_status", "MFJ")

    # --- Income ---
    wages_primary = d(params.get("wages_primary"))
    wages_spouse = d(params.get("wages_spouse"))
    total_wages = wages_primary + wages_spouse

    interest = d(params.get("interest"))
    dividends_ordinary = d(params.get("dividends_ordinary"))
    capital_gain = d(params.get("capital_gain"))
    schedule_c_net = d(params.get("schedule_c_net"))
    other_income = d(params.get("other_income"))

    gross_income = total_wages + interest + dividends_ordinary + capital_gain + schedule_c_net + other_income

    # --- SE Tax (if applicable) ---
    se_tax, se_deductible_half = compute_se_tax(schedule_c_net, total_wages)

    # --- Adjustments (above-the-line) ---
    # 401(k) is already reflected in wages (pre-tax reduces Box 1)
    # IRA and HSA are Schedule 1 adjustments
    ira_deduction = d(params.get("ira_deduction"))
    hsa_deduction = d(params.get("hsa_contributions"))
    other_adjustments = d(params.get("adjustments"))
    total_adjustments = ira_deduction + hsa_deduction + se_deductible_half + other_adjustments

    # --- AGI ---
    agi = gross_income - total_adjustments

    # --- Federal Deduction ---
    itemized_components = {
        "state_local_tax": params.get("state_local_tax"),
        "real_estate_tax": params.get("real_estate_tax"),
        "personal_property_tax": params.get("personal_property_tax"),
        "mortgage_interest": params.get("mortgage_interest"),
        "charitable": params.get("charitable"),
        "medical_expenses": params.get("medical_expenses"),
        "other_itemized": params.get("other_itemized"),
    }
    fed_deduction = compute_federal_deduction(agi, itemized_components, filing_status)

    # --- QBI Deduction ---
    taxable_before_qbi = max(Decimal("0"), agi - fed_deduction["amount"])
    qbi_carryforward = d(params.get("qbi_carryforward"))
    qbi_deduction, new_carryforward = compute_qbi_deduction(
        schedule_c_net, taxable_before_qbi, qbi_carryforward, filing_status
    )

    # --- Federal Taxable Income ---
    total_deductions = fed_deduction["amount"] + qbi_deduction
    federal_taxable = max(Decimal("0"), agi - total_deductions)

    # --- Federal Tax ---
    brackets = FEDERAL_BRACKETS.get(filing_status, FEDERAL_BRACKETS["MFJ"])
    federal_tax = apply_brackets(federal_taxable, brackets)

    # --- Additional Medicare Tax ---
    medicare_wages_primary = d(params.get("medicare_wages_primary", params.get("wages_primary")))
    medicare_wages_spouse = d(params.get("medicare_wages_spouse", params.get("wages_spouse")))
    total_medicare_wages = medicare_wages_primary + medicare_wages_spouse
    # Add SE income to Medicare wages for threshold calculation
    if schedule_c_net > SE_TAX_THRESHOLD:
        total_medicare_wages += schedule_c_net * SE_NET_FACTOR

    medicare_threshold = MEDICARE_TAX_THRESHOLD.get(filing_status, MEDICARE_TAX_THRESHOLD["MFJ"])
    if total_medicare_wages > medicare_threshold:
        additional_medicare = cents((total_medicare_wages - medicare_threshold) * ADDITIONAL_MEDICARE_RATE)
    else:
        additional_medicare = Decimal("0")

    # --- Maryland State Tax ---
    # MD subtractions
    us_obligation_interest = d(params.get("us_obligation_interest"))
    two_income_subtraction = Decimal("0")
    if filing_status == "MFJ" and wages_primary > Decimal("0") and wages_spouse > Decimal("0"):
        smaller_income = min(wages_primary, wages_spouse)
        two_income_subtraction = min(smaller_income, MD_TWO_INCOME_SUBTRACTION_MAX)
    total_md_subtractions = us_obligation_interest + two_income_subtraction

    md_agi = agi - total_md_subtractions

    # MD deduction
    md_deduction = compute_md_deduction(agi, itemized_components, filing_status)

    # MD exemption
    num_exemptions = int(params.get("num_exemptions", 2 if filing_status == "MFJ" else 1))
    md_exemption = compute_md_exemption(agi, filing_status, num_exemptions)

    # MD taxable net income
    md_taxable = max(Decimal("0"), md_agi - md_deduction["amount"] - md_exemption)

    # MD state tax
    md_brackets = MD_BRACKETS.get(filing_status, MD_BRACKETS["MFJ"])
    md_state_tax = apply_brackets(md_taxable, md_brackets)

    # MD local tax
    county = params.get("county", "Montgomery")
    local_rate = MD_LOCAL_RATES.get(county, MD_LOCAL_RATES["default"])
    md_local_tax = cents(md_taxable * local_rate)

    # MD capital gains surtax
    md_cap_gains_surtax = Decimal("0")
    if agi > MD_CAP_GAINS_SURTAX_THRESHOLD and capital_gain > Decimal("0"):
        md_cap_gains_surtax = cents(capital_gain * MD_CAP_GAINS_SURTAX_RATE)

    # --- Total Tax ---
    total_tax = cents(federal_tax + se_tax + additional_medicare + md_state_tax + md_local_tax + md_cap_gains_surtax)

    # --- Effective Rate ---
    effective_rate = Decimal("0")
    if gross_income > Decimal("0"):
        effective_rate = total_tax / gross_income

    return {
        "gross_income": str(cents(gross_income)),
        "total_adjustments": str(cents(total_adjustments)),
        "agi": str(cents(agi)),
        "deduction_type": fed_deduction["type"],
        "deduction_amount": str(cents(fed_deduction["amount"])),
        "qbi_deduction": str(cents(qbi_deduction)),
        "taxable_income": str(cents(federal_taxable)),
        "federal_tax": str(cents(federal_tax)),
        "se_tax": str(cents(se_tax)),
        "additional_medicare_tax": str(cents(additional_medicare)),
        "md_deduction_type": md_deduction["type"],
        "md_deduction_amount": str(cents(md_deduction["amount"])),
        "md_exemption": str(cents(md_exemption)),
        "md_taxable_income": str(cents(md_taxable)),
        "md_state_tax": str(cents(md_state_tax)),
        "md_local_tax": str(cents(md_local_tax)),
        "md_cap_gains_surtax": str(cents(md_cap_gains_surtax)),
        "total_tax": str(cents(total_tax)),
        "effective_rate": pct(effective_rate),
    }


# ---------------------------------------------------------------------------
# Scenario Application
# ---------------------------------------------------------------------------

def apply_scenario(baseline, scenario):
    """Apply a what-if scenario to the baseline parameters.

    Returns a modified copy of the baseline dict with scenario changes applied.
    Also returns notes about the scenario.
    """
    modified = dict(baseline)
    notes = []
    scenario_name = scenario.get("name", "custom")

    if scenario_name in ("max_401k", "max_401k_both"):
        # 401(k) reduces W-2 Box 1 wages but NOT Box 5 Medicare wages
        # (Source: retirement-hsa-limits.md, 401(k) rules)
        current = d(baseline.get("retirement_contributions_primary"))
        target = d(scenario.get("retirement_contributions_primary", RETIREMENT_401K_LIMIT))
        delta = target - current
        if delta > Decimal("0"):
            modified["wages_primary"] = str(d(baseline.get("wages_primary")) - delta)
            modified["retirement_contributions_primary"] = str(target)
            notes.append(f"401(k) primary: +${float(cents(delta)):,.0f} pre-tax contribution reduces W-2 Box 1 wages")
            notes.append("401(k) does NOT reduce Medicare wages (Box 5) — Additional Medicare Tax unaffected")
            notes.append("401(k) limit ($23,500) — verify against IRS.gov (retirement-hsa-limits.md)")

    if scenario_name in ("max_401k_spouse", "max_401k_both"):
        current = d(baseline.get("retirement_contributions_spouse"))
        target = d(scenario.get("retirement_contributions_spouse", RETIREMENT_401K_LIMIT))
        delta = target - current
        if delta > Decimal("0"):
            modified["wages_spouse"] = str(d(baseline.get("wages_spouse")) - delta)
            modified["retirement_contributions_spouse"] = str(target)
            notes.append(f"401(k) spouse: +${float(cents(delta)):,.0f} pre-tax contribution reduces W-2 Box 1 wages")
            if "401(k) does NOT reduce Medicare wages" not in str(notes):
                notes.append("401(k) does NOT reduce Medicare wages (Box 5) — Additional Medicare Tax unaffected")
                notes.append("401(k) limit ($23,500) — verify against IRS.gov (retirement-hsa-limits.md)")

    if scenario_name == "add_ira":
        filing_status = baseline.get("filing_status", "MFJ")
        ira_amount = d(scenario.get("ira_contribution", IRA_LIMIT))
        # Must check deductibility based on baseline AGI (before IRA)
        baseline_agi = _quick_agi(baseline)
        deductible = compute_ira_deductibility(baseline_agi, ira_amount, filing_status)
        modified["ira_deduction"] = str(deductible)
        if deductible == Decimal("0"):
            notes.append(f"Traditional IRA is NOT deductible at MAGI ${float(cents(baseline_agi)):,.0f} "
                         f"(phase-out ends at ${float(IRA_DEDUCTIBILITY_PHASEOUT[filing_status]['upper']):,.0f} MFJ with employer plan)")
            notes.append("Consider backdoor Roth IRA instead (no current-year deduction)")
        else:
            notes.append(f"Traditional IRA deduction: ${float(cents(deductible)):,.0f}")
        notes.append("IRA limit ($7,000) — verify against IRS.gov (retirement-hsa-limits.md)")

    if scenario_name == "add_ira_spouse":
        filing_status = baseline.get("filing_status", "MFJ")
        ira_amount = d(scenario.get("ira_contribution_spouse", IRA_LIMIT))
        baseline_agi = _quick_agi(baseline)
        deductible = compute_ira_deductibility(baseline_agi, ira_amount, filing_status)
        modified["ira_deduction"] = str(d(modified.get("ira_deduction")) + deductible)
        if deductible == Decimal("0"):
            notes.append(f"Spouse traditional IRA is NOT deductible at MAGI ${float(cents(baseline_agi)):,.0f}")
            notes.append("Consider backdoor Roth IRA for spouse instead")
        else:
            notes.append(f"Spouse traditional IRA deduction: ${float(cents(deductible)):,.0f}")
        notes.append("IRA limit ($7,000) — verify against IRS.gov (retirement-hsa-limits.md)")

    if scenario_name == "max_hsa":
        hsa_amount = d(scenario.get("hsa_contributions", HSA_FAMILY_LIMIT))
        current_hsa = d(baseline.get("hsa_contributions"))
        delta = hsa_amount - current_hsa
        if delta > Decimal("0"):
            modified["hsa_contributions"] = str(hsa_amount)
            notes.append(f"HSA contribution: ${float(cents(hsa_amount)):,.0f} (reduces AGI)")
            notes.append("Direct HSA contributions do NOT reduce Medicare wages — only payroll contributions do")
            notes.append("Must be enrolled in qualifying HDHP")
            notes.append("HSA family limit ($8,550) — verify against IRS.gov (retirement-hsa-limits.md)")

    if scenario_name in ("increase_charitable", "charitable_daf"):
        charitable_amount = d(scenario.get("charitable", Decimal("10000") if scenario_name == "increase_charitable" else Decimal("25000")))
        modified["charitable"] = str(charitable_amount)
        notes.append(f"Charitable contributions: ${float(cents(charitable_amount)):,.0f}")
        if scenario_name == "charitable_daf":
            notes.append("Donor-advised fund: large one-time contribution for multi-year giving impact")
        notes.append("(Source: 2025-tax-numbers.md — charitable deductions require itemizing)")

    if scenario_name == "adjust_withholding":
        # This scenario does not change tax liability — it computes optimal withholding
        notes.append("Withholding adjustment does not change total tax liability")
        notes.append("See output for recommended per-paycheck withholding amounts")

    if scenario_name == "increase_schedule_c_revenue":
        new_net = d(scenario.get("schedule_c_net", Decimal("5000")))
        modified["schedule_c_net"] = str(new_net)
        if new_net > SE_TAX_THRESHOLD:
            notes.append(f"Schedule C net profit ${float(cents(new_net)):,.0f} triggers self-employment tax (>$400)")
            notes.append("(Source: self-employment-qbi.md, SE Tax Calculation)")
        qbi_cf = d(baseline.get("qbi_carryforward"))
        if qbi_cf > Decimal("0") and new_net > Decimal("0"):
            notes.append(f"QBI carryforward of ${float(cents(qbi_cf)):,.0f} offsets future QBI deduction base")
            notes.append("(Source: self-employment-qbi.md, QBI Loss Carryforward)")

    if scenario_name == "add_schedule_c_expenses":
        new_net = d(scenario.get("schedule_c_net", Decimal("-2000")))
        modified["schedule_c_net"] = str(new_net)
        notes.append(f"Schedule C net: ${float(cents(new_net)):,.0f}")
        notes.append("(Source: schedule-c-guide.md, Business Expenses)")

    # For custom scenarios, apply any direct overrides
    if scenario_name == "custom":
        for key, value in scenario.items():
            if key != "name":
                modified[key] = value
        notes.append("Custom scenario — verify all parameters")

    return modified, notes


def _quick_agi(params):
    """Quick AGI estimate for phase-out checks (before scenario changes)."""
    wages = d(params.get("wages_primary")) + d(params.get("wages_spouse"))
    interest = d(params.get("interest"))
    dividends = d(params.get("dividends_ordinary"))
    cap_gain = d(params.get("capital_gain"))
    sched_c = d(params.get("schedule_c_net"))
    other = d(params.get("other_income"))
    adjustments = d(params.get("adjustments")) + d(params.get("hsa_contributions")) + d(params.get("ira_deduction"))
    return wages + interest + dividends + cap_gain + sched_c + other - adjustments


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def what_if(data):
    """Run a what-if scenario comparison.

    Input: {"baseline": {...}, "scenario": {"name": "...", ...}}
    Output: {"scenario_name": "...", "baseline": {...}, "modified": {...}, "savings": {...}, "notes": [...]}
    """
    baseline = data.get("baseline", {})
    scenario = data.get("scenario", {})
    scenario_name = scenario.get("name", "custom")

    # Ensure baseline has ira_deduction field
    if "ira_deduction" not in baseline:
        baseline["ira_deduction"] = "0"

    # Compute baseline tax
    baseline_result = compute_total_tax(baseline)

    # Apply scenario
    modified_params, notes = apply_scenario(baseline, scenario)

    # Compute modified tax
    modified_result = compute_total_tax(modified_params)

    # Compute savings (positive = tax saved)
    savings = {}
    for key in ["federal_tax", "se_tax", "additional_medicare_tax", "md_state_tax", "md_local_tax", "md_cap_gains_surtax", "total_tax"]:
        baseline_val = d(baseline_result[key])
        modified_val = d(modified_result[key])
        savings[key] = str(cents(baseline_val - modified_val))

    # Effective rate change
    baseline_rate = d(baseline_result["effective_rate"].replace("%", ""))
    modified_rate = d(modified_result["effective_rate"].replace("%", ""))
    savings["effective_rate_change"] = f"{float(cents(modified_rate - baseline_rate))}%"

    # For adjust_withholding, compute recommended withholding
    withholding_recommendation = None
    if scenario_name == "adjust_withholding":
        total_tax = d(modified_result["total_tax"])
        paychecks_per_year = int(scenario.get("pay_periods", 26))
        fed_tax = d(modified_result["federal_tax"]) + d(modified_result["additional_medicare_tax"]) + d(modified_result["se_tax"])
        state_tax = d(modified_result["md_state_tax"]) + d(modified_result["md_local_tax"]) + d(modified_result["md_cap_gains_surtax"])
        withholding_recommendation = {
            "total_tax_liability": str(cents(total_tax)),
            "federal_per_paycheck": str(cents(fed_tax / Decimal(str(paychecks_per_year)))),
            "state_per_paycheck": str(cents(state_tax / Decimal(str(paychecks_per_year)))),
            "pay_periods": paychecks_per_year,
        }

    result = {
        "scenario_name": scenario_name,
        "baseline": baseline_result,
        "modified": modified_result,
        "savings": savings,
        "notes": notes,
    }

    if withholding_recommendation:
        result["withholding_recommendation"] = withholding_recommendation

    return result


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: what_if.py \'{"baseline": {...}, "scenario": {"name": "max_401k_both", ...}}\''
        }))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = what_if(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
