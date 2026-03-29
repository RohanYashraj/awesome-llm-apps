"""PDF export: Markdown → HTML → headless Chromium print PDF (Playwright).

Uses the same rendering path as “Print to PDF” in Chrome—typical for chat/document export UIs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from xml.sax.saxutils import escape

from bs4 import BeautifulSoup

_MD_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.nl2br",
    "markdown.extensions.sane_lists",
]

_PRINT_CSS = """
/* Letter size; non-zero @page margin so Chromium does not paint content flush to the sheet edge. */
@page {
  size: letter;
  margin: 0.75in;
}
html {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 11px;
  line-height: 1.5;
  color: #1a1a1a;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
body {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
h1 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #e0e0e0;
}
.meta {
  font-size: 10px;
  color: #666;
  margin: 0 0 16px 0;
}
h2.section {
  font-size: 11px;
  font-weight: 600;
  margin: 18px 0 8px 0;
  color: #222;
}
.question-block {
  font-size: 10px;
  line-height: 1.45;
  margin: 0 0 16px 0;
  padding: 10px 12px;
  background: #f6f7f9;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
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
  background: #f0f0f2;
  font-weight: 600;
}
.output-block a {
  color: #0b57d0;
  text-decoration: none;
}
.output-block hr {
  border: none;
  border-top: 1px solid #ccc;
  margin: 12px 0;
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
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{safe_title}</title>
<style>
{_PRINT_CSS}
</style>
</head>
<body>
<h1>{safe_title}</h1>
<p class="meta"><em>Generated {safe_meta}</em></p>
<h2 class="section">Your question</h2>
<div class="question-block">{question_html}</div>
<h2 class="section">Agent output</h2>
<div class="output-block">
{body_html}
</div>
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
                page.set_content(html_doc, wait_until="load")
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
