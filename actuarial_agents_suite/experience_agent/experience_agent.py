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
    actual_to_expected,
    compute_decrement_rates,
    credibility_weight,
    trend_analysis,
    whittaker_henderson_graduation,
)

SKILL_SUBDIR = "experience-study"

SYSTEM_PROMPT_BASE = """You are a senior actuarial experience study analyst. You have deep expertise in
mortality, morbidity, lapse, and withdrawal experience studies following SOA
(Society of Actuaries) and CAS standards.

Your capabilities:
- Analyse experience data loaded into the 'uploaded_data' DuckDB table.
- Compute Actual-to-Expected (A/E) ratios, credibility weights, graduated rates
  (Whittaker-Henderson), crude decrement rates, and trend analyses using the
  provided actuarial tools.
- Write SQL queries against the uploaded data using DuckDB tools.
- Use pandas for additional data manipulation.

When conducting an experience study:
1. Start by understanding the data: exposures, decrements, expected basis,
   segmentation variables (age, gender, duration, product, etc.).
2. Compute crude decrement rates and A/E ratios by relevant segments.
3. Assess credibility of the observed experience.
4. Graduate rates if sufficient data exists (Whittaker-Henderson smoothing).
5. Analyse trends over calendar/policy years.
6. Present results in clear tables segmented by key risk factors.
7. Provide conclusions on whether to update assumptions, blend with industry
   tables, or rely on standard tables.
8. Reference relevant SOA studies and ASOP 25 (Credibility) when applicable.
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


def run_experience_agent():
    st.set_page_config(page_title="Experience Study Agent", page_icon="📊", layout="wide")
    st.title("📊 Actuarial Experience Study Agent")
    st.caption(
        "Experience analysis powered by Gemini — A/E ratios, credibility, "
        "graduation, decrement rates, and trend analysis."
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

        st.header("Study Options")
        study_type = st.selectbox(
            "Study Type",
            ["Mortality", "Lapse / Persistency", "Morbidity / Disability", "Withdrawal", "Other"],
        )

    uploaded_file = st.file_uploader(
        "Upload experience data (CSV or Excel)", type=["csv", "xlsx"]
    )

    if uploaded_file is not None and "gemini_api_key" in st.session_state:
        temp_path, columns, df = preprocess_and_save(uploaded_file)

        if temp_path and columns and df is not None:
            st.write("**Uploaded Data Preview:**")
            st.dataframe(df, width="stretch")
            st.write("**Columns:**", columns)

            duckdb_tools = DuckDbTools()
            duckdb_tools.load_local_csv_to_table(path=temp_path, table="uploaded_data")

            experience_agent = Agent(
                model=Gemini(
                    id="gemini-3.1-pro-preview",
                    api_key=st.session_state.gemini_api_key,
                ),
                tools=[
                    duckdb_tools,
                    PandasTools(),
                    actual_to_expected,
                    credibility_weight,
                    whittaker_henderson_graduation,
                    compute_decrement_rates,
                    trend_analysis,
                ],
                system_message=build_system_prompt(),
                markdown=True,
            )

            user_query = st.text_area(
                "Ask about the experience study:",
                placeholder="e.g. Compute A/E mortality ratios by age band and assess credibility.",
            )

            st.info("💡 Check your terminal for detailed agent output")

            if st.button("Analyse"):
                if not user_query.strip():
                    st.warning("Please enter a query.")
                else:
                    context = f"[Study type: {study_type}]\n\n{user_query}"
                    with st.spinner("Running experience analysis..."):
                        try:
                            response = experience_agent.run(context)
                            content = response.content if hasattr(response, "content") else str(response)
                            st.markdown(content)
                        except Exception as e:
                            st.error(f"Agent error: {e}")


if __name__ == "__main__":
    run_experience_agent()
