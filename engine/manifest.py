"""
manifest.py — The return manifest: every computed line carries its value,
its source (input or computation), and its citation to reference/curated/
(Rule 1). Lines the engine cannot compute with a citation become BLOCKED
items or MISSING inputs — the engine never estimates (Rule 2).
"""

from decimal import Decimal

from engine.tax_math import cents


class Manifest:
    def __init__(self, tax_year, filing_status):
        self.tax_year = tax_year
        self.filing_status = filing_status
        self.forms = {}          # form -> {line_key: {value, source, citation}}
        self.blocked = []        # [{form, item, reason, citation}]
        self.missing = []        # [{field, needed_for, why, citation}]
        self.notes = []

    def put(self, form, line, value, source, citation):
        """Record a computed line. value: Decimal (stored as str) or bool/str."""
        if isinstance(value, Decimal):
            value = str(cents(value))
        self.forms.setdefault(form, {})[line] = {
            "value": value, "source": source, "citation": citation,
        }

    def get(self, form, line, default=Decimal("0")):
        entry = self.forms.get(form, {}).get(line)
        if entry is None:
            return default
        try:
            return Decimal(entry["value"])
        except Exception:
            return default

    def block(self, form, item, reason, citation):
        self.blocked.append({
            "form": form, "item": item, "reason": reason, "citation": citation,
        })

    def need(self, field, needed_for, why, citation=""):
        self.missing.append({
            "field": field, "needed_for": needed_for, "why": why,
            "citation": citation,
        })

    def note(self, text):
        self.notes.append(text)

    def to_dict(self):
        return {
            "tax_year": self.tax_year,
            "filing_status": self.filing_status,
            "forms": self.forms,
            "blocked_for_accountant": self.blocked,
            "missing_inputs": self.missing,
            "notes": self.notes,
        }
