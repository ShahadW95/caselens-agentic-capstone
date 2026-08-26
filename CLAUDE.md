# CLAUDE.md — Track B (Teammate + Claude Code)

Read `docs/prompts/00_CASELENS_MASTER_CONTEXT.md` and `docs/prompts/02_TEAMMATE_CLAUDE_TRACK.md`
in full before any session — those are the shared master caselines context and this
track's prompt pack. This file only scopes Claude Code's track; it does not duplicate
the master context.

## Owned paths

```
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
```

Never edit `src/caselens/contracts.py` or `src/caselens/protocols.py` directly once
frozen — use the `contract-change` Issue process described in the master context.

## Checkpoint order

- **B0** (this session): curate source manifest and case research plan. DRAFTED in this PR.
- **B1**: structured case data (`timeline.json`, `claims.json`, `evidence.json`,
  `financial_amounts.json`, `causal_graph.json`) + `test_case_data.py`. Depends on B0
  and Track A's frozen contracts (already merged in this repo — see
  `src/caselens/contracts.py`).
- **B2**: RAG preparation and retrieval (`src/caselens/rag/`) + `test_rag.py`. Depends on B1.
- **B3**: three deterministic tools (`src/caselens/tools/`) + `test_tools.py`. Depends on B1.
- **B4**: three real specialists (`src/caselens/specialists/`) + `test_specialists.py`.
  Depends on B2 and B3.

Stop after each checkpoint. Do not continue automatically to the next one.

## Rules inherited from the master contract

1. Use frozen Pydantic contracts once they exist; do not invent new shared schemas.
2. Every fact and financial figure must trace to `data/cases/case_001/source_manifest.json`.
3. No live API calls except the explicit connection-check script, and never with secrets committed.
4. No live web research at runtime — retrieval is local/offline only, over the curated case pack.
5. Distinguish `FICTITIOUS_STATEMENT_BALANCE`, `ESTIMATED_PRINCIPAL_LOSS`,
   `FORFEITURE_ORDER`, `RECOVERY`, `DISTRIBUTION` for every dollar figure.
6. Keep `CRIMINAL_CASE` status independent from `SIPA_LIQUIDATION`/`DOJ_VICTIM_FUND` status.
7. Report checkpoint results using the `CHECKPOINT RESULT` handoff format from the master doc.
