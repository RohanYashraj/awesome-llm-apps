"""Streamed agent runs: human-readable event logs and PDF export."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

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

_MAX_ARG_LEN = 3000
_MAX_RESULT_LEN = 6000

_SQL_TOOL_NAMES = {"run_query", "inspect_query", "describe_table", "summarize_table"}
_PANDAS_TOOL_NAMES = {"run_dataframe_operation", "create_pandas_dataframe"}
_ACTUARIAL_TOOL_NAMES = {
    "actuarial_triangle_factors",
    "actuarial_bornhuetter_ferguson",
    "actuarial_loss_ratio_summary",
    "actuarial_frequency_severity",
    "actuarial_credibility",
    "actuarial_actual_to_expected",
    "actuarial_validation_checks",
    "actuarial_data_quality",
}


def _truncate(s: str, limit: int) -> str:
    s = s.strip()
    if len(s) <= limit:
        return s
    half = (limit - 30) // 2
    return s[:half] + "\n  ... [truncated] ...\n" + s[-half:]


def _format_json_compact(obj: Any) -> str:
    try:
        return json.dumps(obj, default=str, indent=2, ensure_ascii=False)
    except TypeError:
        return str(obj)


def _extract_sql(tool_name: str, args: dict | None) -> str | None:
    """Pull the SQL query string from DuckDB tool args."""
    if not args:
        return None
    if tool_name in ("run_query", "inspect_query"):
        return args.get("query")
    if tool_name in ("describe_table", "summarize_table"):
        table = args.get("table", "")
        return f"-- {tool_name}: {table}" if table else None
    return None


def _extract_pandas_op(tool_name: str, args: dict | None) -> str | None:
    """Pull the pandas operation description from PandasTools args."""
    if not args:
        return None
    if tool_name == "run_dataframe_operation":
        df_name = args.get("dataframe_name", "df")
        op = args.get("operation", "")
        params = args.get("operation_parameters", {})
        params_str = ", ".join(f"{k}={v!r}" for k, v in params.items()) if params else ""
        return f"{df_name}.{op}({params_str})"
    if tool_name == "create_pandas_dataframe":
        df_name = args.get("dataframe_name", "df")
        func = args.get("create_using_function", "")
        params = args.get("function_parameters", {})
        params_str = ", ".join(f"{k}={v!r}" for k, v in params.items()) if params else ""
        return f"{df_name} = pd.{func}({params_str})"
    return None


def _extract_actuarial_formula(tool_name: str, args: dict | None) -> str | None:
    """Build a human-readable formula string for actuarial helper tool calls."""
    if not args:
        return None

    if tool_name == "actuarial_triangle_factors":
        rows = len(args.get("cumulative_triangle", []))
        return f"age_to_age_factors(triangle[{rows} origins]) -> CDF"

    if tool_name == "actuarial_bornhuetter_ferguson":
        n = len(args.get("earned_premium", []))
        elr = args.get("a_priori_loss_ratio", "?")
        return f"BF(origins={n}, ELR={elr}) -> IBNR + ultimate per origin"

    if tool_name == "actuarial_loss_ratio_summary":
        n = len(args.get("earned_premium", []))
        return f"loss_ratio_summary(periods={n}) -> aggregate/avg/min/max LR"

    if tool_name == "actuarial_frequency_severity":
        n = len(args.get("claim_count", []))
        return f"freq_severity(periods={n}) -> frequency, severity, pure_premium"

    if tool_name == "actuarial_credibility":
        claims = args.get("observed_claims", "?")
        std = args.get("full_credibility_standard", 1082)
        return f"credibility(claims={claims}, standard={std}) -> Z factor"

    if tool_name == "actuarial_actual_to_expected":
        n = len(args.get("actual", []))
        return f"actual_to_expected(periods={n}) -> A/E aggregate + per-period"

    if tool_name == "actuarial_validation_checks":
        req = len(args.get("required_columns", []))
        pres = len(args.get("present_columns", []))
        return f"validation_checks(required={req}, present={pres}) -> gaps"

    if tool_name == "actuarial_data_quality":
        rows = args.get("row_count", "?")
        cols = args.get("column_count", "?")
        return f"data_quality(rows={rows}, cols={cols}) -> usability verdict"

    return None


def _format_tool_started(t) -> str:
    """Format a tool call start with prominent SQL/pandas/formula display."""
    name = t.tool_name or "?"
    args = t.tool_args

    sql = _extract_sql(name, args)
    if sql is not None:
        return (
            f"[sql] {name}\n"
            f"  ┌─────────────────────────────────────\n"
            f"  │ {_truncate(sql, _MAX_ARG_LEN).replace(chr(10), chr(10) + '  │ ')}\n"
            f"  └─────────────────────────────────────"
        )

    pandas_op = _extract_pandas_op(name, args)
    if pandas_op is not None:
        return (
            f"[pandas] {name}\n"
            f"  >>> {_truncate(pandas_op, _MAX_ARG_LEN)}"
        )

    formula = _extract_actuarial_formula(name, args)
    if formula is not None:
        args_s = _format_json_compact(args) if args else "{}"
        return (
            f"[formula] {formula}\n"
            f"  args: {_truncate(args_s, _MAX_ARG_LEN)}"
        )

    args_s = _format_json_compact(args) if args else "{}"
    return f"[tool_call] {name}\n  args: {_truncate(args_s, _MAX_ARG_LEN)}"


def _format_tool_completed(t, ev_content) -> str:
    """Format a tool call completion with result preview."""
    name = t.tool_name if t else "?"
    res = ""
    if t and t.result is not None:
        res = str(t.result)
    elif ev_content is not None:
        res = str(ev_content)

    is_sql = name in _SQL_TOOL_NAMES
    is_pandas = name in _PANDAS_TOOL_NAMES
    is_actuarial = name in _ACTUARIAL_TOOL_NAMES

    if is_sql:
        tag = "sql"
    elif is_pandas:
        tag = "pandas"
    elif is_actuarial:
        tag = "formula"
    else:
        tag = "tool_call"

    return f"[{tag}] {name} -> completed\n  result: {_truncate(res, _MAX_RESULT_LEN)}"


def format_stream_event(ev: Any) -> str | None:
    """Turn an Agno stream event into one structured log line (or None to skip)."""
    if isinstance(ev, RunStartedEvent):
        return f"[analysis] run_started model={ev.model or '?'}"

    if isinstance(ev, ModelRequestStartedEvent):
        return f"[analysis] llm_request model={ev.model or 'model'}"

    if isinstance(ev, ModelRequestCompletedEvent):
        parts = []
        if ev.input_tokens is not None:
            parts.append(f"in={ev.input_tokens}")
        if ev.output_tokens is not None:
            parts.append(f"out={ev.output_tokens}")
        if ev.total_tokens is not None:
            parts.append(f"total={ev.total_tokens}")
        extra = " ".join(parts) if parts else "done"
        return f"[analysis] llm_completed {extra}"

    if isinstance(ev, ToolCallStartedEvent):
        t = ev.tool
        if t is None:
            return "[tool_call] started (no details)"
        return _format_tool_started(t)

    if isinstance(ev, ToolCallCompletedEvent):
        t = ev.tool
        return _format_tool_completed(t, ev.content)

    if isinstance(ev, ToolCallErrorEvent):
        name = ev.tool.tool_name if ev.tool else "?"
        return f"[tool_call] {name} ERROR: {ev.error or '?'}"

    if isinstance(ev, RunErrorEvent):
        return f"[error] {ev.content or ev.error_type or 'Run error'}"

    if isinstance(ev, (RunContentEvent, RunCompletedEvent)):
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
    initial_lines: list[str] | None = None,
) -> tuple[str, str, RunOutput | None]:
    """
    Run agent with streaming events; returns (log_text, output_markdown, run_output).

    Includes a wall-clock timer in the final log.
    """
    wall_start = time.monotonic()
    log_lines: list[str] = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_lines.append(f"[{ts}] user_message chars={len(query)}")

    if initial_lines:
        for line in initial_lines:
            if line and line.strip():
                log_lines.append(line.strip())

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

    elapsed_s = time.monotonic() - wall_start
    log_lines.append(f"[final_answer] completed in {elapsed_s:.1f}s chars={len(content)}")

    full_log = "\n\n".join(log_lines)
    if log_callback:
        log_callback(full_log)

    return full_log, content, final
