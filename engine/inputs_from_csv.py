"""
inputs_from_csv.py — Best-effort builder: analysis/tax-doc-summary.csv +
analysis/prior-year-carryovers-<year>.json -> the return-engine input JSON.

Maps what the CSV can prove and lists everything else in "unmapped_rows" /
engine missing-inputs territory for the /tax-interview loop. Never guesses:
a value the CSV doesn't contain stays absent.

Usage:
    python engine/inputs_from_csv.py '{"csv_path": "analysis/tax-doc-summary.csv", "carryovers_path": "analysis/prior-year-carryovers-2024.json", "filing_status": "MFJ", "out_path": "analysis/return-inputs.json"}'
"""

import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.tax_math import ZERO, cents, d


def load_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build(data):
    csv_path = data.get("csv_path", "analysis/tax-doc-summary.csv")
    rows = load_rows(csv_path)
    filing_status = data.get("filing_status", "MFJ")

    inputs = {
        "tax_year": int(data.get("tax_year", 2025)),
        "filing_status": filing_status,
        "num_dependents": data.get("num_dependents", 0),
        "income": {"interest": [], "dividends_ordinary": []},
        "adjustments": {},
        "itemized": {},
        "qbi": {},
        "carryovers": {},
        "payments": {},
        "georgia": {},
    }
    used = set()
    inc = inputs["income"]

    def take(i):
        used.add(i)

    wages = fed_wh = ga_wh = medicare = ss_wages = ZERO
    qual_div = cg_dist = mortgage = re_tax = ZERO
    est_fed = est_ga = ZERO

    for i, row in enumerate(rows):
        doc = row.get("document", "")
        box = row.get("box_or_line", "")
        val = d(row.get("value"))
        dl = doc.lower()

        if dl.startswith("w-2"):
            if box == "Box 1":
                wages += val; take(i)
            elif box == "Box 2":
                fed_wh += val; take(i)
            elif box == "Box 4":
                take(i)  # SS tax withheld — informational
            elif box == "Box 3":
                ss_wages += val; take(i)
            elif box == "Box 5":
                medicare += val; take(i)
            elif box == "Box 17":
                ga_wh += val; take(i)
        elif "1099-int" in dl:
            if box == "Box 1":
                inc["interest"].append({"payer": doc, "amount": str(cents(val))}); take(i)
            elif box == "Box 4":
                fed_wh += val; take(i)
        elif "1099-div" in dl:
            if box == "Box 1a":
                inc["dividends_ordinary"].append({"payer": doc, "amount": str(cents(val))}); take(i)
            elif box == "Box 1b":
                qual_div += val; take(i)
            elif box == "Box 2a":
                cg_dist += val; take(i)
            elif box == "Box 4":
                fed_wh += val; take(i)
        elif "1098" in dl and "1098-e" not in dl and "1098-t" not in dl:
            if box == "Box 1":
                mortgage += val; take(i)
            elif box == "Box 4":
                re_tax += val; take(i)  # property tax if manager reports it there
        elif "1040-es" in dl or "estimated" in dl:
            if "georgia" in dl or "500-es" in dl or "ga " in dl:
                est_ga += val; take(i)
            else:
                est_fed += val; take(i)

    if wages:
        inc["wages"] = str(cents(wages))
        inc["medicare_wages"] = str(cents(medicare))
        inc["w2_ss_wages"] = str(cents(ss_wages))
    if qual_div:
        inc["dividends_qualified"] = str(cents(qual_div))
    if cg_dist:
        inc["capital_gain_distributions"] = str(cents(cg_dist))
    if mortgage:
        inputs["itemized"]["mortgage_interest"] = str(cents(mortgage))
    if re_tax:
        inputs["itemized"]["real_estate_tax"] = str(cents(re_tax))
    inputs["payments"]["federal_withholding"] = str(cents(fed_wh))
    inputs["payments"]["federal_estimated_payments"] = str(cents(est_fed))
    inputs["georgia"]["ga_withholding"] = str(cents(ga_wh))
    inputs["georgia"]["ga_estimated_payments"] = str(cents(est_ga))

    # Prior-year carryovers (validated by validate_prior_year.py)
    co_path = data.get("carryovers_path")
    if co_path and Path(co_path).exists():
        co = json.loads(Path(co_path).read_text())
        fed = co.get("federal", {}) or {}
        inputs["carryovers"]["qbi_carryforward_form_8995_line_16"] = \
            fed.get("qbi_carryforward_form_8995_line_16", "0")
        # The prior-year schema stores one combined number; the interview
        # splits it short/long if the prior Schedule D is available.
        inputs["carryovers"]["capital_loss_carryforward_combined"] = \
            fed.get("capital_loss_carryforward", "0")
        inputs["payments"]["prior_year_total_tax"] = fed.get("total_tax_line_24")
        inputs["payments"]["prior_year_agi"] = fed.get("agi_line_11")
        inputs["income"]["state_refund_candidate"] = \
            co.get("state_refund_received_during_current_year", "0")
        inputs["_prior_year_itemized"] = fed.get("itemized")

    unmapped = [
        {"row": i, "document": rows[i].get("document"),
         "box_or_line": rows[i].get("box_or_line"), "value": rows[i].get("value")}
        for i in range(len(rows)) if i not in used
    ]

    out_path = data.get("out_path")
    result = {"inputs": inputs, "unmapped_rows": unmapped,
              "mapped": len(used), "total_rows": len(rows)}
    if out_path:
        Path(out_path).write_text(json.dumps(inputs, indent=2))
        result["written_to"] = out_path
    return result


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": 'Usage: inputs_from_csv.py \'{"csv_path": ...}\''}))
        sys.exit(1)
    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)
    try:
        print(json.dumps(build(data), indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
