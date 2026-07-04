"""
income.py — Schedule B, Schedule D / Form 8949 aggregation, and the
Qualified Dividends and Capital Gain Tax Worksheet.

Sources: investment-income.md (Schedule B), schedule-d-8949-guide.md
(Schedule D line map, carryover worksheet, QDCG worksheet), 2025-tax-numbers.md
(QDCG thresholds via engine.constants_2025). The engine computes with a
citation or BLOCKs — never estimates (CLAUDE.md Rules 1-3).
"""

from decimal import Decimal

from engine.constants_2025 import (
    CAPITAL_LOSS_LIMIT,
    FEDERAL_BRACKETS,
    QDCG_THRESHOLDS,
    SCHEDULE_B_THRESHOLD,
)
from engine.tax_math import ZERO, cents, d, tax_from_table_or_schedule


def schedule_b(m, income):
    """Schedule B Parts I/II; required over $1,500 of interest or dividends.
    (Source: investment-income.md, Schedule B; 2025-tax-numbers.md)"""
    interest_items = income.get("interest", []) or []
    dividend_items = income.get("dividends_ordinary", []) or []
    total_interest = sum((d(i.get("amount")) for i in interest_items), ZERO)
    total_ordinary_div = sum((d(i.get("amount")) for i in dividend_items), ZERO)

    required = total_interest > SCHEDULE_B_THRESHOLD or total_ordinary_div > SCHEDULE_B_THRESHOLD
    m.put("Schedule B", "line_2_total_interest", total_interest,
          "sum of 1099-INT box 1", "investment-income.md, Interest Income")
    m.put("Schedule B", "line_4_taxable_interest", total_interest,
          "line 2 (no excludable savings-bond interest modeled)",
          "investment-income.md, Interest Income")
    m.put("Schedule B", "line_6_total_dividends", total_ordinary_div,
          "sum of 1099-DIV box 1a", "investment-income.md, Dividends")
    m.put("Schedule B", "schedule_b_required", required,
          f"interest or dividends > ${SCHEDULE_B_THRESHOLD}",
          "2025-tax-numbers.md, Other Key Federal Numbers")
    if required and not (interest_items and all(i.get("payer") for i in interest_items)):
        if total_interest > SCHEDULE_B_THRESHOLD:
            m.need("income.interest[].payer", "Schedule B Part I",
                   "Schedule B lists each payer by name",
                   "investment-income.md, Schedule B")
    return total_interest, total_ordinary_div


def schedule_d(m, income, carryovers, filing_status):
    """Schedule D from 1099-B category totals + carryovers.

    Category keys (from the 1099-B): short_a/short_b/short_c (8949 boxes
    A/B/C), long_d/long_e/long_f (boxes D/E/F), each
    {proceeds, basis, adjustments}. (Source: schedule-d-8949-guide.md,
    Form 8949 Categories and Schedule D Line Map)
    """
    b = income.get("form_1099b", {}) or {}
    cg_dist = d(income.get("capital_gain_distributions"))

    def net(cat):
        c = b.get(cat, {}) or {}
        return d(c.get("proceeds")) - d(c.get("basis")) + d(c.get("adjustments"))

    st_carry = d(carryovers.get("capital_loss_carryforward_short"))
    lt_carry = d(carryovers.get("capital_loss_carryforward_long"))

    line_1a = net("short_a")
    line_2 = net("short_b")
    line_3 = net("short_c")
    # K-1 capital gains skip Form 8949 entirely (Exception 2)
    line_5_k1 = d(income.get("k1_net_short_term_gain"))
    line_7 = line_1a + line_2 + line_3 + line_5_k1 - st_carry
    if line_5_k1 != ZERO:
        m.put("Schedule D", "line_5_k1_short_term", line_5_k1,
              "K-1 box 8 (1065) / box 7 (1120-S) / box 3 (1041)",
              "schedule-d-8949-guide.md, Schedule D without Form 8949; k1-guide.md")
    m.put("Schedule D", "line_1a_short_basis_reported", line_1a,
          "1099-B box A proceeds - basis + adjustments",
          "schedule-d-8949-guide.md, Schedule D Line Map")
    m.put("Schedule D", "line_6_st_carryover", -st_carry,
          "prior-year carryover (negative)",
          "schedule-d-8949-guide.md, Capital Loss Carryover Worksheet")
    m.put("Schedule D", "line_7_net_short_term", line_7,
          "lines 1a-3 + line 6", "schedule-d-8949-guide.md, Schedule D Line Map")

    line_8a = net("long_d")
    line_9 = net("long_e")
    line_10 = net("long_f")
    line_12_k1 = d(income.get("k1_net_long_term_gain"))
    line_13 = cg_dist
    line_15 = line_8a + line_9 + line_10 + line_12_k1 + line_13 - lt_carry
    if line_12_k1 != ZERO:
        m.put("Schedule D", "line_12_k1_long_term", line_12_k1,
              "K-1 box 9a (1065) / box 8a (1120-S) / box 4a (1041)",
              "schedule-d-8949-guide.md, Schedule D without Form 8949; k1-guide.md")
    m.put("Schedule D", "line_8a_long_basis_reported", line_8a,
          "1099-B box D proceeds - basis + adjustments",
          "schedule-d-8949-guide.md, Schedule D Line Map")
    m.put("Schedule D", "line_13_cap_gain_distributions", line_13,
          "1099-DIV box 2a", "schedule-d-8949-guide.md, Schedule D Line Map")
    m.put("Schedule D", "line_14_lt_carryover", -lt_carry,
          "prior-year carryover (negative)",
          "schedule-d-8949-guide.md, Capital Loss Carryover Worksheet")
    m.put("Schedule D", "line_15_net_long_term", line_15,
          "lines 8a-10 + 13 + 14", "schedule-d-8949-guide.md, Schedule D Line Map")

    line_16 = line_7 + line_15
    m.put("Schedule D", "line_16_total", line_16,
          "line 7 + line 15", "schedule-d-8949-guide.md, Schedule D Line Map")

    # 28% gain / unrecaptured 1250 route to the Schedule D Tax Worksheet —
    # out of engine scope, BLOCK.
    if d(income.get("collectibles_28_pct_gain")) != ZERO or \
            d(income.get("unrecaptured_1250_gain")) != ZERO:
        m.block("Schedule D", "lines 18/19 (28% gain / unrecaptured §1250)",
                "Schedule D Tax Worksheet required instead of the QDCG "
                "worksheet — accountant computes",
                "schedule-d-8949-guide.md, When the QDCG Worksheet Does Not Apply")

    # Loss limit (line 21)
    if line_16 < ZERO:
        limit = CAPITAL_LOSS_LIMIT["MFS"] if filing_status == "MFS" else CAPITAL_LOSS_LIMIT["default"]
        allowed_loss = min(-line_16, limit)
        m.put("Schedule D", "line_21_allowed_loss", -allowed_loss,
              f"smaller of the line 16 loss or ${limit}",
              "schedule-d-8949-guide.md, Loss Limit; 2025-tax-numbers.md")
        to_1040_line_7 = -allowed_loss
        # Next-year carryover (simplified worksheet: assumes taxable income
        # exceeds the allowed loss; the full worksheet adjusts when income
        # is very low — flag instead of guessing there).
        remaining = (-line_16) - allowed_loss
        st_loss = max(-line_7, ZERO)
        used_from_st = min(st_loss, allowed_loss)
        new_st_carry = max(st_loss - used_from_st - max(line_15, ZERO), ZERO)
        new_lt_carry = max(remaining - new_st_carry, ZERO)
        m.put("Schedule D", "next_year_carryover_short", new_st_carry,
              "Capital Loss Carryover Worksheet (short-term first)",
              "schedule-d-8949-guide.md, Capital Loss Carryover Worksheet")
        m.put("Schedule D", "next_year_carryover_long", new_lt_carry,
              "Capital Loss Carryover Worksheet",
              "schedule-d-8949-guide.md, Capital Loss Carryover Worksheet")
        m.note("Capital-loss carryover computed with the standard worksheet "
               "assuming taxable income exceeds the allowed loss; if taxable "
               "income is near zero, have the accountant re-run the worksheet.")
    else:
        to_1040_line_7 = line_16

    return to_1040_line_7, line_15, line_16


def qdcg_worksheet(m, taxable_income, qualified_dividends, sched_d_line_15,
                   sched_d_line_16, filing_status):
    """Qualified Dividends and Capital Gain Tax Worksheet — Form 1040
    line 16 tax when preferential rates apply.

    (Source: schedule-d-8949-guide.md, QDCG Tax Worksheet; thresholds:
    2025-tax-numbers.md, QDCG Tax Rates via engine.constants_2025)
    """
    thresholds = QDCG_THRESHOLDS[filing_status]
    brackets = FEDERAL_BRACKETS[filing_status]

    line_1 = max(taxable_income, ZERO)
    # Line 3: net capital gain = smaller of Sch D 15/16 (not below 0)
    net_cap_gain = max(min(sched_d_line_15, sched_d_line_16), ZERO)
    line_2 = max(qualified_dividends, ZERO)
    line_3 = line_2 + net_cap_gain
    line_4 = ZERO  # investment interest election (Form 4952) not modeled
    line_5 = max(line_3 - line_4, ZERO)
    line_6 = max(line_1 - line_5, ZERO)   # ordinary-rate income

    zero_max = thresholds["zero_max"]
    fifteen_max = thresholds["fifteen_max"]

    line_8 = min(line_1, zero_max)
    line_9 = min(line_6, line_8)
    line_10 = line_8 - line_9              # taxed at 0%
    line_11 = min(line_1, line_5)
    line_13 = line_11 - line_10
    line_14 = min(line_1, fifteen_max)
    line_15 = line_6 + line_10
    line_16 = max(line_14 - line_15, ZERO)
    line_17 = min(line_13, line_16)        # taxed at 15%
    line_18 = cents(line_17 * Decimal("0.15"))
    line_19 = line_10 + line_17
    line_20 = line_11 - line_19            # taxed at 20%
    line_21 = cents(line_20 * Decimal("0.20"))
    # Lines 22/24: Tax Table under $100K, Tax Computation Worksheet above
    line_22 = tax_from_table_or_schedule(line_6, brackets)
    line_23 = line_18 + line_21 + line_22
    line_24 = tax_from_table_or_schedule(line_1, brackets)
    tax = min(line_23, line_24)

    m.put("QDCG Worksheet", "preferential_income", line_5,
          "qualified dividends + net capital gain",
          "schedule-d-8949-guide.md, QDCG Tax Worksheet")
    m.put("QDCG Worksheet", "taxed_at_0pct", line_10,
          "worksheet line 10", "schedule-d-8949-guide.md, QDCG Tax Worksheet")
    m.put("QDCG Worksheet", "taxed_at_15pct", line_17,
          "worksheet line 17", "schedule-d-8949-guide.md, QDCG Tax Worksheet")
    m.put("QDCG Worksheet", "taxed_at_20pct", line_20,
          "worksheet line 20", "schedule-d-8949-guide.md, QDCG Tax Worksheet")
    m.put("QDCG Worksheet", "tax", tax,
          "smaller of worksheet tax or all-ordinary tax",
          "schedule-d-8949-guide.md, QDCG Tax Worksheet")
    return tax
