"""
aca.py — Form 8962, Premium Tax Credit reconciliation (annual method).

Source: aca-premium-tax-credit.md (raw: reference/Raw/i8962.pdf, f8962.pdf;
repayment caps cross-checked in rp-24-40.pdf §2.07). 2025 keeps the
ARPA/IRA enhanced structure: 0.0000 applicable figure at <=150% FPL, 8.5%
cap, no 400% cliff.

Engine-BLOCK territory (per the curated ref): MFS filers, shared-policy
allocation (Part IV), year-of-marriage alternative (Part V), below-100%-FPL
special eligibility, mid-year premium/coverage changes (monthly method),
and the self-employed health-insurance circular calculation (Pub 974).

Inputs (the "aca" section of the engine input JSON):
    {"household_size": 2,
     "form_1095a": {"annual_premiums": "...",   # line 33 col A
                    "annual_slcsp": "...",      # line 33 col B
                    "annual_aptc": "..."},      # line 33 col C
     "full_year_unchanged_coverage": true,
     "dependents_magi": "0", "nontaxable_social_security": "0",
     "excluded_foreign_income": "0",
     "shared_policy": false, "married_during_year": false,
     "se_health_insurance_deduction_claimed": false}
"""

from decimal import Decimal, ROUND_HALF_UP

from engine.tax_math import ZERO, cents, d, whole

# Federal poverty line, 48 contiguous states + DC — 2024 guidelines govern
# 2025 coverage. Table 1-1 is linear: $15,060 + $5,380 per additional
# person (matches every printed size 1-5 row).
# (Source: aca-premium-tax-credit.md, Federal Poverty Line)
FPL_BASE = Decimal("15060")
FPL_PER_ADDITIONAL = Decimal("5380")

# Table 5 repayment limitation, filing statuses other than Single.
# (Source: aca-premium-tax-credit.md, Repayment Limitation)
REPAYMENT_CAP_OTHER = [
    (Decimal("200"), Decimal("750")),
    (Decimal("300"), Decimal("1950")),
    (Decimal("400"), Decimal("3250")),
]
REPAYMENT_CAP_SINGLE = [
    (Decimal("200"), Decimal("375")),
    (Decimal("300"), Decimal("975")),
    (Decimal("400"), Decimal("1625")),
]


def fpl_for_household(size):
    return FPL_BASE + FPL_PER_ADDITIONAL * (Decimal(str(size)) - 1)


def applicable_figure(pct):
    """Table 2: 0.0000 at <=150; linear 0.0004/point to 300; 0.00025/point
    to 400 (round half-up, 4 decimals); 0.0850 at 400+.
    (Source: aca-premium-tax-credit.md, Applicable Figure)"""
    if pct <= 150:
        return Decimal("0.0000")
    if pct >= 400:
        return Decimal("0.0850")
    if pct <= 300:
        raw = (pct - Decimal("150")) * Decimal("0.0004")
    else:
        raw = Decimal("0.06") + (pct - Decimal("300")) * Decimal("0.00025")
    return raw.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def form_8962(m, aca, agi, tax_exempt_interest, filing_status):
    """Returns (net_ptc -> Schedule 3 line 9, aptc_repayment -> Schedule 2
    line 1a). Either may be zero. BLOCKs instead of guessing on the cases
    the curated ref routes to Pub 974 / Parts IV-V."""
    if not aca:
        return ZERO, ZERO

    cite = "aca-premium-tax-credit.md"
    if filing_status == "MFS":
        m.block("Form 8962", "Premium Tax Credit",
                "MFS filers are generally ineligible for the PTC (limited "
                "exceptions) — accountant reviews", cite + ", MFS Restriction")
        return ZERO, ZERO
    for flag, item in (("shared_policy", "shared-policy allocation (Part IV)"),
                       ("married_during_year", "alternative calculation for year of marriage (Part V)")):
        if aca.get(flag):
            m.block("Form 8962", item,
                    "requires the allocation/alternative computation — "
                    "accountant computes", cite)
            return ZERO, ZERO
    if not aca.get("full_year_unchanged_coverage", False):
        m.block("Form 8962", "monthly computation (lines 12-23)",
                "coverage or premiums changed during the year — provide the "
                "1095-A monthly rows (lines 21-32) or route to the accountant",
                cite + ", Computation Flow")
        return ZERO, ZERO
    if aca.get("se_health_insurance_deduction_claimed"):
        m.block("Form 8962", "SE health insurance circularity",
                "claiming the self-employed health-insurance deduction for "
                "marketplace premiums requires the Pub 974 iterative "
                "calculation — accountant computes", cite + ", SE Circularity")
        return ZERO, ZERO

    a1095 = aca.get("form_1095a", {}) or {}
    premiums = d(a1095.get("annual_premiums"))
    slcsp = d(a1095.get("annual_slcsp"))
    aptc = d(a1095.get("annual_aptc"))
    size = int(aca.get("household_size", 0))
    if size < 1 or (premiums == ZERO and aptc == ZERO):
        m.need("aca.household_size / aca.form_1095a", "Form 8962",
               "Form 1095-A line 33 columns A/B/C and the tax-family size "
               "drive the reconciliation", cite)
        return ZERO, ZERO

    # Line 2a/3: household income = MAGI (+ dependents' MAGI when they file)
    magi = (agi + tax_exempt_interest
            + d(aca.get("nontaxable_social_security"))
            + d(aca.get("excluded_foreign_income")))
    household_income = magi + d(aca.get("dependents_magi"))
    fpl = fpl_for_household(size)

    # Line 5: truncate to a whole percentage; over 400 -> enter 401
    pct = (household_income / fpl * 100).to_integral_value(rounding="ROUND_FLOOR")
    if pct > 400:
        pct = Decimal("401")
    if pct < 100:
        m.block("Form 8962", "household income below 100% of FPL",
                "special eligibility rules apply below 100% FPL — accountant "
                "reviews", cite)
        return ZERO, ZERO

    figure = applicable_figure(pct)
    contribution = whole(household_income * figure)   # line 8a, whole dollars
    line_11d = max(slcsp - contribution, ZERO)
    ptc = min(premiums, line_11d)                     # line 11(e) = line 24

    m.put("Form 8962", "line_4_fpl", fpl, f"48-state FPL, household of {size}",
          cite + ", Federal Poverty Line")
    m.put("Form 8962", "line_5_pct_of_fpl", pct,
          "household income / FPL, truncated", cite + ", Line 5")
    m.put("Form 8962", "line_7_applicable_figure", str(figure),
          "Table 2", cite + ", Applicable Figure")
    m.put("Form 8962", "line_8a_annual_contribution", contribution,
          "household income x applicable figure", cite + ", Computation Flow")
    m.put("Form 8962", "line_24_total_ptc", ptc,
          "lesser of premiums or (SLCSP - contribution)", cite + ", Computation Flow")
    m.put("Form 8962", "line_25_aptc", aptc, "1095-A line 33 column C", cite)

    if ptc >= aptc:
        net_ptc = cents(ptc - aptc)
        m.put("Form 8962", "line_26_net_ptc", net_ptc,
              "line 24 - line 25 -> Schedule 3 line 9", cite + ", Computation Flow")
        return net_ptc, ZERO

    excess = aptc - ptc
    caps = REPAYMENT_CAP_SINGLE if filing_status == "Single" else REPAYMENT_CAP_OTHER
    cap = None
    for ceiling, amount in caps:
        if pct < ceiling:
            cap = amount
            break
    repayment = cents(excess if cap is None else min(excess, cap))
    m.put("Form 8962", "line_27_excess_aptc", cents(excess),
          "line 25 - line 24", cite)
    m.put("Form 8962", "line_28_repayment_limit",
          "uncapped (400%+)" if cap is None else cap,
          "Table 5 by FPL band and filing status", cite + ", Repayment Limitation")
    m.put("Form 8962", "line_29_repayment", repayment,
          "smaller of excess or the cap -> Schedule 2 line 1a", cite)
    return ZERO, repayment
