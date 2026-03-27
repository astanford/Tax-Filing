# Retirement and HSA Contribution Limits (2025)

## Source
- IRS Notice 2024-80, "2025 Limitations Adjusted as Provided in Section 415(d), etc." (Oct 2024)
- IRS Revenue Procedure 2024-25, "HSA Inflation Adjusted Amounts for 2025" (May 2024)
- IRC §401(a)(17), §402(g), §414(v), §408(a), §408A, §219(g), §223
- Form 1040 Instructions (2025), Schedule 1 Lines 20, 13 (IRA deduction, HSA deduction)
- Publication 590-A (2025), "Contributions to Individual Retirement Arrangements"
- Publication 969 (2025), "Health Savings Accounts and Other Tax-Favored Health Plans"

**Verification note:** Raw source PDFs for IRS Notice 2024-80 and Revenue Procedure 2024-25 are not in `reference/Raw/`. All limits below should be verified against IRS.gov before relying on them.

## Applicable To
- **Forms:** Schedule 1 (Lines 13, 20); Form 8889; Form 8606; Form 5498
- **Workflow Steps:** `/tax-advisor` what-if scenarios (retirement, HSA contributions)

---

## Rules

### 401(k) / 403(b) / 457(b) Employee Contributions

| Parameter | 2025 Value | Citation |
|-----------|-----------|---------|
| Employee elective deferral limit | **$23,500** | [IRS Notice 2024-80, §II.A; IRC §402(g)] |
| Catch-up contribution (age 50+) | **$7,500** | [IRS Notice 2024-80, §II.B; IRC §414(v)] |
| Enhanced catch-up (age 60–63) | **$11,250** | [IRS Notice 2024-80, §II.B; SECURE 2.0 Act §109] |
| Total annual additions (employee + employer) | **$70,000** | [IRS Notice 2024-80, §II.C; IRC §415(c)] |

- Pre-tax 401(k) contributions reduce W-2 Box 1 (wages) but do **NOT** reduce W-2 Box 5 (Medicare wages). [IRC §3121(a)(5)]
- Roth 401(k) contributions do NOT reduce W-2 Box 1 — they are after-tax.
- Employer matching contributions do not count toward the $23,500 employee limit but do count toward the $70,000 total limit.

### Traditional IRA

| Parameter | 2025 Value | Citation |
|-----------|-----------|---------|
| Contribution limit (under age 50) | **$7,000** | [IRS Notice 2024-80, §III; IRC §219(b)] |
| Contribution limit (age 50+) | **$8,000** | [IRS Notice 2024-80, §III; IRC §219(b)(5)] |

#### Deductibility Phase-Out (Covered by Employer Retirement Plan)

If the taxpayer (or spouse) is an **active participant** in an employer plan (W-2 Box 13 "Retirement plan" checked), the traditional IRA deduction phases out:

| Filing Status | Full Deduction Below | Phase-Out Range | No Deduction Above | Citation |
|--------------|---------------------|-----------------|-------------------|---------|
| Single / HoH | $79,000 MAGI | $79,000–$89,000 | $89,000 | [IRS Notice 2024-80, §III.B] |
| MFJ (contributing spouse covered) | $126,000 MAGI | $126,000–$146,000 | $146,000 | [IRS Notice 2024-80, §III.B] |
| MFJ (contributing spouse NOT covered, other spouse IS) | $236,000 MAGI | $236,000–$246,000 | $246,000 | [IRS Notice 2024-80, §III.B] |
| MFS | $0 MAGI | $0–$10,000 | $10,000 | [IRC §219(g)(7)] |

- If NEITHER spouse is covered by an employer plan, the full IRA deduction is available at any income level.
- Non-deductible contributions are still allowed (reported on Form 8606). These can be used for a "backdoor Roth" conversion.

### Roth IRA

| Parameter | 2025 Value | Citation |
|-----------|-----------|---------|
| Contribution limit (under age 50) | **$7,000** | [IRC §408A(c)(2)] |
| Contribution limit (age 50+) | **$8,000** | [IRC §408A(c)(3)] |

#### Income Phase-Out for Direct Contributions

| Filing Status | Full Contribution Below | Phase-Out Range | No Contribution Above | Citation |
|--------------|------------------------|-----------------|----------------------|---------|
| MFJ | $236,000 MAGI | $236,000–$246,000 | $246,000 | [IRS Notice 2024-80, §III.C] |
| Single / HoH | $150,000 MAGI | $150,000–$165,000 | $165,000 | [IRS Notice 2024-80, §III.C] |
| MFS | $0 MAGI | $0–$10,000 | $10,000 | [IRC §408A(c)(3)(B)] |

- **Backdoor Roth:** Non-deductible traditional IRA contribution + Roth conversion is available at any income level. Not a deduction — does not reduce AGI or tax liability in the contribution year.

### Health Savings Account (HSA)

| Parameter | 2025 Value | Citation |
|-----------|-----------|---------|
| Self-only coverage | **$4,300** | [Revenue Procedure 2024-25; IRC §223(b)] |
| Family coverage | **$8,550** | [Revenue Procedure 2024-25; IRC §223(b)] |
| Catch-up (age 55+) | **$1,000** | [IRC §223(b)(3)] |
| HDHP minimum deductible (self-only) | $1,650 | [Revenue Procedure 2024-25] |
| HDHP minimum deductible (family) | $3,300 | [Revenue Procedure 2024-25] |
| HDHP out-of-pocket max (self-only) | $8,300 | [Revenue Procedure 2024-25] |
| HDHP out-of-pocket max (family) | $16,600 | [Revenue Procedure 2024-25] |

- HSA contributions are deductible on Schedule 1, Line 13 — reduces AGI.
- Contributions via payroll reduce both W-2 Box 1 AND Box 5 (Medicare wages). [IRC §3121(a)]
- Direct contributions reduce AGI but do NOT reduce Medicare wages.
- Must be enrolled in a qualifying High Deductible Health Plan (HDHP).
- No income limit or phase-out for HSA eligibility or deduction.

---

## Your Situation Notes

<!-- Add notes specific to your filing situation here.
     Example: "Our AGI is ~$X, which means [phase-out/threshold] applies."
     See reference/HOW-TO-CURATE.md for the recommended format. -->

