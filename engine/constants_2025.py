"""
constants_2025.py — Single source of truth for 2025 tax-year constants.

Every constant cites a file in reference/curated/ (Rule 1). Where the curated
file has a committed raw source in reference/Raw/, that is noted too. All
skill scripts import from this module — no script defines its own copy.

Corrections made when this module was created (2026-07-03), verified against
Rev. Proc. 2024-40 (reference/Raw/rp-24-40.pdf, IRS official):
  - MFJ top-bracket base tax was $188,770 in the old script tables and the
    curated file; the correct value is $202,154.50 ($188,769.75 is the
    SINGLE top-bracket base).
  - Single bases for the 24%/32%/35% brackets were each $0.50 high
    ($17,651.50/$40,199.50/$57,231.50; correct: $17,651/$40,199/$57,231).
  - HoH top-bracket base was $187,032; correct: $187,031.50.
  - MFS was approximated by the Single table; it has its own table (37%
    bracket starts at $375,800, base $101,077.25).

All amounts are Decimal (Rule 3 — no float math).
"""

from decimal import Decimal

TAX_YEAR = 2025


# ---------------------------------------------------------------------------
# Federal Income Tax Brackets — all filing statuses
# (Source: 2025-tax-numbers.md, Federal Income Tax Brackets;
#  raw source: reference/Raw/rp-24-40.pdf §2.01 Tables 1-4)
#
# Each tuple: (upper_bound, rate, base_tax_at_lower_bound).
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
        (None,              Decimal("0.37"), Decimal("202154.50")),
    ],
    "HoH": [
        (Decimal("17000"),  Decimal("0.10"), Decimal("0")),
        (Decimal("64850"),  Decimal("0.12"), Decimal("1700")),
        (Decimal("103350"), Decimal("0.22"), Decimal("7442")),
        (Decimal("197300"), Decimal("0.24"), Decimal("15912")),
        (Decimal("250500"), Decimal("0.32"), Decimal("38460")),
        (Decimal("626350"), Decimal("0.35"), Decimal("55484")),
        (None,              Decimal("0.37"), Decimal("187031.50")),
    ],
    "Single": [
        (Decimal("11925"),  Decimal("0.10"), Decimal("0")),
        (Decimal("48475"),  Decimal("0.12"), Decimal("1192.50")),
        (Decimal("103350"), Decimal("0.22"), Decimal("5578.50")),
        (Decimal("197300"), Decimal("0.24"), Decimal("17651")),
        (Decimal("250525"), Decimal("0.32"), Decimal("40199")),
        (Decimal("626350"), Decimal("0.35"), Decimal("57231")),
        (None,              Decimal("0.37"), Decimal("188769.75")),
    ],
    "MFS": [
        (Decimal("11925"),  Decimal("0.10"), Decimal("0")),
        (Decimal("48475"),  Decimal("0.12"), Decimal("1192.50")),
        (Decimal("103350"), Decimal("0.22"), Decimal("5578.50")),
        (Decimal("197300"), Decimal("0.24"), Decimal("17651")),
        (Decimal("250525"), Decimal("0.32"), Decimal("40199")),
        (Decimal("375800"), Decimal("0.35"), Decimal("57231")),
        (None,              Decimal("0.37"), Decimal("101077.25")),
    ],
}


# ---------------------------------------------------------------------------
# Qualified Dividends and Capital Gain (QDCG) rate thresholds
# (Source: 2025-tax-numbers.md, QDCG Tax Rates;
#  raw source: reference/Raw/rp-24-40.pdf §2.03)
# Taxable income up to zero_max → 0%; up to fifteen_max → 15%; above → 20%.
# ---------------------------------------------------------------------------

QDCG_THRESHOLDS = {
    "MFJ":    {"zero_max": Decimal("96700"), "fifteen_max": Decimal("600050")},
    "MFS":    {"zero_max": Decimal("48350"), "fifteen_max": Decimal("300000")},
    "HoH":    {"zero_max": Decimal("64750"), "fifteen_max": Decimal("566700")},
    "Single": {"zero_max": Decimal("48350"), "fifteen_max": Decimal("533400")},
}


# ---------------------------------------------------------------------------
# Standard Deduction (Source: 2025-tax-numbers.md, Standard Deduction)
# ---------------------------------------------------------------------------

STANDARD_DEDUCTION = {
    "MFJ": Decimal("31500"),
    "Single": Decimal("15750"),
    "MFS": Decimal("15750"),
    "HoH": Decimal("23625"),
}

# Additional standard deduction per condition (age 65+ or blind)
# (Source: 2025-tax-numbers.md, Standard Deduction)
ADDITIONAL_STD_DEDUCTION = {
    "MFJ": Decimal("1600"),
    "Single": Decimal("2000"),
    "HoH": Decimal("2000"),
    "MFS": Decimal("1600"),
}


# ---------------------------------------------------------------------------
# SALT Deduction Cap — OBBBA (Source: salt-deduction-2025.md;
# 2025-tax-numbers.md, SALT Deduction Cap)
# ---------------------------------------------------------------------------

SALT_CAP = {
    "MFJ":    {"base": Decimal("40000"), "floor": Decimal("10000"), "threshold": Decimal("500000")},
    "Single": {"base": Decimal("40000"), "floor": Decimal("10000"), "threshold": Decimal("500000")},
    "HoH":    {"base": Decimal("40000"), "floor": Decimal("10000"), "threshold": Decimal("500000")},
    "MFS":    {"base": Decimal("20000"), "floor": Decimal("5000"),  "threshold": Decimal("250000")},
}

SALT_PHASE_OUT_RATE = Decimal("0.30")


# ---------------------------------------------------------------------------
# Medical expense itemized-deduction floor
# (Source: 2025-tax-numbers.md; Schedule A rules)
# ---------------------------------------------------------------------------

MEDICAL_THRESHOLD_RATE = Decimal("0.075")


# ---------------------------------------------------------------------------
# Additional Medicare Tax — Form 8959
# (Source: additional-medicare-tax.md; 2025-tax-numbers.md)
# ---------------------------------------------------------------------------

MEDICARE_TAX_THRESHOLD = {
    "MFJ": Decimal("250000"),
    "Single": Decimal("200000"),
    "HoH": Decimal("200000"),
    "MFS": Decimal("125000"),
}

ADDITIONAL_MEDICARE_RATE = Decimal("0.009")


# ---------------------------------------------------------------------------
# Self-Employment Tax — Schedule SE
# (Source: self-employment-qbi.md; 2025-tax-numbers.md, Social Security)
# ---------------------------------------------------------------------------

SE_TAX_THRESHOLD = Decimal("400")
SE_TAX_RATE = Decimal("0.153")        # 12.4% SS + 2.9% Medicare
SE_NET_FACTOR = Decimal("0.9235")     # 92.35% adjustment
SS_WAGE_BASE = Decimal("176100")
SS_RATE = Decimal("0.124")
MEDICARE_SE_RATE = Decimal("0.029")


# ---------------------------------------------------------------------------
# Other key federal numbers (Source: 2025-tax-numbers.md, Other Key Federal
# Numbers)
# ---------------------------------------------------------------------------

CAPITAL_LOSS_LIMIT = {"default": Decimal("3000"), "MFS": Decimal("1500")}
SCHEDULE_B_THRESHOLD = Decimal("1500")
STANDARD_MILEAGE_RATE = Decimal("0.70")   # business, per mile [IRS Notice 2025-02]
QBI_THRESHOLD_MFJ = Decimal("394600")     # [IRC §199A]

# Form 8995 eligibility: 2025 taxable income before QBI must not exceed
# these; above them Form 8995-A applies (engine BLOCKs to accountant).
# (Source: k1-guide.md, Box 20 code Z; self-employment-qbi.md)
QBI_THRESHOLD = {
    "MFJ": Decimal("394600"),
    "Single": Decimal("197300"),
    "HoH": Decimal("197300"),
    "MFS": Decimal("197300"),
}


# ---------------------------------------------------------------------------
# Net Investment Income Tax — Form 8960
# (Source: niit-form-8960.md; statutory §1411 thresholds, not inflation
# indexed)
# ---------------------------------------------------------------------------

NIIT_RATE = Decimal("0.038")
NIIT_THRESHOLD = {
    "MFJ": Decimal("250000"),
    "Single": Decimal("200000"),
    "HoH": Decimal("200000"),
    "MFS": Decimal("125000"),
}


# ---------------------------------------------------------------------------
# Georgia — Form 500 (Source: georgia-500-guide.md; 2025-tax-numbers.md,
# Georgia sections; raw source: reference/Raw/2025-it511-booklet.pdf)
# ---------------------------------------------------------------------------

GA_TAX_RATE = Decimal("0.0519")

GA_STANDARD_DEDUCTION = {
    "MFJ": Decimal("24000"),
    "Single": Decimal("12000"),
    "MFS": Decimal("12000"),
    "HoH": Decimal("12000"),  # GA gives HoH no premium over Single
}

GA_DEPENDENT_EXEMPTION = Decimal("4000")
GA_ITEMIZER_CREDIT_PER_TAXPAYER = Decimal("300")


# ---------------------------------------------------------------------------
# Retirement / HSA limits (Source: retirement-hsa-limits.md)
# ⚠️ VERIFY AGAINST IRS.GOV — raw sources not yet curated. Any output that
# uses these must carry the verification warning (tax-advisor Rule 7).
# ---------------------------------------------------------------------------

RETIREMENT_401K_LIMIT = Decimal("23500")
IRA_LIMIT = Decimal("7000")
HSA_FAMILY_LIMIT = Decimal("8550")
HSA_SELF_LIMIT = Decimal("4300")

# Traditional IRA deductibility phase-out (covered by employer plan)
# (Source: retirement-hsa-limits.md, Traditional IRA Deductibility)
IRA_DEDUCTIBILITY_PHASEOUT = {
    "MFJ": {"lower": Decimal("126000"), "upper": Decimal("146000")},
    "Single": {"lower": Decimal("79000"), "upper": Decimal("89000")},
    "HoH": {"lower": Decimal("79000"), "upper": Decimal("89000")},
    "MFS": {"lower": Decimal("0"), "upper": Decimal("10000")},
}


FILING_STATUSES = ("MFJ", "Single", "HoH", "MFS")
