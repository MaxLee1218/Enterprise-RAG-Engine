from __future__ import annotations

from tests.asgi_client import asgi_request


def test_demo_is_read_only_client_for_ask_contract() -> None:
    from app.api import app

    response = asgi_request(app, "GET", "/demo")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "Enterprise RAG Engine · Demo" in response.text
    assert "fetch('/ask'" in response.text
    assert "No documents are uploaded or modified" in response.text


def test_demo_is_excluded_from_openapi_contract() -> None:
    from app.api import app

    schema = app.openapi()

    assert "/demo" not in schema["paths"]
    assert "/ask" in schema["paths"]
    assert "/health" in schema["paths"]
