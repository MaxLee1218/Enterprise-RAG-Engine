from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_has_frozen_runtime_contract() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.11-slim AS builder" in dockerfile
    assert "FROM python:3.11-slim AS runtime" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "EXPOSE 8000" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "http://127.0.0.1:8000/health" in dockerfile
    assert "--reload" not in dockerfile
    assert "COPY . " not in dockerfile
    assert "COPY .\n" not in dockerfile

    command_line = next(
        line for line in dockerfile.splitlines() if line.startswith("CMD [")
    )
    command = json.loads(command_line.removeprefix("CMD "))
    assert command == [
        "uvicorn",
        "app.api:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]


def test_docker_context_excludes_secrets_and_runtime_data() -> None:
    ignored = {
        line.strip()
        for line in (PROJECT_ROOT / ".dockerignore")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert {".git", ".venv", ".env", "data", "models", "logs", "reports"} <= ignored
    assert "enterprise-documents" in ignored
    assert "tests" in ignored


def test_runtime_dependency_set_excludes_development_and_evaluation_tools() -> None:
    requirements = (PROJECT_ROOT / "requirements-runtime.txt").read_text(
        encoding="utf-8"
    )

    assert "fastapi==" in requirements
    assert "sentence-transformers==" in requirements
    assert "chromadb==" in requirements
    assert "pytest" not in requirements
    assert "ragas" not in requirements
    assert "streamlit" not in requirements
