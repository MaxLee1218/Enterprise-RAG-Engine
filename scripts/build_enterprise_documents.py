from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = PROJECT_ROOT / "enterprise-documents"
DEFAULT_MANIFEST = CORPUS_ROOT / "manifest.json"
DEFAULT_POLICY_RULES = CORPUS_ROOT / "policy_rules.json"

REQUIRED_CROSS_REFERENCES = {
    "SQM-001": ("KPI-SQ-002", "POL-SQ-007", "QP-SQ-012"),
    "QP-INSP-004": ("KPI-SQ-002", "QP-SQ-012"),
    "POL-SQ-007": ("SQM-001", "QP-SQ-012"),
    "KPI-SQ-002": ("SQM-001", "QP-INSP-004"),
    "QP-SQ-012": ("KPI-SQ-002", "POL-SQ-007"),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build controlled synthetic Supplier Quality PDFs from Markdown."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--policy-rules", type=Path, default=DEFAULT_POLICY_RULES)
    return parser.parse_args(argv)


def build_corpus(manifest_path: Path, policy_path: Path) -> dict[str, Any]:
    manifest = _read_object(manifest_path, "manifest")
    rules = _read_object(policy_path, "policy rules")
    documents = manifest.get("documents")
    if not isinstance(documents, list) or len(documents) != 5:
        raise ValueError("manifest must contain exactly five documents")

    _validate_policy_rules(rules)
    _validate_manifest_documents(documents)
    for document in documents:
        source_path = manifest_path.parent / _required_text(document, "source_file")
        source_text = source_path.read_text(encoding="utf-8")
        _validate_source(document, source_text, rules)
        pdf_path = manifest_path.parent / _required_text(document, "pdf_file")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        _render_pdf(document, source_text, pdf_path)
        document["sha256"] = _sha256(pdf_path)
        document["page_count"] = _pdf_page_count(pdf_path)
        document["chunk_count"] = None
        document["ingestion_status"] = "not_indexed"

    manifest["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest["policy_rules_sha256"] = _sha256(policy_path)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read valid {label}: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return payload


def _validate_policy_rules(rules: dict[str, Any]) -> None:
    rate = rules.get("defect_rate") or {}
    if rate.get("numerator") != "SUM(rejected_quantity)":
        raise ValueError("policy numerator must be SUM(rejected_quantity)")
    if rate.get("denominator") != "SUM(total_quantity)":
        raise ValueError("policy denominator must be SUM(total_quantity)")
    classification = rules.get("classification") or {}
    acceptable = classification.get("acceptable") or {}
    review = classification.get("review_required") or {}
    corrective = classification.get("corrective_action_required") or {}
    if acceptable.get("max_exclusive") != 0.02:
        raise ValueError("acceptable maximum must be exclusive 2 percent")
    if review.get("min_inclusive") != 0.02 or review.get("max_inclusive") != 0.05:
        raise ValueError("review range must include 2 through 5 percent")
    if corrective.get("min_exclusive") != 0.05:
        raise ValueError("corrective action threshold must be above 5 percent")
    consecutive = rules.get("consecutive_quarter_management_review") or {}
    if consecutive.get("threshold_min_inclusive") != 0.02:
        raise ValueError("consecutive-quarter threshold must include 2 percent")
    if consecutive.get("consecutive_periods") != 2:
        raise ValueError("management review must require two consecutive periods")
    if (rules.get("major_deviation") or {}).get("escalation_required") is not True:
        raise ValueError("major deviation escalation must be required")


def _validate_manifest_documents(documents: list[Any]) -> None:
    required_fields = (
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
        "source_file",
        "pdf_file",
        "filename",
    )
    ids: set[str] = set()
    filenames: set[str] = set()
    for item in documents:
        if not isinstance(item, dict):
            raise ValueError("each manifest document must be an object")
        for field in required_fields:
            _required_text(item, field)
        document_id = item["document_id"]
        filename = item["filename"]
        if document_id in ids:
            raise ValueError(f"duplicate document_id: {document_id}")
        if filename in filenames:
            raise ValueError(f"duplicate filename: {filename}")
        if item["status"] != "active":
            raise ValueError(f"document must be active: {document_id}")
        ids.add(document_id)
        filenames.add(filename)


def _validate_source(
    document: dict[str, Any], source: str, rules: dict[str, Any]
) -> None:
    document_id = _required_text(document, "document_id")
    required_values = (
        _required_text(document, "title"),
        document_id,
        _required_text(document, "version"),
        _required_text(document, "effective_date"),
        _required_text(document, "owner"),
        _required_text(document, "approved_by"),
        _required_text(document, "classification"),
    )
    for value in required_values:
        if value not in source:
            raise ValueError(f"{document_id} source is missing required value: {value}")
    for section_name in (
        "Purpose",
        "Scope",
        "Definitions",
        "Roles and Responsibilities",
        "Exceptions",
        "Records and Evidence",
        "Related Documents",
        "Revision History",
    ):
        if not re.search(rf"^##\s+\d+\.\s+.*{re.escape(section_name)}", source, re.MULTILINE):
            raise ValueError(
                f"{document_id} source is missing required section: {section_name}"
            )
    for reference in REQUIRED_CROSS_REFERENCES[document_id]:
        if reference not in source:
            raise ValueError(f"{document_id} source is missing cross-reference {reference}")
    if "| ---" not in source:
        raise ValueError(f"{document_id} source must contain a table")

    if document_id in {"SQM-001", "KPI-SQ-002", "QP-SQ-012"}:
        for phrase in (
            "1.99% is Acceptable",
            "2.00% is Review Required",
            "5.00% is Review Required",
            "5.01% is Corrective Action Required",
        ):
            if phrase not in source:
                raise ValueError(f"{document_id} source is missing boundary: {phrase}")
    if document_id in {"SQM-001", "QP-INSP-004", "KPI-SQ-002"}:
        for phrase in (
            (rules.get("defect_rate") or {}).get("numerator"),
            (rules.get("defect_rate") or {}).get("denominator"),
        ):
            if not isinstance(phrase, str) or phrase not in source:
                raise ValueError(f"{document_id} source is missing KPI phrase: {phrase}")


def _render_pdf(document: dict[str, Any], markdown: str, output_path: Path) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as error:
        raise RuntimeError("reportlab is required to build enterprise PDFs") from error

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocumentTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            textColor=colors.HexColor("#17365D"),
            alignment=TA_CENTER,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ControlNotice",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#8A1C1C"),
            alignment=TA_CENTER,
            spaceBefore=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#17365D"),
            spaceBefore=11,
            spaceAfter=6,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubsectionHeading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=colors.HexColor("#2F5597"),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ControlledBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.5,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ListBody",
            parent=styles["ControlledBody"],
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=3,
        )
    )
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.62 * inch,
        leftMargin=0.62 * inch,
        topMargin=0.68 * inch,
        bottomMargin=0.65 * inch,
        title=_required_text(document, "title"),
        author=_required_text(document, "owner"),
        subject=f"Controlled synthetic Supplier Quality document {_required_text(document, 'document_id')}",
    )
    story: list[Any] = [
        Spacer(1, 0.65 * inch),
        Paragraph(_escape(_required_text(document, "title")), styles["DocumentTitle"]),
        Paragraph(
            f"{_escape(_required_text(document, 'document_id'))} | Version {_escape(_required_text(document, 'version'))}",
            styles["Heading2"],
        ),
        Spacer(1, 0.2 * inch),
        _control_table(document, styles, colors, Table, TableStyle, Paragraph),
        Paragraph("INTERNAL CONTROLLED DOCUMENT", styles["ControlNotice"]),
        Paragraph(
            "Synthetic enterprise document for RAG verification. No real company confidential information.",
            styles["ControlNotice"],
        ),
        PageBreak(),
    ]
    story.extend(
        _markdown_flowables(
            markdown,
            styles=styles,
            colors=colors,
            Paragraph=Paragraph,
            Spacer=Spacer,
            Table=Table,
            TableStyle=TableStyle,
        )
    )
    doc.build(story, canvasmaker=_numbered_canvas(document))


def _control_table(document: dict[str, Any], styles: Any, colors: Any, Table: Any, TableStyle: Any, Paragraph: Any) -> Any:
    rows = [
        ("Document ID", document["document_id"]),
        ("Document Type", document["document_type"]),
        ("Version", document["version"]),
        ("Effective Date", document["effective_date"]),
        ("Document Owner", document["owner"]),
        ("Approved By", document["approved_by"]),
        ("Classification", document["classification"]),
        ("Business Function", document["business_function"]),
        ("Status", document["status"]),
    ]
    data = [
        [
            Paragraph(f"<b>{_escape(label)}</b>", styles["ControlledBody"]),
            Paragraph(_escape(str(value)), styles["ControlledBody"]),
        ]
        for label, value in rows
    ]
    table = Table(data, colWidths=[130, 310], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9EADBA")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#D9EAF7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _markdown_flowables(markdown: str, **parts: Any) -> list[Any]:
    styles = parts["styles"]
    Paragraph = parts["Paragraph"]
    Spacer = parts["Spacer"]
    Table = parts["Table"]
    TableStyle = parts["TableStyle"]
    colors = parts["colors"]
    lines = markdown.splitlines()
    flowables: list[Any] = []
    index = 0
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines).strip()
            if text:
                flowables.append(Paragraph(_inline(text), styles["ControlledBody"]))
            paragraph_lines.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        if not line.strip():
            flush_paragraph()
            index += 1
            continue
        if line.startswith("# "):
            flush_paragraph()
            index += 1
            continue
        if line.startswith("## "):
            flush_paragraph()
            flowables.append(Paragraph(_inline(line[3:]), styles["SectionHeading"]))
            index += 1
            continue
        if line.startswith("### "):
            flush_paragraph()
            flowables.append(Paragraph(_inline(line[4:]), styles["SubsectionHeading"]))
            index += 1
            continue
        if line.startswith("|"):
            flush_paragraph()
            table_lines: list[str] = []
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            rows = _parse_markdown_table(table_lines)
            if rows:
                cell_rows = [
                    [Paragraph(_inline(cell), styles["ControlledBody"]) for cell in row]
                    for row in rows
                ]
                column_count = len(cell_rows[0])
                available = 520
                table = Table(
                    cell_rows,
                    colWidths=[available / column_count] * column_count,
                    repeatRows=1,
                    hAlign="LEFT",
                )
                table.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AAB7C2")),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 4),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )
                flowables.extend([table, Spacer(1, 7)])
            continue
        if re.match(r"^(?:[-*]|\d+\.)\s+", line):
            flush_paragraph()
            match = re.match(r"^([-*]|\d+\.)\s+(.*)$", line)
            assert match is not None
            marker = "-" if match.group(1) in {"-", "*"} else match.group(1)
            flowables.append(
                Paragraph(f"{_escape(marker)} {_inline(match.group(2))}", styles["ListBody"])
            )
            index += 1
            continue
        paragraph_lines.append(line)
        index += 1
    flush_paragraph()
    return flowables


def _parse_markdown_table(lines: list[str]) -> list[list[str]]:
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in lines]
    if len(rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]):
        rows.pop(1)
    if not rows:
        return []
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("Markdown table rows must have equal column counts")
    return rows


def _numbered_canvas(document: dict[str, Any]) -> Any:
    from reportlab.pdfgen import canvas

    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._saved_pages: list[dict[str, Any]] = []
            self.setTitle(_required_text(document, "title"))
            self.setAuthor(_required_text(document, "owner"))
            self.setSubject(f"Synthetic controlled document {document['document_id']}")
            self.setKeywords("Supplier Quality, synthetic enterprise knowledge, controlled document")

        def showPage(self) -> None:
            self._saved_pages.append(dict(self.__dict__))
            self._startPage()

        def save(self) -> None:
            page_count = len(self._saved_pages)
            for page_number, state in enumerate(self._saved_pages, start=1):
                self.__dict__.update(state)
                self.setFont("Helvetica", 7.5)
                self.setFillColorRGB(0.25, 0.25, 0.25)
                self.drawString(45, 25, f"{document['document_id']} | Version {document['version']} | Internal")
                self.drawRightString(567, 25, f"Page {page_number} of {page_count}")
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

    return NumberedCanvas


def _required_text(item: dict[str, Any], field: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"manifest field {field} must be a non-blank string")
    return value.strip()


def _inline(value: str) -> str:
    escaped = _escape(value)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    return escaped


def _escape(value: str) -> str:
    return html.escape(value, quote=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pdf_page_count(path: Path) -> int:
    from pypdf import PdfReader

    return len(PdfReader(path).pages)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = build_corpus(args.manifest, args.policy_rules)
    except Exception as error:
        print(f"Document build failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(f"Built documents: {len(manifest['documents'])}")
    for document in manifest["documents"]:
        print(
            f"{document['document_id']} | {document['filename']} | "
            f"pages={document['page_count']} | sha256={document['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
