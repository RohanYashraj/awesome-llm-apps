"""PDF export: Markdown → HTML → headless Chromium print PDF (Playwright).

Uses the same rendering path as “Print to PDF” in Chrome—typical for chat/document export UIs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from xml.sax.saxutils import escape

from bs4 import BeautifulSoup

MAESTROSAI_URL = "https://maestrosai.in"
MAESTROSAI_DOMAIN = "maestrosai.in"

_MD_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.nl2br",
    "markdown.extensions.sane_lists",
    "markdown.extensions.tables",
]

# Match Streamlit / maestrosai.in look; fonts loaded in HTML <head> for Chromium print.
_PRINT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700&display=swap');

/* Letter size; non-zero @page margin so Chromium does not paint content flush to the sheet edge. */
@page {
  size: letter;
  margin: 0.75in;
}
html {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  font-size: 11px;
  line-height: 1.5;
  color: #0f172a;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
body {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* —— MaestrosAI brand header —— */
.pdf-brand {
  margin: 0 0 18px 0;
  padding: 14px 16px;
  border-radius: 10px;
  background: linear-gradient(125deg, #e0f2fe 0%, #f0fdfa 45%, #fffbeb 100%);
  border: 1px solid rgba(13, 148, 136, 0.2);
  border-left: 4px solid #0d9488;
}
.pdf-brand-row {
  display: table;
  width: 100%;
  margin-bottom: 10px;
}
.pdf-brand-mark {
  display: table-cell;
  vertical-align: middle;
  width: 40px;
}
.pdf-brand-mark-inner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(145deg, #14b8a6 0%, #0f766e 100%);
  color: #fff;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 10px;
  text-align: center;
  line-height: 36px;
  letter-spacing: -0.02em;
}
.pdf-brand-text {
  display: table-cell;
  vertical-align: middle;
  padding-left: 10px;
}
.pdf-brand-name {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.14em;
  color: #0f172a;
  text-transform: uppercase;
}
.pdf-brand-tag {
  font-size: 8px;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #64748b;
  margin-top: 2px;
}
.pdf-badge {
  display: inline-block;
  font-size: 7px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 999px;
  background: linear-gradient(90deg, #7c3aed 0%, #db2777 100%);
  color: #fff;
  margin-bottom: 8px;
}
.pdf-doc-title {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
  margin: 0 0 6px 0;
  letter-spacing: -0.02em;
}
.meta {
  font-size: 9px;
  color: #64748b;
  margin: 0;
}
.meta a {
  color: #0f766e;
  text-decoration: none;
  font-weight: 600;
}

h2.section {
  font-family: 'Inter', sans-serif;
  font-size: 10px;
  font-weight: 700;
  margin: 18px 0 8px 0;
  color: #0f766e;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.question-block {
  font-size: 10px;
  line-height: 1.45;
  margin: 0 0 16px 0;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid rgba(13, 148, 136, 0.25);
  border-left: 3px solid #14b8a6;
  white-space: pre-wrap;
  word-wrap: break-word;
}
.output-block {
  margin: 0;
  font-size: 11px;
}
.output-block h1 { font-size: 16px; border: none; padding: 0; }
.output-block h2 { font-size: 14px; margin-top: 14px; }
.output-block h3 { font-size: 13px; margin-top: 12px; }
.output-block h4, .output-block h5, .output-block h6 { font-size: 12px; margin-top: 10px; }
.output-block p { margin: 6px 0; }
.output-block ul, .output-block ol {
  margin: 6px 0 10px 0;
  padding-left: 22px;
}
.output-block li { margin: 4px 0; }
.output-block li > p { margin: 0.2em 0; }
.output-block pre {
  font-family: ui-monospace, "Cascadia Code", "SF Mono", Menlo, Consolas, monospace;
  font-size: 10px;
  line-height: 1.35;
  background: #f4f4f5;
  border: 1px solid #e5e5e7;
  border-radius: 4px;
  padding: 10px 12px;
  margin: 8px 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
.output-block code {
  font-family: ui-monospace, "Cascadia Code", "SF Mono", Menlo, Consolas, monospace;
  font-size: 10px;
  background: #f0f0f2;
  padding: 2px 5px;
  border-radius: 3px;
}
.output-block pre code {
  background: transparent;
  padding: 0;
  border: none;
}
.output-block blockquote {
  margin: 8px 0;
  padding-left: 12px;
  border-left: 3px solid #d0d0d4;
  color: #444;
}
.output-block table {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 10px;
}
.output-block th, .output-block td {
  border: 1px solid #ddd;
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}
.output-block th {
  background: #ecfdf5;
  font-weight: 600;
  color: #0f172a;
  border-color: #99f6e4;
}
.output-block a {
  color: #0f766e;
  text-decoration: none;
  font-weight: 500;
}
.pdf-footer {
  margin-top: 28px;
  padding-top: 14px;
  border-top: 1px solid rgba(15, 23, 42, 0.12);
  font-size: 9px;
  color: #64748b;
  line-height: 1.5;
}
.pdf-footer-brand {
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.04em;
}
.pdf-footer a {
  color: #0f766e;
  text-decoration: none;
  font-weight: 600;
}
.output-block hr {
  border: none;
  border-top: 1px solid #ccc;
  margin: 16px 0;
  page-break-after: avoid;
}
.output-block table {
  page-break-inside: avoid;
}
.output-block h2, .output-block h3 {
  page-break-after: avoid;
}
.output-block li {
  page-break-inside: avoid;
}
.output-block pre {
  page-break-inside: avoid;
}
.output-block strong {
  color: #0f172a;
}
"""


def _truncate(s: str, limit: int) -> str:
    s = s.strip()
    if len(s) <= limit:
        return s
    return s[: limit - 25] + "\n… [truncated] …"


def _markdown_to_html(md: str) -> str:
    import markdown

    return markdown.markdown(md or "", extensions=_MD_EXTENSIONS)


def _strip_colon_only_paragraphs(html: str) -> str:
    """
    Python-Markdown + sane_lists can emit <p>:</p> under list items (definition-style).
    Remove those so the PDF does not show a lone colon line.
    """
    wrapped = f'<div class="md-sanitize-root">{html}</div>'
    soup = BeautifulSoup(wrapped, "html.parser")
    root = soup.find("div", class_="md-sanitize-root")
    if root is None:
        return html
    for p in list(root.find_all("p")):
        if p.get_text(strip=True) == ":":
            p.decompose()
    return root.decode_contents()


def _question_to_safe_html(query: str) -> str:
    """Plain-text question: escape and preserve line breaks."""
    t = _truncate(query, 20000)
    return escape(t).replace("\n", "<br/>\n")


def _build_html_document(
    *,
    title: str,
    meta_ts: str,
    question_html: str,
    body_html: str,
) -> str:
    safe_title = escape(title)
    safe_meta = escape(meta_ts)
    safe_url = escape(MAESTROSAI_URL)
    safe_domain = escape(MAESTROSAI_DOMAIN)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{safe_title} · MAESTROSAI</title>
<style>
{_PRINT_CSS}
</style>
</head>
<body>
<header class="pdf-brand">
  <div class="pdf-badge">Actuarial suite · Powered by Gemini</div>
  <div class="pdf-brand-row">
    <div class="pdf-brand-mark"><div class="pdf-brand-mark-inner">AI</div></div>
    <div class="pdf-brand-text">
      <div class="pdf-brand-name">MAESTROSAI</div>
      <div class="pdf-brand-tag">Insurance AI systems</div>
    </div>
  </div>
  <div class="pdf-doc-title">{safe_title}</div>
  <p class="meta"><em>Generated {safe_meta}</em> · <a href="{safe_url}">{safe_domain}</a></p>
</header>
<h2 class="section">Your question</h2>
<div class="question-block">{question_html}</div>
<h2 class="section">Agent output</h2>
<div class="output-block">
{body_html}
</div>
<footer class="pdf-footer">
  <span class="pdf-footer-brand">MAESTROSAI</span> — Insurance AI systems ·
  <a href="{safe_url}">{safe_domain}</a><br/>
  Draft decision support only. Not professional actuarial advice, legal advice, or filing-ready output.
</footer>
</body>
</html>
"""


def build_run_pdf_bytes(
    *,
    title: str,
    query: str,
    output_text: str,
) -> bytes:
    """
    Build a PDF with rendered Markdown for the agent answer only (no activity log).

    Uses Playwright + Chromium ``page.pdf()`` (same engine as Chrome print-to-PDF).
    One-time setup: ``uv run playwright install chromium``
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "PDF export requires the 'playwright' package. Run: uv sync"
        ) from e

    md_src = _truncate(output_text or "", 50000)
    raw_html = _markdown_to_html(md_src)
    body_html = _strip_colon_only_paragraphs(raw_html)
    question_html = _question_to_safe_html(query)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html_doc = _build_html_document(
        title=title,
        meta_ts=ts,
        question_html=question_html,
        body_html=body_html,
    )

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_content(html_doc, wait_until="networkidle")
                # Use CSS @page margins (see _PRINT_CSS). API margins + @page margin:0 previously
                # produced edge-to-edge content in headless Chromium; prefer_css_page_size honors @page.
                pdf_bytes = page.pdf(
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
    except Exception as e:
        err = str(e).lower()
        if "executable doesn't exist" in err or "browserType.launch" in err or "chromium" in err:
            raise RuntimeError(
                "Chromium is not installed for Playwright. Run:\n"
                "  cd actuarial_agents_suite && uv run playwright install chromium\n"
                "See README.md (PDF export)."
            ) from e
        raise RuntimeError(
            f"PDF export failed (Chromium print). {e!s}"
        ) from e

    return pdf_bytes if isinstance(pdf_bytes, (bytes, bytearray)) else bytes(pdf_bytes)
