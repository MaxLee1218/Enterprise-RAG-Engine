from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = PROJECT_ROOT / "enterprise-documents"
DEFAULT_MANIFEST = CORPUS_ROOT / "manifest.json"
DEFAULT_POLICY_RULES = CORPUS_ROOT / "policy_rules.json"

REQUIRED_PDF_FACTS = {
    "SQM-001": (
        "Less than 2.00%",
        "two consecutive quarters requires management review",
        "Major deviations must be escalated regardless",
    ),
    "QP-INSP-004": (
        "SUM(total_quantity)",
        "SUM(rejected_quantity)",
        "inspection record count shall never be used as Inspected Count",
    ),
    "POL-SQ-007": (
        "Major nonconformances must be escalated",
        "Critical nonconformances require immediate escalation",
    ),
    "KPI-SQ-002": (
        "Inspected Count = SUM(total_quantity)",
        "Defect Count = SUM(rejected_quantity)",
        "Period-over-period change = current period Defect Rate - previous period Defect Rate",
    ),
    "QP-SQ-012": (
        "1.99% is Acceptable",
        "2.00% is Review Required",
        "5.00% is Review Required",
        "5.01% is Corrective Action Required",
    ),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Supplier Quality source, PDFs, manifest, and optional index."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--policy-rules", type=Path, default=DEFAULT_POLICY_RULES)
    parser.add_argument("--persist-path", type=Path)
    parser.add_argument("--collection", default="supplier_quality_demo")
    parser.add_argument("--update-manifest", action="store_true")
    return parser.parse_args(argv)


def validate_corpus(
    manifest_path: Path,
    policy_path: Path,
    *,
    persist_path: Path | None = None,
    collection: str = "supplier_quality_demo",
    update_manifest: bool = False,
) -> dict[str, Any]:
    manifest = _read_object(manifest_path)
    rules = _read_object(policy_path)
    documents = manifest.get("documents")
    if not isinstance(documents, list) or len(documents) != 5:
        raise ValueError("manifest must contain exactly five documents")
    if manifest.get("policy_rules_sha256") != _sha256(policy_path):
        raise ValueError("manifest policy_rules_sha256 does not match policy_rules.json")

    from pypdf import PdfReader

    results: list[dict[str, Any]] = []
    ids: set[str] = set()
    for document in documents:
        if not isinstance(document, dict):
            raise ValueError("manifest document must be an object")
        document_id = _required_text(document, "document_id")
        if document_id in ids:
            raise ValueError(f"duplicate document_id: {document_id}")
        ids.add(document_id)
        source_path = manifest_path.parent / _required_text(document, "source_file")
        pdf_path = manifest_path.parent / _required_text(document, "pdf_file")
        if not source_path.is_file() or not pdf_path.is_file():
            raise ValueError(f"missing source or PDF for {document_id}")
        if _sha256(pdf_path) != document.get("sha256"):
            raise ValueError(f"PDF checksum mismatch for {document_id}")
        reader = PdfReader(pdf_path)
        if not reader.pages:
            raise ValueError(f"PDF has no pages: {document_id}")
        if len(reader.pages) != document.get("page_count"):
            raise ValueError(f"PDF page count mismatch for {document_id}")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        normalized_text = " ".join(text.split())
        if len(text.strip()) < 1000:
            raise ValueError(f"PDF extracted text is unexpectedly short: {document_id}")
        for value in (
            document_id,
            _required_text(document, "title"),
            _required_text(document, "version"),
            _required_text(document, "owner"),
            *REQUIRED_PDF_FACTS[document_id],
        ):
            if " ".join(value.split()) not in normalized_text:
                raise ValueError(f"PDF {document_id} is missing required text: {value}")
        metadata = reader.metadata or {}
        if _required_text(document, "title") not in str(metadata.get("/Title", "")):
            raise ValueError(f"PDF title metadata mismatch for {document_id}")
        results.append(
            {
                "document_id": document_id,
                "filename": document["filename"],
                "version": document["version"],
                "pages": len(reader.pages),
                "sha256": document["sha256"],
                "chunks": None,
                "status": "built",
            }
        )

    _validate_rule_contract(rules)
    index_total = None
    if persist_path is not None:
        index_total = _validate_index(
            persist_path,
            collection,
            documents,
            results,
        )
        if update_manifest:
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    return {
        "documents": results,
        "document_count": len(results),
        "index_total_chunks": index_total,
        "policy_consistent": True,
    }


def _validate_index(
    persist_path: Path,
    collection: str,
    documents: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> int:
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=str(persist_path),
        settings=Settings(
            anonymized_telemetry=False,
            chroma_api_impl="chromadb.api.segment.SegmentAPI",
        ),
    )
    target = client.get_collection(collection)
    result_by_id = {item["document_id"]: item for item in results}
    counted = 0
    for document in documents:
        document_id = document["document_id"]
        stored = target.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"],
        )
        chunk_ids = stored.get("ids") or []
        metadatas = stored.get("metadatas") or []
        texts = stored.get("documents") or []
        if not chunk_ids:
            raise ValueError(f"index has no chunks for {document_id}")
        for chunk_id, metadata, text in zip(chunk_ids, metadatas, texts):
            if not isinstance(metadata, dict):
                raise ValueError(f"index metadata missing for chunk {chunk_id}")
            for field in ("document_id", "title", "version", "source", "chunk_id"):
                if not metadata.get(field):
                    raise ValueError(f"index chunk {chunk_id} is missing metadata.{field}")
            if metadata["document_id"] != document_id:
                raise ValueError(f"index document_id mismatch for chunk {chunk_id}")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"index chunk text is blank: {chunk_id}")
        chunk_count = len(chunk_ids)
        document["chunk_count"] = chunk_count
        document["ingestion_status"] = "indexed"
        result_by_id[document_id]["chunks"] = chunk_count
        result_by_id[document_id]["status"] = "indexed"
        counted += chunk_count
    if target.count() != counted:
        raise ValueError(
            "isolated collection contains chunks outside the five-document corpus"
        )
    return counted


def _validate_rule_contract(rules: dict[str, Any]) -> None:
    rate = rules.get("defect_rate") or {}
    if rate.get("numerator") != "SUM(rejected_quantity)":
        raise ValueError("unexpected defect-rate numerator")
    if rate.get("denominator") != "SUM(total_quantity)":
        raise ValueError("unexpected defect-rate denominator")
    expected_boundaries = {
        "1.99%": "acceptable",
        "2.00%": "review_required",
        "5.00%": "review_required",
        "5.01%": "corrective_action_required",
    }
    if rules.get("boundary_examples") != expected_boundaries:
        raise ValueError("boundary examples do not match the controlled contract")
    consecutive = rules.get("consecutive_quarter_management_review") or {}
    if consecutive.get("threshold_min_inclusive") != 0.02:
        raise ValueError("consecutive-quarter threshold must include 2 percent")
    if consecutive.get("consecutive_periods") != 2:
        raise ValueError("consecutive-quarter rule must require two periods")
    if (rules.get("major_deviation") or {}).get("escalation_required") is not True:
        raise ValueError("major-deviation escalation must be required")


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return payload


def _required_text(item: dict[str, Any], field: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"manifest field {field} must be a non-blank string")
    return value.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = validate_corpus(
            args.manifest,
            args.policy_rules,
            persist_path=args.persist_path,
            collection=args.collection,
            update_manifest=args.update_manifest,
        )
    except Exception as error:
        print(f"Document validation failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
