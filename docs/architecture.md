# CASE//LENS Architecture

## Governing boundary

The LLM interprets and explains. LangGraph controls routing, joining, retries,
and budgets. Python validates all inputs/outputs and executes deterministic
tools. Curated local sources ground factual and legal claims.

## Exactly five roles

1. Case Director — the sole Supervisor
2. Source & Evidence Specialist
3. Legal Explanation Specialist
4. Timeline & What-If Specialist
5. Editorial Integrity Reviewer

Specialists do not call one another. The Supervisor owns the plan, delegation,
join, and one response. The Reviewer performs one bounded review and adds no new
facts.

## Implemented A2 workflow

```mermaid
flowchart TD
    U[Validated user request] --> D[Case Director plan]
    D -->|Evidence route| E[Source & Evidence Specialist]
    D -->|Legal route| L[Legal Explanation Specialist]
    D -->|Timeline or What If| T[Timeline & What-If Specialist]
    E --> J[Supervisor join]
    L --> J
    T --> J
    J --> B[Build typed draft brief]
    B --> R[Editorial Integrity Reviewer]
    R -->|Approved| V[Final Python validation]
    R -->|One defect| C[One bounded correction]
    C --> R
    V --> O[Streamlit brief and safe trace]
    D -->|Invalid or over budget| S[Safe stop]
    E -->|Insufficient or failed| S
    L -->|Insufficient or failed| S
    T -->|Invalid or failed| S
```

The compiled LangGraph prevents a second repair loop; the diagram's correction
edge represents exactly zero or one correction followed by one recheck.

Explain Judgment fans out to independent Evidence and Legal nodes and uses a
barrier join. The development fakes share no dependency, so this is genuine
parallel graph scheduling rather than decorative concurrency. Evidence-required
What-If plans are sequential for a real reason: the Timeline/What-If node
receives the completed evidence-validation task ID before simulating the
allowed change.

## Reasoning patterns

- Plan-and-Execute: the Director creates a small mode-dependent plan.
- ReAct: a selected specialist chooses only an allowed retrieval/tool action,
  observes structured output, and returns a bounded finding.
- Bounded Reflection: the Reviewer returns at most one structured defect and a
  second failure stops safely.

## State and ownership

The A1 `CaseLensState` is immutable and typed. It contains session/request and
closed-case status, safe short-term messages, plans/tasks, retrieval
rounds/references, specialist-owned findings, reserved draft/review/final brief
slots, validation errors, retry/call/step/turn counters, audit events, workflow
status, and completion reason. Input, memory, Supervisor, each specialist, and
the future Reviewer can update only their explicit field sets. Messages,
errors, audit events, and retrieval references use append-only reducers.

## Memory

Short-term memory retains safe user questions, safe final answers, language,
selected IDs, and concise finding summaries. Reset starts a new session. Raw
prompts, chain-of-thought, model payloads, and personal long-term memory are
excluded. The curated knowledge base is read-only at runtime.

## Agentic RAG

Track B validates approved documents, chunks by H2 section, generates
`gemini-embedding-2` embeddings at 768 dimensions, and stores transparent NumPy
vectors with metadata. A RAG specialist may plan, retrieve, assess, reformulate
once, then return cited sufficiency or explicit insufficiency. Retrieval must
affect the finding or final brief.

## Deterministic tools

- Timeline routes may call `query_case_timeline`.
- Claim routes may call `check_claim_support`.
- What-If routes may call `simulate_counterfactual` for curated changes.
- Explain-judgment normally uses legal RAG, not decorative tool calls.

## Safe observability

The UI may display agent/phase, route, retrieval count and approved source
titles, tool/status, validation, review, and completion. It may not display
prompts, hidden reasoning, model payloads, credentials, environment values,
unapproved sources, or uncited allegations as fact.

## Stopping and budgets

One Supervisor plan, one normal call per selected specialist, two retrieval
rounds per RAG specialist, one structured-output repair, and one editorial
review plus one correction are the maximums. Completion, clarification,
insufficient evidence, bounded tool/model failure, or step/turn exhaustion ends
the graph. Recursive delegation and peer-to-peer specialist calls are forbidden.

## Integration boundary

Track A injects development fakes through the v1 protocols. Track B implements
the same methods with real RAG/tools. Integration changes the adapter factory,
not the graph or shared schemas.

## A2 complete fake-backed workflow status

The deterministic pre-router validates all five modes. The Supervisor creates a
strict mode-specific plan and the compiled graph executes only selected nodes
through injected v1 adapters. It joins findings without relabeling status or
citations, builds a strict draft, performs deterministic and injected editorial
review, allows one correction, validates the final contract, and completes or
stops safely. Adapter exceptions and malformed outputs are bounded, completed
states are idempotent, and turn, specialist-call, retry, correction, and
graph-step budgets are enforced. All current runtime evidence remains offline
and development-fake-backed; A4 will replace adapters without changing graph
control flow.
