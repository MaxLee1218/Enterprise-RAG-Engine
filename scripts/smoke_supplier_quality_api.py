from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "supplier_quality_api_report.json"
NOT_FOUND = "Not found in knowledge base."

CASES = (
    {
        "query": "What defect rate is considered acceptable?",
        "facts": ("below 2.00%", "acceptable"),
        "documents": ("SQM-001", "KPI-SQ-002"),
    },
    {
        "query": "What happens when a supplier's defect rate exceeds 5%?",
        "facts": ("corrective action",),
        "documents": ("SQM-001", "QP-SQ-012"),
    },
    {
        "query": "What happens when a supplier exceeds the review threshold for two consecutive quarters?",
        "facts": ("management review",),
        "documents": ("SQM-001", "QP-SQ-012"),
    },
    {
        "query": "Do major deviations require escalation?",
        "facts": ("escalat",),
        "documents": ("POL-SQ-007", "QP-SQ-012", "SQM-001"),
    },
    {
        "query": "How is supplier defect rate calculated?",
        "facts": ("rejected_quantity", "total_quantity"),
        "documents": ("KPI-SQ-002",),
    },
    {
        "query": "What does inspected count mean?",
        "facts": ("sum(total_quantity)", "individual"),
        "documents": ("KPI-SQ-002", "QP-INSP-004"),
    },
    {
        "query": "When does poor supplier performance need leadership attention?",
        "facts": ("repeated threshold performance", "leadership"),
        "documents": ("SQM-001", "QP-SQ-012"),
    },
    {
        "query": "How should a 6% defect rate with a major deviation be handled?",
        "facts": ("corrective action", "major deviation", "escalat"),
        "documents": ("SQM-001", "POL-SQ-007"),
        "all_documents": ("SQM-001", "POL-SQ-007"),
    },
    {
        "query": "How is a 1.99% defect rate classified?",
        "facts": ("acceptable",),
        "documents": ("SQM-001", "KPI-SQ-002", "QP-SQ-012"),
    },
    {
        "query": "How is a 2.00% defect rate classified?",
        "facts": ("review required",),
        "documents": ("SQM-001", "KPI-SQ-002", "QP-SQ-012"),
    },
    {
        "query": "How is a 5.00% defect rate classified?",
        "facts": ("review required",),
        "documents": ("SQM-001", "KPI-SQ-002", "QP-SQ-012"),
    },
    {
        "query": "How is a 5.01% defect rate classified?",
        "facts": ("corrective action required",),
        "documents": ("SQM-001", "KPI-SQ-002", "QP-SQ-012"),
    },
    {
        "query": "What is the company's employee vacation policy?",
        "abstain": True,
    },
    {
        "query": "What is the corporate cafeteria reimbursement limit?",
        "abstain": True,
    },
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run authorized full HTTP checks against Supplier Quality RAG."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8011")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser.parse_args(argv)


def run_smoke(base_url: str, timeout: float) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    with httpx.Client(base_url=base_url, timeout=timeout, trust_env=False) as client:
        health_response = client.get("/health")
        health_response.raise_for_status()
        health = health_response.json()
        if health.get("status") != "ok":
            raise ValueError("health response is not ok")

        for index, case in enumerate(CASES, start=1):
            trace_id = f"supplier-quality-api-{index:03d}"
            response = client.post(
                "/ask",
                headers={"X-Trace-ID": trace_id},
                json={"question": case["query"]},
            )
            response.raise_for_status()
            payload = response.json()
            answer = str(payload.get("answer") or "")
            sources = payload.get("sources") or []
            contexts = payload.get("contexts") or []
            errors: list[str] = []
            if payload.get("route") != "rag":
                errors.append("route is not rag")
            if payload.get("rag_trace_id") != trace_id:
                errors.append("trace id was not preserved")
            if not isinstance(payload.get("latency_ms"), (int, float)):
                errors.append("latency_ms is missing")
            normalized_answer = " ".join(
                answer.casefold().replace("_", " ").split()
            )
            if case.get("abstain"):
                if answer.strip() != NOT_FOUND:
                    errors.append("unsupported question did not abstain")
            else:
                if not contexts or not sources:
                    errors.append("evidence-backed response has no sources or contexts")
                for fact in case.get("facts") or ():
                    normalized_fact = " ".join(
                        str(fact).casefold().replace("_", " ").split()
                    )
                    if normalized_fact not in normalized_answer:
                        errors.append(f"answer missing fact: {fact}")
                actual_document_ids = {
                    str((item.get("metadata") or {}).get("document_id") or "")
                    for item in contexts
                    if isinstance(item, dict)
                }
                expected_documents = set(case.get("documents") or ())
                if expected_documents and not expected_documents.intersection(
                    actual_document_ids
                ):
                    errors.append("expected source document is absent")
                required_documents = set(case.get("all_documents") or ())
                if not required_documents.issubset(actual_document_ids):
                    errors.append("required multi-document evidence is absent")
                _validate_evidence_metadata(sources, contexts, errors)
            records.append(
                {
                    "query": case["query"],
                    "trace_id": trace_id,
                    "status_code": response.status_code,
                    "answer": answer,
                    "source_document_ids": sorted(
                        {
                            str((item.get("metadata") or {}).get("document_id") or "")
                            for item in sources
                            if isinstance(item, dict)
                        }
                        - {""}
                    ),
                    "context_count": len(contexts),
                    "latency_ms": payload.get("latency_ms"),
                    "passed": not errors,
                    "errors": errors,
                }
            )
    passed = sum(bool(record["passed"]) for record in records)
    abstention_records = records[-2:]
    return {
        "health": health,
        "cases": len(records),
        "passed": passed,
        "failed": len(records) - passed,
        "abstention_passed": sum(
            record["answer"].strip() == NOT_FOUND for record in abstention_records
        ),
        "records": records,
    }


def _validate_evidence_metadata(
    sources: list[Any], contexts: list[Any], errors: list[str]
) -> None:
    for label, items in (("source", sources), ("context", contexts)):
        for item in items:
            if not isinstance(item, dict):
                errors.append(f"{label} is not an object")
                continue
            metadata = item.get("metadata")
            if not isinstance(metadata, dict):
                errors.append(f"{label} metadata is missing")
                continue
            for field in ("document_id", "version", "chunk_id", "source"):
                if not metadata.get(field):
                    errors.append(f"{label} metadata.{field} is missing")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_smoke(args.base_url, args.timeout)
    except Exception as error:
        print(f"Supplier Quality API smoke failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
