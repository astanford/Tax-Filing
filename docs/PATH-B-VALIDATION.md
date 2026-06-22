# Path B Validation Findings

*Date: 2026-06-22*

Validation of Claude Fable's prior-year ingestion artifacts before building
the `ingest/` subsystem. Verdicts: **GO** (sound as-is), **FIX** (gap found
and corrected here), **NO-GO** (needs redesign). All test fixtures use
fabricated data per Rule 4.

## PII firewall — `validate_prior_year.py` (`pii_scan`)

**Verdict:** GO

Covered by `tests/test_pii_firewall.py`: clean data passes; dashed SSNs,
bare 9+ digit account-like integers, long digit runs, every blocked key
fragment, and array-nested PII are all rejected; legitimate money strings
are not false-flagged.
