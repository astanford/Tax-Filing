"""
other_taxes.py — Schedule SE, Form 8959 (Additional Medicare), Form 8960
(NIIT), and Form 8995 (QBI, simplified form only).

Sources: self-employment-qbi.md, additional-medicare-tax.md,
niit-form-8960.md, k1-guide.md, passthrough-loss-limitations.md,
2025-tax-numbers.md (via engine.constants_2025).
"""

from decimal import Decimal

from engine.constants_2025 import (
    ADDITIONAL_MEDICARE_RATE,
    MEDICARE_SE_RATE,
    MEDICARE_TAX_THRESHOLD,
    NIIT_RATE,
    NIIT_THRESHOLD,
    QBI_THRESHOLD,
    SE_NET_FACTOR,
    SE_TAX_THRESHOLD,
    SS_RATE,
    SS_WAGE_BASE,
)
from engine.tax_math import ZERO, cents, d


def schedule_se(m, sc_net, k1_se_box14a, w2_ss_wages):
    """Schedule SE from Schedule C net + K-1 box 14A.
    (Source: self-employment-qbi.md, SE Tax Calculation; k1-guide.md, Box 14)
    Returns (se_tax, deductible_half)."""
    se_base = sc_net + k1_se_box14a
    if se_base <= SE_TAX_THRESHOLD:
        m.put("Schedule SE", "se_tax", ZERO,
              f"net SE earnings ${se_base} not over ${SE_TAX_THRESHOLD}",
              "self-employment-qbi.md, SE Tax Calculation")
        return ZERO, ZERO

    net_se = se_base * SE_NET_FACTOR
    ss_room = max(SS_WAGE_BASE - w2_ss_wages, ZERO)
    ss_subject = min(net_se, ss_room)
    se_tax = cents(ss_subject * SS_RATE + net_se * MEDICARE_SE_RATE)
    half = cents(se_tax / Decimal("2"))

    m.put("Schedule SE", "line_4a_net_se_earnings", cents(net_se),
          "92.35% of Schedule C net + K-1 box 14A",
          "self-employment-qbi.md, SE Tax Calculation")
    m.put("Schedule SE", "line_12_se_tax", se_tax,
          "12.4% SS (to wage base) + 2.9% Medicare",
          "self-employment-qbi.md, SE Tax Calculation; 2025-tax-numbers.md, Social Security")
    m.put("Schedule SE", "line_13_deduction_half", half,
          "one-half of SE tax -> Schedule 1",
          "self-employment-qbi.md, SE Tax Calculation")
    return se_tax, half


def form_8959(m, medicare_wages, se_base, filing_status):
    """Additional Medicare Tax: 0.9% over the threshold; wages and SE income
    stack (SE threshold reduced by wages).
    (Source: additional-medicare-tax.md; 2025-tax-numbers.md)"""
    threshold = MEDICARE_TAX_THRESHOLD[filing_status]
    wage_excess = max(medicare_wages - threshold, ZERO)
    tax_on_wages = cents(wage_excess * ADDITIONAL_MEDICARE_RATE)

    se_income = max(se_base * SE_NET_FACTOR, ZERO) if se_base > SE_TAX_THRESHOLD else ZERO
    se_threshold = max(threshold - medicare_wages, ZERO)
    se_excess = max(se_income - se_threshold, ZERO)
    tax_on_se = cents(se_excess * ADDITIONAL_MEDICARE_RATE)

    total = cents(tax_on_wages + tax_on_se)
    m.put("Form 8959", "line_7_tax_on_wages", tax_on_wages,
          f"0.9% of Medicare wages over ${threshold}",
          "additional-medicare-tax.md")
    m.put("Form 8959", "line_13_tax_on_se", tax_on_se,
          "0.9% of SE income over the wage-reduced threshold",
          "additional-medicare-tax.md")
    m.put("Form 8959", "line_18_total", total,
          "wages portion + SE portion", "additional-medicare-tax.md")
    return total


def form_8960(m, magi, investment_income, investment_expenses, filing_status):
    """Net Investment Income Tax: 3.8% of the smaller of NII or MAGI over
    the threshold. (Source: niit-form-8960.md)"""
    threshold = NIIT_THRESHOLD[filing_status]
    nii = max(investment_income - investment_expenses, ZERO)
    excess = max(magi - threshold, ZERO)
    niit = cents(min(nii, excess) * NIIT_RATE)

    m.put("Form 8960", "line_8_net_investment_income", nii,
          "interest + dividends + net capital gain + passive net income - expenses",
          "niit-form-8960.md, What Counts as Investment Income")
    m.put("Form 8960", "line_15_excess_magi", excess,
          f"MAGI over ${threshold}", "niit-form-8960.md")
    m.put("Form 8960", "line_17_niit", niit,
          "3.8% of the smaller of NII or excess MAGI",
          "niit-form-8960.md")
    return niit


def form_8995(m, qbi_net, qbi_carryforward, reit_ptp_income, taxable_before_qbi,
              net_capital_gain, filing_status):
    """Form 8995 simplified QBI deduction. Above the taxable-income threshold
    the engine BLOCKs (Form 8995-A: SSTB/wage/UBIA limits).
    (Source: self-employment-qbi.md, QBI Deduction Rules; k1-guide.md,
    Box 20 code Z)

    Returns (deduction, new_qbi_carryforward, new_reit_carryforward)."""
    threshold = QBI_THRESHOLD[filing_status]
    if taxable_before_qbi > threshold:
        m.block("Form 8995", "QBI deduction",
                f"taxable income before QBI (${taxable_before_qbi}) exceeds the "
                f"Form 8995 threshold (${threshold}) — Form 8995-A with "
                f"SSTB/W-2-wage/UBIA limits required; accountant computes",
                "self-employment-qbi.md, Which Form; k1-guide.md, Box 20 code Z")
        return ZERO, qbi_carryforward, ZERO

    combined_qbi = qbi_net - qbi_carryforward
    if combined_qbi <= ZERO:
        new_carry = -combined_qbi
        m.put("Form 8995", "line_16_qbi_carryforward", new_carry,
              "net QBI loss carries forward (file Form 8995 even at $0)",
              "self-employment-qbi.md, QBI Loss Carryforward")
        qbi_component = ZERO
    else:
        new_carry = ZERO
        qbi_component = cents(combined_qbi * Decimal("0.20"))

    reit_component = cents(max(reit_ptp_income, ZERO) * Decimal("0.20"))
    tentative = qbi_component + reit_component
    income_limit = cents(max(taxable_before_qbi - net_capital_gain, ZERO) * Decimal("0.20"))
    deduction = min(tentative, income_limit)

    m.put("Form 8995", "line_10_qbi_deduction_before_limit", tentative,
          "20% of net QBI + 20% of REIT/PTP income",
          "self-employment-qbi.md, QBI Deduction Rules")
    m.put("Form 8995", "line_14_income_limit", income_limit,
          "20% of (taxable income before QBI - net capital gain)",
          "self-employment-qbi.md, QBI Deduction Rules")
    m.put("Form 8995", "line_15_deduction", deduction,
          "smaller of tentative deduction or income limit",
          "self-employment-qbi.md, QBI Deduction Rules")
    return deduction, new_carry, ZERO
