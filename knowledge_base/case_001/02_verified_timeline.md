---
document_id: KB_CASE001_02_TIMELINE
title: Verified Timeline
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
  - https://www.sec.gov/news/press/2008/2008-293.htm
  - https://www.sec.gov/news/press/2009/2009-243.htm
  - https://www.sec.gov/news/press/2009/2009-60.htm
  - https://www.sec.gov/news/testimony/2009/ts091009hdk.htm
  - https://www.sipc.org/news-and-media/news-releases/20180705
  - https://www.justice.gov/archives/opa/pr/justice-departments-10th-distribution-brings-total-provided-over-43b-nearly-full-recovery
  - https://www.sipc.org/news-and-media/news-releases/20260227
classification: PUBLIC
---

## Timeline table

| Date | Track | Event | Source |
|---|---|---|---|
| For decades (no precise start year asserted) | SCHEME | BLMIS operates a Ponzi scheme, fabricating client statements and trade confirmations behind the reported split-strike-conversion strategy | [SRC_DOJ_SDNY_CASEPAGE] [SRC_FBI_HISTORY] |
| 2008-12-11 | REGULATORY | SEC files initial civil charge against Madoff and BLMIS | [SRC_SEC_2008_CIVIL_CHARGE] |
| December 2008 | CRIMINAL | Madoff is arrested on federal charges | [SRC_DOJ_SDNY_CASEPAGE] |
| 2009 | REGULATORY | SEC brings action describing fabricated books and computer-generated trading records | [SRC_SEC_2009_FABRICATED_RECORDS] |
| 2009 | REGULATORY | SEC brings action concerning the purported BLMIS auditor | [SRC_SEC_2009_AUDITOR_ACTION] |
| 2009-03-12 | CRIMINAL | Madoff pleads guilty, without a plea agreement, to all 11 federal felony counts | [SRC_DOJ_SDNY_CASEPAGE] |
| 2009-06-29 | CRIMINAL | Madoff is sentenced to 150 years in federal prison | [SRC_DOJ_SDNY_CASEPAGE] |
| 2009-09-10 | REGULATORY | SEC OIG testifies before Congress summarizing complaints, examinations, and missed verification opportunities before the scheme's collapse | [SRC_SEC_OIG_TESTIMONY] |
| 2018-07-05 | RECOVERY | SIPC reports an estimated principal loss of approximately USD 17.5 billion | [SRC_SIPC_2018_RELEASE] |
| Ongoing (as of source-pack cutoff) | RECOVERY | DOJ Madoff Victim Fund distributes over USD 4.3 billion to victims across multiple distribution rounds | [SRC_DOJ_VICTIM_FUND] |
| 2021 | CRIMINAL | Madoff dies in federal custody | [SRC_DOJ_SDNY_CASEPAGE] |
| 2026-02-27 | RECOVERY | SIPC issues a further distribution update; this date is also the source-pack cutoff | [SRC_SIPC_2026_DISTRIBUTION] |

## Status separation

`CRIMINAL_CASE` is **CLOSED** — final as of the 2009-06-29 sentencing (and Madoff's 2021
death in custody does not reopen it). `SIPA_LIQUIDATION` and `DOJ_VICTIM_FUND` are
**ONGOING / POST_CONVICTION_CONTEXT** as of the 2026-02-27 cutoff
[SRC_SIPC_2026_DISTRIBUTION] [SRC_DOJ_VICTIM_FUND]. These proceeding statuses must never
be merged into one status: ongoing recovery/distribution activity does not mean guilt or
sentencing is still being litigated, and the closed criminal case does not mean recovery
administration has ended.
