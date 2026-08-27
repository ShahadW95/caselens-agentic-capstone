from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from caselens.contracts import MVP_CASE_ID  # noqa: E402
from caselens.services.case_loader import (  # noqa: E402
    CaseLoaderError,
    CasePack,
    load_case_pack,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "case_001_minimal"
REAL_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "cases" / "case_001"

FILES = (
    "case_metadata.json",
    "timeline.json",
    "claims.json",
    "evidence.json",
    "financial_amounts.json",
    "causal_graph.json",
    "source_manifest.json",
)


def _read_fixture() -> dict[str, object]:
    return {name: json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8")) for name in FILES}


def _write_case_dir(directory: Path, files: dict[str, object]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        (directory / name).write_text(json.dumps(files[name]), encoding="utf-8")
    return directory


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def test_loads_the_minimal_fixture_pack() -> None:
    pack = load_case_pack(MVP_CASE_ID, case_dir=FIXTURE_DIR)
    assert isinstance(pack, CasePack)
    assert pack.case_metadata.case_id == MVP_CASE_ID
    assert len(pack.timeline) == 1
    assert len(pack.claims) == 1
    assert len(pack.evidence) == 1
    assert len(pack.financial_amounts) == 1
    assert len(pack.causal_graph.nodes) == 1


def test_loads_the_real_curated_case_pack() -> None:
    pack = load_case_pack(MVP_CASE_ID)
    assert pack.case_metadata.display_title == "United States v. Bernard L. Madoff"
    assert len(pack.timeline) == 12
    assert len(pack.claims) == 7
    assert len(pack.evidence) == 12
    assert len(pack.financial_amounts) == 5
    assert len(pack.source_manifest.sources) == 11

    proceeding_types = {p.proceeding_type.value for p in pack.case_metadata.proceedings}
    assert proceeding_types == {
        "CRIMINAL_CASE",
        "SEC_ENFORCEMENT",
        "SIPA_LIQUIDATION",
        "DOJ_VICTIM_FUND",
    }
    criminal = next(
        p for p in pack.case_metadata.proceedings if p.proceeding_type.value == "CRIMINAL_CASE"
    )
    recovery = [
        p
        for p in pack.case_metadata.proceedings
        if p.proceeding_type.value in {"SIPA_LIQUIDATION", "DOJ_VICTIM_FUND"}
    ]
    assert criminal.status.value == "CLOSED_FINAL"
    assert all(p.status.value != "CLOSED_FINAL" for p in recovery)

    amount_kinds = {a.amount_kind.value for a in pack.financial_amounts}
    assert amount_kinds == {
        "FICTITIOUS_STATEMENT_BALANCE",
        "ESTIMATED_PRINCIPAL_LOSS",
        "FORFEITURE_ORDER",
        "RECOVERY",
        "DISTRIBUTION",
    }


def test_timeline_is_deterministically_ordered() -> None:
    first = load_case_pack(MVP_CASE_ID)
    second = load_case_pack(MVP_CASE_ID)
    assert [e.event_id for e in first.timeline] == [e.event_id for e in second.timeline]
    # Precisely-dated events sort chronologically ahead of same-precision ties.
    ids = [e.event_id for e in first.timeline]
    assert ids.index("EVT_SEC_CIVIL_CHARGE_2008") < ids.index("EVT_GUILTY_PLEA_2009_03_12")
    assert ids.index("EVT_GUILTY_PLEA_2009_03_12") < ids.index("EVT_SENTENCING_2009_06_29")


def test_65b_and_17_5b_are_distinct_amount_kinds() -> None:
    pack = load_case_pack(MVP_CASE_ID)
    by_id = {a.amount_id: a for a in pack.financial_amounts}
    fictitious = by_id["FIN_FICTITIOUS_STATEMENT_BALANCE_65B"]
    principal_loss = by_id["FIN_ESTIMATED_PRINCIPAL_LOSS_17_5B"]
    assert fictitious.amount_kind.value == "FICTITIOUS_STATEMENT_BALANCE"
    assert principal_loss.amount_kind.value == "ESTIMATED_PRINCIPAL_LOSS"
    assert fictitious.amount_kind != principal_loss.amount_kind


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------


def test_unsupported_case_id_is_rejected() -> None:
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack("NOT_A_REAL_CASE")
    assert excinfo.value.code == "UNSUPPORTED_CASE"


def test_missing_file_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    del files["evidence.json"]
    case_dir = tmp_path / "case_001"
    case_dir.mkdir()
    for name, content in files.items():
        (case_dir / name).write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "MISSING_FILE"


def test_malformed_json_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    (case_dir / "claims.json").write_text("{not valid json", encoding="utf-8")
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "MALFORMED_JSON"


def test_duplicate_id_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    duplicate_event = copy.deepcopy(files["timeline.json"][0])
    files["timeline.json"] = [files["timeline.json"][0], duplicate_event]
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "DUPLICATE_ID"


def test_dangling_source_id_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    files["timeline.json"][0]["source_ids"] = ["FIX_SRC_DOES_NOT_EXIST"]
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "DANGLING_REFERENCE_ID"


def test_dangling_cross_reference_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    files["timeline.json"][0]["evidence_ids"] = ["FIX_EVID_DOES_NOT_EXIST"]
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "DANGLING_REFERENCE_ID"


def test_invalid_date_order_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    files["timeline.json"][0]["date_precision"] = "MONTH"
    files["timeline.json"][0]["event_date"] = None
    files["timeline.json"][0]["start_date"] = "2020-06-01"
    files["timeline.json"][0]["end_date"] = "2020-01-01"
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "SCHEMA_VALIDATION_FAILED"


def test_invalid_causal_edge_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    files["causal_graph.json"]["edges"] = [
        {
            "edge_id": "FIX_EDGE_BAD",
            "from_node_id": "FIX_CN_1",
            "to_node_id": "FIX_CN_DOES_NOT_EXIST",
            "edge_type": "PRECEDES",
            "rationale": "Fixture rationale.",
            "source_ids": ["FIX_SRC_A"],
        }
    ]
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "DANGLING_CAUSAL_NODE"


def test_causal_graph_cycle_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    second_node = copy.deepcopy(files["causal_graph.json"]["nodes"][0])
    second_node["node_id"] = "FIX_CN_2"
    files["causal_graph.json"]["nodes"].append(second_node)
    files["causal_graph.json"]["edges"] = [
        {
            "edge_id": "FIX_EDGE_1",
            "from_node_id": "FIX_CN_1",
            "to_node_id": "FIX_CN_2",
            "edge_type": "PRECEDES",
            "rationale": "Fixture rationale.",
            "source_ids": ["FIX_SRC_A"],
        },
        {
            "edge_id": "FIX_EDGE_2",
            "from_node_id": "FIX_CN_2",
            "to_node_id": "FIX_CN_1",
            "edge_type": "PRECEDES",
            "rationale": "Fixture rationale.",
            "source_ids": ["FIX_SRC_A"],
        },
    ]
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "CAUSAL_GRAPH_CYCLE"


def test_non_allowlisted_change_target_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    files["causal_graph.json"]["allowed_changes"][0]["target_node_id"] = "FIX_CN_DOES_NOT_EXIST"
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "NON_ALLOWLISTED_CHANGE_TARGET"


def test_claim_status_outside_the_deterministic_four_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    files["claims.json"][0]["status"] = "ALLEGED"
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "SCHEMA_VALIDATION_FAILED"


def test_proceeding_status_incompatible_with_type_is_rejected(tmp_path: Path) -> None:
    files = _read_fixture()
    files["case_metadata.json"]["proceedings"][0]["status"] = "ONGOING_RECOVERY"
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "SCHEMA_VALIDATION_FAILED"


def test_final_status_requires_a_tier_a_source(tmp_path: Path) -> None:
    files = _read_fixture()
    files["source_manifest.json"]["sources"][0]["source_tier"] = "C"
    case_dir = _write_case_dir(tmp_path / "case_001", files)
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=case_dir)
    assert excinfo.value.code == "FINAL_STATUS_NOT_AUTHORITATIVE"


def test_missing_case_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(CaseLoaderError) as excinfo:
        load_case_pack(MVP_CASE_ID, case_dir=tmp_path / "does_not_exist")
    assert excinfo.value.code == "MISSING_FILE"


def test_safe_error_conversion_never_marks_retry_allowed() -> None:
    try:
        load_case_pack("NOT_A_REAL_CASE")
    except CaseLoaderError as exc:
        fields = exc.to_safe_error_fields()
        assert fields["code"] == "UNSUPPORTED_CASE"
        assert fields["retry_allowed"] is False
        assert "error_id" in fields and "user_message" in fields
