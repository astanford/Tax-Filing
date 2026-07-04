"""
return_engine.py — Orchestrates the full federal + Georgia return into a
cited manifest.

Input: one JSON document (assembled by the skills from
analysis/tax-doc-summary.csv, analysis/prior-year-carryovers-*.json, and
interview answers). Output: the return manifest — every line with value,
source, and citation; BLOCKED items for the accountant; MISSING inputs for
the interview loop. The engine computes with a citation or stops — it never
estimates (CLAUDE.md Rules 1-3).

Usage:
    python engine/return_engine.py '<json>'         # or
    python engine/return_engine.py --file inputs.json

Computation order (docs/FULL-RETURN-PLAN.md, Phase 3):
  income schedules (B, D/8949, C/E results as inputs) -> SE tax ->
  adjustments/AGI -> deduction -> QBI -> 1040 tax via QDCG worksheet ->
  other taxes (8959/8960, AMT screen) -> GA 500 -> payments/safe harbor.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.aca import form_8962
from engine.assemble import (
    amt_screen,
    federal_deduction,
    georgia_500,
    payments_and_safe_harbor,
)
from engine.income import qdcg_worksheet, schedule_b, schedule_d
from engine.manifest import Manifest
from engine.other_taxes import form_8959, form_8960, form_8995, schedule_se
from engine.tax_math import ZERO, cents, d


def compute_return(inputs):
    tax_year = int(inputs.get("tax_year", 2025))
    filing_status = inputs.get("filing_status", "MFJ")
    if filing_status not in ("MFJ", "Single", "HoH", "MFS"):
        return {"error": f"Unknown filing status {filing_status!r}"}
    m = Manifest(tax_year, filing_status)

    income = inputs.get("income", {}) or {}
    carryovers = inputs.get("carryovers", {}) or {}
    payments = inputs.get("payments", {}) or {}

    # --- Income schedules ---
    interest, ordinary_div = schedule_b(m, income)
    qualified_div = d(income.get("dividends_qualified"))
    line_7_capital, sched_d_15, sched_d_16 = schedule_d(
        m, income, carryovers, filing_status)

    wages = d(income.get("wages"))                       # supported; 0 for this filer
    sc_net = d(income.get("schedule_c_net"))             # schedule_c_calculator.py
    se_k1 = d(income.get("k1_box14a_se_earnings"))       # k1_passthrough_calculator.py
    sched_e_total = (d(income.get("schedule_e_line_26"))
                     + d(income.get("schedule_e_part2_line_32"))
                     + d(income.get("schedule_e_part3_line_37")))
    m.put("Schedule E", "line_41_total", sched_e_total,
          "Part I line 26 + Part II line 32 + Part III line 37 "
          "(from schedule_e_calculator.py / k1_passthrough_calculator.py)",
          "schedule-e-guide.md, Totals; k1-guide.md, Schedule E Part II mechanics")
    state_refund_taxable = d(income.get("state_refund_taxable"))
    other_income = d(income.get("other_income"))

    # --- SE tax (needed before AGI for the half-SE adjustment) ---
    w2_ss_wages = d(income.get("w2_ss_wages"))
    se_tax, se_half = schedule_se(m, sc_net, se_k1, w2_ss_wages)

    # --- Schedule 1 ---
    sched_1_income = state_refund_taxable + sc_net + sched_e_total + other_income
    m.put("Schedule 1", "line_10_additional_income", sched_1_income,
          "state refund (if taxable) + Schedule C + Schedule E + other",
          "1040-line-by-line.md, Schedule 1")
    adj = inputs.get("adjustments", {}) or {}
    hsa = d(adj.get("hsa_deduction"))
    ira = d(adj.get("ira_deduction"))
    student_loan = d(adj.get("student_loan_interest"))
    other_adj = d(adj.get("other_adjustments"))
    if student_loan > ZERO:
        m.note("Student-loan interest entered as already-limited; the $2,500 "
               "cap and MAGI phase-out are in student-loan-interest.md — "
               "verify before filing.")
    total_adjustments = hsa + ira + student_loan + se_half + other_adj
    m.put("Schedule 1", "line_25_adjustments", total_adjustments,
          "HSA + IRA + student loan + half SE tax + other",
          "schedule-1a-deductions.md; self-employment-qbi.md")

    # --- Form 1040 income/AGI ---
    total_income = (wages + interest + ordinary_div + line_7_capital
                    + sched_1_income)
    agi = total_income - total_adjustments
    m.put("Form 1040", "line_1_wages", wages, "W-2 box 1 sum", "1040-line-by-line.md")
    m.put("Form 1040", "line_2b_interest", interest, "Schedule B line 4",
          "investment-income.md")
    m.put("Form 1040", "line_3a_qualified_dividends", qualified_div,
          "1099-DIV box 1b sum", "investment-income.md")
    m.put("Form 1040", "line_3b_dividends", ordinary_div, "Schedule B line 6",
          "investment-income.md")
    m.put("Form 1040", "line_7_capital_gain", line_7_capital,
          "Schedule D line 16 (or allowed loss)", "schedule-d-8949-guide.md")
    m.put("Form 1040", "line_8_schedule_1_income", sched_1_income,
          "Schedule 1 line 10", "1040-line-by-line.md")
    m.put("Form 1040", "line_9_total_income", total_income,
          "lines 1+2b+3b+7+8", "1040-line-by-line.md")
    m.put("Form 1040", "line_10_adjustments", total_adjustments,
          "Schedule 1 line 25", "1040-line-by-line.md")
    m.put("Form 1040", "line_11_agi", agi, "line 9 - line 10",
          "1040-line-by-line.md")

    # --- Deduction ---
    itemized = inputs.get("itemized", {}) or {}
    ded_type, ded_amount, salt_after_cap = federal_deduction(
        m, agi, itemized, filing_status)
    m.put("Form 1040", "line_12_deduction", ded_amount,
          f"{ded_type} (larger of standard vs Schedule A)",
          "2025-tax-numbers.md, Standard Deduction; salt-deduction-2025.md")

    # --- QBI ---
    taxable_before_qbi = max(agi - ded_amount, ZERO)
    qbi = inputs.get("qbi", {}) or {}
    net_cap_gain_for_limit = max(min(sched_d_15, sched_d_16), ZERO) + max(qualified_div, ZERO)
    qbi_ded, qbi_carry_out, _ = form_8995(
        m,
        d(qbi.get("qbi_net")),
        d(carryovers.get("qbi_carryforward_form_8995_line_16")),
        d(qbi.get("reit_ptp_income")),
        taxable_before_qbi,
        net_cap_gain_for_limit,
        filing_status,
    )
    m.put("Form 1040", "line_13_qbi_deduction", qbi_ded, "Form 8995 line 15",
          "self-employment-qbi.md")

    m.put("Form 1040", "line_14_deductions_total", ded_amount + qbi_ded,
          "line 12e + line 13a (Schedule 1-A not modeled)", "1040-line-by-line.md")
    taxable_income = max(taxable_before_qbi - qbi_ded, ZERO)
    m.put("Form 1040", "line_15_taxable_income", taxable_income,
          "line 11 - line 12 - line 13", "1040-line-by-line.md")

    # --- Tax (QDCG worksheet handles preferential rates) ---
    federal_tax = qdcg_worksheet(m, taxable_income, qualified_div,
                                 sched_d_15, sched_d_16, filing_status)
    m.put("Form 1040", "line_16_tax", federal_tax,
          "QDCG worksheet (or ordinary brackets when no preferential income)",
          "schedule-d-8949-guide.md, QDCG Tax Worksheet; 2025-tax-numbers.md")

    # --- Other taxes (Schedule 2) ---
    medicare_wages = d(income.get("medicare_wages"))
    add_medicare = form_8959(m, medicare_wages, sc_net + se_k1, filing_status)

    # Net capital gain enters NII once: the 1040 line 7 amount when positive.
    passive_investment_income = max(sched_e_total, ZERO)
    investment_income = (interest + ordinary_div + max(line_7_capital, ZERO)
                         + passive_investment_income)
    niit = form_8960(m, agi, investment_income,
                     d(inputs.get("investment_expenses_8960")), filing_status)
    m.note("Form 8960 MAGI approximated by AGI (no foreign-earned-income "
           "exclusion in scope). (Source: niit-form-8960.md)")

    sched_2_total = se_tax + add_medicare + niit
    m.put("Schedule 2", "line_21_other_taxes", sched_2_total,
          "SE tax + Additional Medicare + NIIT", "additional-medicare-tax.md; niit-form-8960.md")

    # --- ACA Premium Tax Credit reconciliation (Form 8962) ---
    tax_exempt_interest = d(income.get("tax_exempt_interest"))
    net_ptc, aptc_repayment = form_8962(
        m, inputs.get("aca"), agi, tax_exempt_interest, filing_status)
    if aptc_repayment > ZERO:
        m.put("Schedule 2", "line_1a_excess_aptc_repayment", aptc_repayment,
              "Form 8962 line 29", "aca-premium-tax-credit.md")
    if net_ptc > ZERO:
        m.put("Schedule 3", "line_9_net_premium_tax_credit", net_ptc,
              "Form 8962 line 26", "aca-premium-tax-credit.md")

    # Form flow: 17 = Schedule 2 line 3 (excess APTC repayment); 18 = 16+17;
    # credits (19-21) out of scope; 22 = 18 - 21; 23 = Sch2 line 21;
    # 24 = 22 + 23.
    m.put("Form 1040", "line_17_schedule_2_line_3", aptc_repayment,
          "Schedule 2 Part I (excess APTC repayment; AMT screened separately)",
          "aca-premium-tax-credit.md; 1040-line-by-line.md")
    m.put("Form 1040", "line_18_tax_plus_sch2_line3", federal_tax + aptc_repayment,
          "line 16 + line 17", "1040-line-by-line.md")
    m.put("Form 1040", "line_22_tax_after_credits", federal_tax + aptc_repayment,
          "line 18 (CTC/education/other credits out of scope — see roadmap)",
          "1040-line-by-line.md")
    m.put("Form 1040", "line_23_other_taxes", sched_2_total,
          "Schedule 2 line 21", "1040-line-by-line.md")
    total_tax = cents(federal_tax + aptc_repayment + sched_2_total)
    m.put("Form 1040", "line_24_total_tax", total_tax,
          "line 22 + line 23", "1040-line-by-line.md")

    # --- AMT screen ---
    amt_screen(m, taxable_income, salt_after_cap, ded_type, federal_tax,
               filing_status)

    # --- Payments + safe harbor (net PTC is a refundable credit on line 31) ---
    balance = payments_and_safe_harbor(
        m, total_tax,
        d(payments.get("federal_withholding")),
        d(payments.get("federal_estimated_payments")),
        payments.get("prior_year_total_tax"),
        payments.get("prior_year_agi"),
        filing_status,
        refundable_credits=net_ptc,
    )

    # --- Georgia ---
    ga_tax = georgia_500(m, agi, ded_type, ded_amount, inputs, filing_status,
                         int(inputs.get("num_dependents", 0)))

    # --- Carryovers out (prior-year schema keys) ---
    m.put("Carryovers Out", "qbi_carryforward_form_8995_line_16", qbi_carry_out,
          "Form 8995 line 16", "self-employment-qbi.md")

    result = m.to_dict()
    result["summary"] = {
        "federal_total_tax": str(cents(total_tax)),
        "federal_balance_due_or_refund": str(cents(balance)),
        "georgia_tax_after_credits": str(cents(ga_tax)),
        "blocked_count": len(m.blocked),
        "missing_count": len(m.missing),
    }
    return result


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--file":
        data = json.loads(Path(sys.argv[2]).read_text())
    elif len(sys.argv) >= 2:
        try:
            data = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON: {e}"}))
            sys.exit(1)
    else:
        print(json.dumps({"error": "Usage: return_engine.py '<json>' | --file inputs.json"}))
        sys.exit(1)

    try:
        print(json.dumps(compute_return(data), indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
