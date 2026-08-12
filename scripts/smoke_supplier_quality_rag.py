from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.bm25_retriever import BM25Retriever
from app.embeddings import Embedder
from app.hybrid_retriever import HybridRetriever
from app.retriever import Retriever
from app.reranker import CrossEncoderReranker
from app.vector_store import ChromaVectorStore


DEFAULT_DATASET = (
    PROJECT_ROOT / "evaluation" / "dataset" / "supplier_quality_eval_dataset.json"
)
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "supplier_quality_retrieval_report.json"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run real hybrid retrieval gates against the Supplier Quality corpus."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--persist-path", default="data/supplier_quality/chroma")
    parser.add_argument("--collection", default="supplier_quality_demo")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--candidate-k", type=int, default=10)
    parser.add_argument("--no-reranker", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def run_smoke(
    dataset_path: Path,
    persist_path: str,
    collection: str,
    *,
    top_k: int = 5,
    candidate_k: int = 10,
    rerank: bool = True,
) -> dict[str, Any]:
    if top_k < 1 or candidate_k < top_k:
        raise ValueError("candidate_k must be greater than or equal to positive top_k")
    cases = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("dataset must be a non-empty JSON list")

    store = ChromaVectorStore(collection_name=collection, persist_path=persist_path)
    try:
        stored = store.collection.get(include=["documents", "metadatas"])
        documents = [
            {
                "id": item_id,
                "text": (stored.get("documents") or [])[index],
                "metadata": (stored.get("metadatas") or [])[index] or {},
            }
            for index, item_id in enumerate(stored.get("ids") or [])
        ]
        document_ids = {
            str((document.get("metadata") or {}).get("document_id") or "")
            for document in documents
        }
        expected_corpus_ids = {
            "SQM-001",
            "QP-INSP-004",
            "POL-SQ-007",
            "KPI-SQ-002",
            "QP-SQ-012",
        }
        if document_ids != expected_corpus_ids:
            raise ValueError(
                "isolated collection document IDs do not match the Supplier Quality corpus"
            )
        embedder = Embedder()
        dense = Retriever(embedder=embedder, vector_store=store, default_top_k=candidate_k)
        hybrid = HybridRetriever(
            sparse_retriever=BM25Retriever(documents),
            dense_retriever=dense,
            sparse_weight=0.5,
            dense_weight=0.5,
            candidate_multiplier=2,
        )
        reranker = None
        if rerank:
            reranker = CrossEncoderReranker(
                "cross-encoder/ms-marco-TinyBERT-L2-v2",
                batch_size=16,
                max_length=256,
                device="cpu",
                local_files_only=True,
            )

        records: list[dict[str, Any]] = []
        positives = 0
        passed = 0
        for case in cases:
            if case.get("expected_no_evidence"):
                records.append(
                    {
                        "query": case["question"],
                        "result": "deferred_to_grounded_generation",
                        "passed": None,
                    }
                )
                continue
            positives += 1
            candidates = hybrid.retrieve(case["question"], top_k=candidate_k)
            results = (
                reranker.rerank(case["question"], candidates, top_k=top_k)
                if reranker is not None
                else candidates[:top_k]
            )
            document_ids = [
                str((result.get("metadata") or {}).get("document_id") or "")
                for result in results
            ]
            combined_text = " ".join(
                " ".join(str(result.get("text") or "").casefold().split())
                for result in results
            )
            expected_ids = set(case.get("expected_document_ids") or [])
            expected_all = set(case.get("expected_all_document_ids") or [])
            facts = case.get("reference_contexts") or []
            source_ok = bool(expected_ids.intersection(document_ids))
            all_sources_ok = expected_all.issubset(document_ids)
            fact_ok = any(
                " ".join(str(fact).casefold().split()) in combined_text
                for fact in facts
            )
            case_passed = source_ok and all_sources_ok and fact_ok
            if case_passed:
                passed += 1
            records.append(
                {
                    "query": case["question"],
                    "expected_document_ids": sorted(expected_ids),
                    "actual_document_ids": document_ids,
                    "source_ok": source_ok,
                    "all_sources_ok": all_sources_ok,
                    "fact_ok": fact_ok,
                    "passed": case_passed,
                }
            )
        return {
            "strategy": "hybrid+reranker" if reranker is not None else "hybrid",
            "cases": len(cases),
            "positive_cases": positives,
            "passed": passed,
            "failed": positives - passed,
            "retrieval_gate_rate": passed / positives if positives else None,
            "negative_cases_deferred": len(cases) - positives,
            "records": records,
        }
    finally:
        store.close()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_smoke(
            args.dataset,
            args.persist_path,
            args.collection,
            top_k=args.top_k,
            candidate_k=args.candidate_k,
            rerank=not args.no_reranker,
        )
    except Exception as error:
        print(f"Supplier Quality smoke failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
