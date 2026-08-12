from __future__ import annotations

import logging

import pytest
from fastapi import HTTPException

from tests.asgi_client import asgi_request


def test_get_pipeline_reports_expected_not_ready_without_traceback(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import app.api as api_module

    def not_ready(*_args: object, **_kwargs: object) -> object:
        raise api_module.VectorStoreNotReadyError("not initialized")

    monkeypatch.setattr(api_module, "_pipeline", None)
    monkeypatch.setattr(api_module, "get_default_dual_path_pipeline", not_ready)

    with caplog.at_level(logging.WARNING, logger=api_module.__name__):
        with pytest.raises(HTTPException) as raised:
            api_module.get_pipeline()

    assert raised.value.status_code == 503
    assert raised.value.detail == (
        "Vector store is not ready. Please run scripts/ingest.py first."
    )
    record = next(
        item for item in caplog.records if item.message == "Vector store is not ready."
    )
    assert record.levelno == logging.WARNING
    assert record.exc_info is None


def test_unexpected_pipeline_error_is_classified_without_logging_details(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import app.api as api_module

    class FailingPipeline:
        def ask(self, *_args: object, **_kwargs: object) -> object:
            raise RuntimeError("sk-sensitive host=/Users/operator/private")

    monkeypatch.setattr(api_module, "log_request", lambda _entry: None)
    api_module.app.dependency_overrides[api_module.get_pipeline] = FailingPipeline
    try:
        with caplog.at_level(logging.ERROR, logger=api_module.__name__):
            response = asgi_request(
                api_module.app,
                "POST",
                "/ask",
                json={"question": "What is RAG?"},
            )
    finally:
        api_module.app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {"detail": "RAG pipeline failed."}
    record = next(
        item for item in caplog.records if item.message == "RAG pipeline failed."
    )
    assert record.exc_info is None
    assert record.error_type == "RuntimeError"
    assert "sk-sensitive" not in record.getMessage()
    assert "/Users/operator" not in record.getMessage()
