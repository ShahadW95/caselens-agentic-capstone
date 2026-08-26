---
title: "CASE//LENS — Shahad + Codex Track A"
owner: "Shahad"
assistant: "Codex"
track: "Foundation, contracts, orchestration, memory, functional UI, integration, release"
depends_on: "00_CASELENS_MASTER_CONTEXT.md"
status: "v1.1 — Madoff case revision"
---

# CASE//LENS — Shahad + Codex Track A

## Your responsibility

You own the system spine: repository guardrails, typed contracts, shared state, short-term memory, Supervisor, LangGraph orchestration, bounded reviewer, functional Streamlit interface, integration, and final release evidence.

You do not own the curated case data, RAG implementation, deterministic case tools, or the three real specialist implementations. Build against frozen protocols and fake adapters until the teammate’s backend merges.

## How to use this track

1. Read `00_CASELENS_MASTER_CONTEXT.md` completely.
2. Fill the decision table before live model or case implementation.
3. Execute one prompt below at a time.
4. Begin every prompt on its named branch or confirm the current branch.
5. Review the diff and test output.
6. Commit and push the checkpoint.
7. Update its GitHub Issue/Project item.
8. Stop before the next prompt.

Use this session header before every prompt:

```text
Read docs/prompts/00_CASELENS_MASTER_CONTEXT.md and docs/prompts/01_SHAHAD_CODEX_TRACK.md completely. Inspect the current branch, git status, recent commits, and the files relevant to this checkpoint.

Execute only Prompt A[NUMBER].
Current branch: [BRANCH].
Linked GitHub Issue: [ISSUE].
Do not edit Track B-owned files. Preserve all existing and teammate-authored work. Before editing, report the current state and exact files you intend to change. Stop after the checkpoint handoff report.
```

---

# PROMPT A0 — FOUNDATION, GITHUB GUARDRAILS, AND FROZEN CONTRACTS

## Purpose

Create the shared foundation that lets both tracks work independently. This is the only implementation checkpoint that Track B must depend on before writing Python modules.

## Branch

```text
foundation/shared-contracts
```

## May edit

```text
AGENTS.md
README.md
app.py
requirements.txt
.env.example
.gitignore
.github/
docs/project_definition.md
docs/architecture.md
docs/agent_contracts.md
docs/integration_contract.md
docs/rubric_evidence.md
src/caselens/__init__.py
src/caselens/config.py
src/caselens/contracts.py
src/caselens/protocols.py
src/caselens/llm.py
src/caselens/adapters.py
tests/test_contracts.py
tests/fixtures/
package marker and empty directories required by the target structure
```

## Must not edit

```text
substantive files under data/
substantive files under knowledge_base/
src/caselens/rag/
src/caselens/tools/
src/caselens/specialists/
Track B test files
```

## Copy this prompt into Codex

```text
We are implementing Prompt A0 for CASE//LENS. Read the shared master context completely before editing.

Inspect the current folder, branch, git status, and existing user/teammate files. Provide a concise foundation plan and list the exact files you will change. Stop if the folder contains a conflicting unrelated application or unresolved merge changes.

Create the Python 3.11+ repository foundation for Streamlit, LangGraph, Pydantic v2, python-dotenv, one Google Gemini provider boundary using the current `google-genai` package, a transparent local vector-index dependency boundary, pytest, and optional Ruff. Keep requirements minimal. Use only the frozen model identifiers from the master context; do not substitute preview/legacy models.

Create:

1. `AGENTS.md` with:
   - inspect-before-edit rule;
   - Track A and Track B ownership paths from the master context;
   - shared-file change protocol;
   - architecture boundaries;
   - offline-test requirement;
   - secret-safety rules;
   - no chain-of-thought rule;
   - no destructive Git commands or force push;
   - mandatory checkpoint handoff format.

2. `.gitignore` that excludes:
   - `.env` and local secrets;
   - Python caches and virtual environments;
   - generated vector indexes and local storage;
   - Streamlit secrets;
   - IDE/system temporary files;
   - test and coverage caches.

3. `.env.example` with `GEMINI_API_KEY=` empty and safe non-secret defaults for `GEMINI_CHAT_MODEL=gemini-3.7-flash`, `GEMINI_EMBEDDING_MODEL=gemini-embedding-2`, and `GEMINI_EMBEDDING_DIMENSIONS=768`. Never create, read, or inspect a real `.env`.

4. `requirements.txt` with only dependencies needed by the approved stack, including the current `google-genai` SDK. Do not add the retired `google-generativeai` package, multiple LLM frameworks, vector stores, UI frameworks, or databases.

5. `.github/workflows/ci.yml` that runs on pull requests to `main` and pushes to `main`, uses Python 3.11, installs dependencies, compiles Python, runs `pytest -q`, and runs Ruff only if configured. CI must require no secret and no live API call.

6. `.github/pull_request_template.md` requiring:
   - linked Issue;
   - track/owner;
   - owned files changed;
   - acceptance criteria;
   - tests with actual results;
   - manual verification;
   - contract change declaration;
   - screenshots only when relevant;
   - reviewer checklist.

7. `.github/ISSUE_TEMPLATE/task.yml` with owner, branch, dependency, allowed paths, acceptance criteria, verification command, and blocker fields.

8. README outline containing every mandatory section from the capstone rubric, including the Advanced Agentic AI Systems Engineering and SDAIA Academy acknowledgement/link. Mark unimplemented sections as checkpoint status, not as complete features.

9. Documentation:
   - `docs/project_definition.md`: problem, target user, input, output, value, why multi-agent, MVP exclusions, completion condition;
   - `docs/architecture.md`: exactly one Supervisor and four specialists, reasoning patterns, state, RAG, tools, safe observability, stopping, and a Mermaid workflow diagram;
   - `docs/agent_contracts.md`: every role’s responsibility, input, allowed actions, forbidden actions, output, completion evidence;
   - `docs/integration_contract.md`: protocol method signatures, contract version `v1`, fake-versus-real adapter behavior, ownership, and contract-change process;
   - `docs/rubric_evidence.md`: map every rubric row to a planned file, runtime evidence, test, demo action, owner, and current status.

10. Strict Pydantic models and enums in `src/caselens/contracts.py` for at least:
    - `InteractionMode`;
    - `WorkflowStatus`;
    - `SourceTier` and `ClaimStatus`;
    - `AmountKind`, `FinancialAmount`, `ProceedingType`, `ProceedingStatus`, and `ProceedingRecord`;
    - `CaseQuery`;
    - `SafeMessage`;
    - `DelegationTask` and `DelegationPlan`;
    - `SourceCitation`;
    - `RetrievalPlan`, `RetrievedChunk`, and `EvidenceAssessment`;
    - `EvidenceFinding`;
    - `LegalFinding`;
    - `TimelineEvent` and `TimelineFinding`;
    - `CounterfactualFinding`;
    - `ReviewDefect`, `ReviewResult`;
    - `AuditEvent`;
    - `CaseResearchBrief`;
    - `SafeError`.

Contract rules:
    - citations carry stable source/document/chunk/heading/type/tier identifiers and original URL where available;
    - findings separate established facts, allegations, disputed items, and unknowns;
    - confidence is bounded;
    - counterfactual output always contains a hypothetical disclaimer and unknowns;
    - final brief cannot label an allegation as an established fact;
    - defined boundaries must not use free-form dictionaries;
    - no raw chain-of-thought field exists;
    - user/session contracts include a validated language value `ar` or `en`;
    - case ID is allowlisted as `US_SDNY_09CR00213_DC` for the MVP;
    - every monetary figure includes its `AmountKind`, currency, as-of date, sources, and measurement note so fictitious statement balances are never confused with principal loss, forfeiture, recovery, or distribution;
    - the closed criminal case and the separately ongoing SIPA recovery process use distinct typed proceeding records and statuses.

11. Protocols in `src/caselens/protocols.py` for the three backend specialists and reviewer/model boundaries. The callable signatures must match the shared master context and return the strict contracts.

12. `src/caselens/config.py` with safe missing-credential behavior and no secret logging. Configuration must accept the same values from local environment variables and Streamlit Community Cloud secrets without committing either. The provider boundary must send no private user profile or secret content.

13. One `src/caselens/llm.py` boundary shell. Do not scatter client creation across files and do not make a live call in this checkpoint.

14. Deterministic fake specialist adapters in `src/caselens/adapters.py` for Track A tests. Clearly mark them as test/demo-development fakes. They must return valid contracts with fictional source IDs and must never be selected in final live mode.

15. A minimal Streamlit app showing:
    - project title and clear MVP description;
    - `Foundation ready` checkpoint status;
    - the five role contracts;
    - a safe setup warning when provider configuration is missing;
    - no live model call.

16. Offline tests for:
    - import smoke check;
    - enum and confidence validation;
    - required citations;
    - invalid status mixing;
    - counterfactual disclaimer requirement;
    - protocol/fake adapter compatibility;
    - `.env` ignored;
    - no secret values in committed sample configuration.

Do not implement state, LangGraph routing, memory, live agents, RAG, tools, case content, or visual styling yet.

Run:
- `python -m compileall app.py src tests`
- `pytest -q`
- a Streamlit startup smoke check without a key.

Stop and return the mandatory checkpoint handoff. Explicitly state whether the integration contract is ready to freeze as `v1`.
```

## Acceptance evidence

- CI file exists and normal tests require no API key.
- Contracts reject unsupported/malformed outputs.
- Fake adapters implement the same protocols expected from Track B.
- Streamlit starts safely without calling a model.
- README and rubric map contain all mandatory headings.
- Teammate reviews the Foundation PR before merge.

## Human action after A0

1. Push the branch.
2. Open a PR linked to Issue A0.
3. Ask the teammate to review `contracts.py`, `protocols.py`, and `integration_contract.md` first.
4. Merge only after CI passes and both agree.
5. Both tracks merge the new `main`.

---

# PROMPT A1 — TYPED STATE, MEMORY, AND MODE ROUTING WITH FAKES

## Purpose

Implement the orchestration skeleton without waiting for Track B. Every route uses fake adapters that match the frozen `v1` protocols.

## Branch

```text
feat/orchestration-ui
```

## May edit

```text
src/caselens/state.py
src/caselens/memory.py
src/caselens/supervisor.py
src/caselens/graph.py
src/caselens/adapters.py
tests/test_routing.py
tests/test_memory.py
docs/architecture.md
docs/integration_contract.md only for clarifications that do not change v1
```

## Copy this prompt into Codex

```text
Implement Prompt A1 only. Read the master context, AGENTS.md, frozen v1 contracts/protocols, and relevant tests. Confirm that the branch contains the merged Foundation checkpoint. Do not edit Track B files or change the v1 schemas.

Before editing, report the current state and files to change.

Implement:

1. Typed `CaseLensState` with all required master-context fields and safe defaults.
2. A new-session factory with stable session ID, turn budget, empty append-only collections, and no hidden mutable global.
3. Short-term memory that preserves safe user/final messages, selected IDs, and concise finding summaries. It must support follow-up references without storing raw chain-of-thought or model payloads.
4. A deterministic pre-router that validates mode-specific input:
   - ASK_CASE requires a question;
   - VIEW_TIMELINE accepts optional filters;
   - CHECK_CLAIM requires a known-looking claim ID contract value;
   - EXPLAIN_VERDICT requires a focused question or default judgment question; keep the stable internal enum but display `اشرح الحكم | Explain the Judgment` because Madoff pleaded guilty and there was no jury verdict;
   - WHAT_IF requires event ID and allowed change ID.
5. A Supervisor planning boundary that creates a strict mode-dependent `DelegationPlan`:
   - ASK_CASE -> Evidence;
   - VIEW_TIMELINE -> Timeline/Analysis;
   - CHECK_CLAIM -> Evidence with claim tool intent;
   - EXPLAIN_VERDICT -> Evidence and Legal, then join;
   - WHAT_IF -> Timeline/Analysis and evidence validation only when required by the plan.
6. Use dependency-aware execution. Specialists never call one another.
7. Add safe `AuditEvent` entries for validation, route, delegation, join, error, and completion. Never store hidden reasoning.
8. Enforce state ownership and explicit reducers.
9. Enforce turn, specialist-call, retry, and graph-step budgets.
10. Build the routing skeleton against fake adapters only. Do not import Track B implementation modules.

Add offline tests for:
- valid route for every interaction mode;
- only required specialists are selected;
- Explain Verdict joins Evidence and Legal;
- invalid/missing mode input returns safe clarification without a crash;
- state ownership;
- event ordering;
- turn and call budgets;
- follow-up memory resolution using safe summaries;
- reset clears memory;
- no specialist peer-to-peer call;
- no raw reasoning field or payload in state.

Do not implement the final reviewer, full Streamlit workbench, real RAG/tools/specialists, or visual styling.

Run compile and offline tests. Stop with the mandatory checkpoint handoff and list the exact v1 protocol methods exercised by fakes.
```

## Acceptance evidence

- Every UI mode maps to a distinct meaningful route.
- State ownership and safe memory are tested.
- Track A can progress without Track B implementation.
- No shared contract changed.

---

# PROMPT A2 — COMPLETE LANGGRAPH ORCHESTRATION AND BOUNDED REVIEW

## Purpose

Create a headless complete workflow using fake specialists, including aggregation, review, repair, stopping, and safe failure behavior.

## Branch

Continue:

```text
feat/orchestration-ui
```

## May edit

```text
src/caselens/graph.py
src/caselens/supervisor.py
src/caselens/reviewer.py
src/caselens/state.py when v1-compatible
src/caselens/services/result_builder.py
src/caselens/adapters.py
tests/test_routing.py
tests/test_end_to_end.py
docs/architecture.md
```

## Copy this prompt into Codex

```text
Implement Prompt A2 only. Read the master context, AGENTS.md, v1 integration contract, current graph/state, and tests. Preserve A1 behavior and do not edit Track B files or shared schemas.

Plan the graph nodes, conditional edges, joins, review path, and stopping paths before editing.

Implement a LangGraph workflow with explicit nodes for:
- validate request;
- Supervisor plan;
- selected specialist execution through injected protocol adapters;
- join validated findings;
- build draft brief;
- Editorial Integrity review;
- one bounded correction when a structured defect is returned;
- final validation;
- complete or safe insufficient/error stop.

Requirements:

1. The graph must inject specialist implementations through a factory/adapters boundary. Do not construct real specialists inside graph nodes.
2. Mode routing remains dynamic; do not call every specialist or every tool in a fixed sequence.
3. Explain Verdict may run Evidence and Legal independently when their inputs permit it, then join. If the implementation keeps them sequential, document the real dependency and do not fake parallelism.
4. The result builder must preserve status categories and citations from specialist findings.
5. Editorial review checks:
   - every factual/legal conclusion has citations;
   - allegations, disputed items, opinions, and unknowns remain labeled;
   - counterfactual language is non-certain and contains its disclaimer;
   - no legal advice or diagnosis appears;
   - final educational disclaimer exists.
6. Reviewer may return one `ReviewDefect`. The responsible draft/reviewer correction occurs once. A second failure stops as insufficient/escalated.
7. Malformed model/adapter output may receive one structured repair attempt. A second invalid result stops safely.
8. Clear stopping conditions:
   - reviewed final brief;
   - invalid input requiring user clarification;
   - insufficient evidence after budget;
   - tool/model failure after bounded handling;
   - maximum turn/step budget.
9. Append safe trace events for agent, retrieval count/reference, tool name/status, validation, review, and completion. Do not include prompts or hidden reasoning.
10. Build a headless `run_case_query` service entry point usable by Streamlit and tests.

Use fake adapters to add tests for:
- complete path for all five modes;
- Explain Verdict aggregation;
- valid citations preserved into final brief;
- unsupported claim rejected or labeled insufficient;
- one review defect repaired;
- second defect stops;
- adapter exception converted to safe failure;
- malformed output bounded repair;
- graph maximum step protection;
- no duplicate specialist call after completion;
- final response contains no raw reasoning/prompt fields.

Do not implement visual UI polish, live provider calls, or Track B backend code.

Run compile and all offline tests. Stop with the mandatory handoff and include a compact route-to-node table.
```

## Acceptance evidence

- A headless fake-backed vertical slice completes all modes.
- Reviewer and stopping are bounded and visible.
- Failures do not create false success.
- Integration still requires only adapter replacement.

---

# PROMPT A3 — FUNCTIONAL, UNSTYLED STREAMLIT WORKBENCH

## Purpose

Create the complete user workflow before aesthetic design. It may still use fake adapters while Track B finishes.

## Branch

Continue:

```text
feat/orchestration-ui
```

## May edit

```text
app.py
src/caselens/ui.py
src/caselens/memory.py
Track A integration tests
README checkpoint status only
```

## Copy this prompt into Codex

```text
Implement Prompt A3 only. Read the master context and current headless workflow. Keep the interface functional and deliberately unstyled; visual redesign is a later user-owned prompt after integration.

Before editing, list the user states and files to change.

Build a Streamlit workbench with:

0. Bilingual behavior:
   - Arabic is the default on first load;
   - a persistent `العربية | English` toggle changes UI labels, help, errors, disclaimers, and requested final-answer language;
   - stable IDs and source metadata remain unchanged;
   - Arabic legal text shows the original English legal term on first use where useful;
   - language persists in typed session state and safe memory;
   - no duplicate Arabic RAG corpus or automatic translation of source titles is required.

1. Case Briefing:
   - CASE//LENS name and plain-language value;
   - one curated United States v. Bernard L. Madoff case card supplied through a loader boundary;
   - a concise “numbers mean different things” cue distinguishing fictitious balances, estimated principal loss, forfeiture, and recovered/distributed funds;
   - closed-case status and jurisdiction;
   - clear educational/not-legal-advice note;
   - Start Session.

2. Investigation/Research Workbench:
   - mode selector for the five interaction modes;
   - mode-specific fields with examples;
   - submit/run action;
   - loading and disabled states that prevent duplicate submission;
   - short-term conversation display using safe messages only.

3. Result panels:
   - concise answer;
   - established facts;
   - allegations/disputed/unknown items in visibly different labels;
   - legal explanation when applicable;
   - timeline table when applicable;
   - What If assumptions/effects/unknowns/disclaimer when applicable;
   - citations showing title, source type/tier, section/heading, and link where safe;
   - confidence and limitations.

4. Safe Agent Trace:
   - phase/status;
   - selected specialist;
   - retrieval result count and source titles;
   - tool name and status;
   - validation/review/completion status;
   - never raw prompts, chain-of-thought, model payloads, or environment values.

5. Error/empty states:
   - missing question;
   - missing claim/event/change selection;
   - missing provider configuration;
   - unavailable evidence;
   - tool/adapter failure;
   - reset confirmation.

6. Streamlit session state must preserve the workflow session and safe memory across reruns without duplicating completed calls.

7. Keep all product logic outside `app.py`; `app.py` should be a small entry point.

Use fake adapters and fixture case metadata if Track B is not merged. Make the fake status visible only in a developer/checkpoint indicator, and ensure production live mode cannot silently use fakes.

Add focused tests for UI-facing service behavior where practical. Start Streamlit and manually complete one fake-backed path plus one missing-input path.

Do not add branding polish, animation, custom image generation, authentication, deployment, or new features. This checkpoint proves bilingual function, not final bilingual visual design.

Run all tests and a Streamlit startup check. Stop with the mandatory handoff and exact manual steps used.
```

## Acceptance evidence

- Full user path works with fakes.
- The UI demonstrates agent/stage/retrieval/tool/status evidence.
- No hidden reasoning or source-status ambiguity is shown.
- Visual design remains intentionally deferred.

---

# PROMPT A4 — INTEGRATE TRACK B REAL BACKEND

## Purpose

Merge the teammate’s validated backend and replace production fakes without rewriting the graph.

## Dependency

Track B’s backend PR must be merged to `main` with passing CI and a completed backend handoff.

## Branch preparation

```bash
git status
git fetch origin
git switch feat/orchestration-ui
git merge origin/main
pytest -q
```

If merge conflicts affect frozen contracts or Track B-owned implementation, stop and resolve them with both teammates before continuing.

## Copy this prompt into Codex

```text
Implement Prompt A4 only. Track B has merged. Read the master context, AGENTS.md, backend handoff, v1 integration contract, Track B modules/tests, and the current Track A graph/UI. Inspect git status and resolve no ownership-sensitive conflict silently.

First report:
- whether real implementations satisfy v1 protocols;
- any contract mismatch;
- current tests;
- exact integration files to change.

Before adding any production provider call, read the selected provider's current official SDK/API documentation and inspect the actually installed package version. Do not rely on remembered model names or outdated examples. Record the official documentation link and the verified provider/model/configuration values in the integration handoff and README notes.

Integrate through the existing adapter/factory boundary:

1. Wire the real case loader, Evidence Specialist, Legal Specialist, Timeline/What-If Specialist, RAG, and tool registry.
2. Keep fake adapters available only for offline tests and explicit developer fixtures. Production mode must fail safely rather than silently use a fake.
3. Preserve dynamic mode routing and tool selection.
4. Preserve source metadata and status categories from backend results to UI citations.
5. Ensure short-term follow-up memory works with real result summaries.
6. Ensure generated vector index behavior is clear:
   - safe missing-index message;
   - documented build command;
   - no generated index tracked in Git.
7. Add an explicit `scripts/check_model_connection.py` flow without printing secrets. It must be opt-in, never run from imports or pytest, and verify separately:
   - one minimal response;
   - one response that validates against a small strict Pydantic schema;
   - one structured tool-selection-compatible response using the application's boundary.
   Report each as pass/fail/skipped without printing credentials or unsafe raw payloads.
   Use `gemini-3.7-flash` through the current `google-genai` SDK. Confirm the account can access it; do not silently fall back. Also verify `gemini-embedding-2` with a 768-dimensional test embedding and confirm the returned dimension.
8. Handle:
   - missing key;
   - network/provider error;
   - rate limit;
   - invalid structured output;
   - empty retrieval;
   - invalid tool input;
   - unavailable/unknown case record.
9. Add integration tests with fake model and embedding clients but real case loader, retrieval structure, tools, specialists, graph, and result builder.
10. Add one test proving each of the three tools is selected only for its relevant request.
11. Add one test proving retrieved evidence changes or supports the final result and citations reach the UI model.
12. Add one end-to-end happy path and at least two failure paths.
13. Add one bilingual integration test proving the same cited finding can be rendered in Arabic and English without changing source IDs, claim status, or deterministic tool results.

Run:
- compile check;
- full pytest suite;
- optional Ruff;
- case-pack validation;
- knowledge-index build with the configured provider only if credentials are available;
- Streamlit manual walkthrough.

If credentials are absent, do not ask for or display them. Report the exact safe local setup step.

Do not redesign the visual interface or deploy.

Stop with the mandatory handoff including:
- all commands and actual results;
- real adapter mapping;
- retrieval/tool evidence;
- happy and failure paths;
- any remaining release blocker.
```

## Acceptance evidence

- No production fake is used silently.
- Real backend implements v1 without graph rewrite.
- All rubric-critical routes work.
- Full suite and manual application path are verified.

---

# PROMPT A5 — RELEASE DOCUMENTATION, RUBRIC AUDIT, AND DEMO

## Purpose

Prepare the repository for grading after functional integration passes.

## May edit

```text
README.md
docs/architecture.md
docs/agent_contracts.md
docs/rubric_evidence.md
docs/demo_script.md
scripts/final_audit.py
small release-blocking fixes through the correct owner
```

## Copy this prompt into Codex

```text
Implement Prompt A5 only. Read the complete capstone requirements represented in the master context and `docs/rubric_evidence.md`. Inspect the integrated repository and run current checks before editing documentation.

Do not award rubric evidence based on file names or claims. Use actual code, tests, and runtime behavior.

1. Audit every rubric row and update `docs/rubric_evidence.md` with:
   - status: proven, partial, or missing;
   - implementation file;
   - runtime evidence;
   - test evidence;
   - demo action;
   - owner;
   - release risk.

2. Fix only mandatory release blockers that fall inside Track A ownership. For a Track B blocker, open/list a precise Issue instead of rewriting teammate-owned code.

3. Complete README with all required items:
   - title and short pitch;
   - Advanced Agentic AI Systems Engineering;
   - visible SDAIA Academy statement and official GitHub link;
   - team name and both members/contributions;
   - comprehensive product description;
   - problem, target user, solution, value;
   - why multi-agent;
   - architecture diagram;
   - roles/contracts;
   - reasoning, delegation, stopping, aggregation;
   - state and short-term memory;
   - Agentic RAG source preparation, embeddings, local vector index, metadata, and evidence use;
   - three tools and dynamic selection;
   - stack and model/provider values actually tested;
   - repository structure;
   - clean setup, environment, index-build, run, and test instructions;
   - how to use each mode;
   - data/source policy and synthetic/team-authored material labels;
   - example inputs/results;
   - known limitations and future improvements;
   - screenshots after UI is stable;
   - optional verified public URL only if deployment later succeeds.

4. Create/update `docs/demo_script.md` for approximately five minutes and no more than ten slides:
   - problem/user/value;
   - architecture and why agents;
   - state/memory/RAG;
   - three tools;
   - live demo;
   - one failure;
   - honest limitation and future work;
   - both members’ speaking sections.

Target the rehearsed demo at 6 minutes, with a hard acceptable range of 5–7 minutes.

5. Define one deterministic demo sequence:
   - start the closed case;
   - ask `كيف استمر المخطط كل هذه السنوات رغم التحذيرات؟` as the source-grounded question;
   - check `بيرني ميدوف سرق 65 مليار دولار نقدًا` with Tool 2 and show the amount-type distinction;
   - show the scheme, regulatory, criminal, and recovery tracks with Tool 1;
   - explain the 11-count guilty plea and 150-year judgment with legal citations;
   - run `ماذا لو تحققت SEC بصورة مستقلة من التداولات بعد شكوى مبكرة؟` with Tool 3;
   - show the final brief and safe trace;
   - demonstrate rejection of the unsupported claim `كل الجهات الرقابية كانت مرتشية` or an invalid What If input.

6. Add `scripts/final_audit.py` only if it provides lightweight value. It may check required files, missing placeholders, knowledge metadata, `.env` tracking, and test command readiness. Do not create a false security scanner.

7. Perform a secret-safety review of tracked files without printing secret contents.

8. Perform a clean-environment-style README walkthrough and record actual results.

Do not add UI design polish or optional deployment in this checkpoint unless all mandatory evidence already passes and the user explicitly starts those phases.

Stop with:
- rubric status summary;
- release blockers;
- test/manual evidence;
- README walkthrough result;
- exact demo timing plan;
- optional next step only.
```

## Acceptance evidence

- Every capstone row has direct evidence or a named blocker.
- Clean setup instructions are tested.
- GitHub history and team contributions are clear.
- Demo covers routing, memory, RAG, tools, final result, and one failure.
- UI design phase remains safely separate.

---

# OPTIONAL PROMPT A6 — UI VISUAL DESIGN ONLY AFTER INTEGRATION

This placeholder intentionally contains no style direction. Shahad will append her separate design prompt after Prompt A4 passes.

Any UI design prompt must preserve:

- Streamlit functional behavior;
- mode-specific inputs;
- source-status labels;
- citations;
- safe Agent Trace;
- error states;
- keyboard usability and contrast;
- all passing tests;
- no new backend or architecture changes.

---

# PROMPT A7 — OPTIONAL PUBLIC DEPLOYMENT AFTER RELEASE

## Purpose

Attempt the optional deployment point only after the local MVP, full tests, source audit, and release documentation pass. Deployment failure must not damage the working local fallback.

## Dependency

```text
A4 integration complete
A5 release audit complete with no mandatory blocker
A6 complete only if Shahad chose to run the separate visual-design phase
main branch CI green
Shahad has admin permission on the public GitHub repository
```

## Copy this prompt into Codex

```text
Implement Prompt A7 only. Read the master context, current official Streamlit Community Cloud deployment/secrets documentation, README, configuration boundary, and final audit. Do not redesign the application or change agent behavior.

First prove the local fallback still works and list any deployment-specific change required. Keep changes minimal and reversible.

Prepare CASE//LENS for Streamlit Community Cloud:

1. Confirm the public repository, `main` branch, and entry point `app.py` are correct.
2. Confirm Python 3.11 and all runtime dependencies are reproducible from the repository.
3. Ensure Linux-safe paths and no dependency on a developer machine or untracked absolute path.
4. Ensure the required curated case data/knowledge documents are tracked, while generated indexes can either be built safely at startup once with clear caching or prepared through a documented deployment-safe path. Do not commit a secret or oversized accidental artifact.
5. Make configuration accept `GEMINI_API_KEY`, `GEMINI_CHAT_MODEL=gemini-3.7-flash`, `GEMINI_EMBEDDING_MODEL=gemini-embedding-2`, and dimension `768` through Streamlit secrets/environment without printing values.
6. Keep `.streamlit/secrets.toml` ignored and never create or inspect a real secret file in the repository.
7. Add safe startup messages for missing secrets, Gemini rate limit, provider outage, and missing/stale index.
8. Update README with the verified public URL only after it works. Keep complete local run instructions as the presentation fallback.

Human deployment steps must be presented one at a time:
- sign in to Streamlit Community Cloud with GitHub;
- Create app;
- select `ShahadW95/caselens-agentic-capstone`, branch `main`, entrypoint `app.py`;
- select Python 3.11 in Advanced settings;
- add the Gemini key only in the Streamlit Secrets field;
- deploy and inspect logs without pasting secrets into chat.

After the human deploys, verify in a private/incognito browser:
- public app loads;
- Arabic default and English toggle work;
- one source-grounded happy path works;
- one claim check and citation link work;
- one safe failure works;
- refresh does not expose secrets or switch to fake mode;
- no raw provider error, path, prompt, or chain-of-thought appears.

If deployment fails, diagnose without weakening security, committing secrets, deleting the working local configuration, or claiming success. Record the blocker and preserve the local demo fallback.

Run the full offline suite again after any deployment-specific edit. Stop with the public URL or an explicit failed-attempt report, commands/results, local fallback status, and any remaining risk.
```

## Acceptance evidence

- Public URL opens in a private browser.
- Happy and failure paths both work.
- GitHub contains no key or Streamlit secret file.
- The deployed application never silently uses fake adapters.
- README contains the URL and local fallback only when actually verified.

---

# CODEX REVIEW PROMPT — BEFORE OPENING A PR

```text
Review the current branch against the master context, AGENTS.md, the current Track A checkpoint, and the frozen v1 integration contract. Do not edit files.

Report findings by severity with file references and evidence. Check especially:
- modifications outside Track A ownership;
- accidental contract changes;
- state ownership violations;
- fixed/decorative routing;
- unbounded calls or loops;
- fake adapters leaking into production;
- missing validation/error paths;
- chain-of-thought, prompt, source, or secret leakage;
- tests that do not prove claimed behavior;
- merge risk with Track B.

Then list open questions, commands run, actual results, and whether the branch is ready for a Pull Request.
```

# CODEX BUG-DIAGNOSIS PROMPT

```text
Read the master context and relevant checkpoint. Diagnose only; do not fix yet.

Observed behavior: [PASTE]
Expected behavior: [PASTE]
Reproduction: [PASTE]
Current branch: [PASTE]
Recent merge/commit: [PASTE]

Reproduce safely, identify the smallest evidence-supported root cause, affected contract/state boundary, owned files, and regression test. Provide fix options and tradeoffs. Stop for approval before editing.
```
