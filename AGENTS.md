# CASE//LENS Agent Working Agreement

This repository follows the frozen decisions and architecture in
`docs/prompts/00_CASELENS_MASTER_CONTEXT.md`. Read that file and the assigned
track prompt completely before changing code.

## Inspect before editing

Before every checkpoint, inspect the current branch, `git status`, recent
commits, the repository tree, and all files relevant to the checkpoint. Stop
for unresolved merge changes, unrelated conflicting applications, or changes
that cannot be preserved safely. State the exact files to be changed before
editing.

## Ownership

Track A (Shahad + Codex) owns:

- `AGENTS.md`, `app.py`, `.github/`
- `src/caselens/config.py`, `contracts.py`, `protocols.py`, `state.py`,
  `memory.py`, `graph.py`, `supervisor.py`, `reviewer.py`, `ui.py`, and
  `adapters.py`
- `src/caselens/services/result_builder.py`
- `tests/test_contracts.py`, `test_routing.py`, `test_memory.py`, and
  `test_end_to_end.py`
- `docs/architecture.md`, `docs/integration_contract.md`, and final README
  integration

Track B (Zahra + Claude Code) owns:

- `CLAUDE.md`, `data/`, `knowledge_base/`
- `scripts/build_knowledge_index.py`, `scripts/validate_case_pack.py`
- `src/caselens/rag/`, `src/caselens/tools/`,
  `src/caselens/specialists/`, and `src/caselens/services/case_loader.py`
- `tests/test_case_data.py`, `test_rag.py`, `test_tools.py`, and
  `test_specialists.py`
- `docs/source_policy.md` and source/data/RAG/tool README notes

Shared files are `requirements.txt`, `.env.example`, `.gitignore`,
`README.md`, `src/caselens/contracts.py`, `src/caselens/protocols.py`, and
`docs/rubric_evidence.md`. After v1 freezes, a shared-contract change requires
a `contract-change` Issue describing the old and proposed schema, rationale,
affected files, and tests; both teammates must approve before Shahad changes
the contract in a focused pull request.

## Architecture boundaries

- The LLM interprets and explains; LangGraph controls routing and budgets;
  Python validates contracts and runs tools; curated local sources ground
  factual and legal claims.
- There is exactly one Case Director and four bounded specialists.
- Specialists communicate through strict v1 contracts, never peer-to-peer.
- Runtime case knowledge is read-only. No live web grounding is permitted.
- Track A uses explicit development fakes until Track B's real adapters merge.
  Production must never silently select a fake.
- Do not expose raw prompts, chain-of-thought, model payloads, environment
  values, or unapproved sources in state, logs, tests, or the UI.

## Verification and safety

- Normal tests are offline and require no key or live model call.
- Run the checkpoint's compile, test, and manual checks and report actual
  results. Never claim success without evidence.
- Never read, print, or commit `.env`, Streamlit secrets, API keys, or other
  credentials. Samples contain empty secret values only.
- Never use `git reset --hard`, force push, or destructive commands that may
  overwrite teammate work.
- Do not push, merge, publish, deploy, open pull requests, or change GitHub
  settings unless the user explicitly authorizes that action.

## Mandatory checkpoint handoff

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
