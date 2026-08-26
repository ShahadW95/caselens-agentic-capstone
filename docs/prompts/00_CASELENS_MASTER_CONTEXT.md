---
title: "CASE//LENS — Shared Master Context and Collaboration Contract"
course: "Advanced Agentic AI Systems Engineering"
academy: "SDAIA Academy"
team_size: 2
coding_assistants: "Shahad uses Codex; teammate uses Claude Code"
interface: "Streamlit"
orchestration: "LangGraph"
validation: "Pydantic"
status: "v1.1 — Madoff case revision; implementation decisions frozen; team identities confirmed"
language: "English engineering prompts; bilingual Arabic/English product"
---

# CASE//LENS — Shared Master Context and Collaboration Contract

## What this file is

This is the single source of truth for both human teammates and both coding assistants. It defines the approved product, rubric evidence, architecture, contracts, ownership boundaries, GitHub workflow, integration gates, and safety rules.

Both Codex and Claude Code must read this file completely at the beginning of every new coding session. Each assistant must then read only its assigned track file and execute one prompt at a time.

Do not ask either assistant to build the entire project in one request.

---

# 0. Required decisions before implementation

Fill this table together before either coding track implements live data, model access, or specialist prompts.

| Decision | Current value | Required before |
|---|---|---|
| Team name | `LensLab` | README finalization |
| Project name | `CASE//LENS — Beyond the Verdict` | Repository and presentation |
| Shahad GitHub username | `ShahadW95` | Repository setup |
| Teammate name | `Zahra` | Repository setup |
| Teammate GitHub username | `zaa330` | Add collaborator/assign Issues |
| Repository URL | `https://github.com/ShahadW95/caselens-agentic-capstone` (planned) | First clone |
| Selected closed case | `United States v. Bernard L. Madoff — BLMIS Ponzi-scheme criminal case` | Case data implementation |
| Case ID | `US_SDNY_09CR00213_DC` | All data and citations |
| Case jurisdiction | `United States adversarial common-law system; federal criminal proceeding in S.D.N.Y.; guilty plea and sentencing` | Legal knowledge preparation |
| Case final status/date | `Guilty plea to all 11 felony counts on 2009-03-12; 150-year sentence imposed on 2009-06-29; Madoff died in federal custody in 2021` | Source validation |
| Source-pack cutoff | `2026-02-27; criminal guilt is closed, while victim recovery/SIPA liquidation is separately labeled ongoing` | Case scope |
| Product UI language | `Bilingual Arabic/English; Arabic default with English toggle` | UI copy and output language |
| Runtime LLM provider | `Google Gemini Developer API via google-genai` | Live connection check |
| Runtime chat model | `gemini-3.7-flash` | Live connection check |
| Embedding provider/model | `Google Gemini / gemini-embedding-2; 768 dimensions for MVP` | Index build |
| Presentation time | `Target 6 minutes; hard range 5–7 minutes` | Demo rehearsal |
| Deployment attempt | `Yes: Streamlit Community Cloud, only after local MVP passes` | Optional final phase |

The case-selection gate must verify all of the following:

- The case is closed and has a final outcome.
- At least one official court judgment or equivalent primary legal source is publicly accessible.
- The governing law or legal rule can be sourced.
- Enough reliable sources exist to create a timeline and claim/evidence map.
- The team can discuss it without graphic media, doxxing, private data, or unsupported diagnosis.
- The case is small enough to curate in one day.

If any item is uncertain, do not encode the case as fact. Select a different closed case.

## 0.1 Frozen case profile

The MVP covers only **United States v. Bernard L. Madoff**, district case `1:09-cr-00213-DC`, centered on the criminal case against Bernard Madoff and the fraudulent investment-advisory business at Bernard L. Madoff Investment Securities LLC (BLMIS). Madoff pleaded guilty without a plea agreement to all 11 felony counts on 2009-03-12 and received a 150-year sentence on 2009-06-29. His guilt is not an open question. Related prosecutions may appear only where an official source is needed to correct the claim that every participant acted entirely alone; they are not separate cases for the MVP.

This case is especially suitable because it combines global recognition, a decades-long fraud mechanism, fabricated records, regulator warnings and missed opportunities, multiple legal charges, and an unusually important numerical trap. The widely repeated figure near USD 65 billion refers to fictitious account-statement balances or paper value, not simply cash placed into Madoff's hands. SIPC has described approximately USD 17.5 billion in estimated principal lost by customers who filed claims. The product must preserve the amount definition, source, date, and proceeding context instead of presenting incompatible figures as though they measure the same thing.

The criminal prosecution is closed. Victim compensation and the separate Securities Investor Protection Act (SIPA) liquidation/recovery process must be labeled as post-conviction context with its own status and as-of date. They must never make the app imply that guilt or sentence is still being litigated.

Madoff was not a government official. Official SEC and FINRA material supports a more precise and interesting description: he held prominent private securities-industry and self-regulatory-organization roles, including NASD/NASDAQ positions, and participated in an SEC advisory committee. The SEC Office of Inspector General later documented complaints, red flags, and missed opportunities to uncover the fraud. The app must not turn institutional access into an unsupported bribery, conspiracy, or government-employment claim.

Primary seed sources for B0:

1. U.S. Department of Justice, SDNY case page for `United States v. Bernard L. Madoff and Related Cases`: `https://www.justice.gov/usao-sdny/programs/victim-witness-services/united-states-v-bernard-l-madoff-and-related-cases`
2. Federal Bureau of Investigation, case history and mechanism overview: `https://www.fbi.gov/history/cases-and-criminals/bernie-madoff`
3. U.S. Securities and Exchange Commission, initial civil charge dated 2008-12-11: `https://www.sec.gov/news/press/2008/2008-293.htm`
4. SEC Office of Inspector General, investigation of the SEC's failure to uncover the scheme: `https://www.sec.gov/oig/oig-reports-investigation-failure-madoff-ponzi-scheme`
5. SEC OIG testimony summarizing complaints, examinations, and missed verification opportunities: `https://www.sec.gov/news/testimony/2009/ts091009hdk.htm`
6. SEC action describing fabricated books and computer-generated trading records: `https://www.sec.gov/news/press/2009/2009-243.htm`
7. SEC action concerning the purported BLMIS auditor: `https://www.sec.gov/news/press/2009/2009-60.htm`
8. FINRA testimony describing Madoff's NASD/NASDAQ roles: `https://www.finra.org/media-center/speeches-testimony/testimony-committee-banking-housing-and-urban-affairs`
9. Securities Investor Protection Corporation, principal-loss and recovery context: `https://www.sipc.org/news-and-media/news-releases/20180705`
10. SIPC distribution update dated 2026-02-27: `https://www.sipc.org/news-and-media/news-releases/20260227`
11. U.S. Department of Justice Madoff Victim Fund final-distribution summary: `https://www.justice.gov/archives/opa/pr/justice-departments-10th-distribution-brings-total-provided-over-43b-nearly-full-recovery`

The source pack must verify every event, amount definition, and procedural label during B0. Do not assert a single exact start year for the fraud unless the chosen source and the wording match; use “for decades” for the broad duration and record narrower documented milestones separately. Exclude dramatizations, podcasts, unsourced biographies, social-media theories, personality diagnosis, and sensational victim stories from the core RAG corpus.

High-value demo claims and questions:

- “Did Madoff steal USD 65 billion in cash?” — distinguish fictitious statement balances from estimated principal loss, forfeiture, recovery, and distribution figures.
- “Was Madoff a government official?” — no; explain his private industry/SRO influence and SEC advisory participation precisely.
- “Did the SEC receive warnings before the collapse?” — use the SEC OIG record to distinguish documented complaints and missed checks from unsupported corruption claims.
- “Did Madoff act completely alone?” — separate Madoff's own guilty plea from the documented outcomes of related defendants; never assume knowledge by every employee or associate.
- “How could the scheme continue for decades when there were no real advisory trades?” — connect fabricated statements and records, reputation, feeder relationships, and failures of independent verification using cited sources.
- “Why did he face 11 felony counts and a 150-year sentence even after pleading guilty?” — explain the charges, plea, sentencing, and forfeiture without inventing a jury verdict.
- “What if the SEC had independently verified the claimed trades with a third party after an early complaint?” — a bounded regulatory-checkpoint hypothetical about detection likelihood and evidence availability, never a guaranteed alternate date, savings amount, or legal outcome.

Required structured distinctions for this case:

- `AmountKind`: `FICTITIOUS_STATEMENT_BALANCE`, `ESTIMATED_PRINCIPAL_LOSS`, `FORFEITURE_ORDER`, `RECOVERY`, or `DISTRIBUTION`.
- Every financial amount carries currency, value or bounded estimate, as-of date, source IDs, and an explanation of what it measures.
- `ProceedingType`: `CRIMINAL_CASE`, `SEC_ENFORCEMENT`, `SIPA_LIQUIDATION`, or `DOJ_VICTIM_FUND`.
- Every proceeding carries its own `ProceedingStatus`; the closed criminal case and ongoing recovery process must not share one status.
- Timeline events may be filtered by `SCHEME`, `REGULATORY`, `CRIMINAL`, or `RECOVERY` track.

## 0.2 Frozen bilingual behavior

- The interface starts in Arabic and offers a persistent `العربية | English` toggle.
- Internal code, stable IDs, JSON keys, and engineering documentation remain English.
- The curated source digests may remain English because the controlling sources are English; do not duplicate the RAG corpus merely to translate it.
- The final brief, status labels, tool explanations, errors, and disclaimers render in the selected UI language.
- Arabic legal explanations include the original English legal term on first use when it improves precision.
- Source titles, court names, docket numbers, URLs, and quoted fragments remain in their original language.
- Language selection is part of typed session state and short-term memory, not a prompt-only decoration.

## 0.3 Frozen Gemini behavior

- Use the current `google-genai` SDK behind `src/caselens/llm.py`; never use the retired `google-generativeai` package in new code.
- Runtime model ID: `gemini-3.7-flash`.
- Embedding model ID: `gemini-embedding-2`, output dimensionality `768` for this small text corpus.
- For embeddings, distinguish retrieval documents from retrieval queries using the provider's supported task/prompt convention.
- The application uses no live Google Search grounding. All case evidence comes from the curated local case pack.
- Free-tier requests may be rate-limited and their submitted content may be used by the provider to improve products. Therefore send only public court/source summaries and user questions about this public case—never secrets, private records, or personal user data.
- Verify actual model access through the explicit connection script before integration. If the account cannot access either frozen model, record the failing response and make a deliberate config-only fallback decision; never silently switch model IDs.

---

# 1. Product definition

## Product name

**CASE//LENS — Beyond the Verdict**

## One-sentence pitch

CASE//LENS is a source-grounded multi-agent research and learning assistant that helps true-crime and financial-crime enthusiasts and content creators understand one curated closed case through a cited timeline, fact-versus-claim checks, plain-language legal explanation, and bounded “What If?” exploration.

## Business problem

True-crime enthusiasts and content creators often collect case information from court records, official statements, journalism, videos, and social-media commentary. These sources are fragmented and do not carry equal authority. It is easy to mix a court finding with a party allegation, expert opinion, media summary, or public speculation. This makes research slow and increases the risk of inaccurate or harmful content.

## Target user

- A true-crime, fraud, business, or financial-crime creator preparing a responsible research brief.
- An enthusiast who wants to understand a closed case and its legal reasoning.
- A beginner learning how facts, claims, evidence, and court findings differ.

The MVP is not intended for police, investigators, legal representation, active-case participation, or professional legal advice.

## User input

- One selected case from the curated case library; the MVP contains exactly one case.
- One interaction mode:
  - `ASK_CASE`
  - `VIEW_TIMELINE`
  - `CHECK_CLAIM`
  - `EXPLAIN_VERDICT` — internal stable ID; UI label is `اشرح الحكم | Explain the Judgment` because the selected case ended in a guilty plea, not a jury verdict
  - `WHAT_IF`
- A natural-language question or a structured selection relevant to the chosen mode.

## Useful output

A structured `CaseResearchBrief` containing only the applicable sections:

- concise answer;
- verified or court-established facts;
- allegations, disputed claims, or unknowns kept separate;
- relevant timeline events;
- financial figures labeled by what they measure and their as-of date;
- plain-language legal explanation;
- bounded hypothetical impact for What If mode;
- citations with source metadata;
- confidence and limitations;
- a visible statement that the result is educational research, not legal advice.

## Business value

- Reduces time spent organizing fragmented case sources.
- Improves traceability by linking conclusions to sources.
- Helps creators avoid presenting allegations or speculation as established fact.
- Makes court reasoning and evidence status easier for non-specialists to understand.
- Prevents fictitious balances, principal loss, forfeiture, recovery, and distributions from being collapsed into one misleading number.
- Produces a reusable, cited research brief rather than an unsupported chatbot answer.

## Why a normal search page or single agent is insufficient

- Source verification, legal explanation, timeline reasoning, and counterfactual analysis require different context and authority boundaries.
- Financial-amount semantics and proceeding status require deterministic validation rather than fluent guesswork.
- The user’s selected mode should dynamically change routing and tool use.
- The system must preserve conversation context while keeping evidence status explicit.
- A reviewer must detect unsupported or overconfident wording before the final result.
- Structured state is needed to join specialist findings and citations safely.

---

# 2. Fixed MVP scope

## Included

- Exactly one curated closed case.
- Pre-approved, locally stored knowledge documents.
- One Streamlit application.
- One Supervisor and four bounded specialists.
- Typed shared state and short-term session memory.
- Agentic RAG with source metadata and one possible query reformulation.
- Three deterministic local tools beyond RAG.
- Five interaction modes.
- A safe observable execution timeline.
- Offline automated tests using fake model and embedding clients.
- One explicit live model connection test.
- One complete happy-path demo and at least two failure paths.
- Professional GitHub documentation and meaningful commits from both teammates.

## Excluded before submission

- Live web research at runtime.
- Arbitrary user-entered cases.
- Ongoing or unresolved cases.
- Identifying or accusing new suspects.
- Contacting victims, families, witnesses, or authorities.
- Psychological or medical diagnosis generated by the model.
- Graphic crime-scene media.
- Voice generation, podcast generation, or video generation.
- Browser automation.
- Authentication, user accounts, or multi-user persistence.
- More than one case.
- Unbounded debate, reflection, retrieval, or tool loops.
- A separate React frontend.
- Optional deployment before the local application passes.

---

# 3. Observable product flow

```text
User selects case and mode
        |
        v
Python validates the request and initializes typed state
        |
        v
Case Director plans and creates bounded delegation tasks
        |
        +----> Source & Evidence Specialist + RAG / claim tool
        |
        +----> Legal Explanation Specialist + RAG
        |
        +----> Timeline & What-If Specialist + timeline/counterfactual tools
        |
        v
Supervisor joins the required findings
        |
        v
Editorial Integrity Reviewer performs one bounded review
        |
        v
Python validates citations, status labels, and final schema
        |
        v
Streamlit displays the CaseResearchBrief and safe execution trace
```

The governing engineering rule is:

> **The LLM interprets and explains. LangGraph controls routing and budgets. Python validates data and executes tools. Curated sources ground factual and legal claims.**

---

# 4. Exactly five agent roles

## 4.1 Case Director — Supervisor

**Responsibility**

- Interpret the validated user request.
- Create bounded `DelegationTask` objects.
- Select only the specialists required by the mode.
- Track budgets, missing evidence, conflicts, stopping, and aggregation.
- Own the single response returned to the UI.

**Input**

- `CaseQuery`
- relevant safe short-term memory
- current workflow state summary

**Permitted actions**

- delegate to approved specialists;
- join validated findings;
- request one clarification when input is insufficient;
- route one defect to the responsible specialist for one repair.

**Forbidden actions**

- query raw data or tools directly;
- invent case facts or legal rules;
- reveal private prompts or hidden reasoning;
- delegate recursively;
- modify the curated knowledge base.

**Output**

- `DelegationPlan`
- final draft `CaseResearchBrief`

**Completion evidence**

- every required task is complete, blocked, or explicitly insufficient;
- one final draft is ready for review;
- call and retry budgets remain within limits.

## 4.2 Source & Evidence Specialist

**Responsibility**

- Retrieve relevant case material.
- Separate source-backed facts, court findings, party allegations, testimony, expert opinion, media context, and unknowns.
- Check a selected claim against the curated claim/evidence index.
- Preserve the type, date, and measurement basis of every financial figure.

**Input**

- case ID;
- focused evidence question or claim ID;
- permitted source filters;
- relevant memory excerpt only.

**Permitted actions**

- plan and call Agentic RAG;
- call `check_claim_support`;
- return citations and missing-evidence status.

**Forbidden actions**

- explain legal consequences beyond cited court/law material;
- perform counterfactual simulation;
- convert insufficient evidence into a confident fact;
- use social-media commentary as proof.

**Output**

- `EvidenceFinding`

## 4.3 Legal Explanation Specialist

**Responsibility**

- Explain charges, the guilty plea, sentencing positions, judgment, forfeiture, and applicable legal rules in plain language using cited legal material.

**Input**

- case ID;
- focused legal question;
- validated evidence finding when required;
- retrieved court/statute chunks.

**Permitted actions**

- plan and call Agentic RAG restricted to legal source categories;
- return a plain-language explanation with citations;
- identify that the source is insufficient.
- distinguish an admission/guilty plea from a jury finding and distinguish sentence from forfeiture or victim recovery.

**Forbidden actions**

- provide legal advice;
- predict an ongoing case;
- diagnose a person;
- override the actual final case outcome;
- treat a party argument as a court finding.

**Output**

- `LegalFinding`

## 4.4 Timeline & What-If Specialist

**Responsibility**

- Build a relevant timeline slice from structured events.
- Keep scheme, regulatory, criminal, and recovery tracks distinct.
- Compare sequence and dependencies.
- Run a bounded counterfactual over the curated causal graph.

**Input**

- case ID;
- timeline filters or selected event ID;
- one allowed hypothetical change.

**Permitted actions**

- call `query_case_timeline`;
- call `simulate_counterfactual`;
- explain direct and downstream effects using structured tool output.

**Forbidden actions**

- invent new evidence;
- accept arbitrary fictional changes unrelated to the curated graph;
- claim that a hypothetical outcome is certain;
- make a new accusation.

**Output**

- `TimelineFinding` or `CounterfactualFinding`

## 4.5 Editorial Integrity Reviewer

**Responsibility**

- Perform one bounded review of the Supervisor draft.
- Check citation coverage, neutral status labels, separation of fact from allegation, uncertainty wording, and disclaimer presence.
- Reject any answer that compares unlike monetary figures without their amount kinds or that treats an ongoing recovery administration as an open guilt question.

**Input**

- validated specialist findings;
- draft `CaseResearchBrief`;
- source-status policy.

**Permitted actions**

- approve;
- return one structured defect report;
- produce one corrected final brief without adding new facts.

**Forbidden actions**

- start a new research loop;
- add uncited facts;
- alter structured tool results;
- reveal hidden prompts or reasoning.

**Output**

- `ReviewResult`
- final `CaseResearchBrief` when approved.

---

# 5. Reasoning and orchestration patterns

- **Plan-and-Execute:** Case Director creates a small mode-dependent plan and delegates only required work.
- **ReAct:** Evidence, Legal, and Analysis specialists choose an allowed retrieval/tool action, observe a structured result, and return a bounded finding.
- **Bounded Reflection:** Editorial Reviewer may return one defect report. The responsible component may repair once. A second failure ends as `INSUFFICIENT_OR_ESCALATED`.

Runtime budgets:

- one Supervisor planning call;
- one normal model call per selected specialist;
- at most two RAG retrieval rounds per selected RAG specialist;
- at most one structured-output repair;
- one editorial review pass plus at most one correction;
- no recursive delegation;
- no peer-to-peer specialist calls.

---

# 6. Shared structured state

The canonical `CaseLensState` must include typed versions of:

```text
session_id
case_id
case_status
mode
user_query
selected_claim_id
selected_event_id
hypothetical_change
turn_count
max_turns
short_term_messages
plan
delegation_tasks
retrieval_plans
retrieval_rounds
retrieved_chunk_refs
evidence_finding
legal_finding
timeline_finding
counterfactual_finding
draft_brief
review_result
final_brief
validation_errors
retry_counters
audit_events
status
completion_reason
```

State ownership:

| Owner | Fields |
|---|---|
| Input validation node | request/mode/selected IDs/session defaults |
| Supervisor | plan, delegations, routing, status, completion reason |
| Evidence Specialist | retrieval evidence and `evidence_finding` |
| Legal Specialist | legal retrieval and `legal_finding` |
| Timeline/What-If Specialist | tool observations and analysis findings |
| Reviewer | review result and final brief |
| Reducers | append-only messages, retrieval refs, errors, audit events |

No component may write another component’s owned result field.

---

# 7. Memory boundaries

## Short-term memory

- Preserve the active session’s user questions and safe final answers.
- Preserve selected case, last mode, referenced claim/event IDs, and concise finding summaries.
- Allow follow-ups such as “Why did the court reject that argument?”
- Do not persist private chain-of-thought or raw model payloads.
- Reset creates a new session and clears short-term memory.

## Long-term knowledge

- The curated case and legal knowledge base is read-only at runtime.
- Do not implement personal user memory in the MVP.
- Do not allow agents to write back into source documents.

---

# 8. Knowledge base and Agentic RAG

## Knowledge package

For the selected case, create concise research documents under `knowledge_base/case_001/`:

1. `01_case_overview_and_ponzi_mechanism.md`
2. `02_verified_timeline.md`
3. `03_claims_red_flags_and_records.md`
4. `04_guilty_plea_charges_and_sentence.md`
5. `05_regulatory_failure_and_applicable_law.md`
6. `06_victim_recovery_and_editorial_policy.md`

Each document must begin with YAML metadata:

```text
document_id
title
case_id
source_type
source_tier
jurisdiction
case_status
version
effective_or_published_date
last_reviewed
original_source_urls
classification
```

Every factual or legal statement in a team-authored digest must be traceable to a listed original source. Do not copy long copyrighted articles. Prefer official/public-domain material and concise team-authored summaries with links.

## Source tiers

| Tier | Meaning | Use |
|---|---|---|
| A | Official judgment, statute, court docket, government record | May ground facts, legal explanation, and final result |
| B | Official agency statement or reliable public record | May ground facts with context |
| C | Reputable journalism | Context and reported details; label as reporting |
| D | Commentary, creator video, forum, social media | Not core evidence; exclude from MVP RAG or label only as public commentary |

## Offline preparation

```text
Approved documents
  -> validate metadata and source links
  -> normalize text
  -> chunk by H2 section
  -> generate embeddings
  -> store vectors plus metadata in a transparent local NumPy index
  -> write an index manifest
```

Generated index files live under `storage/` and are ignored by Git. Source documents and validation manifests are committed.

## Runtime Agentic RAG

1. Specialist creates `RetrievalPlan`.
2. Python validates the query and source-category filters.
3. `search_knowledge` retrieves top-k chunks with metadata.
4. Specialist returns `EvidenceAssessment`.
5. If insufficient, the specialist may reformulate once.
6. After two rounds, return a cited finding or explicit insufficient evidence.

Retrieved chunks must contain:

```text
chunk_id
document_id
file_path
heading
excerpt
similarity_score
source_type
source_tier
jurisdiction
original_source_urls
```

RAG must affect a decision or final answer. It is not sufficient to display retrieved text in a panel.

---

# 9. Three required local tools beyond RAG

## Tool 1 — `query_case_timeline`

Input:

```text
case_id
start_date | None
end_date | None
actor_ids | []
event_types | []
phase | None
track: SCHEME | REGULATORY | CRIMINAL | RECOVERY | None
```

Output:

```text
status
query_id
events with stable event/evidence/source IDs
summary
safe_error
```

Required errors: invalid date range, unsupported filter, unknown case, and no results.

## Tool 2 — `check_claim_support`

Input:

```text
case_id
claim_id
permitted_evidence_ids | []
```

Output:

```text
status: supported | contradicted | partially_supported | insufficient_evidence
supporting_evidence_ids
contradicting_evidence_ids
missing_information
source_ids
financial_amounts with amount_kind, currency, value_or_range, as_of_date, and measurement_note when relevant
```

The tool is deterministic over the curated claim/evidence map. The LLM may explain the result but cannot change its status.

## Tool 3 — `simulate_counterfactual`

Input:

```text
case_id
event_id
allowed_change_id
```

Output:

```text
status
changed_assumption
directly_affected_nodes
downstream_possible_effects
unchanged_facts
unknowns
confidence_label
mandatory_hypothetical_disclaimer
```

The tool traverses only a curated dependency graph. It must reject arbitrary changes and must never return certainty about an alternative verdict.

## Dynamic selection evidence

- Timeline request selects Tool 1.
- Claim-verification request selects Tool 2.
- What If request selects Tool 3.
- Explain-judgment request (`EXPLAIN_VERDICT` internally) normally uses legal RAG and does not call all tools decoratively.

---

# 10. Safe observability

The UI may show:

```text
Case Director -> selected EXPLAIN_VERDICT route
Evidence Specialist -> retrieved 3 chunks from 2 source documents
Legal Specialist -> evidence sufficient; produced cited finding
Timeline Specialist -> called query_case_timeline; 5 events returned
Editorial Reviewer -> citation and neutrality checks passed
Workflow -> completed
```

The UI must not show:

- raw chain-of-thought;
- hidden system prompts;
- raw model payloads;
- API keys or environment values;
- unapproved source documents;
- uncited allegations presented as facts;
- private personal data.

---

# 11. Technology baseline

- Python 3.11+
- Streamlit
- LangGraph
- Pydantic v2
- Google Gemini Developer API through one `src/caselens/llm.py` boundary using the current `google-genai` SDK
- runtime model `gemini-3.7-flash`
- embedding model `gemini-embedding-2` with 768 output dimensions for the MVP
- transparent local NumPy vector index, matching the course lab pattern
- python-dotenv
- pytest with fake model and embedding clients
- Ruff if setup remains lightweight
- GitHub Actions for offline tests on pull requests

The API key must be read from environment/Streamlit secrets and remain empty in `.env.example`; the frozen non-secret model IDs may be committed. Verify one minimal request, one structured response, one tool-selection-compatible response, and one 768-dimensional embedding before building the complete live path. Do not silently change model IDs when access fails.

Normal tests must not require an API key or consume live API credit.

---

# 12. Target repository

```text
caselens/
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── .github/
│   ├── workflows/
│   │   └── ci.yml
│   ├── ISSUE_TEMPLATE/
│   │   └── task.yml
│   └── pull_request_template.md
├── docs/
│   ├── project_definition.md
│   ├── architecture.md
│   ├── agent_contracts.md
│   ├── integration_contract.md
│   ├── source_policy.md
│   ├── rubric_evidence.md
│   ├── demo_script.md
│   └── prompts/
│       ├── 00_CASELENS_MASTER_CONTEXT.md
│       ├── 01_SHAHAD_CODEX_TRACK.md
│       ├── 02_TEAMMATE_CLAUDE_TRACK.md
│       └── 03_START_HERE_AR.md
├── data/
│   └── cases/
│       └── case_001/
│           ├── case_metadata.json
│           ├── timeline.json
│           ├── claims.json
│           ├── evidence.json
│           ├── financial_amounts.json
│           ├── causal_graph.json
│           └── source_manifest.json
├── knowledge_base/
│   └── case_001/
│       └── *.md
├── scripts/
│   ├── build_knowledge_index.py
│   ├── check_model_connection.py
│   ├── validate_case_pack.py
│   └── final_audit.py
├── storage/
│   └── .gitkeep
├── src/
│   └── caselens/
│       ├── __init__.py
│       ├── config.py
│       ├── contracts.py
│       ├── protocols.py
│       ├── llm.py
│       ├── state.py
│       ├── memory.py
│       ├── graph.py
│       ├── supervisor.py
│       ├── reviewer.py
│       ├── ui.py
│       ├── adapters.py
│       ├── specialists/
│       │   ├── evidence.py
│       │   ├── legal.py
│       │   └── timeline_analysis.py
│       ├── rag/
│       │   ├── loaders.py
│       │   ├── chunking.py
│       │   ├── index.py
│       │   └── retriever.py
│       ├── tools/
│       │   ├── timeline.py
│       │   ├── claim_support.py
│       │   └── counterfactual.py
│       └── services/
│           ├── case_loader.py
│           └── result_builder.py
└── tests/
    ├── fixtures/
    ├── test_contracts.py
    ├── test_case_data.py
    ├── test_rag.py
    ├── test_tools.py
    ├── test_specialists.py
    ├── test_routing.py
    ├── test_memory.py
    └── test_end_to_end.py
```

---

# 13. Parallel ownership contract

## Shahad + Codex — Track A

Owns:

```text
AGENTS.md
app.py
.github/
src/caselens/config.py
src/caselens/contracts.py
src/caselens/protocols.py
src/caselens/state.py
src/caselens/memory.py
src/caselens/graph.py
src/caselens/supervisor.py
src/caselens/reviewer.py
src/caselens/ui.py
src/caselens/adapters.py
src/caselens/services/result_builder.py
tests/test_contracts.py
tests/test_routing.py
tests/test_memory.py
tests/test_end_to_end.py
docs/architecture.md
docs/integration_contract.md
final README integration
```

## Teammate + Claude Code — Track B

Owns:

```text
CLAUDE.md
data/
knowledge_base/
scripts/build_knowledge_index.py
scripts/validate_case_pack.py
src/caselens/rag/
src/caselens/tools/
src/caselens/specialists/
src/caselens/services/case_loader.py
tests/test_case_data.py
tests/test_rag.py
tests/test_tools.py
tests/test_specialists.py
docs/source_policy.md
source/data/RAG/tool README notes
```

## Shared files that require coordination

```text
requirements.txt
.env.example
.gitignore
README.md
src/caselens/contracts.py
src/caselens/protocols.py
docs/rubric_evidence.md
```

After the Foundation PR merges, Track B must not edit shared contracts directly. If a contract change is necessary:

1. Open a GitHub Issue labeled `contract-change`.
2. Describe old schema, proposed schema, reason, affected files, and tests.
3. Both teammates approve in the Issue.
4. Shahad updates the shared contract in a small PR.
5. Both branches merge the new `main` before continuing.

---

# 14. How parallel work avoids waiting

Track A implements the graph and UI against fake implementations of the specialist protocols.

Track B implements real specialists, RAG, tools, and case loaders against the same frozen protocols.

The shared integration contract defines callable boundaries such as:

```text
EvidenceSpecialist.execute(task, state_view) -> EvidenceFinding
LegalSpecialist.execute(task, state_view) -> LegalFinding
TimelineAnalysisSpecialist.execute(task, state_view) -> TimelineFinding | CounterfactualFinding
```

Track A’s fake adapters return valid deterministic findings with test citations. Track B’s real adapters return the same contracts. Integration replaces the fakes through a factory/configuration boundary rather than rewriting the graph.

There are only three required synchronization gates:

1. **Decision and Contract Gate:** choose the case/provider/language and merge typed contracts.
2. **Backend Integration Gate:** Track B proves data, RAG, tools, and specialists; Track A updates from `main` and replaces fakes.
3. **Release Gate:** both review the final end-to-end app, documentation, and demo.

---

# 15. GitHub source-of-truth workflow

Codex and Claude Code do not share conversational memory. GitHub is the source of truth.

## Repository setup

1. One teammate creates one public repository named `caselens-agentic-capstone`.
2. Add the other teammate as a collaborator.
3. Commit this prompt pack to `docs/prompts/` on `main`.
4. Create a GitHub Project using Board view.
5. Use columns: `Todo`, `In Progress`, `In Review`, `Blocked`, `Done`.
6. Create one GitHub Issue per checkpoint and assign exactly one owner.
7. Connect each Pull Request to its Issue using `Closes #<issue-number>`.

GitHub Projects can track Issues and Pull Requests in a board that stays synchronized with GitHub data. Pull Requests should run automated offline checks so both teammates can see a pass/fail result before merge.

## Branches

```text
main
foundation/shared-contracts
research/case-source-pack
feat/orchestration-ui
feat/evidence-rag-tools
fix/<short-name>
```

## No-wait startup

- Shahad starts `foundation/shared-contracts`.
- At the same time, the teammate starts `research/case-source-pack` and changes only `data/`, `knowledge_base/`, and source documentation.
- When foundation merges, the teammate merges `origin/main` into her branch before implementing Python modules.
- After contracts are frozen, Shahad starts graph/UI with fakes while the teammate builds the real backend.

## Safe branch update

```bash
git status
git fetch origin
git switch <your-branch>
git merge origin/main
pytest -q
```

Resolve any conflict before new work. Never use `git reset --hard`, force push, or overwrite the other track.

## Checkpoint completion rule

When a checkpoint is complete, the owner must:

1. Run the required local checks.
2. Commit only reviewed files.
3. Push the branch.
4. Open or update the Pull Request.
5. Link the Issue.
6. Move the Project item to `In Review`.
7. Add this handoff comment:

```text
CHECKPOINT HANDOFF
Owner:
Branch:
Commit:
Issue:
Files changed:
Acceptance criteria met:
Tests run and actual result:
Manual check:
Known limitations:
Contract changes: none | link
Reviewer action needed:
```

The reviewer checks the diff, CI result, and acceptance evidence. After merge, the linked Issue closes and the Project item moves to `Done` manually or through Project automation.

## Pull Request merge order

1. Prompt pack / decisions.
2. Foundation and shared contracts.
3. Case source/data validation.
4. Track B backend PR: RAG, tools, specialists.
5. Track A integration PR: graph, UI, real adapters, end-to-end tests.
6. Documentation/demo corrections.

Before merging a branch that is behind `main`, update it from the base branch and rerun checks. Do not merge two branches that both modify a frozen shared file without resolving ownership first.

---

# 16. GitHub Project issue plan

Create these issues:

| ID | Issue | Owner | Dependency | Completion evidence |
|---|---|---|---|---|
| D0 | Record frozen case, Gemini models, bilingual UI, and team identities | Both | None | Decision table complete |
| A0 | Repository guardrails, CI, schemas, protocols | Shahad | D0 partly | Foundation PR + tests |
| B0 | Curate source manifest and case research plan | Teammate | D0 case | Source review PR |
| A1 | Typed state, memory, supervisor routing with fakes | Shahad | A0 | Routing tests |
| B1 | Structured case data and validation | Teammate | B0 + A0 contracts | Data tests |
| A2 | LangGraph orchestration and bounded reviewer | Shahad | A1 | Headless workflow tests |
| B2 | RAG preparation and retrieval | Teammate | B1 | Retrieval tests + citations |
| B3 | Three deterministic tools | Teammate | B1 | Tool tests + failures |
| A3 | Functional unstyled Streamlit shell | Shahad | A1 | Manual flow with fakes |
| B4 | Three real specialists | Teammate | B2 + B3 | Specialist contract tests |
| I0 | Integrate real adapters and run E2E | Shahad + review by teammate | A2 + A3 + B4 | End-to-end tests + app walkthrough |
| R0 | README, rubric map, demo, secret audit | Both | I0 | Release checklist |
| UI0 | Visual design polish | Shahad | I0 stable | No functional regression |
| DEPLOY | Streamlit Community Cloud deployment attempt | Shahad | R0; UI0 only if used | Public happy/failure path or documented safe failure |

`UI0` must remain blocked until `I0` is complete. This protects the core functionality from design-driven scope expansion. `DEPLOY` is planned but remains blocked until the complete local release passes; a failed cloud attempt must preserve the local fallback.

---

# 17. Continuous integration requirement

The Foundation checkpoint creates `.github/workflows/ci.yml` that runs on Pull Requests to `main` and on pushes to `main`:

```text
checkout
setup Python 3.11
install requirements
python -m compileall app.py src tests
pytest -q
optional ruff check when configured
```

CI must use fake model/embedding clients and require no secrets. A Pull Request is not ready to merge when CI fails.

Do not spend the deadline configuring advanced coverage services, merge queues, or complex branch rules. A simple visible test check and peer review are sufficient for this two-person capstone.

---

# 18. Mandatory assistant behavior

Every Codex or Claude Code prompt inherits these rules:

1. Read this file and the assigned track file completely.
2. Inspect branch and `git status` before editing.
3. State the exact files to be changed.
4. Stay inside the current checkpoint and owned paths.
5. Preserve user and teammate changes.
6. Use the frozen Pydantic contracts.
7. Run offline tests and report actual output.
8. Do not make a live API call unless that checkpoint explicitly requests it.
9. Do not read, print, or commit `.env` or secrets.
10. Do not expose chain-of-thought or raw prompts in the application.
11. Do not claim a feature works without a command or manual reproduction.
12. Stop after the checkpoint. Never continue automatically.

Mandatory assistant handoff:

```text
CHECKPOINT RESULT
- Status: complete | partial | blocked
- Acceptance criteria met:
- Acceptance criteria not met:

FILES CHANGED
- path: purpose

VERIFICATION
- command: actual result
- manual check: actual result

INTEGRATION CONTRACT
- schemas/protocols used:
- contract changes: none | details

KNOWN LIMITATIONS
- ...

SAFE NEXT STEP
- Name only; do not execute.
```

---

# 19. Rubric-to-evidence map

| Rubric item | Runtime evidence | Repository evidence |
|---|---|---|
| Business problem, user, value | Briefing and final research brief | `docs/project_definition.md`, README |
| Supervisor + meaningful specialists | Mode-dependent routing visible in trace | graph and specialist modules |
| Agent contracts | Validated inputs/outputs and allowlists | `contracts.py`, `protocols.py`, `docs/agent_contracts.md` |
| Delegation/reasoning | Plan, specialist selection, retrieval/tool events | `graph.py`, `supervisor.py`, architecture docs |
| Structured handoffs | Pydantic findings and state ownership | `contracts.py`, `state.py` |
| Stopping/aggregation | final review, insufficient-evidence, budget stop | routing tests and final status |
| Structured state | typed case session | `state.py`, state panel |
| Short-term memory | follow-up question uses prior safe context | `memory.py`, memory test |
| Agentic RAG | plan, retrieve, assess, optional reformulation | `rag/`, retrieval panel |
| Embeddings/vector store | generated local index | ingestion script and manifest |
| Retrieval metadata | source tier/file/heading/URL/chunk | evidence cards and tests |
| Evidence affects result | cited legal/evidence finding changes answer | final brief and demo |
| Tool 1 | timeline request | timeline module/trace |
| Tool 2 | claim check request | claim module/trace |
| Tool 3 | What If request | counterfactual module/trace |
| Validation/errors | typed inputs/results and safe failures | tests and UI failure states |
| Complete app | select case through final result | `app.py`, E2E test |
| Safe observability | agent/retrieval/tool/status trace | UI timeline |
| Presentation | five-minute scripted scenario | `docs/demo_script.md` |
| GitHub/docs | clean clone, CI, commits, README | repository root and Actions |

---

# 20. Release definition of done

- [ ] Decision table contains real implementation values and collaborator setup is confirmed.
- [ ] Selected case is closed and source manifest passes human review.
- [ ] One Supervisor and four specialist roles are implemented with distinct contracts.
- [ ] Mode-dependent delegation is visible.
- [ ] Shared state and short-term memory are explicit.
- [ ] RAG performs preparation, embedding, local vector storage, metadata retrieval, and evidence use.
- [ ] Three tools beyond RAG are selected dynamically and affect results.
- [ ] Invalid input, missing evidence, malformed model output, and tool failure are safe.
- [ ] The full Streamlit path works locally.
- [ ] UI shows stage, agent, retrieval, tool, citations, and final status without hidden reasoning.
- [ ] Tests run offline and CI passes.
- [ ] `.env.example` exists and no secret is tracked.
- [ ] README contains every required course/GitHub item and SDAIA Academy acknowledgement/link.
- [ ] Both teammates have meaningful commits and can explain their track and the integrated architecture.
- [ ] Demo includes one happy path, one failure, one limitation, and one future improvement.
- [ ] Optional deployment is attempted only after all mandatory items pass.

---

# 21. Final instruction

Build the smallest complete, source-grounded CASE//LENS vertical slice. Do not optimize for code volume, number of agents, or visual effects. Optimize for a working demonstration in which every major rubric requirement is visible, testable, and explainable by both teammates.
