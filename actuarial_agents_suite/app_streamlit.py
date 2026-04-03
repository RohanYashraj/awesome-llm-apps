"""Actuarial Agents Suite — Streamlit entrypoint."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st
from agent_profiles import AGENT_PROFILES, DIRECT_TAB_ORDER
from agent_run_ui import build_run_pdf_bytes, run_agent_stream
from agents.experience_study_agent import create_experience_study_agent
from agents.orchestrator_agent import choose_route
from agents.pricing_agent import create_pricing_agent
from agents.reserving_agent import create_reserving_agent
from agents.validation_agent import create_validation_agent
from actuarial_utils.validation import has_contradictory_conclusion
from config import get_gemini_api_key_from_env, load_app_env
from data_utils import preprocess_and_save
from tools.factory import build_agent_tooling
from ui_branding import inject_maestros_styles, render_maestros_shell

load_app_env()

st.set_page_config(
    page_title="MaestrosAI · Actuarial Agents",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_maestros_styles()
render_maestros_shell()

_ENV_KEY = get_gemini_api_key_from_env()


def _escape_latex_dollars(text: str) -> str:
    """
    Escape bare `$` signs so Streamlit does not interpret them as LaTeX.

    Streamlit treats `$...$` and `$$...$$` as inline/block math.  Actuarial
    output frequently contains dollar amounts (`$5,000`) which get mangled.
    This escapes `$` to `\\$` except inside fenced code blocks where `$` is
    already literal.
    """
    if not text:
        return text
    lines = text.split("\n")
    result: list[str] = []
    in_code_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            result.append(line)
            continue
        if in_code_fence:
            result.append(line)
            continue
        result.append(line.replace("$", r"\$"))
    return "\n".join(result)


def _require_key() -> bool:
    if not _ENV_KEY:
        st.warning(
            "Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `.env` (see `.env.example`), then restart the app."
        )
        return False
    return True


def _build_agent(profile_key: str, api_key: str, csv_path: str | None, telemetry_log: list[str]):
    def _tool_telemetry(tool_name: str, details: dict) -> None:
        telemetry_log.append(
            f"[tool_call] {tool_name} duration={details.get('duration_ms')}ms "
            f"inputs={details.get('inputs_summary')} result={details.get('result_preview')}"
        )

    tooling = build_agent_tooling(role=profile_key, csv_path=csv_path, telemetry_callback=_tool_telemetry)
    has_data = csv_path is not None

    if profile_key == "reserving":
        return create_reserving_agent(api_key, tools=tooling.tools, has_data=has_data)
    if profile_key == "pricing":
        return create_pricing_agent(api_key, tools=tooling.tools, has_data=has_data)
    if profile_key == "experience_study":
        return create_experience_study_agent(api_key, tools=tooling.tools, has_data=has_data)
    if profile_key == "model_validation":
        return create_validation_agent(api_key, tools=tooling.tools)
    raise ValueError(f"Unsupported profile: {profile_key}")


def _session_key(tab_key: str, field: str) -> str:
    return f"run_{tab_key}_{field}"


def _store_run_result(tab_key: str, *, tab_label: str, query: str, output: str, logs: str) -> None:
    """Persist a run result into session_state so it survives reruns."""
    st.session_state[_session_key(tab_key, "tab_label")] = tab_label
    st.session_state[_session_key(tab_key, "query")] = query
    st.session_state[_session_key(tab_key, "output")] = output
    st.session_state[_session_key(tab_key, "logs")] = logs
    st.session_state["last_agent_run"] = {
        "tab_label": tab_label,
        "query": query,
        "output": output,
        "logs": logs,
    }


def _get_stored_result(tab_key: str) -> dict | None:
    output = st.session_state.get(_session_key(tab_key, "output"))
    if output is None:
        return None
    return {
        "tab_label": st.session_state.get(_session_key(tab_key, "tab_label"), ""),
        "query": st.session_state.get(_session_key(tab_key, "query"), ""),
        "output": output,
        "logs": st.session_state.get(_session_key(tab_key, "logs"), ""),
    }


def _render_stored_result(tab_key: str) -> None:
    """Re-render a previously stored result from session state (survives reruns)."""
    result = _get_stored_result(tab_key)
    if result is None:
        return
    if result["output"]:
        st.subheader("Answer")
        st.markdown(_escape_latex_dollars(result["output"]))
    if result["logs"]:
        with st.expander("Activity log", expanded=False):
            st.code(result["logs"], language="text")


def _run_turn(
    agent,
    query: str,
    *,
    tab_key: str,
    tab_label: str,
    prelude_lines: list[str] | None = None,
    telemetry_log: list[str] | None = None,
) -> None:
    if not query.strip():
        st.warning("Enter a question.")
        return

    log_placeholder = st.empty()
    answer_placeholder = st.empty()

    with st.spinner("Running agent..."):
        try:
            def _refresh_log(text: str) -> None:
                with log_placeholder.expander("Activity log (tools & LLM requests)", expanded=True):
                    st.code(text, language="text")

            log_text, content, _ = run_agent_stream(
                agent,
                query,
                log_callback=_refresh_log,
                initial_lines=prelude_lines or [],
            )
            if telemetry_log:
                log_text = log_text + "\n\n" + "\n".join(telemetry_log)

            output = content or ""
            _store_run_result(tab_key, tab_label=tab_label, query=query, output=output, logs=log_text)

        except Exception as e:
            error_log = f"[error] {e!s}"
            _store_run_result(tab_key, tab_label=tab_label, query=query, output="", logs=error_log)
            st.error(f"Agent error: {e}")

    log_placeholder.empty()
    answer_placeholder.empty()
    _render_stored_result(tab_key)


def _render_route_card(route) -> None:
    """Display a compact routing summary card above the answer."""
    cols = st.columns([2, 1, 1])
    with cols[0]:
        st.markdown(f"**Primary specialist:** {route.primary_label}")
    with cols[1]:
        conf_color = {"high": "green", "medium": "orange", "low": "red"}.get(route.confidence, "gray")
        st.markdown(f"**Confidence:** :{conf_color}[{route.confidence}]")
    with cols[2]:
        if route.additional_agents:
            st.markdown(f"**Also:** {', '.join(route.additional_labels)}")
        else:
            st.markdown("**Also:** _none_")
    if route.rationale:
        st.caption(f"Rationale: {route.rationale}")


def _run_orchestrated_turn(api_key: str, query: str, csv_path: str | None) -> None:
    if not query.strip():
        st.warning("Enter a question.")
        return

    telemetry_log: list[str] = []
    all_log_parts: list[str] = []

    with st.status("Routing to specialist...", expanded=True) as status:
        route = choose_route(api_key, query)
        prelude = route.summary_lines()
        all_log_parts.append("\n".join(prelude))

        _render_route_card(route)

        specialist = _build_agent(route.primary_agent, api_key, csv_path, telemetry_log)
        specialist_query = route.refined_query.strip() if route.refined_query else query

        status.update(label=f"Running {route.primary_label}...", state="running")
        log_text, content, _ = run_agent_stream(
            specialist,
            specialist_query,
            initial_lines=prelude,
        )
        all_log_parts.append(log_text)

        if route.reroute_once:
            status.update(label="Quality gate: refining assumptions...", state="running")
            reroute_query = (
                specialist_query
                + "\n\nBefore finalizing, explicitly list all assumptions (with materiality), "
                "flag any that are missing, and restate a bounded recommendation."
            )
            reroute_log, content, _ = run_agent_stream(
                specialist,
                reroute_query,
                initial_lines=["[route] quality_gate=reroute_once"],
            )
            all_log_parts.append(reroute_log)

        additional_outputs: list[str] = []
        for extra_key in route.additional_agents:
            if extra_key == route.primary_agent:
                continue
            status.update(label=f"Delegating to {AGENT_PROFILES[extra_key].label}...", state="running")
            extra_agent = _build_agent(extra_key, api_key, csv_path, telemetry_log)
            extra_log, extra_content, _ = run_agent_stream(
                extra_agent,
                query,
                initial_lines=[f"[route] delegated={extra_key}"],
            )
            all_log_parts.append(extra_log)
            if extra_content:
                additional_outputs.append(
                    f"### {AGENT_PROFILES[extra_key].label}\n\n{extra_content}"
                )

        if content and has_contradictory_conclusion(content):
            status.update(label="Contradiction check...", state="running")
            validator = _build_agent("model_validation", api_key, csv_path, telemetry_log)
            validation_prompt = (
                "Review the following actuarial draft for internal contradictions, "
                "ambiguous conclusions, or unsupported numeric claims. Suggest corrections.\n\n"
                f"Original question:\n{query}\n\nDraft:\n{content}"
            )
            val_log, val_content, _ = run_agent_stream(
                validator,
                validation_prompt,
                initial_lines=["[analysis] contradiction_check=triggered"],
            )
            all_log_parts.append(val_log)
            if val_content:
                additional_outputs.append(f"### Validation review\n\n{val_content}")

        if telemetry_log:
            all_log_parts.append("\n".join(telemetry_log))

        status.update(label="Complete", state="complete")

    full_log = "\n\n".join(all_log_parts)

    merged_output = content or ""
    if additional_outputs:
        merged_output += "\n\n---\n\n" + "\n\n---\n\n".join(additional_outputs)

    _store_run_result(
        "orchestrator",
        tab_label="Orchestrated copilot",
        query=query,
        output=merged_output,
        logs=full_log,
    )
    _render_stored_result("orchestrator")


# --- Sidebar (top) ---
with st.sidebar:
    st.markdown("### Settings")
    if _ENV_KEY:
        st.caption("Gemini API key is set via environment (`.env`).")
    else:
        st.warning(
            "No API key found. Add `GEMINI_API_KEY` or `GOOGLE_API_KEY` to `.env`, then restart."
        )
    st.caption("Model: `gemini-3.1-pro-preview` · Synthetic or masked data only; drafts, not filings.")


st.markdown("##### Workstreams")
st.caption("Use orchestrator for automatic routing, or run a specialist tab directly.")

# --- Tabs ---
tab_labels = ["Orchestrated copilot"] + [AGENT_PROFILES[k].label for k in DIRECT_TAB_ORDER]
tabs = st.tabs(tab_labels)

# ---- Orchestrator ----
with tabs[0]:
    st.subheader("Orchestrated copilot")
    st.markdown("One entry point that routes to the right actuarial specialist and can delegate across specialists.")
    upload = st.file_uploader("Data file (optional)", type=["csv", "xlsx"], key="u_orc")
    csv_path = None
    if upload is not None:
        csv_path, _, df = preprocess_and_save(upload)
        if csv_path and df is not None:
            st.dataframe(df.head(80), width="stretch")
    query = st.text_area("Question", key="q_orc", height=120)
    if st.button("Run", key="b_orc") and _require_key():
        _run_orchestrated_turn(_ENV_KEY, query, csv_path)
    else:
        _render_stored_result("orchestrator")


def _render_specialist_tab(profile_key: str, tab_index: int) -> None:
    profile = AGENT_PROFILES[profile_key]
    with tabs[tab_index]:
        st.subheader(profile.label)
        st.caption(profile.description)
        csv_path = None
        question = ""
        if profile.tool_policy == "text_only":
            if not _require_key():
                return
            context = st.text_area("Context to review", key=f"ctx_{profile_key}", height=180)
            focus = st.text_area("Question", key=f"q_{profile_key}", height=90)
            question = (context.strip() + "\n\n---\n\n" + focus.strip()).strip()
        else:
            up = st.file_uploader(
                "Data file" if profile.tool_policy == "required_data" else "Data file (optional)",
                type=["csv", "xlsx"],
                key=f"u_{profile_key}",
            )
            if up is not None:
                csv_path, _, df = preprocess_and_save(up)
                if csv_path and df is not None:
                    st.dataframe(df.head(80), width="stretch")
            elif profile.tool_policy == "required_data":
                st.info("Upload a CSV/XLSX dataset to enable this specialist.")
                _render_stored_result(profile_key)
                return
            question = st.text_area("Question", key=f"q_{profile_key}", height=100)

        if st.button("Run", key=f"b_{profile_key}") and _require_key():
            telemetry: list[str] = []
            agent = _build_agent(profile_key, _ENV_KEY, csv_path, telemetry)
            prelude = [f"[route] direct={profile_key}"]
            _run_turn(
                agent,
                question,
                tab_key=profile_key,
                tab_label=profile.label,
                prelude_lines=prelude,
                telemetry_log=telemetry,
            )
        else:
            _render_stored_result(profile_key)


for idx, key in enumerate(DIRECT_TAB_ORDER, start=1):
    _render_specialist_tab(key, idx)


# --- Sidebar: export (after tabs so `last_agent_run` is current) ---
with st.sidebar:
    st.divider()
    st.markdown("### Export")
    last = st.session_state.get("last_agent_run")
    if last and last.get("output"):
        try:
            pdf_bytes = build_run_pdf_bytes(
                title=f"MaestrosAI — {last.get('tab_label', 'Run')}",
                query=last.get("query", ""),
                output_text=last.get("output", ""),
            )
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"actuarial_agent_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf",
                mime="application/pdf",
                key="dl_pdf_last_run",
                help="Question and answer only (no activity log).",
            )
        except Exception as ex:
            st.caption(f"PDF unavailable: {ex}")

        if last.get("logs"):
            st.download_button(
                label="Download activity log",
                data=last.get("logs", ""),
                file_name=f"actuarial_activity_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt",
                mime="text/plain",
                key="dl_logs_last_run",
            )
    else:
        st.caption("Run an agent to enable downloads.")
