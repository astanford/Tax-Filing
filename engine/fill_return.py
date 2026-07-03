"""
fill_return.py — Fill official form PDFs from a return manifest using
curated field maps, with a mandatory read-back diff.

Run with the repo venv (pypdf lives there, quarantined per
engine/requirements.txt):
    .venv/bin/python engine/fill_return.py '{"manifest_path": "analysis/return-manifest.json", "forms": ["f1040"], "out_dir": "output"}'

Field maps: engine/field_maps/<form>.json —
    {"source_pdf": "reference/Raw/f1040.pdf",
     "fields": [{"pdf_field": "topmostSubform[0].Page1[0].f1_54[0]",
                 "manifest_form": "Form 1040", "manifest_line": "line_9_total_income",
                 "format": "whole"}, ...]}
Maps are curated by visual verification (fill sentinels -> render -> eyeball);
see engine/dump_fields.py and the /tax-return skill.

Rule 5 hard guard: any PDF field whose name or partial value suggests SSN,
signature, bank routing/account, or PIN is NEVER written, regardless of map
content. Output PDFs go to the gitignored output/ directory.
"""

import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from pypdf import PdfReader, PdfWriter

_REPO_ROOT = Path(__file__).resolve().parents[1]

SENSITIVE = re.compile(r"ssn|social|signat|routing|account.?num|bank|pin|phone",
                       re.IGNORECASE)


def load_manifest(path):
    return json.loads(Path(path).read_text())


def fmt_value(raw, style):
    if raw is None:
        return ""
    if isinstance(raw, bool):
        return raw
    try:
        val = Decimal(str(raw))
    except Exception:
        return str(raw)
    if style == "whole":
        return f"{val.quantize(Decimal('1'), rounding=ROUND_HALF_UP):,}"
    return f"{val:,.2f}"


def fill_form(form_key, manifest, out_dir):
    map_path = _REPO_ROOT / "engine" / "field_maps" / f"{form_key}.json"
    if not map_path.exists():
        return {"form": form_key, "error": f"No field map at {map_path} — "
                "curate one with engine/dump_fields.py + visual verification"}
    fmap = json.loads(map_path.read_text())
    reader = PdfReader(str(_REPO_ROOT / fmap["source_pdf"]))
    writer = PdfWriter(clone_from=str(_REPO_ROOT / fmap["source_pdf"]))

    filled, skipped_sensitive, missing = [], [], []
    updates = {}
    for spec in fmap["fields"]:
        pdf_field = spec["pdf_field"]
        if SENSITIVE.search(pdf_field) or SENSITIVE.search(spec.get("label", "")):
            skipped_sensitive.append(pdf_field)
            continue
        entry = manifest["forms"].get(spec["manifest_form"], {}).get(spec["manifest_line"])
        if entry is None:
            missing.append(f"{spec['manifest_form']}.{spec['manifest_line']}")
            continue
        value = fmt_value(entry["value"], spec.get("format", "whole"))
        updates[pdf_field.split(".")[-1]] = value
        filled.append({"pdf_field": pdf_field,
                       "manifest_line": f"{spec['manifest_form']}.{spec['manifest_line']}",
                       "value": str(value)})

    for page in writer.pages:
        writer.update_page_form_field_values(page, updates)

    out_path = Path(out_dir) / f"{form_key}-filled.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as fh:
        writer.write(fh)

    # --- Read-back diff: re-open the written PDF and compare every field ---
    verify = PdfReader(str(out_path))
    actual = {k.split(".")[-1]: (v.get("/V") if v else None)
              for k, v in (verify.get_fields() or {}).items()}
    mismatches = []
    for f in filled:
        short = f["pdf_field"].split(".")[-1]
        got = str(actual.get(short) or "")
        if isinstance(f["value"], str) and got != f["value"]:
            mismatches.append({"field": short, "wrote": f["value"], "read_back": got})

    return {
        "form": form_key,
        "written_to": str(out_path),
        "fields_filled": len(filled),
        "read_back_mismatches": mismatches,
        "sensitive_fields_skipped": skipped_sensitive,
        "manifest_lines_missing": missing,
        "note": "SSN, bank, and signature fields are never written (Rule 5).",
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": 'Usage: fill_return.py \'{"manifest_path": ..., "forms": [...], "out_dir": "output"}\''}))
        sys.exit(1)
    data = json.loads(sys.argv[1])
    manifest = load_manifest(data["manifest_path"])
    out_dir = data.get("out_dir", "output")
    results = [fill_form(f, manifest, out_dir) for f in data.get("forms", [])]
    print(json.dumps({"results": results}, indent=2))


if __name__ == "__main__":
    main()
