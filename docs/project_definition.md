# CASE//LENS Project Definition

## Problem

Research about prominent criminal and financial cases is fragmented across
sources with unequal authority. Creators and learners can accidentally present
party allegations, reporting, speculation, or incompatible financial measures
as settled facts.

## Target user

- A true-crime, fraud, business, or financial-crime creator preparing a
  responsible research brief
- An enthusiast seeking a clear understanding of one closed case
- A beginner learning how facts, claims, evidence, and court findings differ

The MVP is not for investigators, parties to an active case, legal
representation, or professional legal advice.

## Input

The user selects the only curated case, `US_SDNY_09CR00213_DC`, chooses Arabic
or English, and uses one of five modes: Ask Case, View Timeline, Check Claim,
Explain the Judgment (`EXPLAIN_VERDICT` internally), or What If. Mode-specific
questions and approved IDs are validated before orchestration.

## Output

A typed `CaseResearchBrief` contains only applicable sections: concise answer,
established facts, separately labeled allegations/disputes/unknowns, relevant
timeline, typed financial amounts, legal explanation, bounded hypothetical,
citations, confidence, limitations, and an educational-not-legal-advice notice.

## Value

CASE//LENS reduces organization time, improves source traceability, teaches
procedural and evidentiary distinctions, and prevents unlike financial figures
from being collapsed into a misleading number.

## Why multi-agent

Evidence verification, legal explanation, temporal/causal analysis, and
editorial review require different tools, source filters, and authority limits.
One Supervisor plans and joins only the necessary work; strict typed handoffs
and deterministic Python checks constrain each specialist.

## MVP exclusions

No live runtime web research, arbitrary cases, active cases, accusations of new
suspects, private records, victim contact, diagnosis, graphic media,
authentication, personal memory, browser automation, media generation,
recursive delegation, unbounded loops, or separate frontend is included.

## Completion condition

The MVP is complete only when the five modes work through the local Streamlit
app, dynamic delegation and safe trace are visible, curated RAG evidence affects
the cited result, all three deterministic tools affect only relevant routes,
offline tests and CI pass, and one happy path plus safe failures are reproducible.

## A0 checkpoint status

The product definition and shared contracts are implemented. Runtime state,
orchestration, memory, data, RAG, tools, real specialists, and full UI remain
future checkpoints.
