import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import streamlit as st
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

from agent_utils import load_skill_markdown
from tools import (
    compute_indicated_rate_change,
    compute_loss_ratio,
    compute_pure_premium,
    large_loss_cap_analysis,
    trending_factors,
)

SKILL_SUBDIR = "pc-pricing"

SYSTEM_PROMPT_BASE = """You are a senior P&C actuarial pricing analyst. You have deep expertise in
property & casualty insurance ratemaking following CAS (Casualty Actuarial Society)
standards and ASOPs (Actuarial Standards of Practice).

Your capabilities:
- Analyse loss and premium data loaded into the 'uploaded_data' DuckDB table.
- Compute loss ratios, indicated rate changes, loss trends, pure premiums, and
  large-loss capping using the provided actuarial tools.
- Write SQL queries against the uploaded data using DuckDB tools.
- Use pandas for additional data manipulation when needed.

When answering:
1. Always reference the data in the 'uploaded_data' table for empirical analysis.
2. Use the actuarial pricing tools for standard calculations.
3. Present numerical results in well-formatted tables.
4. Explain methodology (loss-ratio method, pure-premium method, trending) clearly.
5. Cite relevant ASOPs (e.g., ASOP 13 – Trending, ASOP 25 – Credibility) when applicable.
6. Flag limitations and assumptions explicitly.
"""


def build_system_prompt() -> str:
    skill = load_skill_markdown(SKILL_SUBDIR)
    if not skill:
        return SYSTEM_PROMPT_BASE
    return (
        SYSTEM_PROMPT_BASE
        + "\n\n## Bundled domain skill (from skills/"
        + SKILL_SUBDIR
        + "/SKILL.md)\n\n"
        + skill
    )


def render_data_privacy_note() -> None:
    st.divider()
    st.markdown(
        """
<div style="font-size:0.78rem;line-height:1.45;color:var(--gray-600, #6b7280);margin-top:0.25rem;">
<em>*Data Privacy Declaration*</em><br><br>
This AI tool does not store, retain, or save any user data. All information entered is processed in real time and is not recorded in any database or storage system.<br>
Once the page is refreshed or the session ends, all data is immediately and permanently deleted. No history, logs, or user inputs are preserved beyond the active session.<br>
Users can interact with this tool with full confidence that their data remains private and is not stored at any point.
</div>
        """.strip(),
        unsafe_allow_html=True,
    )


def preprocess_and_save(file):
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file, encoding="utf-8", na_values=["NA", "N/A", "missing"])
        elif file.name.endswith(".xlsx"):
            df = pd.read_excel(file, na_values=["NA", "N/A", "missing"])
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None, None, None

        for col in df.select_dtypes(include=["object"]):
            df[col] = df[col].astype(str).replace({r'"': '""'}, regex=True)

        for col in df.columns:
            if "date" in col.lower():
                df[col] = pd.to_datetime(df[col], errors="coerce")
            elif df[col].dtype == "object":
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            temp_path = tmp.name
            df.to_csv(temp_path, index=False, quoting=csv.QUOTE_ALL)

        return temp_path, df.columns.tolist(), df
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, None


def run_pricing_agent():
    st.set_page_config(page_title="P&C Pricing Agent", page_icon="💲", layout="wide")
    st.title("💲 P&C Pricing Agent")
    st.caption(
        "Actuarial pricing analysis powered by Gemini — loss ratios, rate indications, "
        "trending, pure premiums, and large-loss treatment."
    )

    with st.sidebar:
        st.header("API Keys")
        gemini_api_key = st.text_input("Gemini API Key", type="password")
        st.caption("Get your key from [Google AI Studio](https://aistudio.google.com/apikey).")
        if gemini_api_key:
            st.session_state.gemini_api_key = gemini_api_key
            st.success("API key saved!")
        else:
            st.warning("Please enter your Gemini API key to proceed.")

    uploaded_file = st.file_uploader(
        "Upload loss / premium data (CSV or Excel)", type=["csv", "xlsx"]
    )

    if uploaded_file is not None and "gemini_api_key" in st.session_state:
        temp_path, columns, df = preprocess_and_save(uploaded_file)

        if temp_path and columns and df is not None:
            st.write("**Uploaded Data Preview:**")
            st.dataframe(df, width="stretch")
            st.write("**Columns:**", columns)

            duckdb_tools = DuckDbTools()
            duckdb_tools.load_local_csv_to_table(path=temp_path, table="uploaded_data")

            pricing_agent = Agent(
                model=Gemini(
                    id="gemini-3-flash-preview",
                    api_key=st.session_state.gemini_api_key,
                ),
                tools=[
                    duckdb_tools,
                    PandasTools(),
                    compute_loss_ratio,
                    compute_indicated_rate_change,
                    trending_factors,
                    compute_pure_premium,
                    large_loss_cap_analysis,
                ],
                system_message=build_system_prompt(),
                markdown=True,
            )

            if "generated_code" not in st.session_state:
                st.session_state.generated_code = None

            user_query = st.text_area(
                "Ask a pricing question about the data:",
                placeholder="e.g. Compute the loss ratio by year and indicate the overall rate change needed.",
            )

            st.info("💡 Check your terminal for detailed agent output")

            if st.button("Analyse"):
                if not user_query.strip():
                    st.warning("Please enter a query.")
                else:
                    with st.spinner("Running pricing analysis..."):
                        try:
                            response = pricing_agent.run(user_query)
                            content = response.content if hasattr(response, "content") else str(response)
                            st.markdown(content)
                        except Exception as e:
                            st.error(f"Agent error: {e}")

    render_data_privacy_note()


if __name__ == "__main__":
    run_pricing_agent()
