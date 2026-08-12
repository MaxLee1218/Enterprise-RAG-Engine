import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List

from docx import Document
from pypdf import PdfReader


def _clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()
    return text


def _load_txt(file_path: Path) -> str:
    try:
        text = file_path.read_text(encoding="utf-8")
        return _clean_text(text)
    except UnicodeDecodeError as e:
        raise ValueError(f"failed to decode document as UTF-8: {file_path}") from e
    except Exception as e:
        print(f"[Loader Warning] Failed to load {file_path}: {e}")
        return ""


def _load_docx(file_path: Path) -> str:
    try:
        document = Document(file_path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        text = "\n".join(paragraphs)
        return _clean_text(text)
    except Exception as e:
        print(f"[Loader Warning] Failed to load {file_path}: {e}")
        return ""


def _load_pdf(file_path: Path) -> str:
    try:
        reader = PdfReader(file_path)
        page_texts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text is None or page_text.strip() == "":
                continue
            page_texts.append(page_text.strip())

        text = "\n".join(page_texts)
        return _clean_text(text)
    except Exception as e:
        print(f"[Loader Warning] Failed to load {file_path}: {e}")
        return ""


LOADERS: dict[str, Callable[[Path], str]] = {
    ".pdf": _load_pdf,
    ".txt": _load_txt,
    ".md": _load_txt,
    ".docx": _load_docx,
}

MANIFEST_FILENAME = "manifest.json"
MANIFEST_SEARCH_DEPTH = 3
MANIFEST_METADATA_FIELDS = (
    "document_id",
    "title",
    "document_type",
    "version",
    "effective_date",
    "owner",
    "approved_by",
    "classification",
    "business_function",
    "language",
    "source_system",
    "status",
)


def _relative_source(file_path: Path, base_path: Path | None) -> str:
    if base_path is None:
        return str(file_path)

    try:
        return file_path.relative_to(base_path).as_posix()
    except ValueError:
        return file_path.name


def load_document_file(
    file_path: str | Path,
    base_path: str | Path | None = None,
) -> Dict[str, object]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"document file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"document path must be a file: {path}")

    loader = LOADERS.get(path.suffix.lower())
    if loader is None:
        raise ValueError(f"unsupported document extension: {path.suffix}")

    resolved_base = Path(base_path) if base_path is not None else None
    text = loader(path)
    if not text.strip():
        raise ValueError(f"document is empty: {path}")

    relative_path = _relative_source(path, resolved_base)
    metadata: dict[str, Any] = {
        "source": relative_path,
        "filename": path.name,
        "relative_path": relative_path,
    }
    metadata.update(_load_manifest_metadata(path))
    return {
        "text": text,
        "metadata": metadata,
    }


def _load_manifest_metadata(file_path: Path) -> dict[str, Any]:
    """Load additive document metadata from the nearest corpus manifest."""
    for manifest_path in _manifest_candidates(file_path):
        if not manifest_path.is_file():
            continue
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid document manifest: {manifest_path}") from error
        if not isinstance(payload, dict):
            raise ValueError(f"document manifest must contain an object: {manifest_path}")
        documents = payload.get("documents")
        if not isinstance(documents, list):
            raise ValueError(
                f"document manifest must contain a documents list: {manifest_path}"
            )
        matched = _match_manifest_document(file_path, manifest_path.parent, documents)
        if matched is None:
            continue
        metadata: dict[str, Any] = {}
        for field in MANIFEST_METADATA_FIELDS:
            value = matched.get(field)
            if isinstance(value, (str, int, float, bool)) and not (
                isinstance(value, str) and not value.strip()
            ):
                metadata[field] = value
        return metadata
    return {}


def _manifest_candidates(file_path: Path) -> list[Path]:
    candidates: list[Path] = []
    current = file_path.parent
    for _ in range(MANIFEST_SEARCH_DEPTH):
        candidates.append(current / MANIFEST_FILENAME)
        if current.parent == current:
            break
        current = current.parent
    return candidates


def _match_manifest_document(
    file_path: Path,
    manifest_root: Path,
    documents: list[Any],
) -> dict[str, Any] | None:
    resolved_file = file_path.resolve()
    for item in documents:
        if not isinstance(item, dict):
            continue
        pdf_file = item.get("pdf_file")
        if isinstance(pdf_file, str) and pdf_file.strip():
            if (manifest_root / pdf_file).resolve() == resolved_file:
                return item
        filename = item.get("filename")
        if isinstance(filename, str) and filename == file_path.name:
            return item
    return None


def load_documents(folder_path: str = "data/raw") -> List[Dict[str, str]]:
    base_path = Path(folder_path)
    if not base_path.exists():
        return []

    documents = []

    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in LOADERS:
            continue

        try:
            document = load_document_file(file_path, base_path=base_path)
        except ValueError:
            continue

        documents.append(
            {
                "text": str(document["text"]),
                "source": str(document["metadata"]["source"]),
            }
        )

    return documents
