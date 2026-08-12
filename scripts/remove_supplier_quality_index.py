from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


DEFAULT_PERSIST_PATH = Path("data/supplier_quality/chroma")
DEFAULT_COLLECTION = "supplier_quality_demo"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect or explicitly delete only the Supplier Quality demo collection."
    )
    parser.add_argument("--persist-path", type=Path, default=DEFAULT_PERSIST_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument(
        "--confirm-delete",
        help=(
            "Delete only when this value exactly matches --collection. "
            "Without it the command is read-only."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.collection != DEFAULT_COLLECTION:
        print(
            f"Refusing non-demo collection: {args.collection}. "
            f"Expected {DEFAULT_COLLECTION}.",
            file=sys.stderr,
        )
        return 1
    if not args.persist_path.exists():
        print(f"Supplier Quality index path does not exist: {args.persist_path}")
        return 0

    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=str(args.persist_path),
        settings=Settings(
            anonymized_telemetry=False,
            chroma_api_impl="chromadb.api.segment.SegmentAPI",
        ),
    )
    try:
        collection = client.get_collection(args.collection)
    except Exception:
        print(f"Supplier Quality collection does not exist: {args.collection}")
        return 0
    count = collection.count()
    if args.confirm_delete != args.collection:
        print(
            f"Read-only inspection: collection={args.collection} chunks={count}. "
            f"Pass --confirm-delete {args.collection} to delete this collection only."
        )
        return 0
    client.delete_collection(args.collection)
    print(f"Deleted collection={args.collection} chunks={count} from {args.persist_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
