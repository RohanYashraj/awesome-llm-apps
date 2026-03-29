"""
Actuarial Agents Suite — Streamlit entrypoint.

Run from this directory:
  streamlit run app_streamlit.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import streamlit as st
from agno.tools.duckdb import DuckDbTools

from agents.reserving_agent import create_reserving_agent
from agents.pricing_agent import create_pricing_agent
from agents.experience_study_agent import create_experience_study_agent
from agents.validation_agent import create_validation_agent
from agents.pension_agent import create_pension_agent
from agents.ifrs_agent import create_ifrs_reporting_agent
from agents.research_agent import create_regulatory_research_agent
from agent_run_ui import build_run_pdf_bytes, run_agent_stream
from config import get_gemini_api_key_from_env, load_app_env
from data_utils import preprocess_and_save
from skills_loader import skill_exists
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


def _require_key() -> bool:
    if not _ENV_KEY:
        st.warning(
            "Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `.env` (see `.env.example`), then restart the app."
        )
        return False
    return True


def _run_turn(agent, query: str, *, tab_label: str) -> None:
    if not query.strip():
        st.warning("Enter a question.")
        return
    with st.expander("Activity log (tools & LLM requests)", expanded=True):
        log_area = st.empty()

    def _refresh_log(text: str) -> None:
        log_area.code(text, language="text")

    st.subheader("Answer")
    out_area = st.empty()

    with st.spinner("Running agent…"):
        try:
            log_text, content, _ = run_agent_stream(agent, query, log_callback=_refresh_log)
            _refresh_log(log_text)
            out_area.markdown(content or "_No text response._")
            st.session_state["last_agent_run"] = {
                "tab_label": tab_label,
                "query": query,
                "logs": log_text,
                "output": content or "",
            }
        except Exception as e:
            st.error(f"Agent error: {e}")
            _refresh_log(f"[error] {e!s}")
            st.session_state["last_agent_run"] = {
                "tab_label": tab_label,
                "query": query,
                "logs": f"[error] {e!s}",
                "output": "",
            }


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
st.caption("Choose a tab below. Upload data where prompted, then run your question.")

# --- Tabs ---
(
    tab_reserving,
    tab_pricing,
    tab_experience,
    tab_validation,
    tab_pension,
    tab_ifrs,
    tab_research,
) = st.tabs(
    [
        "P&C Reserving",
        "Pricing & rate",
        "Experience study",
        "Model validation",
        "Pension / benefits",
        "IFRS & risk narrative",
        "Regulatory research",
    ]
)

# ---- P&C Reserving ----
with tab_reserving:
    st.subheader("P&C loss development & reserving")
    st.markdown(
        "Upload a triangle or claims/policy extract (CSV/XLSX). Data loads as DuckDB table **`uploaded_data`**."
    )
    up = st.file_uploader("Data file", type=["csv", "xlsx"], key="u_res")
    if up is not None and _require_key():
        temp_path, columns, df = preprocess_and_save(up)
        if temp_path and df is not None:
            st.dataframe(df, width="stretch")
            duck = DuckDbTools()
            duck.load_local_csv_to_table(path=temp_path, table="uploaded_data")
            extra = ["actuarial-reserving-pc"] if skill_exists("actuarial-reserving-pc") else None
            agent = create_reserving_agent(_ENV_KEY, duck, extra_skills=extra)
            q = st.text_area("Question", key="q_res", height=100)
            if st.button("Run", key="b_res"):
                _run_turn(agent, q, tab_label="P&C Reserving")
    elif up is None:
        st.info("Upload a triangle or claims/policy extract to enable SQL/pandas tools.")
        st.caption("Demo data: `fixtures/sample_loss_triangle.csv`.")

# ---- Pricing ----
with tab_pricing:
    st.subheader("Pricing & rate review")
    st.markdown("Optional upload for rating/exposure data as **`uploaded_data`**.")
    up = st.file_uploader("Data file (optional)", type=["csv", "xlsx"], key="u_pr")
    if _require_key():
        duck = None
        if up is not None:
            temp_path, _, df = preprocess_and_save(up)
            if temp_path and df is not None:
                st.dataframe(df.head(50), width="stretch")
                duck = DuckDbTools()
                duck.load_local_csv_to_table(path=temp_path, table="uploaded_data")
        else:
            st.info("No file uploaded—the agent answers **conceptually** (no SQL on `uploaded_data`).")
            st.caption("Demo upload: `fixtures/sample_pricing_rating.csv`.")
        agent = create_pricing_agent(_ENV_KEY, duck)
        q = st.text_area("Question", key="q_pr", height=100)
        if st.button("Run", key="b_pr"):
            _run_turn(agent, q, tab_label="Pricing & rate")

# ---- Experience study ----
with tab_experience:
    st.subheader("Experience study analyst")
    up = st.file_uploader("Data file", type=["csv", "xlsx"], key="u_ex")
    if up is not None and _require_key():
        temp_path, _, df = preprocess_and_save(up)
        if temp_path and df is not None:
            st.dataframe(df, width="stretch")
            duck = DuckDbTools()
            duck.load_local_csv_to_table(path=temp_path, table="uploaded_data")
            agent = create_experience_study_agent(_ENV_KEY, duck)
            q = st.text_area("Question", key="q_ex", height=100)
            if st.button("Run", key="b_ex"):
                _run_turn(agent, q, tab_label="Experience study")
    elif up is None:
        st.info("Upload experience data to enable SQL/pandas tools.")
        st.caption("Demo data: `fixtures/sample_experience_study.csv`.")

# ---- Model validation ----
with tab_validation:
    st.subheader("Model validation copilot")
    st.markdown("Paste **documentation excerpts**, **test plans**, or **code** below (no execution).")
    st.caption("Example context: `fixtures/sample_model_validation_context.md` (copy/paste).")
    if _require_key():
        agent = create_validation_agent(_ENV_KEY)
        context = st.text_area("Context to review", key="v_ctx", height=180)
        q = st.text_area("What should the reviewer focus on?", key="q_val", height=80)
        if st.button("Run", key="b_val"):
            combined = (context.strip() + "\n\n---\n\n" + q.strip()).strip()
            _run_turn(agent, combined, tab_label="Model validation")

# ---- Pension ----
with tab_pension:
    st.subheader("Pension & benefits")
    st.caption("Optional demo upload: `fixtures/sample_pension_plan.csv`.")
    up = st.file_uploader("Optional liability/member data", type=["csv", "xlsx"], key="u_pe")
    if _require_key():
        if up is not None:
            temp_path, _, df = preprocess_and_save(up)
            if temp_path and df is not None:
                st.dataframe(df.head(100), width="stretch")
                duck = DuckDbTools()
                duck.load_local_csv_to_table(path=temp_path, table="uploaded_data")
                agent = create_pension_agent(_ENV_KEY, duck)
        else:
            agent = create_pension_agent(_ENV_KEY, None)
        q = st.text_area("Question", key="q_pe", height=100)
        if st.button("Run", key="b_pe"):
            _run_turn(agent, q, tab_label="Pension / benefits")

# ---- IFRS & risk ----
with tab_ifrs:
    st.subheader("IFRS 17 & risk / capital narrative")
    st.markdown("Conceptual help only—not accounting advice.")
    st.caption("Example prompts: `fixtures/sample_ifrs_questions.md`.")
    if _require_key():
        agent = create_ifrs_reporting_agent(_ENV_KEY)
        q = st.text_area("Question", key="q_if", height=120)
        if st.button("Run", key="b_if"):
            _run_turn(agent, q, tab_label="IFRS & risk narrative")

# ---- Regulatory research ----
with tab_research:
    st.subheader("Regulatory & methodology research")
    st.markdown("Uses **ddgs** metasearch (multiple backends)—verify citations before relying on them.")
    st.caption("Example questions: `fixtures/sample_research_questions.txt`.")
    if _require_key():
        agent = create_regulatory_research_agent(_ENV_KEY)
        q = st.text_area("Research question", key="q_rr", height=120)
        if st.button("Run", key="b_rr"):
            _run_turn(agent, q, tab_label="Regulatory research")

# --- Sidebar: export (after tabs so `last_agent_run` is current) ---
with st.sidebar:
    st.divider()
    st.markdown("### Export")
    last = st.session_state.get("last_agent_run")
    if last:
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
    else:
        st.caption("Run an agent to download.")