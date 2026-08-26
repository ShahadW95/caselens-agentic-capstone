# CASE//LENS Rubric Evidence Plan

Status meanings: **foundation** is directly evidenced in A0, **planned** names a
future checkpoint and must not be presented as implemented, and **blocked**
requires an external dependency.

| Rubric row | Planned implementation file | Runtime evidence | Test evidence | Demo action | Owner | A0 status |
|---|---|---|---|---|---|---|
| Business problem, user, value | `docs/project_definition.md`, `README.md` | Briefing and final brief | UI/service tests later | Open case briefing | Track A | foundation |
| Supervisor plus meaningful specialists | `src/caselens/graph.py`, specialist modules | Mode-dependent safe trace | routing/specialist tests | Compare routes | Both | planned A1–B4 |
| Agent contracts | `contracts.py`, `protocols.py`, `docs/agent_contracts.md` | Validated handoffs | `test_contracts.py` | Show rejected malformed object | Track A | foundation |
| Delegation and reasoning | `supervisor.py`, `graph.py` | Plan/delegation/join events | routing tests | Run Explain Judgment | Track A | planned A1–A2 |
| Structured handoffs | `contracts.py`, future `state.py` | Typed specialist findings | contract/state tests | Inspect safe trace/result | Track A | foundation contract; runtime planned |
| Stopping and aggregation | `graph.py`, `reviewer.py`, `result_builder.py` | Completion/insufficient/budget stop | E2E tests | Show one bounded failure | Track A | planned A2 |
| Structured state | `state.py` | Typed session/status | routing tests | Inspect state panel | Track A | planned A1 |
| Short-term memory | `memory.py` | Safe follow-up context | memory tests | Ask a follow-up | Track A | planned A1/A3 |
| Agentic RAG | `src/caselens/rag/` | plan/retrieve/assess/reformulate | RAG tests | Show evidence affecting answer | Track B | planned B2 |
| Embeddings/vector store | RAG index and build script | Local index manifest | index/RAG tests | Show build/manifest | Track B | planned B2 |
| Retrieval metadata | RAG contracts and implementation | Citation/source cards | RAG/integration tests | Expand citation | Both | foundation contract; runtime planned |
| Evidence affects result | specialists/result builder | Cited finding in brief | E2E evidence assertion | Compare supported/unsupported | Both | planned B4/A4 |
| Tool 1 timeline | `src/caselens/tools/timeline.py` | Timeline-only tool event | tool/routing tests | Filter timeline track | Track B | planned B3 |
| Tool 2 claim support | `src/caselens/tools/claim_support.py` | Deterministic claim status | tool/routing tests | Check USD 65B claim | Track B | planned B3 |
| Tool 3 counterfactual | `src/caselens/tools/counterfactual.py` | Bounded causal output | tool/routing tests | Run SEC verification What If | Track B | planned B3 |
| Dynamic tool selection | `graph.py`, specialist/tool adapters | Only relevant tool appears | integration tests | Compare three routes | Both | planned A1/B4/A4 |
| Validation and errors | `contracts.py`, graph/UI boundaries | Safe error/clarification | contract and E2E failures | Submit missing/invalid input | Both | foundation contract; runtime planned |
| Complete Streamlit app | `app.py`, `ui.py` | Start-to-brief workflow | UI/E2E tests | Complete happy path | Track A | A0 checkpoint only; planned A3/A4 |
| Safe observability | `AuditEvent`, graph/UI | Safe phase/source/tool/status trace | no-leak tests | Show trace | Track A | foundation schema; runtime planned |
| Bilingual behavior | query/brief/state/UI | Arabic default and English toggle | bilingual tests | Toggle same cited result | Both | foundation contract; runtime planned |
| Financial amount semantics | `FinancialAmount`, data/tools/UI | Typed labels and dates | contract/data/tool tests | Explain unlike USD figures | Both | foundation contract; data planned |
| Proceeding separation | `ProceedingRecord`, data/UI | Criminal closed; recovery separate | contract/data tests | Compare statuses | Both | foundation contract; data planned |
| Offline provider safety | config/LLM boundary, CI | Keyless startup | contract/import tests | Start without key | Track A | foundation |
| Presentation | `docs/demo_script.md` | Six-minute sequence | final audit | Rehearsed demo | Both | planned A5 |
| GitHub collaboration/docs | `.github/`, README, history | CI and review evidence | offline CI | Show PR/Issue evidence | Both | foundation; teammate review pending |
| SDAIA/course acknowledgement | `README.md` | Visible repository acknowledgement | final audit later | Show README opening | Track A | foundation |
| Optional deployment | Streamlit Cloud config | Verified public URL and failures | full offline regression | Open incognito app | Track A | blocked until release |

## A0 release risk

The v1 schema is a freeze candidate, not yet peer-approved. Zahra must review
contracts/protocols/integration documentation and CI must pass before Track B
implements Python adapters against v1.
