---
document_id: KB_CASE001_04_PLEA_CHARGES_SENTENCE
title: Guilty Plea, Charges, and Sentence
case_id: US_SDNY_09CR00213_DC
source_type: TEAM_DIGEST
source_tier: A
jurisdiction: United States adversarial common-law system; federal criminal proceeding in S.D.N.Y.
case_status: CLOSED_CRIMINAL_GUILTY_PLEA
version: 0.1.0
effective_or_published_date: 2026-08-26
last_reviewed: 2026-08-26
original_source_urls:
  - https://www.justice.gov/usao-sdny/programs/victim-witness-services/united-states-v-bernard-l-madoff-and-related-cases
classification: PUBLIC
---

## The plea

On 2009-03-12, Madoff pleaded guilty, without a plea agreement, to all 11 federal felony
counts charged against him [SRC_DOJ_SDNY_CASEPAGE]. There was no jury trial and no jury
verdict in this case — the case concluded by admission, not adjudication of contested
evidence [SRC_DOJ_SDNY_CASEPAGE].

## Why the product's internal `EXPLAIN_VERDICT` mode is labeled "Explain the Judgment"

Because there was no jury verdict, the UI-facing label for the internal `EXPLAIN_VERDICT`
mode is **"Explain the Judgment"**, not "Explain the Verdict." The Legal Explanation
Specialist must explain the charges, the guilty plea, and the court's sentencing judgment,
and must never invent or imply a jury verdict, trial testimony, or trial evidentiary
findings that did not occur.

## The sentence

On 2009-06-29, the court sentenced Madoff to 150 years in federal prison
[SRC_DOJ_SDNY_CASEPAGE].

## Three separate concepts: sentence, forfeiture, and victim recovery/distribution

These are three distinct concepts and three distinct `AmountKind`/proceeding contexts, and
must never be conflated:

1. **Sentence** — the criminal punishment (150 years' imprisonment) imposed as part of the
   closed `CRIMINAL_CASE` [SRC_DOJ_SDNY_CASEPAGE]. This is not a monetary amount.
2. **Forfeiture order** (`AmountKind: FORFEITURE_ORDER`) — a court-ordered surrender of
   assets tied to the criminal case, distinct from any later recovery or distribution
   figure.
3. **Victim recovery / distribution** (`AmountKind: RECOVERY` / `DISTRIBUTION`) — funds
   returned to victims through the separate `SIPA_LIQUIDATION` and `DOJ_VICTIM_FUND`
   proceedings, which are ongoing as of the source-pack cutoff and carry their own as-of
   dates [SRC_SIPC_2026_DISTRIBUTION] [SRC_DOJ_VICTIM_FUND].

## Guidance for the Legal Explanation Specialist

- Never predict an alternate outcome, alternate sentence, or alternate verdict; the guilty
  plea and 150-year sentence are the actual, final, closed-case outcome.
- Never conflate sentence, forfeiture order, and recovery/distribution figures, or present
  them as a single number.
- Always state which of the three concepts a given answer addresses.
