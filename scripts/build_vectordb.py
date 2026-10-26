# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""Build the offline knowledge base (ChromaDB) from tracked repo content.

Canonical one-command rebuild for the project's vector database. Reads
every tracked curriculum JSON under ``scripts/data_collection/data/content``
and upserts deterministic hash-ID chunks into ``satya_data/chroma_db`` -
so contributors can verify a content PR locally, and the release
pipeline rebuilds the complete DB that ships to students.

Usage:
    python scripts/build_vectordb.py [--check]
    python scripts/build_vectordb.py --db <path>
"""

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.rag_data_preparation.content_flattener import (  # noqa: E402
    ContentValidationError,
    flatten_content_file,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

CONTENT_DIR = PROJECT_ROOT / "scripts" / "data_collection" / "data" / "content"
DEFAULT_DB = PROJECT_ROOT / "satya_data" / "chroma_db"
BATCH = 100


def collect_content_files() -> list:
    """Tracked curriculum files (deterministic order for reproducibility)."""
    return sorted(CONTENT_DIR.glob("*.json"))


def validate_all(files: list) -> list:
    """Flatten and validate every content file (no chroma/model I/O)."""
    items = []
    for path in files:
        try:
            flat = flatten_content_file(path)
        except ContentValidationError as e:
            logger.error(f"[X] {e}")
            raise SystemExit(1) from e
        logger.info(f"[ok] {path.name}: {len(flat)} concepts")
        items.extend(flat)
    return items


def build_db(items: list, db_path: Path) -> dict:
    """Embed + upsert the validated items and prune stale revisions."""
    import chromadb
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    client = chromadb.PersistentClient(path=str(db_path))

    per_collection = {}
    for name in sorted({i["collection"] for i in items}):
        group = [i for i in items if i["collection"] == name]
        coll = client.get_or_create_collection(name=name)
        new_ids = {i["id"] for i in group}
        existing_ids = set(coll.get(include=[])["ids"])
        stale = sorted(existing_ids - new_ids)
        if stale:
            coll.delete(ids=stale)
            logger.info(f"    {name}: pruned {len(stale)} stale chunks")
        for start in range(0, len(group), BATCH):
            batch = group[start : start + BATCH]
            coll.upsert(
                ids=[i["id"] for i in batch],
                documents=[i["text"] for i in batch],
                embeddings=model.encode(
                    [i["text"] for i in batch], convert_to_numpy=True
                ).tolist(),
                metadatas=[i["metadata"] for i in batch],
            )
        per_collection[name] = coll.count()

    for name, count in sorted(per_collection.items()):
        logger.info(f"    {name}: {count} chunks")
    return per_collection


def main():
    parser = argparse.ArgumentParser(description="Build the offline knowledge base")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate content only (no DB/model I/O) - exit 1 on any problem",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="ChromaDB path (default: satya_data/chroma_db)",
    )
    parser.add_argument(
        "--out-manifest",
        type=Path,
        default=None,
        help="Optional JSON report path (item ids + per-collection counts)",
    )
    args = parser.parse_args()

    files = collect_content_files()
    if not files:
        logger.error("[X] no content files found under %s", CONTENT_DIR)
        sys.exit(1)

    items = validate_all(files)

    manifest = {
        "content_files": [p.name for p in files],
        "items": [{"id": i["id"], "collection": i["collection"]} for i in items],
        "per_collection": dict.fromkeys(sorted({i["collection"] for i in items}), 0),
    }

    if not args.check:
        counts = build_db(items, args.db)
        manifest["per_collection"] = counts
        logger.info("Knowledge base rebuilt at %s", args.db)
    else:
        logger.info(
            "[check] content valid; %d concepts across %d collections",
            len(items),
            len(manifest["per_collection"]),
        )

    if args.out_manifest:
        args.out_manifest.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_manifest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)
        logger.info("Manifest written to %s", args.out_manifest)


if __name__ == "__main__":
    main()
