# Contributing

Tax Filing Skills is maintained by Daisy. Contributions are welcome — typo fixes, bug fixes, new curated reference files, and new skills. One thing to know up front: this repo treats tax accuracy as non-negotiable. Every rule must cite an IRS or state source, and all arithmetic runs through Python scripts. If you're on board with that, read on.

## Before You Contribute

Please skim these first so we're speaking the same language:

- [README.md](README.md) — what the skills do and how the pipeline fits together
- [CLAUDE.md](CLAUDE.md) — the five project rules (also copied below)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — how skills, scripts, and references interact
- [reference/HOW-TO-CURATE.md](reference/HOW-TO-CURATE.md) — required reading for anyone touching tax rules
- [docs/KNOWN-PITFALLS.md](docs/KNOWN-PITFALLS.md) — common filing mistakes we already account for

## What We're Looking For

In rough order of "easiest to land" to "needs discussion first":

- **Typos, broken links, doc fixes** — open a PR directly.
- **Bug fixes in existing Python scripts** — open a PR with a short before/after example showing the bad output and the corrected output.
- **New curated reference files** (e.g. another state, a new form, a new deduction) — open an issue first so we can confirm scope and citation sources.
- **New skills** — open an issue first. New skills must follow the conventions below and fit the existing pipeline.
- **Tax-year updates (2026 and beyond)** — coordinate via issue so thresholds stay consistent across all 13 curated files.

## What We're NOT Looking For

- Tax advice or interpretations not backed by an IRS or state citation
- LLM-generated rule summaries or arithmetic without a source
- Personal tax data, real SSNs, real account numbers, or anything that looks like it came from `my-tax-docs/`
- Changes that modify the four core skills' behavior without an issue discussion first
- Dependencies beyond the Python standard library — scripts are intentionally zero-dep

## The Five Project Rules

Copied verbatim from [CLAUDE.md](CLAUDE.md) so you see them without a second click:

1. Every tax rule must cite a file in `reference/curated/`
2. If unverifiable: "I cannot verify this — check IRS.gov"
3. All math via Python scripts — no LLM arithmetic
4. No personal information stored in skill files
5. Forms must leave SSN, bank, and signature fields blank

These rules apply to every contribution. If your change can't satisfy them, it probably belongs in a fork rather than this repo.

## Adding a New Skill

- **Location:** `.claude/skills/{skill-name}/SKILL.md`
- **Naming:** kebab-case. The skill name in frontmatter must match the directory name.
- **Required frontmatter:**
  ```yaml
  ---
  name: skill-name
  description: One-paragraph summary of what the skill does. Triggers on: 'phrase1', 'phrase2', 'phrase3'.
  ---
  ```
- **Session handoff pattern:** follow what the existing skills do — check for `analysis/tax-doc-summary.csv`, report status, ask the user for the next step, and stop early if the CSV is missing and your skill needs it.
- **Disclaimer:** any user-facing output must include the standard disclaimer (not tax advice, verify against source documents, etc.).
- **Scripts:** go in `.claude/skills/{skill-name}/scripts/`, snake_case filenames, JSON-in / JSON-out, `Decimal` for all money math. See [.claude/skills/tax-audit/scripts/cross_check.py](.claude/skills/tax-audit/scripts/cross_check.py) for the established pattern.

## Adding a Curated Reference File

[reference/HOW-TO-CURATE.md](reference/HOW-TO-CURATE.md) is the source of truth — read it before you start. The short version:

- File lives in `reference/curated/`, kebab-case filename (e.g. `california-540-guide.md`).
- Every fact needs an inline citation like `[Pub 936 (2025), Page 2]`, `[Schedule A Instructions (2025), Line 5e]`, or `[IRC §199A]`.
- If you can't cite it, don't include it.

## Adding or Fixing a Python Script

- **Input:** a single JSON string passed as `sys.argv[1]`.
- **Output:** JSON to stdout. Nothing else — no stray `print()` calls.
- **Arithmetic:** always `Decimal`, never `float`. Use the `d()` helper pattern from the existing scripts for safe conversion.
- **Dependencies:** Python standard library only. No pip installs.
- **Docstring:** include a usage example at the top so someone can copy-paste and run it.

## PR Checklist

Paste this into your PR description and tick what applies:

- [ ] One focused change per PR
- [ ] Any new tax rule cites a file in `reference/curated/`
- [ ] No personal data, real SSNs, or real account numbers anywhere in the diff
- [ ] Python scripts use `Decimal` and have no third-party dependencies
- [ ] New skills include frontmatter with `name` and `description`
- [ ] Standard disclaimer present in any user-facing output
- [ ] Tested against the sample data in `examples/` where applicable

## Reporting Bugs

Open a GitHub issue with:

- Which skill, script, or reference file is involved
- What you expected
- What actually happened
- A sanitized example (no real tax data — use round numbers or the fictional data from `examples/`)

If you think the bug is a tax-accuracy issue (wrong threshold, wrong formula, misread rule), cite the IRS or state source you believe is correct. That turns a report into a fix.

## Security and Privacy

If you find a bug that could leak personal tax data or expose files from `my-tax-docs/` or `analysis/`, please open a private security advisory on GitHub rather than a public issue.

## Recognition

Every contributor will be credited. This project exists to help individuals learn more about tax filing and do it themselves with confidence — it gets better when more people bring their situations, questions, and edge cases to it.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
