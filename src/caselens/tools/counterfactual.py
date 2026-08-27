"""Tool 3 — simulate_counterfactual: bounded traversal of the curated causal graph.

Only ever changes exactly one allowlisted input (an ``AllowedChange`` already
curated in ``causal_graph.json``). Never invents a new suspect, diagnosis,
motive, evidence, verdict probability, or guilt conclusion; the mandatory
hypothetical disclaimer is always present on a successful result.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..contracts import ConfidenceLabel, MVP_CASE_ID, NonEmptyText, StableId
from ..services.case_loader import AllowedChange, CaseLoaderError, CausalGraph, load_case_pack
from . import ToolError, ToolSpec, register_tool

__all__ = [
    "SimulateCounterfactualRequest",
    "UnchangedFactSummary",
    "SimulateCounterfactualResult",
    "simulate_counterfactual",
]

DEFAULT_MAX_TRAVERSAL_NODES = 10
DEFAULT_MAX_TRAVERSAL_DEPTH = 2


class SimulateCounterfactualRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: str
    event_id: StableId
    allowed_change_id: StableId


class UnchangedFactSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    text: NonEmptyText
    source_ids: tuple[StableId, ...]


class SimulateCounterfactualResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    status: str  # "ok"
    event_id: StableId
    allowed_change_id: StableId
    original_condition: NonEmptyText
    changed_assumption: NonEmptyText
    directly_affected_nodes: tuple[StableId, ...]
    downstream_possible_effects: tuple[NonEmptyText, ...]
    unchanged_facts: tuple[UnchangedFactSummary, ...]
    unknowns: tuple[NonEmptyText, ...]
    confidence_label: ConfidenceLabel
    mandatory_hypothetical_disclaimer: NonEmptyText
    source_ids: tuple[StableId, ...]


def _bounded_downstream_traversal(
    graph: CausalGraph, start_node_ids: set[str], *, max_nodes: int, max_depth: int
) -> tuple[str, ...]:
    adjacency: dict[str, list[str]] = {node.node_id: [] for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.from_node_id].append(edge.to_node_id)

    visited: set[str] = set(start_node_ids)
    frontier: set[str] = set(start_node_ids)
    for _ in range(max_depth):
        next_frontier: set[str] = set()
        for node_id in frontier:
            for neighbour in adjacency.get(node_id, ()):
                if neighbour not in visited:
                    next_frontier.add(neighbour)
        if not next_frontier:
            break
        if len(visited) + len(next_frontier) > max_nodes:
            raise ToolError(
                "TRAVERSAL_LIMIT_EXCEEDED",
                f"The downstream traversal would exceed the {max_nodes}-node safety limit.",
            )
        visited |= next_frontier
        frontier = next_frontier
    return tuple(sorted(visited))


def simulate_counterfactual(
    request: SimulateCounterfactualRequest,
    *,
    max_traversal_nodes: int = DEFAULT_MAX_TRAVERSAL_NODES,
    max_traversal_depth: int = DEFAULT_MAX_TRAVERSAL_DEPTH,
) -> SimulateCounterfactualResult:
    if request.case_id != MVP_CASE_ID:
        raise ToolError("UNSUPPORTED_CASE", f"Case '{request.case_id}' is not part of the curated case library.")

    try:
        pack = load_case_pack(request.case_id)
    except CaseLoaderError as exc:
        raise ToolError("CASE_DATA_UNAVAILABLE", exc.user_message) from exc

    known_events = {e.event_id for e in pack.timeline}
    if request.event_id not in known_events:
        raise ToolError("UNKNOWN_EVENT_ID", f"'{request.event_id}' is not a known timeline event id.")

    changes_by_id = {c.change_id: c for c in pack.causal_graph.allowed_changes}
    change: AllowedChange | None = changes_by_id.get(request.allowed_change_id)
    if change is None:
        raise ToolError(
            "UNKNOWN_CHANGE_ID", f"'{request.allowed_change_id}' is not a known allowed change id."
        )
    if change.event_id != request.event_id:
        raise ToolError(
            "UNKNOWN_CHANGE_FOR_EVENT",
            f"Change '{change.change_id}' is not defined for event '{request.event_id}'.",
        )

    nodes_by_id = {n.node_id for n in pack.causal_graph.nodes}
    if change.target_node_id not in nodes_by_id:
        raise ToolError("GRAPH_INTEGRITY_ERROR", "The change's target node is missing from the causal graph.")

    node_labels = {n.node_id: n.label for n in pack.causal_graph.nodes}
    original_condition = node_labels[change.target_node_id]

    direct_effect_ids = tuple(effect.node_id for effect in change.direct_effects)
    for node_id in direct_effect_ids:
        if node_id not in nodes_by_id:
            raise ToolError("GRAPH_INTEGRITY_ERROR", "A direct effect references a node missing from the graph.")

    start_nodes = {change.target_node_id, *direct_effect_ids}
    downstream_node_ids = _bounded_downstream_traversal(
        pack.causal_graph, start_nodes, max_nodes=max_traversal_nodes, max_depth=max_traversal_depth
    )

    extra_downstream_labels = tuple(
        f"This change may also structurally propagate to '{node_labels[nid]}' via the curated causal graph."
        for nid in downstream_node_ids
        if nid not in start_nodes
    )
    downstream_possible_effects = tuple(
        effect.description for effect in change.direct_effects
    ) + change.downstream_possible_effects + extra_downstream_labels

    unchanged_facts = tuple(
        UnchangedFactSummary(text=fact.text, source_ids=fact.source_ids) for fact in change.unchanged_facts
    )

    nodes_by_id_full = {n.node_id: n for n in pack.causal_graph.nodes}
    source_ids: set[str] = set(nodes_by_id_full[change.target_node_id].source_ids)
    for node_id in direct_effect_ids:
        source_ids.update(nodes_by_id_full[node_id].source_ids)
    for fact in change.unchanged_facts:
        source_ids.update(fact.source_ids)
    source_ids = tuple(sorted(source_ids))

    return SimulateCounterfactualResult(
        status="ok",
        event_id=request.event_id,
        allowed_change_id=change.change_id,
        original_condition=original_condition,
        changed_assumption=change.description,
        directly_affected_nodes=direct_effect_ids,
        downstream_possible_effects=downstream_possible_effects,
        unchanged_facts=unchanged_facts,
        unknowns=change.unknowns,
        confidence_label=ConfidenceLabel.LOW,
        mandatory_hypothetical_disclaimer=change.mandatory_hypothetical_disclaimer,
        source_ids=source_ids,
    )


register_tool(
    ToolSpec(
        name="simulate_counterfactual",
        description="Traverse the curated causal graph for one allowlisted hypothetical change, bounded and disclaimed.",
        permission_category="read_case_data",
        input_schema=SimulateCounterfactualRequest.model_json_schema(),
        result_schema=SimulateCounterfactualResult.model_json_schema(),
    )
)
