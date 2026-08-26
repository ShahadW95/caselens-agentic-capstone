# CASE//LENS Source Policy

This policy governs how sources are tiered, cited, and used across the curated case pack.
It is a Track B–owned document (see `AGENTS.md`). Contract-affecting changes go through
the `contract-change` Issue process described in
`docs/prompts/00_CASELENS_MASTER_CONTEXT.md`; this file itself is edited directly by
Track B.

## Source tier table

| Tier | Meaning | Use |
|---|---|---|
| A | Official judgment, statute, court docket, government record | May ground facts, legal explanation, and final result |
| B | Official agency statement or reliable public record | May ground facts with context |
| C | Reputable journalism | Context and reported details; label as reporting |
| D | Commentary, creator video, forum, social media | Not core evidence; excluded from the core RAG corpus, or labeled only as public commentary |

## Rules

1. **Every fact must cite a source_id.** Any factual or financial statement in a
   team-authored knowledge-base digest must be traceable to a `source_id` listed in
   `data/cases/case_001/source_manifest.json`.
2. **No copying long copyrighted journalism.** Summarize in original language and link to
   the original; do not reproduce long passages from copyrighted articles or transcripts.
3. **Every financial figure needs full amount metadata.** Each dollar figure must carry an
   `AmountKind` (`FICTITIOUS_STATEMENT_BALANCE`, `ESTIMATED_PRINCIPAL_LOSS`,
   `FORFEITURE_ORDER`, `RECOVERY`, or `DISTRIBUTION`), a currency, a value or bounded
   range, an as-of date, one or more `source_id`s, and a measurement note explaining what
   it measures.
4. **`CRIMINAL_CASE` status must never merge with `SIPA_LIQUIDATION`/`DOJ_VICTIM_FUND`
   status.** These proceedings carry independent `ProceedingStatus` values and independent
   as-of dates; a closed criminal case and ongoing recovery administration must never be
   collapsed into a single status.
5. **Excluded categories never enter the retrieval corpus.** Dramatizations, podcasts,
   unsourced biographies, social-media theories, personality diagnosis, and sensational
   victim stories (see `source_manifest.json`'s `excluded_categories`) must never be
   indexed for retrieval, and Tier D material is excluded from the core RAG corpus.
6. **Adding a new source requires three things, in order:** (a) a new entry in
   `data/cases/case_001/source_manifest.json` with a stable `source_id` and tier, (b) a
   written tier justification, and (c) at least one citation of that `source_id` from a
   knowledge-base document — before any specialist may rely on it.
7. **Ownership.** This file is Track B–owned. Contract-affecting changes (e.g., changes
   that would require a new field on a frozen Pydantic contract) go through the
   `contract-change` Issue process instead of a direct edit to `contracts.py` or
   `protocols.py`.

## Status

B0 source manifest and six knowledge-base digests are drafted for the Madoff case using
the 11 seed sources listed in `docs/prompts/00_CASELENS_MASTER_CONTEXT.md`, pending human
review before B1 begins.
