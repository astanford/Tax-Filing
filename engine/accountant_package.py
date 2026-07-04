"""
accountant_package.py — Generate the accountant review memo from a return
manifest: positions taken, every BLOCKED item, simplifications, citations,
and a prior-year comparison when carryover data is present.

Usage:
    python engine/accountant_package.py '{"manifest_path": "analysis/return-manifest.json", "carryovers_path": "analysis/prior-year-carryovers-2024.json", "out_path": "output/accountant-package.md"}'
"""

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.tax_math import d

KEY_LINES = [
    ("Form 1040", "line_9_total_income", "Total income"),
    ("Form 1040", "line_11_agi", "AGI"),
    ("Form 1040", "line_12_deduction", "Deduction"),
    ("Form 1040", "line_15_taxable_income", "Taxable income"),
    ("Form 1040", "line_16_tax", "Tax (QDCG worksheet)"),
    ("Form 1040", "line_23_other_taxes", "Other taxes (SE/8959/8960)"),
    ("Form 1040", "line_24_total_tax", "Total tax"),
    ("Form 1040", "line_33_total_payments", "Total payments"),
    ("GA Form 500", "line_15c_ga_taxable_income", "GA taxable income"),
    ("GA Form 500", "line_22_tax_after_credits", "GA tax after credits"),
]

PRIOR_MAP = {
    "AGI": "agi_line_11",
    "Taxable income": "taxable_income_line_15",
    "Total tax": "total_tax_line_24",
}


def build(data):
    manifest = json.loads(Path(data["manifest_path"]).read_text())
    prior = {}
    cp = data.get("carryovers_path")
    if cp and Path(cp).exists():
        prior = json.loads(Path(cp).read_text()).get("federal", {})

    lines = [
        f"# Accountant Review Package — Tax Year {manifest['tax_year']}",
        "",
        f"Filing status: **{manifest['filing_status']}**. Prepared with the "
        "Tax-Filing engine: every computed line cites a curated IRS/GA "
        "reference; anything the engine could not compute with a citation is "
        "listed under *Items for your review* — those are yours, not ours.",
        "",
        "Identity fields (SSN, bank, signature) are intentionally blank on "
        "all attached forms.",
        "",
        "## Key results" ,
        "",
        "| Line | Amount | Prior year | Source |",
        "|---|---|---|---|",
    ]
    for form, key, label in KEY_LINES:
        entry = manifest["forms"].get(form, {}).get(key)
        if not entry:
            continue
        prior_val = prior.get(PRIOR_MAP.get(label, ""), "")
        lines.append(f"| {label} | {entry['value']} | {prior_val} | {entry['citation']} |")

    lines += ["", "## Items for your review (engine-blocked)", ""]
    if manifest.get("blocked_for_accountant"):
        for b in manifest["blocked_for_accountant"]:
            lines.append(f"- **{b['form']} — {b['item']}**: {b['reason']} "
                         f"*(ref: {b['citation']})*")
    else:
        lines.append("- None — every in-scope item computed cleanly.")

    lines += ["", "## Disclosed simplifications and notes", ""]
    for n in manifest.get("notes", []):
        lines.append(f"- {n}")

    lines += ["", "## Line-by-line citations", ""]
    for form, entries in manifest["forms"].items():
        lines.append(f"### {form}")
        lines.append("| Line | Value | Source | Citation |")
        lines.append("|---|---|---|---|")
        for key, e in entries.items():
            lines.append(f"| {key} | {e['value']} | {e['source']} | {e['citation']} |")
        lines.append("")

    lines += [
        "---",
        "*These materials assist with tax return preparation and do not "
        "constitute tax advice. Please verify all values against source "
        "documents.*",
    ]

    out = "\n".join(lines)
    out_path = data.get("out_path")
    if out_path:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(out)
        return {"written_to": str(p), "blocked_items": len(manifest.get("blocked_for_accountant", []))}
    return {"markdown": out}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": 'Usage: accountant_package.py \'{"manifest_path": ...}\''}))
        sys.exit(1)
    print(json.dumps(build(json.loads(sys.argv[1])), indent=2))


if __name__ == "__main__":
    main()
