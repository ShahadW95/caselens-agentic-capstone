---
document_id: KB_CASE001_06_VICTIM_RECOVERY_EDITORIAL
title: Victim Recovery and Editorial Policy
case_id: US_SDNY_09CR00213_DC
source_type: TEAM_DIGEST_RECOVERY_EDITORIAL
source_tier: A
jurisdiction: United States adversarial common-law system; federal criminal proceeding in S.D.N.Y.
case_status: CLOSED_CRIMINAL_GUILTY_PLEA
version: 0.1.0
effective_or_published_date: 2026-08-26
last_reviewed: 2026-08-26
original_source_urls:
  - https://www.sipc.org/news-and-media/news-releases/20180705
  - https://www.sipc.org/news-and-media/news-releases/20260227
  - https://www.justice.gov/archives/opa/pr/justice-departments-10th-distribution-brings-total-provided-over-43b-nearly-full-recovery
classification: PUBLIC
---

## The numerical trap

Two figures are widely repeated for this case and must never be presented as
interchangeable:

- **~USD 65 billion** — `AmountKind: FICTITIOUS_STATEMENT_BALANCE`. This is the aggregate
  paper value reported on fabricated BLMIS client account statements, not cash placed with
  Madoff and not a single verified loss amount [SRC_DOJ_SDNY_CASEPAGE] [SRC_FBI_HISTORY].
- **~USD 17.5 billion** — `AmountKind: ESTIMATED_PRINCIPAL_LOSS`. This is SIPC's estimate
  of actual principal lost by customers who filed claims, net of withdrawals, as reported
  2018-07-05 [SRC_SIPC_2018_RELEASE].

**Editorial rule:** every dollar figure presented for this case must state its
`AmountKind`, its as-of date, and its source_id(s). The ~65B and ~17.5B figures must never
be presented as interchangeable or as measuring the same thing.

## Recovery and distribution status

- SIPC has continued distributions to customers with allowed claims; the most recent
  distribution update in this pack is dated 2026-02-27 [SRC_SIPC_2026_DISTRIBUTION].
- The DOJ Madoff Victim Fund has distributed over USD 4.3 billion to victims across
  multiple rounds [SRC_DOJ_VICTIM_FUND].

**Editorial rule:** every `RECOVERY` and `DISTRIBUTION` figure needs its own `AmountKind`
and as-of date; it must never be combined with `FICTITIOUS_STATEMENT_BALANCE` or
`ESTIMATED_PRINCIPAL_LOSS` figures without an explicit measurement-basis explanation.

`SIPA_LIQUIDATION` and `DOJ_VICTIM_FUND` status must stay independent from `CRIMINAL_CASE`
status. Ongoing recovery or distribution activity must never imply that guilt or the
sentence is still being litigated; the criminal case is closed
[SRC_DOJ_SDNY_CASEPAGE] [SRC_SIPC_2026_DISTRIBUTION] [SRC_DOJ_VICTIM_FUND].

## Content exclusion policy

- **Tier D** sources (commentary, creator video, forum, social media) are excluded from
  the core RAG corpus entirely.
- **Tier C** sources (reputable journalism) may be used only as explicitly labeled
  reporting context, never as the sole ground for a fact, legal conclusion, or financial
  figure.
- Dramatizations, podcasts, unsourced biographies, social-media theories, personality
  diagnosis, and sensational victim stories are excluded from this case pack, per
  `source_manifest.json`'s `excluded_categories`.
