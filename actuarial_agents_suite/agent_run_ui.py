"""Streamed agent runs: human-readable event logs and PDF export."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from xml.sax.saxutils import escape

from pdf_export import build_run_pdf_bytes

from agno.run.agent import (
    ModelRequestCompletedEvent,
    ModelRequestStartedEvent,
    RunCompletedEvent,
    RunContentEvent,
    RunErrorEvent,
    RunOutput,
    RunStartedEvent,
    ToolCallCompletedEvent,
    ToolCallErrorEvent,
    ToolCallStartedEvent,
)

_MAX_ARG_LEN = 4000
_MAX_RESULT_LEN = 8000


def _truncate(s: str, limit: int) -> str:
    s = s.strip()
    if len(s) <= limit:
        return s
    return s[: limit - 20] + "\n… [truncated] …"


def format_stream_event(ev: Any) -> str | None:
    """Turn an Agno stream event into one log line (or None to skip)."""
    if isinstance(ev, RunStartedEvent):
        m = ev.model or "?"
        return f"[run] Started (model={m})"
    if isinstance(ev, ModelRequestStartedEvent):
        return f"[llm] Request started — {ev.model or 'model'}"
    if isinstance(ev, ModelRequestCompletedEvent):
        parts = []
        if ev.total_tokens is not None:
            parts.append(f"tokens={ev.total_tokens}")
        if ev.input_tokens is not None:
            parts.append(f"in={ev.input_tokens}")
        if ev.output_tokens is not None:
            parts.append(f"out={ev.output_tokens}")
        extra = ", ".join(parts) if parts else "done"
        return f"[llm] Request completed — {extra}"
    if isinstance(ev, ToolCallStartedEvent):
        t = ev.tool
        if t is None:
            return "[tool] Starting (no details)"
        name = t.tool_name or "?"
        args = t.tool_args
        try:
            args_s = json.dumps(args, default=str, indent=2) if args else "{}"
        except TypeError:
            args_s = str(args)
        return f"[tool] {name} ▶ args:\n{_truncate(args_s, _MAX_ARG_LEN)}"
    if isinstance(ev, ToolCallCompletedEvent):
        t = ev.tool
        name = t.tool_name if t else "?"
        res = ""
        if t and t.result is not None:
            res = str(t.result)
        elif ev.content is not None:
            res = str(ev.content)
        return f"[tool] {name} ◀ result:\n{_truncate(res, _MAX_RESULT_LEN)}"
    if isinstance(ev, ToolCallErrorEvent):
        name = ev.tool.tool_name if ev.tool else "?"
        err = ev.error or "?"
        return f"[tool] {name} ✖ error: {err}"
    if isinstance(ev, RunErrorEvent):
        return f"[error] {ev.content or ev.error_type or 'Run error'}"
    if isinstance(ev, RunContentEvent):
        # Very chatty; omit token deltas
        return None
    if isinstance(ev, RunCompletedEvent):
        return None
    evname = getattr(ev, "event", None)
    if isinstance(evname, str) and evname:
        return f"[event] {evname}"
    return None


def run_agent_stream(
    agent: Any,
    query: str,
    *,
    log_callback: Callable[[str], None] | None = None,
) -> tuple[str, str, RunOutput | None]:
    """
    Run agent with streaming events; returns (log_text, output_markdown, run_output).

    Uses Agno's stream=True, stream_events=True, yield_run_output=True.
    If ``log_callback`` is set, it is invoked with the full log text whenever a new line is appended.
    """
    log_lines: list[str] = []
    log_lines.append(f"[{datetime.now(timezone.utc).isoformat()}] User message ({len(query)} chars)")
    if log_callback:
        log_callback("\n\n".join(log_lines))
    final: RunOutput | None = None
    iterator = agent.run(
        query,
        stream=True,
        stream_events=True,
        yield_run_output=True,
    )
    for item in iterator:
        if isinstance(item, RunOutput):
            final = item
            continue
        line = format_stream_event(item)
        if line:
            log_lines.append(line)
            if log_callback:
                log_callback("\n\n".join(log_lines))
    content = ""
    if final is not None:
        c = final.content
        content = c if isinstance(c, str) else (str(c) if c is not None else "")
    return "\n\n".join(log_lines), content, final
