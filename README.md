# CASE//LENS — Beyond the Verdict

CASE//LENS is a source-grounded multi-agent research and learning assistant for
understanding one curated closed case through cited evidence, legal explanation,
timeline analysis, claim checking, and bounded What-If exploration.

> Checkpoint status: **A0 foundation implemented.** Contracts, protocols,
> guardrails, offline tests, and a minimal keyless Streamlit checkpoint exist.
> State, orchestration, memory, case content, RAG, tools, real specialists, and
> the complete workbench remain planned work.

## Course and academy acknowledgement

This capstone is for **Advanced Agentic AI Systems Engineering** at
[SDAIA Academy](https://sdaia.gov.sa/en/Sectors/BuildingCapacity/academy/Pages/AboutSdaiaAcademy.aspx).
SDAIA Academy is acknowledged as the program provider. The planned official
project repository is
[ShahadW95/caselens-agentic-capstone](https://github.com/ShahadW95/caselens-agentic-capstone).

## Team

- Team: **LensLab**
- Shahad (`ShahadW95`): Track A foundation, contracts, orchestration, memory,
  functional UI, integration, and release evidence.
- Zahra (`zaa330`): Track B case data, source pack, RAG, tools,
  and real specialist implementations.

Current status: contribution paths are assigned; implementation beyond A0 is
not yet complete.

## Product description

The MVP serves true-crime and financial-crime creators, enthusiasts, and
learners researching the closed United States v. Bernard L. Madoff criminal
case. It produces a structured `CaseResearchBrief` while keeping established
facts, allegations, disputed items, and unknowns separate. Financial values are
labeled as fictitious statement balances, estimated principal loss,
forfeiture, recovery, or distribution instead of being compared as if they
measure the same thing.

Current status: product and contract definition complete; runtime research
workflow not implemented.

## Problem, target user, solution, and value

Case sources vary in authority and are easy to misstate. CASE//LENS helps a
creator or learner organize a single closed case, trace conclusions to curated
sources, understand legal procedure in plain language, and avoid turning
allegations or incompatible dollar figures into misleading claims.

See `docs/project_definition.md` for the complete A0 definition.

## Why multi-agent

Evidence assessment, legal explanation, timeline/counterfactual analysis, and
editorial integrity have different inputs and authority limits. One Supervisor
delegates only required work to three execution specialists, then one bounded
reviewer checks the joined brief. Strict contracts prevent fluent output from
overriding deterministic evidence or tool status.

Current status: role contracts frozen for review; orchestration begins at A1.

## Architecture

The governing rule is: the LLM interprets and explains; LangGraph controls
routing and budgets; Python validates and executes tools; curated local sources
ground factual and legal claims.

See `docs/architecture.md` for the Mermaid workflow and planned runtime
boundaries.

## Agent roles and contracts

Exactly five roles are defined:

1. Case Director (Supervisor)
2. Source & Evidence Specialist
3. Legal Explanation Specialist
4. Timeline & What-If Specialist
5. Editorial Integrity Reviewer

See `docs/agent_contracts.md`, `src/caselens/contracts.py`, and
`src/caselens/protocols.py`.

## Reasoning, delegation, stopping, and aggregation

The planned workflow combines bounded Plan-and-Execute, specialist ReAct over
allowed RAG/tools, and one editorial review/repair. It forbids recursive
delegation and peer-to-peer specialist calls. The final workflow will stop on a
reviewed brief, clarification, insufficient evidence, bounded failure, or
budget exhaustion.

Current status: documented, not implemented in A0.

## State and short-term memory

Typed session state will preserve the case, language, mode, selected IDs,
validated findings, safe messages, budgets, and safe audit events. It will not
store chain-of-thought, raw prompts, or raw model payloads. No personal or
long-term user memory is in scope.

Current status: contract inputs exist; state and memory begin at A1.

## Agentic RAG and evidence use

Track B will validate team-authored source digests, chunk them by section,
generate `gemini-embedding-2` vectors at 768 dimensions, and store them with
metadata in a transparent local NumPy index. Specialists may retrieve twice at
most and must return a cited finding or explicit insufficiency. Live Google
Search grounding is excluded.

Current status: planned; no source pack or index is implemented in A0.

## Deterministic tools and dynamic selection

- `query_case_timeline` for timeline requests
- `check_claim_support` for claim-verification requests
- `simulate_counterfactual` for approved What-If changes

Explain-judgment requests normally use legal RAG and do not call every tool.

Current status: contracts described; Track B implementation is not part of A0.

## Technology stack

- Python 3.11+
- Streamlit
- LangGraph
- Pydantic v2
- Google Gemini Developer API through `google-genai`
- Chat model `gemini-3.7-flash`
- Embedding model `gemini-embedding-2`, 768 dimensions
- Transparent local NumPy vector index
- pytest offline tests

No model identifier or access has been live-verified in A0. The application
makes no live model call in this checkpoint.

## Repository structure

```text
app.py                         Minimal A0 Streamlit checkpoint
src/caselens/                  Track A contracts and boundaries
tests/                         Offline tests and fixtures
docs/                          Definition, architecture, contracts, rubric map
docs/prompts/                  Preserved project source-of-truth prompts
.github/                       Offline CI and collaboration templates
data/, knowledge_base/         Planned Track B-owned case content
storage/                       Ignored generated vector index
```

## Setup

Prerequisite: Python 3.11 or newer.

```bash
python -m venv .venv
```

Activate the virtual environment using the command for your shell, then:

```bash
python -m pip install -r requirements.txt
```

Do not create or share a real `.env` during A0 validation. `.env.example`
contains an empty key and frozen non-secret defaults.

Current status: setup commands will be validated during the A0 handoff.

## Configuration

Supported environment or Streamlit-secret names are:

```text
GEMINI_API_KEY=
GEMINI_CHAT_MODEL=gemini-3.7-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_EMBEDDING_DIMENSIONS=768
CASELENS_ADAPTER_MODE=live
```

The key remains empty in committed samples. Normal tests and the A0 app require
no key. Development fakes require explicit construction and must not be
selected silently in live mode.

## Run the checkpoint app

```bash
streamlit run app.py
```

Expected A0 behavior: the page shows `Foundation ready`, the five roles, and a
safe missing-configuration warning without making a model call.

## Test

```bash
python -m compileall app.py src tests
pytest -q
```

CI runs these commands on pull requests to `main` and pushes to `main`, without
credentials or live provider calls.

## How to use each mode

The five planned modes are `ASK_CASE`, `VIEW_TIMELINE`, `CHECK_CLAIM`,
`EXPLAIN_VERDICT` (UI label: Explain the Judgment), and `WHAT_IF`. The complete
user workflow is intentionally deferred until A3; the A0 app does not accept a
case query.

## Data and source policy

Only approved local sources for the frozen Madoff case may ground factual and
legal claims. Official court/government records receive the highest authority;
commentary and social media are excluded from core evidence. Team-authored
digests must be labeled and traceable to original URLs. Generated indexes are
local ignored artifacts.

Current status: policy requirements are frozen; Track B prepares and validates
the actual source pack.

## Example inputs and results

Planned example: check whether “Madoff stole USD 65 billion in cash.” The result
must distinguish fictitious statement balances from estimated principal loss,
forfeiture, recovery, and distributions, with sources and as-of dates.

Current status: example behavior is not implemented or claimed in A0.

## Security, privacy, and safe observability

The UI may show route, specialist, retrieval count/source title, tool/status,
validation, review, and completion events. It must never show secrets,
environment values, private prompts, chain-of-thought, raw model payloads, or
unapproved sources. Provider requests are restricted to public case summaries
and public-case questions.

## Known limitations

- A0 contains no state machine, LangGraph workflow, memory, RAG, tools, or real
  specialist implementation.
- The case data and source pack are not yet present.
- Frozen Gemini model access is not live-verified until the explicit integration
  checkpoint.
- GitHub collaborator setup and contribution verification remain human repository actions.
- This product is educational research, not legal advice.

## Future improvements

After the MVP: consider additional curated closed cases, broader source packs,
and richer evaluation only after safety and evidence contracts remain stable.
Authentication, active cases, live web research, and unbounded debate are not
MVP improvements.

## Rubric evidence

`docs/rubric_evidence.md` maps every required rubric row to planned runtime,
repository, test, demo, owner, and current A0 status.

## Demo and screenshots

The final demo will show meaningful routing, RAG evidence, all three tools, a
cited brief, safe trace, and one failure path. Screenshots will be added only
after the functional UI is stable. No deployment or public URL is claimed.

## Deployment

Optional Streamlit Community Cloud deployment is blocked until the local MVP,
integration tests, source audit, release documentation, and final UI are ready.
Local execution remains the presentation fallback.

## License and educational disclaimer

License selection is pending team confirmation. CASE//LENS provides educational
research support only and is not legal advice.
