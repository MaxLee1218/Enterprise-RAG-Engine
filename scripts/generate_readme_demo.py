"""Generate the README demo animation from checked-in HTTP smoke evidence."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "supplier_quality_api_report.json"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "assets" / "demo.gif"
SOCIAL_PREVIEW_PATH = PROJECT_ROOT / "docs" / "assets" / "social-preview.png"
FONT_PATH = Path("/System/Library/Fonts/SFNSMono.ttf")
FALLBACK_FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (FONT_PATH, FALLBACK_FONT_PATH):
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _record(report: dict, trace_id: str) -> dict:
    return next(item for item in report["records"] if item["trace_id"] == trace_id)


def _lines(text: str, width: int) -> list[str]:
    return [line for paragraph in text.splitlines() for line in (wrap(paragraph, width) or [""])]


def _frame(*, title: str, query: str, answer: str, sources: list[str], status: str) -> Image.Image:
    image = Image.new("RGB", (1200, 680), "#07111f")
    draw = ImageDraw.Draw(image)
    heading = _font(36)
    body = _font(21)
    small = _font(17)

    draw.rounded_rectangle((38, 35, 1162, 645), radius=25, fill="#0d192b", outline="#334155", width=2)
    draw.ellipse((68, 61, 80, 73), fill="#fb7185")
    draw.ellipse((90, 61, 102, 73), fill="#fbbf24")
    draw.ellipse((112, 61, 124, 73), fill="#34d399")
    draw.text((150, 54), "Enterprise RAG Engine · verified demo", font=small, fill="#94a3b8")
    draw.text((70, 112), title, font=heading, fill="#f8fafc")
    draw.text((70, 173), "QUESTION", font=small, fill="#38bdf8")
    draw.rounded_rectangle((70, 202, 1130, 257), radius=12, fill="#07111f", outline="#1e3a52")
    draw.text((91, 218), query, font=body, fill="#e2e8f0")
    draw.text((70, 292), status, font=small, fill="#34d399")

    y = 327
    for line in _lines(answer, 84)[:8]:
        draw.text((70, y), line, font=body, fill="#e2e8f0")
        y += 31

    source_text = " · ".join(sources) if sources else "No sources returned"
    draw.line((70, 576, 1130, 576), fill="#26364b", width=2)
    draw.text((70, 598), f"EVIDENCE  {source_text}", font=small, fill="#a78bfa")
    return image


def _social_preview() -> Image.Image:
    image = Image.new("RGB", (1280, 640), "#07111f")
    draw = ImageDraw.Draw(image)
    title = _font(64)
    subtitle = _font(28)
    body = _font(20)
    small = _font(17)

    draw.ellipse((-140, 390, 310, 840), fill="#0b4764")
    draw.ellipse((1010, -170, 1450, 270), fill="#352766")
    draw.rounded_rectangle((54, 52, 1226, 588), radius=30, fill="#0d192b", outline="#334155", width=2)
    draw.text((96, 96), "TRACEABLE ENTERPRISE KNOWLEDGE", font=small, fill="#38bdf8")
    draw.text((92, 150), "Enterprise RAG Engine", font=title, fill="#f8fafc")
    draw.text((96, 238), "Answers with evidence, not just confidence.", font=subtitle, fill="#cbd5e1")
    draw.text((96, 315), "Hybrid retrieval", font=body, fill="#34d399")
    draw.text((330, 315), "Cross-Encoder reranking", font=body, fill="#a78bfa")
    draw.text((685, 315), "Grounded sources", font=body, fill="#38bdf8")
    draw.text((96, 405), "696", font=title, fill="#f8fafc")
    draw.text((96, 478), "offline tests", font=small, fill="#94a3b8")
    draw.text((350, 405), "18/18", font=title, fill="#f8fafc")
    draw.text((350, 478), "retrieval gates", font=small, fill="#94a3b8")
    draw.text((655, 405), "14/14", font=title, fill="#f8fafc")
    draw.text((655, 478), "HTTP scenarios", font=small, fill="#94a3b8")
    draw.text((972, 420), "FastAPI  ·  Chroma", font=body, fill="#cbd5e1")
    draw.text((972, 458), "BM25  ·  RAGAS", font=body, fill="#cbd5e1")
    draw.text((972, 510), "github.com/MaxLee1218", font=small, fill="#64748b")
    return image


def main() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    grounded = _record(report, "supplier-quality-api-005")
    abstention = _record(report, "supplier-quality-api-013")
    grounded_answer = grounded["answer"].split("\n\n来源：", 1)[0]

    frames = [
        _frame(
            title="01 · Retrieve",
            query=grounded["query"],
            answer="Dense and BM25 candidates are normalized, fused, and reranked.",
            sources=["KPI-SQ-002", "QP-SQ-012", "SQM-001"],
            status="HYBRID RETRIEVAL → CROSS-ENCODER",
        ),
        _frame(
            title="02 · Ground",
            query=grounded["query"],
            answer=grounded_answer,
            sources=grounded["source_document_ids"],
            status="ANSWER GROUNDED IN RETRIEVED CONTEXT",
        ),
        _frame(
            title="03 · Abstain when evidence is missing",
            query=abstention["query"],
            answer=abstention["answer"],
            sources=[],
            status="CONTROLLED NO-EVIDENCE BEHAVIOR",
        ),
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=[1700, 2600, 2200],
        loop=0,
        optimize=True,
    )
    _social_preview().save(SOCIAL_PREVIEW_PATH, optimize=True)
    print(f"wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {SOCIAL_PREVIEW_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
