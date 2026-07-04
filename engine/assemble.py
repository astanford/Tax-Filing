"""
assemble.py — deduction choice, Form 1040 + Schedules 1/2/3 assembly,
Georgia Form 500, payments + estimated-tax safe harbor, and the AMT screen.

Sources: 1040-line-by-line.md, salt-deduction-2025.md, mortgage-interest.md,
georgia-500-guide.md, estimated-tax-safe-harbor.md, 2025-tax-numbers.md
(via engine.constants_2025).
"""

from decimal import Decimal

from engine.constants_2025 import (
    GA_DEPENDENT_EXEMPTION,
    GA_ITEMIZER_CREDIT_PER_TAXPAYER,
    GA_STANDARD_DEDUCTION,
    GA_TAX_RATE,
    MEDICAL_THRESHOLD_RATE,
    SALT_CAP,
    SALT_PHASE_OUT_RATE,
    STANDARD_DEDUCTION,
)
from engine.tax_math import ZERO, cents, d


def federal_deduction(m, agi, itemized, filing_status):
    """Standard vs itemized (Schedule A) with the OBBBA SALT cap.
    (Source: 2025-tax-numbers.md, Standard Deduction; salt-deduction-2025.md;
    mortgage-interest.md)"""
    standard = STANDARD_DEDUCTION[filing_status]

    total_salt = (d(itemized.get("state_local_income_tax"))
                  + d(itemized.get("real_estate_tax"))
                  + d(itemized.get("personal_property_tax")))
    cap = SALT_CAP[filing_status]
    effective_cap = cap["base"]
    if agi > cap["threshold"]:
        effective_cap = max(cap["floor"],
                            cap["base"] - SALT_PHASE_OUT_RATE * (agi - cap["threshold"]))
    salt_after_cap = min(total_salt, effective_cap)

    mortgage = d(itemized.get("mortgage_interest"))
    charitable = d(itemized.get("charitable"))
    medical = max(d(itemized.get("medical_expenses")) - MEDICAL_THRESHOLD_RATE * agi, ZERO)
    other = d(itemized.get("other_itemized"))
    itemized_total = salt_after_cap + mortgage + charitable + medical + other

    m.put("Schedule A", "line_5e_salt_after_cap", cents(salt_after_cap),
          f"SALT ${total_salt} capped at ${cents(effective_cap)}",
          "salt-deduction-2025.md, Overall SALT Cap")
    m.put("Schedule A", "line_17_total_itemized", cents(itemized_total),
          "SALT + mortgage + charitable + medical (7.5% floor) + other",
          "salt-deduction-2025.md; mortgage-interest.md; 2025-tax-numbers.md")

    if itemized_total > standard:
        return "itemized", cents(itemized_total), cents(salt_after_cap)
    return "standard", standard, cents(salt_after_cap)


def georgia_500(m, fed_agi, ded_type, fed_deduction_amount, inputs, filing_status,
                num_dependents):
    """GA Form 500 flow. Georgia locks the deduction type to federal.
    (Source: georgia-500-guide.md; 2025-tax-numbers.md, Georgia sections)"""
    ga = inputs.get("georgia", {}) or {}
    additions = d(ga.get("ga_additions"))          # e.g. bonus-depr addback
    us_obligations = d(ga.get("us_obligation_interest"))
    other_subtractions = d(ga.get("ga_other_subtractions"))

    ga_agi = fed_agi + additions - us_obligations - other_subtractions
    m.put("GA Form 500", "line_8_federal_agi", fed_agi,
          "Form 1040 line 11", "georgia-500-guide.md, Line 8")
    m.put("GA Form 500", "line_9_ga_adjustments", additions - us_obligations - other_subtractions,
          "GA Schedule 1 additions - subtractions",
          "georgia-500-guide.md, Schedule 1")
    m.put("GA Form 500", "line_10_ga_agi", ga_agi,
          "line 8 + line 9", "georgia-500-guide.md, Line 10")

    if ded_type == "itemized":
        other_state_tax = d(ga.get("other_state_income_tax"))
        ga_ded = max(fed_deduction_amount - other_state_tax, ZERO)
        m.put("GA Form 500", "line_12c_ga_itemized", ga_ded,
              "federal Schedule A total minus other states' income taxes",
              "georgia-500-guide.md, Lines 11-12c")
    else:
        ga_ded = GA_STANDARD_DEDUCTION[filing_status]
        m.put("GA Form 500", "line_11_ga_standard", ga_ded,
              "GA standard deduction (locked to federal standard choice)",
              "georgia-500-guide.md, Line 11; 2025-tax-numbers.md, Georgia Standard Deduction")

    exemption = cents(GA_DEPENDENT_EXEMPTION * Decimal(str(num_dependents)))
    m.put("GA Form 500", "line_14_dependent_exemption", exemption,
          f"{num_dependents} dependents x ${GA_DEPENDENT_EXEMPTION}",
          "georgia-500-guide.md, Line 14")

    ga_taxable = max(ga_agi - ga_ded - exemption, ZERO)
    ga_tax = cents(ga_taxable * GA_TAX_RATE)
    m.put("GA Form 500", "line_15c_ga_taxable_income", ga_taxable,
          "GA AGI - deduction - exemptions (NOL not modeled)",
          "georgia-500-guide.md, Line 15c")
    m.put("GA Form 500", "line_16_ga_tax", ga_tax,
          "flat 5.19%", "georgia-500-guide.md, Line 16; 2025-tax-numbers.md, Georgia State Income Tax")

    credit = ZERO
    if ded_type == "itemized":
        n = Decimal("2") if filing_status == "MFJ" else Decimal("1")
        credit = min(GA_ITEMIZER_CREDIT_PER_TAXPAYER * n, ga_tax)
        m.put("GA Form 500", "line_19_itemizer_credit", credit,
              "$300/taxpayer, nonrefundable",
              "georgia-500-guide.md, Line 19")
    ga_tax_after_credit = cents(ga_tax - credit)
    m.put("GA Form 500", "line_22_tax_after_credits", ga_tax_after_credit,
          "line 16 - credits", "georgia-500-guide.md")

    ga_withholding = d(ga.get("ga_withholding"))
    ga_estimated = d(ga.get("ga_estimated_payments"))
    ga_balance = cents(ga_tax_after_credit - ga_withholding - ga_estimated)
    m.put("GA Form 500", "line_24_withholding", ga_withholding,
          "W-2 box 17 / 1099 GA withholding", "georgia-500-guide.md, Line 24")
    m.put("GA Form 500", "line_26_estimated_payments", ga_estimated,
          "GA 500-ES payments + prior-year credit", "georgia-500-guide.md")
    m.put("GA Form 500", "balance_due_or_refund", ga_balance,
          "tax after credits - payments (positive = owed)",
          "georgia-500-guide.md, Payments and Balance Due")
    return ga_tax_after_credit


def amt_screen(m, taxable_income, salt_deducted, ded_type, federal_tax, filing_status):
    """Conservative AMT screen (NOT a Form 6251 computation): estimates AMTI
    as taxable income + standard deduction or SALT addback, applies the
    exemption/phase-out and 26%/28% rates; if tentative AMT exceeds regular
    tax, BLOCK for the accountant. Only MFJ parameters are curated.
    (Source: 2025-tax-numbers.md, Alternative Minimum Tax)"""
    if filing_status != "MFJ":
        m.block("Form 6251", "AMT screen",
                "AMT parameters only curated for MFJ — accountant should screen",
                "2025-tax-numbers.md, Alternative Minimum Tax")
        return

    exemption = Decimal("137000")
    phaseout_start = Decimal("1252700")
    rate_break = Decimal("248300")

    addback = salt_deducted if ded_type == "itemized" else STANDARD_DEDUCTION["MFJ"]
    amti_estimate = taxable_income + addback
    exemption_left = exemption
    if amti_estimate > phaseout_start:
        exemption_left = max(exemption - Decimal("0.25") * (amti_estimate - phaseout_start), ZERO)
    amt_base = max(amti_estimate - exemption_left, ZERO)
    if amt_base <= rate_break:
        tentative = cents(amt_base * Decimal("0.26"))
    else:
        tentative = cents(rate_break * Decimal("0.26") + (amt_base - rate_break) * Decimal("0.28"))

    m.put("Form 6251", "amt_screen_tentative", tentative,
          "SCREEN ONLY: (taxable income + deduction addback - exemption) x 26/28%",
          "2025-tax-numbers.md, Alternative Minimum Tax")
    if tentative > federal_tax:
        m.block("Form 6251", "Alternative Minimum Tax",
                f"AMT screen tentative (${tentative}) exceeds regular tax "
                f"(${federal_tax}) — a real Form 6251 is required; accountant computes",
                "2025-tax-numbers.md, Alternative Minimum Tax")


def payments_and_safe_harbor(m, total_tax, withholding, estimated_payments,
                             prior_year_tax, prior_year_agi, filing_status,
                             refundable_credits=ZERO):
    """Payments roll-up + Form 2210 safe-harbor test.
    (Source: estimated-tax-safe-harbor.md)"""
    total_payments = withholding + estimated_payments + refundable_credits
    balance = cents(total_tax - total_payments)
    m.put("Form 1040", "line_25_withholding", withholding,
          "sum of withholding across documents (25d; a W-2/1099/other split "
          "for 25a-c comes from the interview)", "1040-line-by-line.md")
    m.put("Form 1040", "line_26_estimated_payments", estimated_payments,
          "1040-ES payments + prior-year overpayment applied",
          "1040-line-by-line.md")
    if refundable_credits > ZERO:
        m.put("Form 1040", "line_31_schedule_3_line_13", refundable_credits,
              "net premium tax credit (Schedule 3 line 9 -> line 13 total)",
              "aca-premium-tax-credit.md")
    m.put("Form 1040", "line_33_total_payments", total_payments,
          "line 25d + line 26 + line 31 refundable credits",
          "1040-line-by-line.md")
    m.put("Form 1040", "line_37_balance_due" if balance > ZERO else "line_34_overpayment",
          abs(balance), "total tax - total payments", "1040-line-by-line.md")

    if prior_year_tax is None:
        m.need("payments.prior_year_tax", "Form 2210 safe harbor",
               "prior-year total tax determines the 100%/110% safe harbor",
               "estimated-tax-safe-harbor.md, Safe Harbors")
        return balance

    prior_year_tax = d(prior_year_tax)
    pct = Decimal("1.10") if d(prior_year_agi) > Decimal("150000") else Decimal("1.00")
    required = min(cents(total_tax * Decimal("0.90")), cents(prior_year_tax * pct))
    underpaid = balance > Decimal("1000") and total_payments < required
    m.put("Form 2210", "required_annual_payment", required,
          f"smaller of 90% of current tax or {pct * 100}% of prior-year tax",
          "estimated-tax-safe-harbor.md, Safe Harbors")
    m.put("Form 2210", "underpayment_exposure", underpaid,
          "balance due > $1,000 and payments below the required annual payment",
          "estimated-tax-safe-harbor.md, Who Owes the Penalty")
    if underpaid:
        m.block("Form 2210", "underpayment penalty amount",
                "safe harbor missed — quarterly penalty computation (and any "
                "annualized-income relief) is accountant territory",
                "estimated-tax-safe-harbor.md")
    return balance
