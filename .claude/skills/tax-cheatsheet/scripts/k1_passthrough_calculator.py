"""
k1_passthrough_calculator.py — Schedule E Part II/III (K-1 passthrough)
computation with the loss-limitation cascade, plus a COMBINED Form 8582
covering Part I rentals and passthrough rows together.

Limitation ordering per the K-1 instructions (Source:
passthrough-loss-limitations.md, The Four Hurdles):
    1. Basis      — §704(d) partners / §1366(d) S-corp shareholders
    2. At-risk    — §465, Form 6198
    3. Passive    — §469, Form 8582 (PTPs are NEVER on Form 8582 —
                    per-PTP suspension, Source: passthrough-loss-limitations.md, PTP Special Regime)
    4. Excess business loss (§461(l)) — NOT computed here; flagged when
       relevant for accountant review.

Usage:
    python k1_passthrough_calculator.py '{"tax_year": 2025, "filing_status": "MFJ", "magi": "150000", "entities": [{"name": "Acme Partners LP", "entity_type": "partnership", "is_ptp": false, "materially_participates": false, "k1": {"box1_ordinary_business": "-12000"}, "basis_available": "20000", "at_risk_available": "20000", "carryovers": {"basis_carryforward_704d_1366d": "0", "at_risk_carryforward_465": "0", "suspended_passive_loss_form_8582": "0"}}], "part1_buckets": {"rental_activity_income": "0", "rental_activity_losses": "2099", "nonrental_passive_income": "0", "nonrental_passive_losses": "0", "prior_suspended": "0"}, "active_participation": true}'

Inputs per entity:
  - entity_type: "partnership" | "s_corp" | "estate_trust"
  - is_ptp: publicly traded partnership flag (per-PTP netting regime)
  - materially_participates: drives passive vs nonpassive (Source:
    passthrough-loss-limitations.md, Hurdle 3 — Passive Activity Limitation)
  - active_participation_rental: for K-1 box 2 rental RE, allowance
    eligibility (rare for limited partners)
  - k1: current-year amounts. box1_ordinary_business, box2_net_rental_re,
    box4_guaranteed_payments (1065), box14a_se_earnings (1065),
    section_179, qbi_income (box 20Z / 17V / 14I), portfolio boxes
    (interest/dividends) are informational passthroughs to Schedule B.
  - basis_available / at_risk_available: current capacity BEFORE this
    year's losses (from Form 7203 / partner basis worksheet). If omitted
    (null) for a loss entity, the limitation CANNOT be applied — the entity
    is BLOCKED with a note instead of guessing.
  - carryovers: prior-year amounts, keys matching
    prior-year-carryovers-template.json (basis_carryforward_704d_1366d,
    at_risk_carryforward_465, suspended_passive_loss_form_8582,
    qbi_passthrough_form_8995).

Outputs: per-entity cascade detail, Schedule E Part II lines 28-32 and
Part III lines 33-37 (Source: k1-guide.md, Schedule E Part II), the
combined Form 8582, SE-earnings total, QBI summary, and next-year
carryovers in the prior-year schema's key names.

Simplifications disclosed in notes: basis/at-risk applied to the entity's
combined loss (box 1 + box 2 pro-rata, per the allocation rule in the K-1
instructions); suspended passive losses allocated pro-rata across loss
activities; §461(l) excess business loss not computed (flagged);
Form 8995 QBI income limits not applied here (engine's job).

All arithmetic uses Decimal — no float math (per CLAUDE.md rules).
"""

import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

# Shared constants live at the repo root (engine/constants_2025.py).
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


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


ZERO = Decimal("0")

# $25,000 special allowance parameters — same table as
# schedule_e_calculator.py (Source: passive-activity-losses.md,
# Special $25,000 Allowance)
ALLOWANCE_MAX = Decimal("25000")
ALLOWANCE_PHASEOUT_START = Decimal("100000")
ALLOWANCE_PHASEOUT_END = Decimal("150000")
ALLOWANCE_MAX_MFS_APART = Decimal("12500")
ALLOWANCE_PHASEOUT_START_MFS_APART = Decimal("50000")
ALLOWANCE_PHASEOUT_END_MFS_APART = Decimal("75000")
ALLOWANCE_PHASEOUT_RATE = Decimal("0.50")

ENTITY_TYPES = ("partnership", "s_corp", "estate_trust")


def compute_allowance(magi, filing_status, active_participation,
                      mfs_lived_apart_all_year, notes):
    """$25,000 special allowance with 50% phase-out from $100K to $150K MAGI.
    (Source: passive-activity-losses.md, Special $25,000 Allowance)"""
    if not active_participation:
        return ZERO
    max_allowance = ALLOWANCE_MAX
    start = ALLOWANCE_PHASEOUT_START
    end = ALLOWANCE_PHASEOUT_END
    if filing_status == "MFS":
        if not mfs_lived_apart_all_year:
            notes.append("MFS living with spouse: special allowance is $0. (Source: passive-activity-losses.md)")
            return ZERO
        max_allowance = ALLOWANCE_MAX_MFS_APART
        start = ALLOWANCE_PHASEOUT_START_MFS_APART
        end = ALLOWANCE_PHASEOUT_END_MFS_APART
    if magi <= start:
        return max_allowance
    if magi >= end:
        return ZERO
    return cents(max(ZERO, max_allowance - ALLOWANCE_PHASEOUT_RATE * (magi - start)))


def cascade_entity(ent, notes):
    """Run one entity's current-year loss through basis → at-risk.

    Returns a dict with the post-at-risk loss (ready for the passive step),
    income amounts, new basis/at-risk carryforwards, and flags.
    (Source: passthrough-loss-limitations.md, The Four Hurdles)
    """
    name = ent.get("name", "entity")
    entity_type = ent.get("entity_type", "partnership")
    k1 = ent.get("k1", {}) or {}
    co = ent.get("carryovers", {}) or {}

    box1 = d(k1.get("box1_ordinary_business"))
    box2 = d(k1.get("box2_net_rental_re"))
    guaranteed = d(k1.get("box4_guaranteed_payments"))
    sec179 = d(k1.get("section_179"))

    basis_cf = d(co.get("basis_carryforward_704d_1366d"))
    at_risk_cf = d(co.get("at_risk_carryforward_465"))

    # Income items pass straight through (no loss limits on income).
    # Guaranteed payments are always nonpassive ordinary income (1065 only).
    income_items = max(box1, ZERO) + max(box2, ZERO)

    # Current-year loss subject to the cascade: negative box 1/2 plus §179
    # (a deduction, so it consumes basis/at-risk like a loss), plus prior
    # basis-suspended losses (they re-test against basis each year).
    current_loss = max(-box1, ZERO) + max(-box2, ZERO) + max(sec179, ZERO)
    loss_before_basis = current_loss + basis_cf

    result = {
        "name": name,
        "entity_type": entity_type,
        "is_ptp": bool(ent.get("is_ptp", False)),
        "materially_participates": bool(ent.get("materially_participates", False)),
        "active_participation_rental": bool(ent.get("active_participation_rental", False)),
        "income_items": income_items,
        "guaranteed_payments": guaranteed,
        "box1": box1,
        "box2": box2,
        "sec179": sec179,
        "blocked": False,
        "basis_computation_required": False,
        "not_at_risk_box": False,
    }

    if loss_before_basis == ZERO:
        result.update(loss_after_at_risk=ZERO,
                      new_basis_cf=ZERO, new_at_risk_cf=at_risk_cf)
        return result

    # --- 1. Basis limitation (§704(d) / §1366(d)) ---
    basis_available = ent.get("basis_available", None)
    if basis_available is None:
        result["blocked"] = True
        notes.append(
            f"{name}: reports a loss but no basis_available provided — basis "
            f"limitation (§704(d)/§1366(d)) cannot be applied. Provide basis "
            f"(Form 7203 for S corps / partner basis worksheet) or flag for "
            f"the accountant. (Source: passthrough-loss-limitations.md, Hurdle 1 — Basis Limitation)"
        )
        result.update(loss_after_at_risk=ZERO,
                      new_basis_cf=loss_before_basis, new_at_risk_cf=at_risk_cf)
        return result

    basis_available = d(basis_available)
    allowed_by_basis = min(loss_before_basis, max(basis_available, ZERO))
    new_basis_cf = loss_before_basis - allowed_by_basis
    if entity_type == "s_corp":
        # Form 7203 attaches whenever a loss is claimed or the basis box
        # applies. (Source: k1-guide.md, Form 7203)
        result["basis_computation_required"] = True
    if new_basis_cf > ZERO:
        notes.append(
            f"{name}: {fmt(new_basis_cf)} suspended by the basis limitation — "
            f"carries forward indefinitely at the entity level. "
            f"(Source: passthrough-loss-limitations.md, Hurdle 1 — Basis Limitation)"
        )

    # --- 2. At-risk limitation (§465, Form 6198) ---
    loss_before_at_risk = allowed_by_basis + at_risk_cf
    at_risk_available = ent.get("at_risk_available", None)
    if at_risk_available is None:
        # Common case: at-risk equals basis when there are no nonrecourse
        # amounts; but we do not assume — require the input for loss entities.
        result["blocked"] = True
        notes.append(
            f"{name}: reports a loss but no at_risk_available provided — "
            f"at-risk limitation (§465/Form 6198) cannot be applied. "
            f"(Source: passthrough-loss-limitations.md, Hurdle 2 — At-Risk Limitation)"
        )
        result.update(loss_after_at_risk=ZERO,
                      new_basis_cf=new_basis_cf, new_at_risk_cf=loss_before_at_risk)
        return result

    at_risk_available = d(at_risk_available)
    allowed_at_risk = min(loss_before_at_risk, max(at_risk_available, ZERO))
    new_at_risk_cf = loss_before_at_risk - allowed_at_risk
    if new_at_risk_cf > ZERO:
        result["not_at_risk_box"] = True   # Line 28 column (f); Form 6198 attaches
        notes.append(
            f"{name}: {fmt(new_at_risk_cf)} suspended by the at-risk limitation "
            f"(Form 6198 required; check Line 28 column (f)). "
            f"(Source: passthrough-loss-limitations.md, Hurdle 2 — At-Risk Limitation)"
        )

    # Share of the allowed loss attributable to §179 (pro-rata through the
    # cascade, per the allocation rule in the K-1 instructions) — used to
    # split Line 28 columns (i) and (j) for nonpassive entities.
    sec179_allowed = ZERO
    if loss_before_basis > ZERO and sec179 > ZERO:
        sec179_allowed = cents(allowed_at_risk * (sec179 / loss_before_basis))

    result.update(loss_after_at_risk=allowed_at_risk,
                  sec179_allowed=sec179_allowed,
                  new_basis_cf=new_basis_cf, new_at_risk_cf=new_at_risk_cf)
    return result


def compute(data):
    tax_year = int(data.get("tax_year", 2025))
    filing_status = data.get("filing_status", "MFJ")
    magi = d(data.get("magi"))
    active_participation = bool(data.get("active_participation", True))
    mfs_apart = bool(data.get("mfs_lived_apart_all_year", False))
    entities = data.get("entities", [])
    part1 = data.get("part1_buckets", {}) or {}

    if not entities:
        return {"error": "No entities provided"}

    notes = []
    unknown = [e.get("entity_type") for e in entities
               if e.get("entity_type", "partnership") not in ENTITY_TYPES]
    if unknown:
        return {"error": f"Unknown entity_type(s) {unknown} — use partnership, s_corp, or estate_trust"}

    # --- Per-entity basis → at-risk cascade ---
    cascaded = [cascade_entity(e, notes) for e in entities]

    # --- 3. Passive limitation: build the COMBINED Form 8582 ---
    # Bucket 1 (allowance-eligible): Part I rentals w/ active participation
    # + K-1 box 2 rental RE with active participation.
    # Bucket 2 (no allowance): all other passive activities.
    # PTPs: excluded from Form 8582 entirely — per-PTP netting.
    # (Source: passive-activity-losses.md, Form 8582 Flow;
    #  passthrough-loss-limitations.md, PTP Special Regime)
    b1_income = d(part1.get("rental_activity_income"))
    b1_loss = d(part1.get("rental_activity_losses")) + d(part1.get("prior_suspended"))
    b2_income = d(part1.get("nonrental_passive_income"))
    b2_loss = d(part1.get("nonrental_passive_losses"))

    ptp_results = []
    passive_rows = []   # (entity_index, bucket, income, loss) for allocation

    for i, c in enumerate(cascaded):
        suspended_cf = d((entities[i].get("carryovers") or {}).get("suspended_passive_loss_form_8582"))
        if c["is_ptp"]:
            # Per-PTP regime: income nets against same-PTP current +
            # suspended losses; net loss carries forward per PTP.
            income = c["income_items"]
            loss = c["loss_after_at_risk"] + suspended_cf
            allowed = min(income, loss)
            net_income = income - allowed
            new_cf = loss - allowed
            ptp_results.append({
                "name": c["name"],
                "ptp_income_reported": str(cents(net_income)),
                "ptp_loss_allowed": str(cents(allowed)),
                "suspended_passive_loss_form_8582": str(cents(new_cf)),
            })
            if new_cf > ZERO:
                notes.append(
                    f"{c['name']}: PTP loss {fmt(new_cf)} suspended — usable only "
                    f"against this PTP's future income or on complete disposition; "
                    f"NEVER entered on Form 8582. (Source: passthrough-loss-limitations.md, PTP Special Regime)"
                )
            # Part II shows the FULL income (col h) and the allowed loss
            # (col g) — they net on line 32. The ptp summary block reports
            # the net income for planning use.
            c["passive_loss_allowed"] = allowed
            c["passive_income_reported"] = income
            c["new_suspended_cf"] = new_cf
            continue

        if c["materially_participates"]:
            # Nonpassive: loss fully deductible after basis/at-risk (§461(l)
            # screen is the engine's job); suspended passive cf from prior
            # years would only exist if participation changed — flag it.
            if suspended_cf > ZERO:
                notes.append(
                    f"{c['name']}: has a prior suspended PASSIVE loss but is "
                    f"materially participating this year — former-passive-activity "
                    f"rules apply; flag for accountant. (Source: passthrough-loss-limitations.md)"
                )
            c["nonpassive"] = True
            c["new_suspended_cf"] = suspended_cf
            continue

        c["nonpassive"] = False
        # Rental RE (box 2) with active participation joins bucket 1;
        # everything else passive joins bucket 2.
        loss = c["loss_after_at_risk"] + suspended_cf
        income = c["income_items"]
        if c["box2"] != ZERO and c["active_participation_rental"]:
            bucket = 1
            b1_income += income
            b1_loss += loss
        else:
            bucket = 2
            b2_income += income
            b2_loss += loss
        passive_rows.append({"idx": i, "bucket": bucket,
                             "income": income, "loss": loss})

    # Form 8582 lines (Source: passive-activity-losses.md, Part II Line 4):
    # 1d = b1 net; 2d = b2 net; 3 = 1d + 2d.
    line_1d = b1_income - b1_loss
    line_2d = b2_income - b2_loss
    line_3 = line_1d + line_2d

    allowance = compute_allowance(magi, filing_status, active_participation,
                                  mfs_apart, notes)
    total_passive_income = b1_income + b2_income
    total_passive_loss = b1_loss + b2_loss

    if line_3 >= ZERO or total_passive_loss == ZERO:
        allowed_loss_total = total_passive_loss
        allowed_by_allowance = ZERO
        suspended_total = ZERO
    else:
        absorbed = min(total_passive_income, total_passive_loss)
        remaining = total_passive_loss - absorbed
        # Line 4 = smaller of the line 1d loss or the line 3 loss
        line_4 = min(max(-line_1d, ZERO), max(-line_3, ZERO))
        allowed_by_allowance = min(line_4, allowance)
        suspended_total = remaining - allowed_by_allowance
        allowed_loss_total = absorbed + allowed_by_allowance

    # Allocate suspension pro-rata across passive loss positions (the real
    # form allocates per-activity in Parts IV-IX — pro-rata disclosed as a
    # simplification).
    for r in passive_rows:
        c = cascaded[r["idx"]]
        if suspended_total > ZERO and total_passive_loss > ZERO:
            share = r["loss"] / total_passive_loss
            entity_suspended = cents(suspended_total * share)
        else:
            entity_suspended = ZERO
        c["new_suspended_cf"] = entity_suspended
        c["passive_loss_allowed"] = r["loss"] - entity_suspended
        c["passive_income_reported"] = r["income"]

    part1_share_suspended = ZERO
    part1_total_loss_in = d(part1.get("rental_activity_losses")) + d(part1.get("prior_suspended")) + d(part1.get("nonrental_passive_losses"))
    if suspended_total > ZERO and total_passive_loss > ZERO and part1_total_loss_in > ZERO:
        part1_share_suspended = cents(suspended_total * (part1_total_loss_in / total_passive_loss))

    # --- Schedule E Part II / III lines ---
    part2_rows, part3_rows = [], []
    total_h = total_k = total_g = total_i = total_j = ZERO   # Part II cols
    total_d3 = total_f3 = total_c3 = total_e3 = ZERO          # Part III cols

    for c in cascaded:
        if c["blocked"]:
            continue
        is_trust = c["entity_type"] == "estate_trust"
        if c.get("nonpassive"):
            # §179 reports in column (j), the rest of the loss in column (i)
            sec179_allowed = c.get("sec179_allowed", ZERO)
            nonpassive_loss = c["loss_after_at_risk"] - sec179_allowed
            nonpassive_income = c["income_items"] + c["guaranteed_payments"]
            passive_loss_allowed = ZERO
            passive_income = ZERO
        else:
            sec179_allowed = ZERO
            nonpassive_loss = ZERO
            nonpassive_income = c["guaranteed_payments"]
            passive_loss_allowed = c.get("passive_loss_allowed", ZERO)
            passive_income = c.get("passive_income_reported", ZERO)

        if is_trust:
            row = {
                "line_33a_name": c["name"],
                "col_c_passive_loss_allowed": str(cents(passive_loss_allowed)),
                "col_d_passive_income": str(cents(passive_income)),
                "col_e_nonpassive_loss": str(cents(nonpassive_loss)),
                "col_f_other_income": str(cents(nonpassive_income)),
            }
            part3_rows.append(row)
            total_c3 += passive_loss_allowed
            total_d3 += passive_income
            total_e3 += nonpassive_loss
            total_f3 += nonpassive_income
        else:
            row = {
                "line_28a_name": c["name"],
                "col_b_type": "P" if c["entity_type"] == "partnership" else "S",
                "col_e_basis_computation_required": c["basis_computation_required"],
                "col_f_not_at_risk": c["not_at_risk_box"],
                "col_g_passive_loss_allowed": str(cents(passive_loss_allowed)),
                "col_h_passive_income": str(cents(passive_income)),
                "col_i_nonpassive_loss": str(cents(nonpassive_loss)),
                "col_j_section_179": str(cents(sec179_allowed)),
                "col_k_nonpassive_income": str(cents(nonpassive_income)),
            }
            part2_rows.append(row)
            total_g += passive_loss_allowed
            total_h += passive_income
            total_i += nonpassive_loss
            total_j += d(row["col_j_section_179"])
            total_k += nonpassive_income

    line_30 = total_h + total_k
    line_31 = total_g + total_i + total_j
    line_32 = line_30 - line_31
    line_35 = total_d3 + total_f3
    line_36 = total_c3 + total_e3
    line_37 = line_35 - line_36

    # --- SE earnings + QBI passthroughs (informational) ---
    se_earnings = sum(d((e.get("k1") or {}).get("box14a_se_earnings")) for e in entities)
    if se_earnings > ZERO:
        notes.append(
            f"Total K-1 box 14A self-employment earnings {fmt(se_earnings)} — "
            f"flows to Schedule SE. (Source: k1-guide.md, Box 14)"
        )
    qbi_items = []
    for i, e in enumerate(entities):
        qbi = d((e.get("k1") or {}).get("qbi_income"))
        if qbi != ZERO:
            c = cascaded[i]
            limited = c["blocked"] or c["new_basis_cf"] > ZERO or \
                c["new_at_risk_cf"] > ZERO or d(str(c.get("new_suspended_cf", 0))) > ZERO
            qbi_items.append({
                "name": c["name"],
                "qbi_reported_box_20z_17v": str(cents(qbi)),
                "loss_limited": bool(limited),
            })
            if limited and qbi < ZERO:
                notes.append(
                    f"{c['name']}: QBI loss is limited by basis/at-risk/passive "
                    f"suspension — only the ALLOWED portion enters Form 8995; "
                    f"flag for the engine/accountant. "
                    f"(Source: passthrough-loss-limitations.md, QBI Interaction)"
                )

    # §461(l) screen: flag when combined allowed business losses are large.
    notes.append(
        "Excess business loss (§461(l)/Form 461) is NOT computed here — the "
        "engine screens it after aggregation. (Source: passthrough-loss-limitations.md, The Four Hurdles)"
    )

    # --- Next-year carryovers (prior-year schema keys) ---
    carryovers_out = []
    for i, c in enumerate(cascaded):
        carryovers_out.append({
            "entity_label": c["name"],
            "entity_type": c["entity_type"],
            "is_ptp": c["is_ptp"],
            "basis_carryforward_704d_1366d": str(cents(c["new_basis_cf"])),
            "at_risk_carryforward_465": str(cents(c["new_at_risk_cf"])),
            "suspended_passive_loss_form_8582": str(cents(d(str(c.get("new_suspended_cf", 0))))),
        })

    blocked = [c["name"] for c in cascaded if c["blocked"]]

    return {
        "schedule_e_part_2": {
            "rows": part2_rows,
            "line_30_income_cols_h_k": str(cents(line_30)),
            "line_31_loss_cols_g_i_j": str(cents(line_31)),
            "line_32_total": str(cents(line_32)),
        },
        "schedule_e_part_3": {
            "rows": part3_rows,
            "line_35_income": str(cents(line_35)),
            "line_36_loss": str(cents(line_36)),
            "line_37_total": str(cents(line_37)),
        },
        "combined_form_8582": {
            "line_1d_rental_net": str(cents(line_1d)),
            "line_2d_other_passive_net": str(cents(line_2d)),
            "line_3_total": str(cents(line_3)),
            "special_allowance_available": str(cents(allowance)),
            "allowed_by_allowance": str(cents(allowed_by_allowance)),
            "allowed_loss_total": str(cents(allowed_loss_total)),
            "suspended_total": str(cents(suspended_total)),
            "part1_rentals_share_of_suspended": str(cents(part1_share_suspended)),
        },
        "ptp": ptp_results,
        "se_earnings_box_14a_total": str(cents(se_earnings)),
        "qbi_passthrough": qbi_items,
        "next_year_carryovers_passthrough": carryovers_out,
        "blocked_entities": blocked,
        "flows_to": "Line 41 = Part I Line 26 + Line 32 + Line 37 -> Schedule 1 Line 5",
        "notes": notes,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": 'Usage: k1_passthrough_calculator.py \'{"tax_year": 2025, "filing_status": "MFJ", "magi": "...", "entities": [...]}\''
        }))
        sys.exit(1)

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    try:
        result = compute(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
