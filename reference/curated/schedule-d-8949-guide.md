# Schedule D + Form 8949 — Capital Gains, Losses, and the QDCG Tax Worksheet

## Source
- Instructions for Schedule D (Form 1040) (2025), Dec 11, 2025 — local copy at `reference/Raw/i1040sd.pdf` (16 pp.) — PRIMARY
- Schedule D (Form 1040) (2025) — the form itself; local copy at `reference/Raw/f1040sd.pdf` (downloaded from IRS.gov/pub/irs-pdf, 2 pp.)
- Form 8949 (2025) — local copy at `reference/Raw/f8949.pdf` (2 pp.)
- Form 1040 Instructions (2025) — local copy at `reference/Raw/i1040gi.pdf` — Line 7 (pp. 31–33), Line 16 (p. 36), QDCG Tax Worksheet (p. 38)
- Rev. Proc. 2024-40 §2.03 — 0%/15%/20% thresholds, already curated in `2025-tax-numbers.md` (cross-reference only)

## Applicable To
- **Forms:** Form 8949; Schedule D; Form 1040 lines 3a, 7a, 7b, 16
- **Workflow Steps:** Step 2 (Investment Income), Step 7 (Tax Computation)
- **Cross-references:** `investment-income.md` (1099-B/1099-DIV box mapping, wash sale rule, qualified dividend holding period, Georgia treatment); `2025-tax-numbers.md` (QDCG rate thresholds); `k1-guide.md` (K-1 capital gains feeding lines 5/12)

---

## Rules

### 1. Form 8949 Categories and When Form 8949 Can Be Skipped

#### Category boxes (from 1099-B "basis reported" status)
Check exactly one box per Form 8949 page; use a separate page for each applicable box. [Form 8949 (2025), Pages 1–2]

| Term | Box | 1099-B status | Totals flow to Schedule D |
|------|-----|---------------|---------------------------|
| Short | A | Basis **reported** to IRS | Line 1b |
| Short | B | Basis **not reported** to IRS | Line 2 |
| Short | C | Transaction **not on a 1099-B** | Line 3 |
| Long | D | Basis **reported** to IRS | Line 8b |
| Long | E | Basis **not reported** to IRS | Line 9 |
| Long | F | Transaction **not on a 1099-B** | Line 10 |

[Form 8949 (2025), Pages 1–2; Schedule D (Form 1040) (2025), Page 1]

- New for 2025: boxes G/H/I (short) and J/K/L (long) are the parallel categories for **digital asset** transactions reported on Form 1099-DA. [Form 8949 (2025), Pages 1–2; Schedule D Instructions (2025), Page 1 "What's New"]
- Short-term = held 1 year or less; long-term = held more than 1 year. [Schedule D Instructions (2025), Page 2]

#### When Form 8949 can be SKIPPED (direct-to-Schedule-D lines 1a/8a)
Exact rule: "You can report on line 1a (for short-term transactions) or line 8a (for long-term transactions) the aggregate totals from any transactions (except sales of collectibles) for which: You received a Form 1099-B or Form 1099-DA (or substitute statement) that shows basis was reported to the IRS and doesn't show any adjustments in box 1f or 1g (Form 1099-B)...; the Ordinary box in box 2 on Form 1099-B isn't checked; ... the QOF box in box 3 on Form 1099-B isn't checked; ... You aren't electing to defer income due to an investment in a QOF and aren't terminating deferral from an investment in a QOF; and You don't need to make any adjustments to the basis or type of gain or loss reported on Form 1099-B... or to your gain or loss." [Schedule D Instructions (2025), Page 10, "Lines 1a and 8a—Transactions Not Reported on Form 8949"]
- Form 8949 itself repeats this: aggregate Box A/D-type transactions "showing basis was reported to the IRS and for which no adjustments or codes are required" may go directly on Schedule D line 1a/8a; "you aren't required to report these transactions on Form 8949." [Form 8949 (2025), Pages 1–2, Note]
- If you choose lines 1a/8a, don't also report those transactions on Form 8949, no explanatory statement is needed, and no Form 8453 is needed when e-filing. [Schedule D Instructions (2025), Page 10]
- Multiple qualifying transactions are combined into one aggregate total per line (sum of proceeds, sum of basis, net gain/loss). [Schedule D Instructions (2025), Pages 10–11, Example 1]
- **Engine rule:** covered lots (Box A/D) with any 1099-B wash-sale or other adjustment must go on Form 8949 (lines 1b/8b), not 1a/8a. If broker basis is wrong, report on Form 8949 with a column (g) correction — never on 1a/8a. [Schedule D Instructions (2025), Page 11, Example 3]

#### Form 8949 column (h) math
Gain/(loss) = column (d) proceeds − column (e) basis, combined with any column (g) adjustment (code in column (f)). [Schedule D Instructions (2025), Page 11, "Lines 1b, 2, 3, 8b, 9, and 10, Column (h)"]

#### Schedule D without Form 8949 (Exception 2 — relevant for K-1 filers)
You must file Schedule D but generally don't have to file Form 8949 if Exception 1 (see §6) doesn't apply, no QOF deferral/termination is involved, and your only capital gains and losses are: capital gain distributions; a capital loss carryover from 2024; gains from Form 2439 or 6252 or Part I of Form 4797; gains/losses from Form 4684, 6781, or 8824; **gains/losses from a partnership, S corporation, estate, or trust (K-1s)**; and 1099-B/1099-DA transactions with basis reported to the IRS, no QOF box checked, and no column (f)/(g) adjustments needed. [Form 1040 Instructions (2025), Pages 31, 33, Exception 2]
- Engine mapping: K-1 net short-term gains → Schedule D line 5; K-1 net long-term gains → line 12 (see `k1-guide.md`); neither touches Form 8949.

### 2. Schedule D Line Map

| Line | Contents | Cite (all Schedule D (Form 1040) (2025)) |
|------|----------|------------------------------------------|
| 1a | Aggregate short-term covered (basis reported, no adjustments); skip 8949 | Page 1 |
| 1b | Form 8949 totals, Box A or G | Page 1 |
| 2 | Form 8949 totals, Box B or H | Page 1 |
| 3 | Form 8949 totals, Box C or I | Page 1 |
| 4 | Short-term gain from 6252; gain/(loss) from 4684, 6781, 8824 | Page 1 |
| 5 | Net short-term gain/(loss) from partnerships, S corps, estates, trusts (K-1s) | Page 1 |
| 6 | **Short-term capital loss carryover** from line 8 of the Capital Loss Carryover Worksheet — form pre-prints parentheses: enter as a **negative** amount | Page 1 |
| 7 | Net short-term gain/(loss): combine lines 1a–6, column (h) | Page 1 |
| 8a | Aggregate long-term covered (basis reported, no adjustments); skip 8949 | Page 1 |
| 8b | Form 8949 totals, Box D or J | Page 1 |
| 9 | Form 8949 totals, Box E or K | Page 1 |
| 10 | Form 8949 totals, Box F or L | Page 1 |
| 11 | Gain from 4797 Part I; long-term gain from 2439 and 6252; gain/(loss) from 4684, 6781, 8824 | Page 1 |
| 12 | Net long-term gain/(loss) from partnerships, S corps, estates, trusts (K-1s) | Page 1 |
| 13 | Capital gain distributions (1099-DIV box 2a total, regardless of holding period) | Page 1; Schedule D Instructions (2025), Page 2 |
| 14 | **Long-term capital loss carryover** from line 13 of the Capital Loss Carryover Worksheet — parentheses: enter as a **negative** amount | Page 1 |
| 15 | Net long-term gain/(loss): combine lines 8a–14, column (h) | Page 1 |
| 16 | Combine lines 7 and 15 | Page 2 |

#### Line 16 → 22 branch logic (verbatim structure from the form)
- **Line 16 is a gain** → enter it on Form 1040 line **7a**, then go to line 17. **Line 16 is a loss** → skip lines 17–20, go to line 21, and also complete line 22. **Line 16 is zero** → skip lines 17–21, enter -0- on Form 1040 line 7a, go to line 22. [Schedule D (Form 1040) (2025), Page 2, Line 16]
- **Line 17:** "Are lines 15 and 16 both gains?" Yes → line 18. No → skip lines 18–21, go to line 22. [Schedule D (Form 1040) (2025), Page 2]
- **Line 18:** amount from line 7 of the **28% Rate Gain Worksheet**, required only if line 17 = Yes and you reported a section 1202 (QSB) exclusion or a collectibles gain/(loss) in Part II of Form 8949. [Schedule D (Form 1040) (2025), Page 2; Schedule D Instructions (2025), Page 11, Line 18]
- **Line 19:** amount from line 18 of the **Unrecaptured Section 1250 Gain Worksheet**, required only if line 17 = Yes and any trigger applies: disposed of depreciated real property (section 1250) held >1 year; installment payments for such property; a K-1, 1099-DIV, or 2439 reporting "unrecaptured section 1250 gain"; or long-term gain on a partnership interest attributable to section 1250 property. [Schedule D (Form 1040) (2025), Page 2; Schedule D Instructions (2025), Pages 11–12, Line 19]
- **Line 20:** "Are lines 18 and 19 both zero or blank and you are not filing Form 4952?" **Yes** → use the **QDCG Tax Worksheet** (1040 line 16 instructions); don't complete lines 21–22. **No** → use the **Schedule D Tax Worksheet** in the Schedule D instructions; don't complete lines 21–22. [Schedule D (Form 1040) (2025), Page 2]
- **Line 21 ($3,000 loss limit):** if line 16 is a loss, enter on line 21 and Form 1040 line 7a the **smaller** of the loss on line 16 or **$3,000 ($1,500 if MFS)** — "When figuring which amount is smaller, treat both amounts as positive numbers" (entered as a negative). [Schedule D (Form 1040) (2025), Page 2; Schedule D Instructions (2025), Page 3, "Capital Losses"]
- **Line 22:** "Do you have qualified dividends on Form 1040 ... line 3a?" Yes → complete the QDCG Tax Worksheet. No → just complete the rest of Form 1040 (ordinary tax). [Schedule D (Form 1040) (2025), Page 2]

### 3. Capital Loss Carryover Worksheet (Lines 6 and 14)

Use only if the prior-year (2024) Schedule D line 21 is a loss AND either (a) that loss is smaller than the loss on 2024 Schedule D line 16, or (b) 2024 Form 1040 line 15 (taxable income) would be less than zero if negative amounts were allowed. Otherwise there is no carryover. [Schedule D Instructions (2025), Page 10, worksheet header]

Worksheet steps (prior year = 2024 feeding 2025): [Schedule D Instructions (2025), Page 10]
1. 2024 Form 1040 line 15 (taxable income; may be treated as negative in parentheses).
2. Loss from 2024 Schedule D line 21, **as a positive amount**.
3. Combine lines 1 and 2; if zero or less, enter -0-.
4. Smaller of line 2 or line 3. (If 2024 Schedule D line 7 is a loss, go to line 5; otherwise enter -0- on line 5 and go to line 9.)
5. Loss from 2024 Schedule D line 7, as a positive amount.
6. Gain, if any, from 2024 Schedule D line 15 (if a loss, enter -0-).
7. Add lines 4 and 6.
8. **Short-term carryover = line 5 − line 7** (floor 0) → this year's Schedule D **line 6**. (If 2024 Schedule D line 15 is a loss, go to line 9; otherwise skip 9–13.)
9. Loss from 2024 Schedule D line 15, as a positive amount.
10. Gain, if any, from 2024 Schedule D line 7 (if a loss, enter -0-).
11. Line 4 − line 5 (floor 0).
12. Add lines 10 and 11.
13. **Long-term carryover = line 9 − line 12** (floor 0) → this year's Schedule D **line 14**.

- Same computation produces the 2025→2026 carryover using this year's lines 7/15/21 in the 2026 worksheet. You have a carryover if line 16 is a loss and either that loss exceeds the line 21 loss, or Form 1040 line 15 would be below zero. [Schedule D Instructions (2025), Page 14, Line 21]
- MFS after a joint year: a carryover from the joint return belongs only to the spouse who actually had the loss. [Schedule D Instructions (2025), Page 10]
- Excess losses carry forward indefinitely; report all gains/losses even if the loss can't all be used this year. [Schedule D Instructions (2025), Page 3, "Capital Losses"]

### 4. Qualified Dividends and Capital Gain Tax Worksheet (Form 1040, Line 16)

Located on **page 38** of the Form 1040 Instructions (2025). Before starting: complete Form 1040 through line 15; if no Schedule D and you have capital gain distributions, check the box on line 7b. [Form 1040 Instructions (2025), Page 38]

All 25 lines (ignoring the Form 2555 foreign-earned-income footnotes, which don't apply):
1. Form 1040 line 15 (taxable income).
2. Form 1040 line 3a (qualified dividends).
3. Filing Schedule D? **Yes** → smaller of Schedule D line 15 or line 16; if either is blank or a loss, enter -0-. **No** → Form 1040 line **7a** (capital gain distributions).
4. Line 2 + line 3.
5. Line 1 − line 4 (floor 0). [ordinary-rate income]
6. 0% threshold: $48,350 single/MFS; **$96,700 MFJ/QSS**; $64,750 HoH. *(= Rev. Proc. 2024-40 §2.03; see `2025-tax-numbers.md`.)*
7. Smaller of line 1 or line 6.
8. Smaller of line 5 or line 7.
9. Line 7 − line 8. **Taxed at 0%.**
10. Smaller of line 1 or line 4.
11. Amount from line 9.
12. Line 10 − line 11.
13. 15% threshold: $533,400 single; $300,000 MFS; **$600,050 MFJ/QSS**; $566,700 HoH. *(= Rev. Proc. 2024-40 §2.03; see `2025-tax-numbers.md`.)*
14. Smaller of line 1 or line 13.
15. Line 5 + line 9.
16. Line 14 − line 15 (floor 0).
17. Smaller of line 12 or line 16.
18. Line 17 × **15%**.
19. Line 9 + line 17.
20. Line 10 − line 19.
21. Line 20 × **20%**.
22. Tax on line 5 (Tax Table if < $100,000; Tax Computation Worksheet if ≥ $100,000).
23. Line 18 + line 21 + line 22.
24. Tax on line 1 (Tax Table / Tax Computation Worksheet, same $100,000 split).
25. **Tax = smaller of line 23 or line 24** → Form 1040 line 16.

[Form 1040 Instructions (2025), Page 38, "Qualified Dividends and Capital Gain Tax Worksheet—Line 16"]

#### Engine invariants (derived directly from the worksheet arithmetic above)
- Preferential-rate income (line 10) = 0% bucket (line 9) + 15% bucket (line 17) + 20% bucket (line 20), since line 20 = line 10 − line 9 − line 17.
- Line 4 (qualified dividends + net LTCG) may exceed line 1 when ordinary income is negative; the line 5 floor and line 10 cap handle this — implement the floors/caps exactly, don't shortcut.
- The line 25 smaller-of guarantees the worksheet never yields more tax than ordinary rates on all income.

### 5. When the QDCG Worksheet Does NOT Apply — Engine BLOCK Conditions

Use the **Schedule D Tax Worksheet** instead of the QDCG worksheet if: you must file Schedule D and line 18 or 19 of Schedule D is more than zero while lines 15 and 16 are gains; **or** you file Form 4952 with an amount on line 4g, even if Schedule D isn't needed. [Form 1040 Instructions (2025), Page 36; Schedule D Instructions (2025), Page 15]
- Don't use the QDCG worksheet or the Schedule D Tax Worksheet at all if: Schedule D line 15 or 16 is zero or less **and** there are no qualified dividends on line 3a; or Form 1040 line 15 (taxable income) is zero or less. Tax is figured with the ordinary Tax Table/Tax Computation Worksheet per the line 16 instructions. [Schedule D Instructions (2025), Page 15, Exception]
- **Form 8615** (kiddie tax on unearned income over $2,700) preempts the normal line 16 methods. [Form 1040 Instructions (2025), Page 36]
- Other non-standard line 16 methods (Schedule J farm income averaging; Foreign Earned Income Tax Worksheet if filing Form 2555) also displace the QDCG worksheet. [Form 1040 Instructions (2025), Page 36]
- **Engine rule:** compute the QDCG worksheet only when Schedule D line 20 = Yes (lines 18 and 19 both zero/blank, no Form 4952) or the no-Schedule-D line 7a path applies. Any 28% rate gain, unrecaptured §1250 gain (e.g., 1099-DIV box 2b, K-1 §1250 statements), Form 4952, Form 8615, Schedule J, or Form 2555 condition → **BLOCK to the accountant**.

#### Schedule D Tax Worksheet — structure only (engine blocks; for audit context)
47-line worksheet at Schedule D Instructions (2025), Pages 15–16. Same 0%/15%/20% thresholds as the QDCG worksheet (its lines 15, 19, 26), plus two extra layers: unrecaptured §1250 gain taxed at **25%** (line 40 = line 39 × 0.25) and 28% rate gain taxed at **28%** (line 43 = line 42 × 0.28). Final tax = smaller of the sum of the layered taxes (line 45) or ordinary tax on all taxable income (line 46), entered on line 47 → Form 1040 line 16. [Schedule D Instructions (2025), Pages 15–16, "Schedule D Tax Worksheet"]

#### 28% Rate Gain Worksheet — inputs (engine blocks if line 7 > 0)
Line 18's worksheet nets: collectibles gains/(losses) from Form 8949 Part II; positive add-back of §1202 exclusions (all of a 50% exclusion, 2/3 of a 60%, 1/3 of a 75%; nothing for 100%); collectibles gain from Forms 4684/6252/6781/8824, 1099-DIV box 2d, Form 2439 box 1d, and K-1s; **minus** long-term carryover (Schedule D line 14) and any net short-term loss (Schedule D line 7). If the combined result > 0 it goes on Schedule D line 18. [Schedule D Instructions (2025), Page 11, "28% Rate Gain Worksheet—Line 18"]

### 6. Capital Gain Distributions Without Schedule D (1040 Line 7a/7b Path)

- No Form 8949 or Schedule D required if not deferring gain in a QOF and both: (1) no capital losses, and the only capital gains are capital gain distributions from 1099-DIV box 2a; and (2) no 1099-DIV has an amount in box 2b (unrecaptured §1250), 2c (§1202), or 2d (collectibles 28%). [Form 1040 Instructions (2025), Page 31, Exception 1]
- If Exception 1 applies: enter total box 2a distributions on Form 1040 **line 7a** and check the "Schedule D not required" box on **line 7b**; then use the QDCG Tax Worksheet for line 16. [Form 1040 Instructions (2025), Page 33]
- 2025 form layout note: the old single "line 7" is now line 7a (amount) + line 7b (checkbox). [Form 1040 Instructions (2025), Pages 31, 33]
- **Any capital loss carryover from 2024 forces Schedule D** — a carryover is a capital loss, so Exception 1 fails (Schedule D may still be filed without Form 8949 under Exception 2). [Form 1040 Instructions (2025), Pages 31, 33, Exceptions 1–2]
- If Schedule D is filed, box 2a distributions go on Schedule D line 13. [Schedule D Instructions (2025), Page 2, "Capital Gain Distributions"]

### 7. Wash Sales and Qualified Dividend Caveat (Brief)

- Wash sale = loss sale with purchase of substantially identical stock/securities within 30 days before or after; loss disallowed; disallowed loss added to basis of the replacement (except IRA/Roth purchases). [Schedule D Instructions (2025), Page 5, "Wash Sales"]
- Reporting: on Form 8949 with code **"W"** in column (f) and the disallowed loss as a **positive** amount in column (g); 1099-B box 1g shows the broker-computed disallowed amount for covered securities. [Schedule D Instructions (2025), Page 5]
- **Engine rule:** treat broker-reported box 1g wash sale adjustments as given (code W passthrough); a wash-sale-adjusted lot can never use lines 1a/8a (it has an adjustment — see §1).
- Qualified dividends (line 3a) require the >60-day holding period within the 121-day window — see `investment-income.md` ("Qualified Dividends" rules, Pub 550 cite). Engine takes 1099-DIV box 1b as given.
- Wash sale mechanics and Georgia treatment of investment income: see `investment-income.md`.

---

## Your Situation Notes

<!-- Add notes specific to your filing situation here.
     Example: "Broker 1099-B shows $X of box 1g wash sale adjustments — those lots
     must go on Form 8949 (Box A/D with code W), not on lines 1a/8a."
     See reference/HOW-TO-CURATE.md for the recommended format. -->
