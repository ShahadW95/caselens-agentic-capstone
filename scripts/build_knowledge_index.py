#!/usr/bin/env python3
"""Build the local vector index for a case's knowledge base.

Offline by default: pass ``--fake-embeddings`` to build with the
deterministic development embedding client (no network, no credentials).
Without that flag the script requires a configured Gemini embedding
credential and is not exercised by the test suite or CI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from caselens.config import FROZEN_EMBEDDING_DIMENSIONS, RuntimeConfig  # noqa: E402
from caselens.rag import RagError  # noqa: E402
from caselens.rag.chunking import chunk_documents  # noqa: E402
from caselens.rag.index import DeterministicFakeEmbeddingClient, build_index, save_index  # noqa: E402
from caselens.rag.loaders import CASE_ID_TO_FOLDER, load_knowledge_documents  # noqa: E402
from caselens.services.case_loader import load_case_pack  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a case's local knowledge-base vector index.")
    parser.add_argument("--case-id", required=True, help="Stable case ID, e.g. US_SDNY_09CR00213_DC")
    parser.add_argument(
        "--fake-embeddings",
        action="store_true",
        help="Use the deterministic offline embedding client instead of a live provider.",
    )
    args = parser.parse_args(argv)

    try:
        case_pack = load_case_pack(args.case_id)
        known_source_ids = frozenset(s.source_id for s in case_pack.source_manifest.sources)
        documents = load_knowledge_documents(args.case_id, known_source_ids=known_source_ids)
        chunks = chunk_documents(documents)
    except RagError as exc:
        print(f"FAIL [{exc.code}]: {exc.user_message}")
        return 1

    if args.fake_embeddings:
        embedding_client = DeterministicFakeEmbeddingClient(dimensions=FROZEN_EMBEDDING_DIMENSIONS)
    else:
        config = RuntimeConfig.from_sources()
        if not config.provider_configured:
            print(
                "FAIL [PROVIDER_NOT_CONFIGURED]: No embedding credential is configured. "
                "Pass --fake-embeddings for an offline build, or configure GEMINI_API_KEY."
            )
            return 1
        print(
            "FAIL [LIVE_ADAPTER_NOT_WIRED]: The live Gemini embedding adapter is not yet wired "
            "behind this boundary in this checkpoint; pending the explicit connection-check script."
        )
        return 1

    try:
        bundle = build_index(args.case_id, chunks, embedding_client)
        output_dir = save_index(bundle, case_folder=CASE_ID_TO_FOLDER[args.case_id])
    except RagError as exc:
        print(f"FAIL [{exc.code}]: {exc.user_message}")
        return 1

    print("PASS: index built successfully.")
    print(f"  case_id: {args.case_id}")
    print(f"  documents: {len(documents)}")
    print(f"  chunks: {len(chunks)}")
    print(f"  embedding_model_id: {bundle.manifest.embedding_model_id}")
    print(f"  embedding_dimensions: {bundle.manifest.embedding_dimensions}")
    print(f"  output_dir: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
