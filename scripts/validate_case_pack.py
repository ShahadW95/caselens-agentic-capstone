#!/usr/bin/env python3
"""Validate a curated case pack under ``data/cases/<folder>/``.

Exit code is 0 only when the pack loads and passes every structural check in
``caselens.services.case_loader.load_case_pack``. Any failure prints a single
``FAIL [<code>]: <message>`` line and exits non-zero.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from caselens.services.case_loader import CaseLoaderError, load_case_pack  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a curated CASE//LENS case pack.")
    parser.add_argument("--case-id", required=True, help="Stable case ID, e.g. US_SDNY_09CR00213_DC")
    args = parser.parse_args(argv)

    try:
        pack = load_case_pack(args.case_id)
    except CaseLoaderError as exc:
        print(f"FAIL [{exc.code}]: {exc.user_message}")
        return 1

    print("PASS: case pack validated successfully.")
    print(f"  case_id: {pack.case_metadata.case_id}")
    print(f"  proceedings: {len(pack.case_metadata.proceedings)}")
    print(f"  timeline events: {len(pack.timeline)}")
    print(f"  claims: {len(pack.claims)}")
    print(f"  evidence items: {len(pack.evidence)}")
    print(f"  financial amounts: {len(pack.financial_amounts)}")
    print(f"  causal nodes: {len(pack.causal_graph.nodes)}")
    print(f"  causal edges: {len(pack.causal_graph.edges)}")
    print(f"  causal allowed changes: {len(pack.causal_graph.allowed_changes)}")
    print(f"  sources: {len(pack.source_manifest.sources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
