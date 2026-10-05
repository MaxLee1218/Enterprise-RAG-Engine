from __future__ import annotations

from fastapi.responses import HTMLResponse


DEMO_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Read-only demo client for Enterprise RAG Engine">
  <title>Enterprise RAG Engine · Demo</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #07111f;
      --panel: rgba(15, 28, 47, .82);
      --line: rgba(148, 163, 184, .2);
      --text: #f8fafc;
      --muted: #94a3b8;
      --cyan: #38bdf8;
      --green: #34d399;
      --violet: #a78bfa;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 15% 15%, rgba(56, 189, 248, .13), transparent 34rem),
        radial-gradient(circle at 85% 5%, rgba(167, 139, 250, .13), transparent 30rem),
        var(--bg);
    }
    main { width: min(1080px, calc(100% - 32px)); margin: 0 auto; padding: 64px 0; }
    .eyebrow { color: var(--cyan); font-size: 13px; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
    h1 { max-width: 790px; margin: 14px 0 12px; font-size: clamp(38px, 7vw, 72px); line-height: .98; letter-spacing: -.055em; }
    .lead { max-width: 680px; color: #cbd5e1; font-size: 18px; line-height: 1.65; }
    .badges { display: flex; flex-wrap: wrap; gap: 9px; margin: 24px 0 36px; }
    .badge { padding: 8px 11px; border: 1px solid var(--line); border-radius: 999px; color: #cbd5e1; background: rgba(15, 23, 42, .65); font-size: 13px; }
    .workspace { display: grid; grid-template-columns: 1.05fr .95fr; overflow: hidden; border: 1px solid var(--line); border-radius: 22px; background: var(--panel); box-shadow: 0 30px 100px rgba(0, 0, 0, .35); backdrop-filter: blur(18px); }
    .ask, .evidence { padding: 28px; }
    .evidence { border-left: 1px solid var(--line); background: rgba(2, 8, 23, .25); }
    label, h2 { display: block; margin: 0 0 12px; font-size: 13px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
    textarea { width: 100%; min-height: 118px; resize: vertical; border: 1px solid var(--line); border-radius: 14px; padding: 15px; color: var(--text); background: rgba(2, 8, 23, .72); font: inherit; line-height: 1.5; outline: none; }
    textarea:focus { border-color: var(--cyan); box-shadow: 0 0 0 3px rgba(56, 189, 248, .12); }
    button { margin-top: 13px; border: 0; border-radius: 12px; padding: 12px 18px; color: #03111c; background: linear-gradient(135deg, var(--cyan), var(--green)); font-weight: 850; cursor: pointer; }
    button:disabled { cursor: wait; opacity: .6; }
    .answer { min-height: 164px; margin-top: 24px; padding: 18px; border: 1px solid var(--line); border-radius: 14px; background: rgba(2, 8, 23, .48); white-space: pre-wrap; line-height: 1.65; }
    .meta { display: flex; gap: 16px; min-height: 24px; margin-top: 12px; color: var(--muted); font-size: 12px; }
    .source { margin-bottom: 12px; padding: 14px; border: 1px solid var(--line); border-radius: 12px; background: rgba(15, 23, 42, .62); }
    .source strong { display: block; color: var(--green); font-size: 13px; }
    .source p { margin: 8px 0 0; color: #cbd5e1; font-size: 13px; line-height: 1.5; }
    .empty { color: var(--muted); line-height: 1.6; }
    footer { margin-top: 18px; color: var(--muted); font-size: 12px; }
    a { color: var(--cyan); }
    @media (max-width: 760px) { .workspace { grid-template-columns: 1fr; } .evidence { border-top: 1px solid var(--line); border-left: 0; } main { padding: 36px 0; } }
  </style>
</head>
<body>
  <main>
    <div class="eyebrow">Traceable enterprise knowledge</div>
    <h1>Answers with evidence,<br>not just confidence.</h1>
    <p class="lead">A read-only client for the repository's <code>POST /ask</code> contract. The API returns the answer, retrieved contexts, provenance metadata, latency, and a request trace ID.</p>
    <div class="badges">
      <span class="badge">Hybrid retrieval</span><span class="badge">Cross-Encoder reranking</span><span class="badge">Grounded sources</span><span class="badge">Explicit abstention</span>
    </div>
    <section class="workspace">
      <div class="ask">
        <label for="question">Ask the knowledge base</label>
        <textarea id="question">How is supplier defect rate calculated?</textarea>
        <button id="submit" type="button">Retrieve grounded answer</button>
        <div id="answer" class="answer">Run the configured API and ask a question. No documents are uploaded or modified by this page.</div>
        <div class="meta"><span id="latency"></span><span id="trace"></span></div>
      </div>
      <aside class="evidence">
        <h2>Retrieved evidence</h2>
        <div id="sources" class="empty">Sources returned by the API will appear here with their document and chunk metadata.</div>
      </aside>
    </section>
    <footer>This demo is intentionally read-only. Ingestion remains an explicit offline operation.</footer>
  </main>
  <script>
    const question = document.getElementById('question');
    const submit = document.getElementById('submit');
    const answer = document.getElementById('answer');
    const sources = document.getElementById('sources');
    const latency = document.getElementById('latency');
    const trace = document.getElementById('trace');

    function renderSources(items) {
      sources.replaceChildren();
      if (!items.length) {
        sources.className = 'empty';
        sources.textContent = 'No sources were returned.';
        return;
      }
      sources.className = '';
      items.forEach((item, position) => {
        const card = document.createElement('div');
        card.className = 'source';
        const title = document.createElement('strong');
        title.textContent = `[${item.index || position + 1}] ${item.source || 'Unknown source'}`;
        const preview = document.createElement('p');
        preview.textContent = item.text_preview || 'Provenance metadata returned without a text preview.';
        card.append(title, preview);
        sources.append(card);
      });
    }

    async function ask() {
      const value = question.value.trim();
      if (!value) { answer.textContent = 'Enter a non-empty question.'; return; }
      submit.disabled = true;
      answer.textContent = 'Retrieving and grounding…';
      sources.className = 'empty';
      sources.textContent = 'Waiting for retrieved evidence…';
      latency.textContent = '';
      trace.textContent = '';
      try {
        const response = await fetch('/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: value })
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
        answer.textContent = payload.answer;
        renderSources(payload.sources || []);
        latency.textContent = `${Math.round(payload.latency_ms)} ms`;
        trace.textContent = `trace ${payload.rag_trace_id}`;
      } catch (error) {
        answer.textContent = error instanceof Error ? error.message : 'Request failed.';
        sources.textContent = 'No evidence available.';
      } finally {
        submit.disabled = false;
      }
    }

    submit.addEventListener('click', ask);
    question.addEventListener('keydown', event => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') ask();
    });
  </script>
</body>
</html>
"""


def demo_page() -> HTMLResponse:
    return HTMLResponse(
        DEMO_PAGE,
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; style-src 'unsafe-inline'; "
                "script-src 'unsafe-inline'; connect-src 'self'; "
                "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'"
            ),
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )
