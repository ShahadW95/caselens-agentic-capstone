from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from caselens.contracts import ConfidenceLabel, MVP_CASE_ID, TimelineTrack  # noqa: E402
from caselens.tools import TOOL_REGISTRY, ToolError  # noqa: E402
from caselens.tools.claim_support import (  # noqa: E402
    CheckClaimSupportRequest,
    check_claim_support,
)
from caselens.tools.counterfactual import (  # noqa: E402
    SimulateCounterfactualRequest,
    simulate_counterfactual,
)
from caselens.tools.timeline import QueryCaseTimelineRequest, query_case_timeline  # noqa: E402

UNKNOWN_CASE = "NOT_A_REAL_CASE"


# ---------------------------------------------------------------------------
# Tool 1 — query_case_timeline
# ---------------------------------------------------------------------------


def test_timeline_filters_by_track_and_is_stably_sorted() -> None:
    result = query_case_timeline(
        QueryCaseTimelineRequest(case_id=MVP_CASE_ID, track=TimelineTrack.CRIMINAL), query_id="q.track"
    )
    assert result.status == "ok"
    ids = [e.event_id for e in result.events]
    assert ids == [
        "EVT_MADOFF_ARREST_DEC_2008",
        "EVT_GUILTY_PLEA_2009_03_12",
        "EVT_SENTENCING_2009_06_29",
        "EVT_MADOFF_DEATH_2021",
    ]
    # All returned events are actually CRIMINAL track.
    assert all(e.track == TimelineTrack.CRIMINAL for e in result.events)
    # Deterministic: same call, same order.
    again = query_case_timeline(
        QueryCaseTimelineRequest(case_id=MVP_CASE_ID, track=TimelineTrack.CRIMINAL), query_id="q.track2"
    )
    assert [e.event_id for e in again.events] == ids


def test_timeline_filters_by_date_range() -> None:
    result = query_case_timeline(
        QueryCaseTimelineRequest(
            case_id=MVP_CASE_ID, start_date=date(2009, 1, 1), end_date=date(2009, 12, 31)
        ),
        query_id="q.range",
    )
    assert result.status == "ok"
    ids = {e.event_id for e in result.events}
    assert "EVT_GUILTY_PLEA_2009_03_12" in ids
    assert "EVT_SENTENCING_2009_06_29" in ids
    assert "EVT_SIPC_PRINCIPAL_LOSS_REPORT_2018_07_05" not in ids


def test_timeline_filters_by_related_id() -> None:
    result = query_case_timeline(
        QueryCaseTimelineRequest(case_id=MVP_CASE_ID, related_id="CLAIM_MADOFF_STOLE_65B_CASH"),
        query_id="q.related",
    )
    assert result.status == "ok"
    assert result.result_count >= 1


def test_timeline_respects_limit() -> None:
    result = query_case_timeline(QueryCaseTimelineRequest(case_id=MVP_CASE_ID, limit=2), query_id="q.limit")
    assert result.result_count == 2
    assert len(result.events) == 2


def test_timeline_empty_result_is_explicit() -> None:
    result = query_case_timeline(
        QueryCaseTimelineRequest(
            case_id=MVP_CASE_ID, start_date=date(1900, 1, 1), end_date=date(1900, 1, 2)
        ),
        query_id="q.empty",
    )
    assert result.status == "empty"
    assert result.result_count == 0
    assert result.empty_result_reason is not None


def test_timeline_invalid_reversed_date_range_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QueryCaseTimelineRequest(case_id=MVP_CASE_ID, start_date=date(2020, 1, 2), end_date=date(2020, 1, 1))


def test_timeline_unknown_case_is_rejected() -> None:
    with pytest.raises(ToolError) as excinfo:
        query_case_timeline(QueryCaseTimelineRequest(case_id=UNKNOWN_CASE), query_id="q.unknown")
    assert excinfo.value.code == "UNSUPPORTED_CASE"


def test_timeline_unknown_related_id_is_rejected() -> None:
    with pytest.raises(ToolError) as excinfo:
        query_case_timeline(
            QueryCaseTimelineRequest(case_id=MVP_CASE_ID, related_id="NOT_A_REAL_ID"), query_id="q.badrel"
        )
    assert excinfo.value.code == "UNKNOWN_ID"


def test_timeline_unsupported_filter_value_is_rejected() -> None:
    with pytest.raises(ValidationError):
        QueryCaseTimelineRequest(case_id=MVP_CASE_ID, track="NOT_A_TRACK")


# ---------------------------------------------------------------------------
# Tool 2 — check_claim_support
# ---------------------------------------------------------------------------


def test_all_four_claim_statuses_are_reachable() -> None:
    supported = check_claim_support(
        CheckClaimSupportRequest(case_id=MVP_CASE_ID, claim_id="CLAIM_SEC_RECEIVED_COMPLAINTS")
    )
    contradicted = check_claim_support(
        CheckClaimSupportRequest(case_id=MVP_CASE_ID, claim_id="CLAIM_MADOFF_STOLE_65B_CASH")
    )
    partially_supported = check_claim_support(
        CheckClaimSupportRequest(case_id=MVP_CASE_ID, claim_id="CLAIM_MADOFF_ACTED_ALONE")
    )
    insufficient = check_claim_support(
        CheckClaimSupportRequest(case_id=MVP_CASE_ID, claim_id="CLAIM_SEC_WAS_CORRUPT")
    )
    assert supported.status == "supported"
    assert contradicted.status == "contradicted"
    assert partially_supported.status == "partially_supported"
    assert insufficient.status == "insufficient_evidence"


def test_supporting_and_contradicting_ids_propagate() -> None:
    result = check_claim_support(
        CheckClaimSupportRequest(case_id=MVP_CASE_ID, claim_id="CLAIM_MADOFF_ACTED_ALONE")
    )
    assert result.supporting_evidence_ids == ("EVID_GUILTY_PLEA_RECORD",)
    assert result.contradicting_evidence_ids == ("EVID_AUDITOR_ACTION_RECORD",)
    assert "SRC_DOJ_SDNY_CASEPAGE" in result.supporting_source_ids


def test_numeric_trap_claim_is_not_falsely_supported() -> None:
    result = check_claim_support(
        CheckClaimSupportRequest(case_id=MVP_CASE_ID, claim_id="CLAIM_MADOFF_STOLE_65B_CASH")
    )
    assert result.status != "supported"
    kinds = {a.amount_kind.value for a in result.financial_amounts}
    assert "FICTITIOUS_STATEMENT_BALANCE" in kinds
    assert "ESTIMATED_PRINCIPAL_LOSS" in kinds


def test_unknown_free_text_claim_returns_insufficient_not_an_error() -> None:
    result = check_claim_support(
        CheckClaimSupportRequest(case_id=MVP_CASE_ID, user_claim_text="What did he have for breakfast?")
    )
    assert result.status == "insufficient_evidence"
    assert result.claim_id is None


def test_unknown_claim_id_is_rejected() -> None:
    with pytest.raises(ToolError) as excinfo:
        check_claim_support(CheckClaimSupportRequest(case_id=MVP_CASE_ID, claim_id="CLAIM_DOES_NOT_EXIST"))
    assert excinfo.value.code == "UNKNOWN_CLAIM_ID"


def test_must_provide_exactly_one_of_claim_id_or_text() -> None:
    with pytest.raises(ValidationError):
        CheckClaimSupportRequest(case_id=MVP_CASE_ID)
    with pytest.raises(ValidationError):
        CheckClaimSupportRequest(
            case_id=MVP_CASE_ID, claim_id="CLAIM_MADOFF_STOLE_65B_CASH", user_claim_text="both given"
        )


def test_claim_support_unknown_case_is_rejected() -> None:
    with pytest.raises(ToolError) as excinfo:
        check_claim_support(CheckClaimSupportRequest(case_id=UNKNOWN_CASE, claim_id="CLAIM_TEST_UNKNOWN_CASE"))
    assert excinfo.value.code == "UNSUPPORTED_CASE"


# ---------------------------------------------------------------------------
# Tool 3 — simulate_counterfactual
# ---------------------------------------------------------------------------

VALID_EVENT_ID = "EVT_SCHEME_OPERATES_FOR_DECADES"
VALID_CHANGE_ID = "CHG_INDEPENDENT_VERIFICATION_AFTER_COMPLAINT"


def test_valid_one_change_counterfactual_traversal() -> None:
    result = simulate_counterfactual(
        SimulateCounterfactualRequest(case_id=MVP_CASE_ID, event_id=VALID_EVENT_ID, allowed_change_id=VALID_CHANGE_ID)
    )
    assert result.status == "ok"
    assert result.directly_affected_nodes == ("CN_SCHEME_CONTINUES",)
    assert len(result.downstream_possible_effects) >= 2
    assert len(result.unchanged_facts) >= 1
    assert len(result.unknowns) >= 1
    assert result.confidence_label == ConfidenceLabel.LOW


def test_disclaimer_is_always_present_and_identifies_hypothetical() -> None:
    result = simulate_counterfactual(
        SimulateCounterfactualRequest(case_id=MVP_CASE_ID, event_id=VALID_EVENT_ID, allowed_change_id=VALID_CHANGE_ID)
    )
    assert "hypothetical" in result.mandatory_hypothetical_disclaimer.lower()


def test_unknown_change_is_rejected() -> None:
    with pytest.raises(ToolError) as excinfo:
        simulate_counterfactual(
            SimulateCounterfactualRequest(
                case_id=MVP_CASE_ID, event_id=VALID_EVENT_ID, allowed_change_id="CHG_DOES_NOT_EXIST"
            )
        )
    assert excinfo.value.code == "UNKNOWN_CHANGE_ID"


def test_unknown_event_is_rejected() -> None:
    with pytest.raises(ToolError) as excinfo:
        simulate_counterfactual(
            SimulateCounterfactualRequest(
                case_id=MVP_CASE_ID, event_id="EVT_DOES_NOT_EXIST", allowed_change_id=VALID_CHANGE_ID
            )
        )
    assert excinfo.value.code == "UNKNOWN_EVENT_ID"


def test_change_mismatched_with_event_is_rejected() -> None:
    # A real event that exists, but is not the one this allowed change is anchored to.
    with pytest.raises(ToolError) as excinfo:
        simulate_counterfactual(
            SimulateCounterfactualRequest(
                case_id=MVP_CASE_ID, event_id="EVT_SENTENCING_2009_06_29", allowed_change_id=VALID_CHANGE_ID
            )
        )
    assert excinfo.value.code == "UNKNOWN_CHANGE_FOR_EVENT"


def test_excessive_traversal_fails_safely() -> None:
    with pytest.raises(ToolError) as excinfo:
        simulate_counterfactual(
            SimulateCounterfactualRequest(
                case_id=MVP_CASE_ID, event_id=VALID_EVENT_ID, allowed_change_id=VALID_CHANGE_ID
            ),
            max_traversal_nodes=1,
        )
    assert excinfo.value.code == "TRAVERSAL_LIMIT_EXCEEDED"


def test_counterfactual_unknown_case_is_rejected() -> None:
    with pytest.raises(ToolError) as excinfo:
        simulate_counterfactual(
            SimulateCounterfactualRequest(case_id=UNKNOWN_CASE, event_id=VALID_EVENT_ID, allowed_change_id=VALID_CHANGE_ID)
        )
    assert excinfo.value.code == "UNSUPPORTED_CASE"


# ---------------------------------------------------------------------------
# Registry, permissions, and no-network guarantees
# ---------------------------------------------------------------------------


def test_all_three_tools_are_registered_with_machine_readable_schemas() -> None:
    assert set(TOOL_REGISTRY) == {"query_case_timeline", "check_claim_support", "simulate_counterfactual"}
    for spec in TOOL_REGISTRY.values():
        assert spec.permission_category == "read_case_data"
        assert isinstance(spec.input_schema, dict) and spec.input_schema
        assert isinstance(spec.result_schema, dict) and spec.result_schema
        assert spec.description


def test_tools_modules_import_no_network_or_model_libraries() -> None:
    import ast

    for module_name in ("timeline", "claim_support", "counterfactual"):
        source = (Path(__file__).resolve().parents[1] / "src" / "caselens" / "tools" / f"{module_name}.py").read_text()
        tree = ast.parse(source)
        imported_roots = {
            (alias.name.split(".")[0])
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        forbidden = {"socket", "requests", "httpx", "urllib", "google", "openai"}
        assert imported_roots.isdisjoint(forbidden), f"{module_name} imports network/model library: {imported_roots & forbidden}"
