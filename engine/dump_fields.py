"""
dump_fields.py — Helper for curating field maps: lists a PDF's text fields
sorted by page and position, and can fill every field with a sentinel that
encodes its own name so a rendered page reveals the field↔line mapping.

Run with the repo venv:
    .venv/bin/python engine/dump_fields.py reference/Raw/f1040s1.pdf            # list
    .venv/bin/python engine/dump_fields.py reference/Raw/f1040s1.pdf out.pdf    # sentinel fill

Then: pdftoppm -png -r 100 out.pdf page && read the page images to see which
sentinel landed on which printed line. Record the mapping in
engine/field_maps/<form>.json (see f1040.json for the format).
"""

import sys

from pypdf import PdfReader, PdfWriter


def list_fields(path):
    r = PdfReader(path)
    rows = []
    for pnum, page in enumerate(r.pages):
        annots = page.get("/Annots")
        if not annots:
            continue
        for a in annots.get_object():
            o = a.get_object()
            if str(o.get("/FT")) == "/Tx":
                rect = [round(float(x)) for x in o["/Rect"]]
                rows.append((pnum + 1, -rect[1], rect[0], str(o.get("/T"))))
    rows.sort()
    for page, ny, x, name in rows:
        print(f"page {page}  y={-ny:4d}  x={x:4d}  {name}")
    return [r[3] for r in rows]


def sentinel_fill(path, out_path):
    names = list_fields(path)
    w = PdfWriter(clone_from=path)
    updates = {}
    for name in names:
        digits = "".join(c for c in name if c.isdigit())[:4]
        updates[name] = digits or name[:6]
    for p in w.pages:
        w.update_page_form_field_values(p, updates)
    with open(out_path, "wb") as fh:
        w.write(fh)
    print(f"\nsentinel-filled -> {out_path} (value = digits of the field name)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if len(sys.argv) >= 3:
        sentinel_fill(sys.argv[1], sys.argv[2])
    else:
        list_fields(sys.argv[1])
