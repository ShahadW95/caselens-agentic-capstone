---
title: "CASE//LENS — Teammate + Claude Code Track B"
owner: "Teammate"
assistant: "Claude Code"
track: "Case sources, structured data, Agentic RAG, deterministic tools, real specialists"
depends_on: "00_CASELENS_MASTER_CONTEXT.md"
status: "v1.1 — Madoff case revision"
---

# CASE//LENS — Teammate + Claude Code Track B

## Your responsibility

You own the evidence backend: a curated source package for exactly one closed case, normalized case data, knowledge documents, Agentic RAG, three deterministic tools, three real specialist implementations, and their offline tests.

You do not own the shared state, Supervisor, LangGraph graph, reviewer, Streamlit UI, result builder, or final application assembly. Implement only the frozen protocols supplied by Track A. Do not change a shared contract silently.

## How to use this track

1. Read `00_CASELENS_MASTER_CONTEXT.md` and this file completely.
2. Confirm the chosen closed case in the decision table before B0.
3. Start B0 at the same time Shahad starts A0; B0 is research/data work and does not need Python contracts.
4. Wait only at the explicit Contract Gate: A0 must merge before B1 Python implementation begins.
5. Execute one prompt below at a time.
6. Review the diff and actual test output.
7. Commit and push the checkpoint, update its Issue/Project item, and stop.

Use this session header before every prompt:

```text
Read docs/prompts/00_CASELENS_MASTER_CONTEXT.md and docs/prompts/02_TEAMMATE_CLAUDE_TRACK.md completely. Also read AGENTS.md and CLAUDE.md when present. Inspect the current branch, git status, recent commits, and all files relevant to this checkpoint.

Execute only Prompt B[NUMBER].
Current branch: [BRANCH].
Linked GitHub Issue: [ISSUE].
Do not edit Track A-owned files. Preserve all existing and teammate-authored work. Before editing, report the current state, dependency status, and exact files you intend to change. Stop after the checkpoint handoff report.
```

---

# PROMPT B0 — CLOSED-CASE SOURCE PACK AND RESEARCH BOUNDARY

## Purpose

Create the traceable source foundation while Track A creates repository contracts. This checkpoint performs research and curation only; it must not implement Python modules or change shared contracts.

## Branch

```text
research/case-source-pack
```

## Dependency

The D0 decision table must identify one case that is legally concluded in the selected jurisdiction. If final status cannot be demonstrated from a reliable source, stop and report the blocker. Do not substitute a different case silently.

## May edit

```text
CLAUDE.md
docs/source_policy.md
data/cases/case_001/source_manifest.json
data/cases/case_001/research_notes.md
knowledge_base/case_001/source_placeholders.md
```

## Must not edit

```text
Track A files
src/
tests/
requirements.txt
.env.example
README.md
raw full-text news articles or copyrighted transcripts
```

## Copy this prompt into Claude Code

```text
We are implementing Prompt B0 for CASE//LENS. Read the master context and Track B instructions completely before editing.

First inspect the branch, repository, and current decisions. The frozen MVP case is `United States v. Bernard L. Madoff`, case ID `US_SDNY_09CR00213_DC`, limited to Madoff's federal criminal case and the BLMIS investment-advisory Ponzi scheme. Confirm through the official DOJ case page that he pleaded guilty without a plea agreement to all 11 felony counts on 2009-03-12 and received a 150-year sentence on 2009-06-29. Treat the criminal guilt case as closed. Treat later DOJ victim-fund distributions and the SIPA liquidation/recovery as separate post-conviction proceedings with their own statuses and as-of dates. If a source contradicts these boundaries, report the conflict and stop before fabricating data.

If decisions are present, create a narrow, auditable research package for one case only.

Research rules:
- Prefer primary official material: published judgment/opinion, court docket or court release, statute/regulation, government or law-enforcement public record.
- Use reputable journalism only for context that primary material does not explain.
- Treat commentary, videos, podcasts, social posts, and unsourced summaries as discovery leads, not proof.
- Never copy full articles, protected transcripts, private material, leaked records, addresses, contact details, graphic content, or irrelevant sensitive personal data.
- Store concise original notes and bibliographic metadata, not scraped corpora.
- Preserve disagreement: do not collapse an allegation, defense position, prosecution position, court finding, and later commentary into one fact.
- Record publication date and event date separately.
- Every source must have a stable source ID and working original URL when available.
- Do not infer guilt, diagnosis, motive, or legal conclusion beyond the source.
- Do not describe Madoff as a government official. Record his sourced NASD/NASDAQ/self-regulatory roles and SEC advisory participation precisely.
- Do not assert one exact fraud start year when official sources differ in breadth. Use `for decades` for the broad statement and record specifically sourced milestones.
- Do not use `USD 65 billion`, `USD 17.5 billion`, forfeiture, recovery, and distribution figures interchangeably. Every amount must say what it measures and its as-of date.

Create `CLAUDE.md` with the Track B ownership boundary, read-before-edit rule, frozen-contract rule, source standards, offline-test rule, secret safety, prohibited claims, and mandatory handoff format. Do not duplicate the complete master context; point to it.

Create `docs/source_policy.md` explaining:
1. permitted case scope and why open/active cases are excluded;
2. source tiers A–D exactly as frozen in the master context;
3. inclusion and exclusion criteria;
4. fact/allegation/disputed/unknown classification;
5. citation and source-ID rules;
6. handling of retractions, corrections, date conflicts, sealed or missing material;
7. privacy, copyright, graphic-content, victim-respect, and no-diagnosis rules;
8. review cadence and a pre-release source audit checklist.

Create `data/cases/case_001/source_manifest.json` as valid UTF-8 JSON with a top-level manifest version, case ID, review status, and source records. Each source record must include:
- source_id;
- title;
- publisher/issuing body;
- source_type;
- source_tier;
- jurisdiction;
- publication_date;
- event_date when relevant;
- original_url;
- access_date;
- language;
- role in the case pack;
- supported topic IDs or planned document IDs;
- correction/retraction status;
- availability note;
- concise relevance note;
- license/copyright handling note.

For every source that supports a monetary figure, also record the intended amount kind (`FICTITIOUS_STATEMENT_BALANCE`, `ESTIMATED_PRINCIPAL_LOSS`, `FORFEITURE_ORDER`, `RECOVERY`, or `DISTRIBUTION`) and as-of date. For every source about a proceeding, record whether it concerns the criminal case, SEC enforcement, SIPA liquidation, or DOJ Victim Fund.

The minimum acceptable manifest has:
- one authoritative item proving the final legal outcome;
- the applicable legal text or authoritative legal explanation;
- one official timeline/evidence source where available;
- enough independent context to explain the case without relying on social media.
Quality matters more than source count. Do not invent a target count.

Keep related defendants' prosecutions outside the MVP except where an official record is required to evaluate the narrow claim that Madoff acted entirely alone. Do not infer that every employee, relative, feeder, auditor, or regulator knew of the fraud. Exclude dramatizations, podcasts, documentaries, social-media theories, personality analysis, unsupported bribery/conspiracy claims, and sensational victim stories from the core evidence pack.

Create `data/cases/case_001/research_notes.md` with:
- verified final-status note;
- question map for overview, timeline, evidence/claims, legal outcome, and bounded counterfactuals;
- facts already established by Tier A/B sources;
- prosecution/claimant position;
- defense/respondent position;
- court findings and outcome;
- the 11-count guilty plea, sentencing, and forfeiture as distinct legal concepts; do not invent a jury verdict;
- amount-definition map separating paper balances, principal loss, forfeiture, recovery, and distribution;
- proceeding-status map separating the closed criminal case from ongoing or later recovery administration;
- regulator-warning map using SEC OIG findings without inferring corruption;
- conflicts and unresolved gaps;
- excluded sensational or unverified claims;
- proposed stable IDs for events, claims, evidence items, and legal rules;
- a source-to-topic coverage table.

Use the master context's official seed sources as the starting set. At minimum, cover: DOJ criminal outcome; FBI mechanism/history; SEC initial action; SEC OIG failure findings; fabricated records/programs; purported auditor; FINRA/NASDAQ roles; principal-loss definition; DOJ Victim Fund; and current SIPC recovery status. Use primary sources wherever available.

Create `knowledge_base/case_001/source_placeholders.md` listing the six required knowledge documents, their intended Tier A/B/C sources, missing coverage, and owner. This is a planning file, not runtime knowledge.

Validate JSON syntax using Python. Check URLs only with safe read-only requests when network access is available; if it is unavailable, mark URL verification as pending instead of pretending. Search the repository for accidentally copied secrets or raw long-form source content. Do not implement any Python backend.

Finish with the mandatory checkpoint result and state whether B1 is ready from a source perspective.
```

## Acceptance evidence

```text
python -m json.tool data/cases/case_001/source_manifest.json
git diff --check
manual review: final case status has a cited authoritative source
manual review: every source has stable ID, tier, URL, relevance, and handling note
manual review: allegations and court findings are separated
manual review: no raw full article, private record, or secret is committed
```

## Human action after B0

1. Open a Pull Request linked to Issue B0.
2. Ask Shahad to review the final-status proof and source boundaries, not rewrite research notes.
3. If A0 is not merged, continue improving only source coverage or stop. Do not start shared Python code.
4. After A0 merges, update this branch from `origin/main`, rerun validation, then begin B1.

---

# PROMPT B1 — STRUCTURED CASE DATA, LOADER, AND VALIDATION

## Purpose

Convert reviewed research into deterministic, internally linked data that can power tools without model guesses.

## Dependency

```text
B0 source review complete
A0 Foundation PR merged
Track B branch updated from origin/main
contract version v1 confirmed
```

## Branch setup

After both the reviewed B0 source PR and A0 Foundation PR are merged:

```bash
git status
git switch main
git fetch origin
git merge --ff-only origin/main
git switch -c feat/evidence-rag-tools
```

Use this same Track B feature branch for B1–B5 unless the team deliberately opens a small `fix/<name>` branch. Push after every checkpoint and keep one Draft Pull Request updated.

## May edit

```text
data/cases/case_001/
scripts/validate_case_pack.py
src/caselens/services/case_loader.py
tests/test_case_data.py
tests/fixtures/case_001_minimal/
docs/source_policy.md
CLAUDE.md
```

## Must not edit

```text
src/caselens/contracts.py
src/caselens/protocols.py
Track A files
shared configuration
```

## Copy this prompt into Claude Code

```text
We are implementing Prompt B1 for CASE//LENS. Verify that A0 is merged and the local branch includes contract version v1. Read the existing Pydantic contracts and protocols; do not change them.

Create normalized case data for exactly `case_001` using only B0 reviewed sources:

1. `case_metadata.json`
   - stable case ID and display title;
   - jurisdiction and court;
   - case status and final-status source IDs;
   - relevant dates;
   - neutral synopsis;
   - legal outcome summary;
   - dataset version and last-reviewed date;
   - editorial warnings and scope exclusions.
   - separate proceeding records for the closed criminal case, SEC enforcement context, SIPA liquidation/recovery, and DOJ Victim Fund, each with its own status and as-of date.

2. `timeline.json`
   - stable event IDs;
   - normalized date or bounded date range;
   - neutral event title and concise description;
   - event category;
   - fact classification;
   - supporting and contradicting source IDs;
   - related claim/evidence IDs;
   - certainty and date precision;
   - track classification: `SCHEME`, `REGULATORY`, `CRIMINAL`, or `RECOVERY`;
   - no invented time when only a date is known.

3. `claims.json`
   - stable claim IDs;
   - normalized claim text;
   - speaker/party or `unknown`;
   - claim context;
   - deterministic status: supported, contradicted, partially_supported, or insufficient_evidence;
   - supporting and contradicting evidence/source IDs;
   - court treatment when available;
   - explanation bounded to the cited material.

4. `evidence.json`
   - stable evidence IDs;
   - neutral label and type;
   - who introduced or reported it;
   - supporting source IDs;
   - related claims/events;
   - admissibility or court-treatment note only when sourced;
   - limitation and dispute fields;
   - do not include graphic assets or private material.

5. `financial_amounts.json`
   - stable amount ID;
   - amount kind: fictitious statement balance, estimated principal loss, forfeiture order, recovery, or distribution;
   - currency and value or explicitly bounded estimate;
   - as-of date and proceeding type;
   - source IDs and concise measurement note;
   - never calculate or compare unlike amount kinds without an explicit explanation.

6. `causal_graph.json`
   - a curated educational dependency graph, not a prediction model;
   - stable node IDs that reference existing events/evidence/claims/legal findings;
   - typed edges with concise sourced rationales;
   - an explicit allowlist of changeable inputs for What If?;
   - direct and bounded downstream impacts for each allowed change;
   - uncertainty notes and a mandatory hypothetical disclaimer;
   - no alternative-guilt theory and no verdict certainty.

Preserve `source_manifest.json` and extend it only for traceability. Do not make unsupported source entries.

Implement `src/caselens/services/case_loader.py` so it:
- accepts an allowlisted case ID, never an arbitrary path;
- loads the JSON files safely;
- validates them into strict internal/Pydantic structures compatible with v1 contracts;
- fails with structured, user-safe errors for missing files, malformed JSON, unknown IDs, unsupported versions, or unsupported cases;
- never logs private paths or file contents;
- returns deterministic ordering.

Implement `scripts/validate_case_pack.py` with a zero exit code only when all checks pass. It must validate:
- required files and UTF-8 JSON;
- required fields, enum values, and version;
- unique IDs;
- every cross-reference resolves;
- every factual claim/event has source support or is explicitly unknown/insufficient;
- every source ID exists in the manifest;
- final case status has authoritative support;
- all financial figures have valid amount kinds, sources, dates, and proceeding context;
- the criminal proceeding is closed while any recovery proceeding preserves its separately sourced status;
- source tiers are valid;
- dates/ranges are logically ordered;
- causal graph has no dangling nodes, cycles where prohibited, or non-allowlisted changes;
- What If? outputs can carry disclaimer and unknowns;
- no arbitrary external file paths are embedded.

Write offline tests with a small fixture and the real curated pack. Include happy paths and failures for duplicate ID, dangling source, invalid date, unsupported case, missing file, and invalid causal edge. Tests must not call a model, embedding API, or network.

Do not alter shared contracts to make the data fit. If v1 cannot express a required field, open a contract-change Issue containing old schema, proposed schema, reason, impacted modules, migration, and tests; then stop that part.

Run the validator, focused tests, all existing tests, and `git diff --check`. Finish with the mandatory checkpoint result.
```

## Acceptance evidence

```text
python scripts/validate_case_pack.py --case-id case_001
pytest -q tests/test_case_data.py
pytest -q
python -m compileall src scripts tests
git diff --check
```

The handoff must list the number of events, claims, evidence items, causal nodes/edges, and sources; these are inventory facts, not quality targets.

---

# PROMPT B2 — AGENTIC RAG PREPARATION AND RETRIEVAL

## Purpose

Build a transparent evidence-retrieval layer in which query planning, metadata, sufficiency assessment, and one bounded reformulation visibly affect the workflow.

## Dependency

```text
B1 validator and tests pass
v1 RetrievalPlan, RetrievedChunk, SourceCitation, and EvidenceAssessment contracts available
embedding provider decision recorded; live credential is not required for tests
```

## Branch

```text
feat/evidence-rag-tools
```

## May edit

```text
knowledge_base/case_001/
scripts/build_knowledge_index.py
src/caselens/rag/
tests/test_rag.py
tests/fixtures/
source/RAG notes in docs/source_policy.md
```

## Copy this prompt into Claude Code

```text
We are implementing Prompt B2 for CASE//LENS. Read the data pack, source policy, frozen contracts, and RAG boundaries. Do not edit Track A or shared contract files.

Replace the planning placeholder with exactly these six concise, original knowledge documents:
- `01_case_overview_and_ponzi_mechanism.md`
- `02_verified_timeline.md`
- `03_claims_red_flags_and_records.md`
- `04_guilty_plea_charges_and_sentence.md`
- `05_regulatory_failure_and_applicable_law.md`
- `06_victim_recovery_and_editorial_policy.md`

Every document must start with YAML metadata containing at least:
`document_id`, `title`, `case_id`, `source_type`, `source_tier`, `jurisdiction`, `case_status`, `version`, `date`, `last_reviewed`, `original_source_urls`, and `classification`.

Writing rules:
- summarize in original language;
- cite stable source IDs beside substantive statements;
- distinguish facts, party allegations, disputes, court findings, and unknowns;
- keep legal explanation informational and tied to selected jurisdiction/date;
- do not include long copied passages, graphic detail, diagnosis, speculation, or uncited social commentary.
- write the canonical digests in English because the controlling sources are English; Track A renders the final answer in Arabic or English. Preserve original source titles and stable IDs rather than duplicating a translated corpus.
- distinguish a guilty plea and sentencing judgment from a jury verdict throughout the legal digest;
- attach a named amount kind and as-of date to every monetary figure;
- distinguish SEC OIG findings about missed opportunities from allegations of corruption or bribery;
- state that the criminal case is closed while separately labeling the sourced status of recovery proceedings.

Implement:

1. `loaders.py`
   - allowlisted case folder;
   - YAML/frontmatter validation;
   - source-ID and manifest cross-check;
   - deterministic document ordering;
   - structured errors.

2. `chunking.py`
   - heading-aware chunks, preserving document ID, heading, source IDs, tier, jurisdiction, status, and stable chunk ID;
   - no overlap across unrelated sections;
   - deterministic output so regenerated indexes are comparable.

3. `index.py`
   - one embedding-client protocol supplied/injected at the boundary, implemented for `gemini-embedding-2` with output dimensionality 768;
   - normalized vectors in a transparent local NumPy index;
   - saved generated index under ignored `storage/`;
   - an index manifest with document hashes, embedding identifier/config, dimension, creation time, and schema version;
   - detect stale or dimension-mismatched indexes;
   - use the provider's retrieval-document convention for indexed chunks and retrieval-query convention for user/search queries;
   - never commit secrets or generated vectors.

4. `retriever.py`
   - create a structured RetrievalPlan from mode/query/task and optional metadata filters;
   - run similarity retrieval with configurable bounded top-k;
   - return strict RetrievedChunk objects with citations and scores;
   - assess sufficiency using coverage, source tier, contradictions, and query intent;
   - if insufficient, reformulate once and retrieve once more;
   - stop after at most two retrieval rounds;
   - preserve both rounds in safe audit metadata without model chain-of-thought;
   - return a structured insufficient-evidence result instead of inventing an answer.

The runtime behavior must be agentic, not a decorative fixed search: ASK_CASE and EXPLAIN_VERDICT may use different filters; CHECK_CLAIM should prioritize evidence/claim and court-finding documents; WHAT_IF should retrieve the affected event/evidence context. Make the choice observable through safe plan fields.

Implement `scripts/build_knowledge_index.py` with explicit `--case-id`, safe output location, clear missing-credential/offline behavior, and no import-time live call.

Testing requirements:
- use a deterministic fake embedding client;
- prove chunk metadata and stable IDs;
- prove relevant top-k ordering on a tiny fixture;
- prove metadata filters affect results;
- prove sufficient evidence stops after one retrieval;
- prove insufficient evidence reformulates exactly once and then stops;
- prove empty query, no results, stale index, dimension mismatch, malformed metadata, and embedding failure return safe failures;
- prove tests require no key/network.

Use only the frozen stable ID `gemini-embedding-2`; do not substitute `gemini-embedding-2-preview` or `gemini-embedding-001` silently. If access has not been verified, keep the production adapter behind the existing boundary and document the pending connection check. Do not scatter SDK calls.

Run focused tests, full tests, compile checks, and a deterministic index build with the fake embedding client. Finish with the mandatory checkpoint result including one example retrieval plan, returned source IDs, and sufficiency decision.
```

## Acceptance evidence

```text
pytest -q tests/test_rag.py
pytest -q
python -m compileall src scripts tests
python scripts/build_knowledge_index.py --case-id case_001 --fake-embeddings
git status --short
git diff --check
manual review: generated index is ignored and citations resolve to the manifest
```

---

# PROMPT B3 — THREE DETERMINISTIC CASE TOOLS

## Purpose

Implement meaningful tools beyond RAG. Each tool must validate input, return a strict structured result, affect the workflow, and expose safe error states.

## Dependency

```text
B1 normalized data and case loader pass validation
v1 tool-related contracts are frozen
```

## Branch

```text
feat/evidence-rag-tools
```

## May edit

```text
src/caselens/tools/
tests/test_tools.py
tests/fixtures/
small Track B-owned loader changes required by proven tool behavior
```

## Copy this prompt into Claude Code

```text
We are implementing Prompt B3 for CASE//LENS. Read the master tool specifications, normalized case pack, loader, and v1 contracts. Do not edit the graph, Supervisor, UI, shared contracts, or specialist modules in this checkpoint.

Implement exactly these three local tools:

1. `query_case_timeline`
   Input:
   - allowlisted case ID;
   - optional start/end date;
   - optional event categories;
   - optional timeline track: scheme, regulatory, criminal, or recovery;
   - optional related claim/evidence ID;
   - bounded limit.
   Output:
   - deterministically ordered TimelineEvent items;
   - applied filters;
   - source citations;
   - result count;
   - empty-result reason when relevant.
   Behavior:
   - use structured timeline data, not model-generated dates;
   - validate ranges and identifiers;
   - never infer missing events.
   - do not combine later recovery administration with the criminal-case outcome.

2. `check_claim_support`
   Input:
   - allowlisted case ID;
   - stable claim ID, or a normalized user claim mapped only when an approved deterministic mapping exists.
   Output:
   - status exactly one of supported, contradicted, partially_supported, insufficient_evidence;
   - normalized claim;
   - supporting and contradicting evidence/source IDs;
   - court treatment when sourced;
   - concise explanation and limitations.
   - relevant financial amounts with amount kind, date, measurement note, and source IDs.
   Behavior:
   - calculate from curated links and statuses;
   - do not let a model convert popularity or repeated reporting into proof;
   - unknown free-text claims return insufficient_evidence or a safe selection request.
   - the claim `Madoff stole USD 65 billion in cash` must not become supported merely because an official source mentions a similar fictitious balance; amount semantics must match.

3. `simulate_counterfactual`
   Input:
   - allowlisted case ID;
   - one allowlisted causal node/event/evidence ID;
   - one supported change operation from the case pack.
   Output:
   - original condition;
   - hypothetical change;
   - direct and bounded downstream impacts;
   - what remains unchanged;
   - unknowns;
   - supporting citations;
   - mandatory disclaimer that this is educational and not an alternate legal verdict.
   Behavior:
   - traverse only the curated causal graph;
   - change exactly one allowed input;
   - enforce depth/node limits;
   - never generate a new suspect, diagnosis, motive, evidence, verdict probability, or guilt conclusion;
   - reject arbitrary scenarios safely.
   - the curated demo change may model independent third-party verification of claimed trades after a documented regulatory complaint; it may describe possible earlier detection or stronger evidence, but never guarantee a discovery date, loss avoided, or alternate sentence.

For all tools:
- use strict Pydantic input/output at the boundary;
- expose name, short description, permission category, input schema, and result schema through a registry Track A can inspect;
- read only allowlisted local case data;
- have no network, shell, arbitrary filesystem, mutation, or secret access;
- return structured safe errors for malformed input, missing case data, unsupported ID, empty result, or internal failure;
- emit safe audit metadata such as tool name, validated parameter summary, status, duration, and result count, but never raw sensitive content or chain-of-thought;
- contain deterministic core logic separated from any LLM adapter.

Tests must prove:
- normal timeline filtering and stable sort;
- invalid/reversed dates and unknown IDs;
- all four claim statuses;
- supporting and contradicting citations propagate;
- an unknown claim cannot be presented as supported;
- valid one-change counterfactual traversal;
- unknown change, multiple changes, excessive traversal, and graph error fail safely;
- mandatory counterfactual disclaimer is always present, including partial/failure-safe outputs where appropriate;
- registry schemas and permissions are machine-readable;
- tools perform no network or model calls.

Run focused tests, all tests, compile checks, and `git diff --check`. Finish with the mandatory checkpoint result and include one safe example input/output summary for each tool.
```

## Acceptance evidence

```text
pytest -q tests/test_tools.py
pytest -q
python -m compileall src tests
git diff --check
manual review: tool results change based on validated inputs and curated data
manual review: every result/failure is structured and safely observable
```

---

# PROMPT B4 — REAL SPECIALISTS USING RAG AND TOOLS

## Purpose

Implement the three non-duplicative specialists behind the frozen protocols. The Supervisor remains the only router; specialists receive bounded tasks and isolated state views.

## Dependency

```text
B2 RAG tests pass
B3 tool tests pass
v1 specialist protocols are unchanged
one runtime model boundary exists in src/caselens/llm.py
```

## Branch

```text
feat/evidence-rag-tools
```

## May edit

```text
src/caselens/specialists/evidence.py
src/caselens/specialists/legal.py
src/caselens/specialists/timeline_analysis.py
tests/test_specialists.py
tests/fixtures/
Track B-owned RAG/tool code only for a proven defect
```

## Must not edit

```text
src/caselens/supervisor.py
src/caselens/graph.py
src/caselens/reviewer.py
src/caselens/ui.py
src/caselens/state.py
src/caselens/contracts.py
src/caselens/protocols.py
```

## Copy this prompt into Claude Code

```text
We are implementing Prompt B4 for CASE//LENS. Read all agent contracts, specialist protocols, RAG and tool registries, and Track A fake adapters before editing. Do not change the protocol to match your implementation.

Implement three real specialists with distinct responsibilities:

1. Source & Evidence Specialist
   - handles ASK_CASE evidence/factual tasks and CHECK_CLAIM tasks delegated by the Supervisor;
   - plans retrieval using task intent and source tiers;
   - dynamically selects retrieval and `check_claim_support` only when relevant;
   - distinguishes established facts, allegations, disputes, contradictions, and unknowns;
   - returns `EvidenceFinding` with source citations and sufficiency;
   - never makes a legal judgment or diagnoses a person.

2. Legal Explanation Specialist
   - handles EXPLAIN_VERDICT (displayed as Explain the Judgment) and legal sub-tasks;
   - prioritizes the criminal information, guilty plea, sentence, forfeiture, applicable legal text, jurisdiction, and time;
   - may retrieve and use structured case data but cannot change the legal outcome or invent a rule;
   - explains the charged conduct, Madoff's admissions/guilty plea, prosecution and defense sentencing positions when sourced, and the court's judgment separately; it must not invent a trial verdict or trial evidence findings;
   - returns `LegalFinding` with plain-language limits and citations;
   - includes an informational-not-legal-advice notice when required by contract.

3. Timeline & What-If Specialist
   - handles VIEW_TIMELINE and WHAT_IF;
   - dynamically uses `query_case_timeline` for timeline work;
   - uses `simulate_counterfactual` only for one allowlisted change;
   - retrieves context when needed, but never replaces deterministic dates/causal edges with model guesses;
   - returns `TimelineFinding` or `CounterfactualFinding` exactly as the protocol specifies;
   - preserves the hypothetical disclaimer and unknowns.

Specialist execution pattern:
- validate the DelegationTask and read-only StateView;
- construct a compact internal action plan represented by safe action labels, not hidden reasoning text;
- select only allowed retrieval/tool actions based on mode, task, and current evidence;
- execute at most the frozen number of retrieval/tool/model steps;
- ask the shared model boundary for strict structured output only when interpretation/explanation is needed;
- validate the model response once;
- on schema failure, perform at most one repair attempt when the boundary supports it, then return SafeError/insufficient evidence;
- attach only citations returned by RAG/tools; never allow a model to fabricate source IDs;
- return the frozen contract and safe audit events.

Use the shared `gemini-3.7-flash` boundary for live interpretation. The final explanatory text must follow the state language (`ar` or `en`), while citations, claim status, source IDs, deterministic tool results, and legal classification remain identical across languages.

Isolation rules:
- a specialist receives only task-relevant state view, not another specialist’s scratch prompt or private reasoning;
- no specialist calls another specialist;
- no specialist routes the workflow or decides final completion;
- no model/client construction outside the shared `llm.py` boundary;
- no provider-specific response object escapes the boundary;
- no runtime web search;
- no arbitrary case or path.

Dynamic-selection proof:
- a timeline task uses the timeline tool but not claim support;
- a known claim check uses claim support and relevant retrieval;
- a verdict explanation prioritizes legal/court sources and does not call counterfactual;
- an allowed What If? uses the counterfactual tool;
- a general supported question may stop after sufficient retrieval without calling every tool.

Write offline tests with a fake structured model and fake/real local tools as appropriate. Assert exact call counts and selected actions. Include:
- one happy path per specialist;
- sufficient evidence and insufficient evidence;
- malformed model result and one bounded repair;
- model exception;
- RAG/tool failure;
- unknown source ID rejection;
- allegation/fact separation;
- counterfactual safety;
- no duplicate specialist responsibility;
- outputs validate against the Track A contracts.

Do not make a live model call in the test suite. If a provider/model decision and local key are available, the separate connection-check script may be run manually only if the master context explicitly permits it. Never print the key or raw provider payload.

Run focused tests, full tests, compile checks, and `git diff --check`. Finish with the mandatory checkpoint result, protocol compatibility statement, and a call-selection matrix from the tests.
```

## Acceptance evidence

```text
pytest -q tests/test_specialists.py
pytest -q
python -m compileall src tests
git diff --check
manual review: specialists return the exact frozen schemas
manual review: test call counts prove dynamic selection and bounded execution
```

---

# PROMPT B5 — BACKEND INTEGRATION READINESS AND HANDOFF

## Purpose

Prove that the complete Track B backend is ready to replace Track A fakes without modifying orchestration. This checkpoint diagnoses and packages; it does not take over Track A integration.

## Dependency

```text
B1–B4 complete
branch updated from origin/main
no unresolved contract-change issue
```

## Branch

```text
feat/evidence-rag-tools
```

## May edit

```text
Track B-owned files only
docs/source_policy.md
CLAUDE.md
```

## Copy this prompt into Claude Code

```text
We are implementing Prompt B5 for CASE//LENS. This is an integration-readiness audit, not a feature expansion.

Update the branch from `origin/main` using a normal merge, resolve only conflicts in Track B-owned files, and stop for human help if a frozen shared file conflicts. Never force push, reset hard, or overwrite Track A changes.

Inspect:
- case manifest and final-status evidence;
- data validator and all cross-references;
- knowledge metadata and citations;
- ignored/generated index behavior;
- RAG two-round stopping and sufficiency;
- all three tool schemas, permissions, failures, and audit metadata;
- all three specialist protocol signatures and structured outputs;
- fake/real adapter compatibility expected by `src/caselens/adapters.py`;
- secret, privacy, copyright, and runtime-network boundaries.

Create no new architecture. Fix only Track B-owned defects demonstrated by a failing test or contract mismatch.

Add or update Track B documentation notes so Shahad can integrate without reading chat history:
- exact factory/import path for each real specialist;
- constructor dependencies;
- required environment variable names, never values;
- case/index preparation commands;
- expected safe missing-key and missing-index behavior;
- known limitations;
- commands and actual results;
- contract version;
- any pending provider live check.

Run:
- data validation;
- deterministic fake index build;
- focused Track B tests;
- entire offline suite;
- compilation;
- diff whitespace check;
- a secret scan that inspects tracked filenames/content patterns without opening or printing `.env`;
- `git status` to prove generated indexes and local secrets are not staged.

If a runtime credential is explicitly configured by the teammate and the provider/model decision is recorded, run the repository's minimal connection-check command once. It must verify:
1. one minimal model response;
2. one strict structured response;
3. one tool-selection-compatible structured response.
Do not run it from pytest, do not expose output containing secrets, and do not claim a live check if it was skipped.

Prepare the mandatory checkpoint handoff plus an `INTEGRATION MAP` containing:
- Track A protocol/factory point;
- Track B implementation;
- return contract;
- prerequisite;
- focused test;
- failure behavior.

Do not edit the Supervisor, graph, UI, final README, or Track A adapters. Open/update the Track B backend Pull Request linked to the correct Issues and stop for Shahad's review.
```

## Acceptance evidence

```text
python scripts/validate_case_pack.py --case-id case_001
python scripts/build_knowledge_index.py --case-id case_001 --fake-embeddings
pytest -q tests/test_case_data.py tests/test_rag.py tests/test_tools.py tests/test_specialists.py
pytest -q
python -m compileall app.py src scripts tests
git diff --check
git status --short
optional manual live check: report run or explicitly skipped
```

---

# CLAUDE CODE REVIEW PROMPT — BEFORE OPENING A PR

```text
Review the current branch against the master context, AGENTS.md, CLAUDE.md, the current Track B checkpoint, source policy, and frozen v1 contracts. Do not edit files.

Report findings by severity with file references and evidence. Check especially:
- modifications outside Track B ownership;
- silent contract or shared-file changes;
- unsupported or sensational claims;
- open-case, privacy, copyright, or diagnosis risks;
- broken source IDs or cross-references;
- invented dates, citations, evidence, rules, or causal effects;
- decorative RAG or tools whose results do not affect outputs;
- unbounded retrieval/model/tool loops;
- provider code outside the boundary;
- generated indexes, secrets, or `.env` staged for commit;
- tests that do not prove the acceptance criteria;
- merge risk with Track A.

Then list open questions, commands run, actual results, and whether the branch is ready for a Pull Request.
```

# CLAUDE CODE BUG-DIAGNOSIS PROMPT

```text
Read the master context, Track B instructions, source policy, and relevant checkpoint. Diagnose only; do not fix yet.

Observed behavior: [PASTE]
Expected behavior: [PASTE]
Reproduction: [PASTE]
Current branch: [PASTE]
Recent merge/commit: [PASTE]

Reproduce safely. Identify the smallest evidence-supported root cause, affected data/source/contract boundary, owned files, and the missing regression test. Separate a source-data defect from RAG, tool, specialist, and integration defects. Provide fix options and tradeoffs. Stop for approval before editing.
```
