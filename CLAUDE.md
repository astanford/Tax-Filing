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