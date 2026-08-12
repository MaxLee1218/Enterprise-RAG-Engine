from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader

from scripts.build_enterprise_documents import _validate_policy_rules, _validate_source
from scripts.validate_enterprise_documents import validate_corpus


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = PROJECT_ROOT / "enterprise-documents"


def _manifest():
    return json.loads((CORPUS_ROOT / "manifest.json").read_text(encoding="utf-8"))


def _rules():
    return json.loads((CORPUS_ROOT / "policy_rules.json").read_text(encoding="utf-8"))


def test_supplier_quality_corpus_contains_five_unique_active_documents():
    documents = _manifest()["documents"]

    assert len(documents) == 5
    assert len({item["document_id"] for item in documents}) == 5
    assert len({item["filename"] for item in documents}) == 5
    assert all(item["status"] == "active" for item in documents)


def test_policy_rules_define_exact_unit_semantics_and_boundaries():
    rules = _rules()

    _validate_policy_rules(rules)
    assert rules["defect_rate"] == {
        "numerator": "SUM(rejected_quantity)",
        "denominator": "SUM(total_quantity)",
        "zero_denominator": "not_calculable",
    }
    assert rules["boundary_examples"] == {
        "1.99%": "acceptable",
        "2.00%": "review_required",
        "5.00%": "review_required",
        "5.01%": "corrective_action_required",
    }
    assert rules["period_over_period"]["unit"] == "percentage points"


def test_all_sources_match_manifest_rules_and_cross_references():
    manifest = _manifest()
    rules = _rules()

    for document in manifest["documents"]:
        source = (CORPUS_ROOT / document["source_file"]).read_text(encoding="utf-8")
        _validate_source(document, source, rules)


def test_all_generated_pdfs_are_selectable_and_have_control_metadata():
    for document in _manifest()["documents"]:
        reader = PdfReader(CORPUS_ROOT / document["pdf_file"])
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        assert len(reader.pages) == document["page_count"] >= 1
        assert len(text) > 1000
        assert document["document_id"] in text
        assert document["title"] in text
        assert document["version"] in text
        assert document["title"] in str((reader.metadata or {}).get("/Title", ""))


def test_generated_corpus_passes_full_artifact_validation():
    result = validate_corpus(
        CORPUS_ROOT / "manifest.json",
        CORPUS_ROOT / "policy_rules.json",
    )

    assert result["document_count"] == 5
    assert result["policy_consistent"] is True
    assert result["index_total_chunks"] is None
