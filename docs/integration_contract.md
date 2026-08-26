# CASE//LENS v1 Integration Contract

## Version and freeze gate

Contract version: **v1**.

This A0 document is a freeze candidate. It becomes frozen only after teammate
review of `src/caselens/contracts.py`, `src/caselens/protocols.py`, and this file,
with CI passing. Frozen case ID, language behavior, model IDs, amount semantics,
proceeding distinctions, ownership, and architecture may not be changed during
adapter implementation.

## Callable specialist boundaries

```python
EvidenceSpecialist.execute(
    task: DelegationTask,
    state_view: SpecialistStateView,
) -> EvidenceFinding

LegalSpecialist.execute(
    task: DelegationTask,
    state_view: SpecialistStateView,
) -> LegalFinding

TimelineAnalysisSpecialist.execute(
    task: DelegationTask,
    state_view: SpecialistStateView,
) -> TimelineFinding | CounterfactualFinding

Reviewer.review(
    draft: CaseResearchBrief,
    context: ReviewContext,
) -> ReviewResult

ModelBoundary.generate(request: ModelRequest) -> ModelResponse
```

Protocols are runtime-checkable and contain no untyped free-form dictionary
boundary. `SpecialistStateView` exposes only validated request data, safe
messages, completion IDs, and retrieved chunk references.

## Contract guarantees

- MVP case ID is only `US_SDNY_09CR00213_DC`.
- Language is only `ar` or `en`.
- Five stable interaction modes are allowed.
- Boundary models forbid unknown fields and are frozen after validation.
- Citation-bearing findings use stable citation/source/document/chunk/heading,
  type/tier, and optional original URL metadata.
- Status-specific collections reject an allegation labeled as established.
- Confidence is `LOW`, `MEDIUM`, or `HIGH`, never certainty.
- Every financial amount has amount kind, currency, value/range, as-of date,
  source IDs, and measurement note.
- A criminal proceeding accepts only `CLOSED_FINAL`; SIPA liquidation uses
  `ONGOING_RECOVERY` or `ADMINISTRATION_CLOSED`, preventing status mixing.
- Counterfactuals require an allowed change, affected nodes, possible effects,
  unchanged cited facts, unknowns, bounded confidence, and a hypothetical
  disclaimer.
- The final brief requires citations, limitations, and a not-legal-advice
  disclaimer. No raw reasoning or prompt field exists.

## Fake and real adapter behavior

Track A's `create_development_fake_adapters()` is an explicit
development/testing factory. Its source and IDs are visibly fictional and its
objects return valid v1 contracts. Live configuration does not call this
factory. Track B real adapters implement the same protocols with curated
sources, RAG, and deterministic tools. A4 swaps injected implementations rather
than rewriting routing or schemas; missing live configuration fails safely.

## Configuration/provider boundary

`RuntimeConfig.from_sources()` accepts the same names from Streamlit secrets or
environment variables and never logs values. Committed defaults freeze
`gemini-3.7-flash`, `gemini-embedding-2`, and 768 dimensions. The `google-genai`
client is constructed lazily only through `src/caselens/llm.py`; A0 performs no
provider request.

## Ownership

Track A owns contracts/protocols and orchestration-facing adapters. Track B owns
data, knowledge, RAG, tools, real specialists, and their tests. Shared files are
coordinated as listed in `AGENTS.md`. No component writes another component's
owned result field.

## Contract-change process after freeze

1. Open a GitHub Issue labeled `contract-change`.
2. Document old schema, proposed schema, reason, affected files, migrations,
   and tests.
3. Obtain approval from both teammates.
4. Shahad changes the shared contract in a focused pull request.
5. Both tracks merge the updated `main` before continuing.

No backend branch changes frozen shared contracts directly or silently adapts
unsupported data.

## A0 review checklist

- Verify fake/protocol runtime compatibility tests.
- Verify malformed enums, confidence, missing citations, mixed proceeding
  statuses, missing hypothetical disclaimer/unknowns, and allegation-to-fact
  promotion are rejected.
- Verify no secret, `.env`, live call, state graph, RAG, tool, or case content is
  introduced.
- Freeze only after peer review and passing CI.
