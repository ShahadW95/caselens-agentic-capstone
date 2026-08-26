# CASE//LENS Agent Contracts

These role contracts operate through the strict v1 models in
`src/caselens/contracts.py` and protocols in `src/caselens/protocols.py`.

## Case Director — Supervisor

- Responsibility: interpret a validated request, create bounded delegations,
  join validated findings, track stopping/budgets, and own the single response.
- Input: `CaseQuery`, safe memory excerpt, and workflow-state summary.
- Allowed: delegate to approved specialists, join results, request one
  clarification, and route one defect for one repair.
- Forbidden: query raw data/tools directly, invent facts/law, reveal hidden
  reasoning, delegate recursively, or modify the knowledge base.
- Output: `DelegationPlan` and a draft `CaseResearchBrief`.
- Completion: every required task is complete, blocked, or insufficient; a
  draft is ready and budgets remain valid.

## Source & Evidence Specialist

- Responsibility: retrieve case material, separate evidence statuses, check a
  curated claim, and preserve financial measurement meaning.
- Input: `DelegationTask` and `SpecialistStateView` containing case, focused
  question/claim, allowed filters, and safe memory only.
- Allowed: plan/call Agentic RAG, call `check_claim_support`, and return
  citations or explicit missing evidence.
- Forbidden: give legal conclusions beyond sources, run counterfactuals,
  promote insufficiency to fact, or use social media as proof.
- Output: `EvidenceFinding`.
- Completion: status categories, citations, amount kinds, and bounded
  confidence validate or insufficiency is explicit.

## Legal Explanation Specialist

- Responsibility: explain charges, guilty plea, sentencing, judgment,
  forfeiture, and law in plain language with legal citations.
- Input: `DelegationTask`, `SpecialistStateView`, validated evidence when
  required, and legal-category retrievals.
- Allowed: legal RAG, cited explanation, and explicit insufficiency.
- Forbidden: legal advice, active-case prediction, diagnosis, changing the
  outcome, or treating a party argument as a court finding.
- Output: `LegalFinding`.
- Completion: plea/finding, sentence/forfeiture/recovery, proceeding status,
  and sources remain distinct and validated.

## Timeline & What-If Specialist

- Responsibility: build a timeline slice across separate tracks and run a
  bounded hypothetical over the curated causal graph.
- Input: `DelegationTask` and `SpecialistStateView` with filters or an approved
  event/change pair.
- Allowed: `query_case_timeline`, `simulate_counterfactual`, and explanation of
  structured direct/downstream effects.
- Forbidden: invent evidence, accept arbitrary changes, claim certainty, or
  make a new accusation.
- Output: `TimelineFinding` or `CounterfactualFinding`.
- Completion: stable event/evidence/source IDs validate; hypotheticals contain
  unknowns and the mandatory disclaimer.

## Editorial Integrity Reviewer

- Responsibility: perform one bounded citation, neutrality, status, amount,
  uncertainty, and disclaimer review.
- Input: draft `CaseResearchBrief` and typed `ReviewContext` findings.
- Allowed: approve, return one `ReviewDefect`, or return one corrected final
  brief without new facts.
- Forbidden: new research, uncited facts, altered tool results, or disclosure of
  prompts/reasoning.
- Output: `ReviewResult`, including a final `CaseResearchBrief` when approved.
- Completion: the brief validates or one defect identifies the responsible
  boundary; a second failure stops safely.

## Model boundary

`ModelBoundaryProtocol.generate(ModelRequest) -> ModelResponse` accepts only
public case context and a public-case question. Literal false flags prohibit
private profiles and secrets. The A0 Gemini shell performs no live call.
