# Tax Filing Skills 2025

Skills for preparing, filing, and optimizing a U.S. federal (Form 1040) and
state tax return using Claude Code. Built for tax year 2025.

## Setup
1. Place your tax documents in the `my-tax-docs/` folder
2. Point Claude Code at this project
3. Start with /tax-prep to extract your document values
4. Use /tax-cheatsheet as you fill each form
5. Run /tax-audit before submitting
6. After filing, use /tax-advisor for next-year planning

## File Locations
| What | Where |
|------|-------|
| Curated IRS/GA references | reference/curated/ |
| Shared 2025 tax constants (single source for all scripts) | engine/constants_2025.py |
| Reference curation guide | reference/HOW-TO-CURATE.md |
| Known pitfalls | docs/KNOWN-PITFALLS.md |
| Example outputs | examples/ |
| Your tax documents | my-tax-docs/ (gitignored) |
| Prior-year returns (PDFs with PII) | my-tax-docs/prior-years/ (gitignored) |
| Generated analysis | analysis/ (gitignored) |
| Prior-year carryover data (no PII) | analysis/prior-year-carryovers-*.json (gitignored) — see docs/PRIOR-YEAR-DATA.md |

## Rules
1. Every tax rule must cite a file in reference/curated/
2. If unverifiable: "I cannot verify this — check IRS.gov"
3. All math via Python scripts — no LLM arithmetic
4. No personal information stored in skill files
5. Forms must leave SSN, bank, and signature fields blank

## Disclaimer
These skills assist with tax return preparation. They do not constitute tax advice. Verify all numbers against source documents. Consult a qualified tax professional for your specific situation.

## How Global Rules Map Here

The home-directory global instructions apply, with these repo-specific clarifications.
**Where anything below could conflict with the Rules section above, the Rules win.**

- **Local Rules are supreme.** Citation discipline (Rule 1), the unverifiable
  disclaimer (Rule 2), Python-only math (Rule 3), no PII in skill files (Rule 4),
  and blank SSN/bank/signature fields (Rule 5) override every global default and
  every clarification in this section. No global guidance relaxes them.
- **repo-analyst MCP: not used in this repo.** It is not registered in this
  environment, and the repo is small enough to Read directly. Ignore the global
  "prefer repo-analyst" mandate here.
- **"Tests" means the pytest suite in tests/.** Run `python -m pytest tests/`
  (CI runs it on every PR via .github/workflows/tests.yml). It covers the
  calculator scripts, cross-checks, the shared constants module
  (engine/constants_2025.py — bracket tables verified against
  reference/Raw/rp-24-40.pdf), and the prior-year PII validator. New or
  changed calculation logic needs tests validated against the source PDFs in
  reference/Raw/.
- **Web research feeds curated references — it does not replace them.** Looking up
  IRS/GA source material is allowed, but a tax rule becomes usable only by going
  through reference/HOW-TO-CURATE.md and citing a file in reference/curated/
  (Rule 1). If a number can't be traced to reference/curated/, say "I cannot
  verify this — check IRS.gov" (Rule 2). A live URL is never a substitute for a
  citation and never a side-channel around the curation process.
- **No LLM arithmetic, ever.** The global "act when allowed" default never
  authorizes computing a tax figure in prose. All math runs through a Python
  script (Rule 3), even for a single line.
- **PII safety is the dominant risk.** Beyond the global "destructive ops need
  confirmation," treat tax documents and prior-year returns as sensitive. The
  authoritative rules are docs/PRIVATE-DATA.md and docs/PRIOR-YEAR-DATA.md;
  never commit anything from my-tax-docs/ or analysis/.
- **gstack app-shipping skills are dormant here.** /ship, /canary, /qa, design
  reviews, etc. target deployable apps; this is a document/skill repo. /browse
  for web access still applies.
