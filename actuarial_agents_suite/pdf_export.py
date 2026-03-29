"""PDF export: Markdown agent output rendered as structured ReportLab flowables."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from bs4 import BeautifulSoup, NavigableString, Tag
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_MD_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.nl2br",
    "markdown.extensions.sane_lists",
]


def _markdown_to_html(md: str) -> str:
    import markdown

    return markdown.markdown(md or "", extensions=_MD_EXTENSIONS)


def _node_to_para_markup(node: Any) -> str:
    """Convert inline / mixed-content nodes to ReportLab Paragraph markup."""
    if isinstance(node, NavigableString):
        return escape(str(node))
    if not isinstance(node, Tag) or node.name is None:
        return ""
    name = node.name.lower()
    if name in ("strong", "b"):
        return "<b>" + "".join(_node_to_para_markup(c) for c in node.children) + "</b>"
    if name in ("em", "i"):
        return "<i>" + "".join(_node_to_para_markup(c) for c in node.children) + "</i>"
    if name == "br":
        return "<br/>"
    if name == "code":
        return '<font name="Courier" size="9">' + escape(node.get_text()) + "</font>"
    if name == "a":
        href = node.get("href") or ""
        inner = "".join(_node_to_para_markup(c) for c in node.children)
        return f'<a href="{escape(href, True)}" color="blue">{inner}</a>'
    if name in ("del", "s", "span", "mark", "sup", "sub"):
        return "".join(_node_to_para_markup(c) for c in node.children)
    return escape(node.get_text())


def _paragraph_from_children(el: Tag, styles: dict[str, ParagraphStyle], style_key: str = "body") -> Paragraph:
    text = "".join(_node_to_para_markup(c) for c in el.children)
    return Paragraph(text, styles[style_key])


def _list_to_flowable(el: Tag, styles: dict[str, ParagraphStyle]) -> ListFlowable:
    bullet = "bullet" if el.name and el.name.lower() == "ul" else "1"
    items: list[ListItem] = []
    for li in el.find_all("li", recursive=False):
        inner: list[Any] = []
        for child in li.children:
            if isinstance(child, NavigableString):
                t = str(child)
                if t.strip():
                    inner.append(Paragraph(_node_to_para_markup(child), styles["list_item"]))
            elif isinstance(child, Tag):
                cn = child.name.lower()
                if cn in ("ul", "ol"):
                    inner.append(_list_to_flowable(child, styles))
                elif cn == "p":
                    inner.append(_paragraph_from_children(child, styles, "list_item"))
                elif cn == "pre":
                    inner.append(
                        Preformatted(child.get_text(), styles["code_block"], maxLineLength=96)
                    )
                else:
                    inner.append(Paragraph("".join(_node_to_para_markup(c) for c in child.children), styles["list_item"]))
        if not inner:
            items.append(ListItem(Paragraph(" ", styles["list_item"])))
        elif len(inner) == 1:
            items.append(ListItem(inner[0]))
        else:
            items.append(ListItem(KeepTogether(inner)))
    return ListFlowable(
        items,
        bulletType=bullet,
        leftIndent=18,
        bulletFontName="Helvetica",
        start=None if bullet == "bullet" else 1,
    )


def _block_to_flowables(el: Tag, styles: dict[str, ParagraphStyle]) -> list[Any]:
    name = (el.name or "").lower()
    out: list[Any] = []

    if name in ("h1", "h2", "h3", "h4"):
        sk = {"h1": "h1", "h2": "h2", "h3": "h3", "h4": "h3"}.get(name, "h3")
        text = "".join(_node_to_para_markup(c) for c in el.children)
        out.append(Paragraph(text, styles[sk]))
        out.append(Spacer(1, 0.08 * inch))
    elif name == "p":
        out.append(_paragraph_from_children(el, styles, "body"))
        out.append(Spacer(1, 0.06 * inch))
    elif name == "blockquote":
        inner_html = "".join(_node_to_para_markup(c) for c in el.children)
        out.append(Paragraph(inner_html, styles["quote"]))
        out.append(Spacer(1, 0.06 * inch))
    elif name == "pre":
        raw = el.get_text()
        out.append(Preformatted(raw, styles["code_block"], maxLineLength=96))
        out.append(Spacer(1, 0.08 * inch))
    elif name in ("ul", "ol"):
        out.append(_list_to_flowable(el, styles))
        out.append(Spacer(1, 0.08 * inch))
    elif name == "table":
        rows: list[list[str]] = []
        for tr in el.find_all("tr", recursive=True):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(("th", "td"), recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            col_n = max(len(r) for r in rows)
            norm = [r + [""] * (col_n - len(r)) for r in rows]
            data = [[Paragraph(escape(c), styles["table_cell"]) for c in row] for row in norm]
            t = Table(data, colWidths=[None] * col_n)
            t.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            out.append(t)
            out.append(Spacer(1, 0.1 * inch))
    elif name == "hr":
        out.append(Spacer(1, 0.06 * inch))
        out.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        out.append(Spacer(1, 0.06 * inch))
    return out


def _html_to_story(html: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.body if soup.body else soup
    story: list[Any] = []
    for child in root.children:
        if isinstance(child, NavigableString) and not str(child).strip():
            continue
        if isinstance(child, Tag):
            story.extend(_block_to_flowables(child, styles))
    return story


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    body = ParagraphStyle(
        "PDFBody",
        parent=base["Normal"],
        fontSize=10,
        leading=13,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    return {
        "title": ParagraphStyle(
            "PDFTitle",
            parent=base["Title"],
            fontSize=16,
            leading=20,
            spaceAfter=8,
        ),
        "meta": ParagraphStyle(
            "PDFMeta",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#555555"),
            spaceAfter=14,
        ),
        "h_section": ParagraphStyle(
            "PDFHSection",
            parent=base["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=10,
            spaceAfter=8,
            textColor=colors.HexColor("#222222"),
        ),
        "h1": ParagraphStyle(
            "PDFH1",
            parent=base["Heading1"],
            fontSize=14,
            leading=17,
            spaceBefore=6,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "PDFH2",
            parent=base["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "PDFH3",
            parent=base["Heading3"],
            fontSize=11,
            leading=14,
            spaceBefore=6,
            spaceAfter=4,
        ),
        "body": body,
        "quote": ParagraphStyle(
            "PDFQuote",
            parent=body,
            leftIndent=14,
            borderPadding=8,
            backColor=colors.HexColor("#f8f8f8"),
        ),
        "list_item": ParagraphStyle(
            "PDFList",
            parent=body,
        ),
        "code_block": ParagraphStyle(
            "PDFCode",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
        ),
        "table_cell": ParagraphStyle(
            "PDFTableCell",
            parent=body,
            fontSize=8,
            leading=10,
        ),
        "question": ParagraphStyle(
            "PDFQuestion",
            parent=body,
            fontSize=9,
            leading=12,
        ),
        "log": ParagraphStyle(
            "PDFLog",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7,
            leading=8,
        ),
    }


def _truncate(s: str, limit: int) -> str:
    s = s.strip()
    if len(s) <= limit:
        return s
    return s[: limit - 25] + "\n… [truncated] …"


def build_run_pdf_bytes(
    *,
    title: str,
    query: str,
    output_text: str,
    log_text: str,
) -> bytes:
    """Build a PDF with rendered Markdown for agent output and monospace log."""
    from reportlab.lib import pagesizes

    styles = _build_styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=pagesizes.letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    story: list[Any] = []
    story.append(Paragraph(escape(title), styles["title"]))
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"<i>Generated {escape(ts)}</i>", styles["meta"]))

    story.append(Paragraph("<b>Your question</b>", styles["h_section"]))
    q_lines = escape(_truncate(query, 20000)).replace("\n", "<br/>")
    story.append(Paragraph(q_lines, styles["question"]))
    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph("<b>Agent output</b>", styles["h_section"]))
    md_src = _truncate(output_text or "", 50000)
    html_out = _markdown_to_html(md_src)
    story.extend(_html_to_story(html_out, styles))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("<b>Run log (tools &amp; LLM)</b>", styles["h_section"]))
    story.append(Preformatted(_truncate(log_text or "", 120000), styles["log"], maxLineLength=120))

    doc.build(story)
    return buf.getvalue()
