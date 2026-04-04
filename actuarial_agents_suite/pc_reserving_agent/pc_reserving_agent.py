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

from tools import (
    bornhuetter_ferguson,
    build_triangle,
    chain_ladder,
    compute_ibnr,
    mack_method_std_error,
)

SYSTEM_PROMPT = """You are a senior P&C actuarial reserving specialist. You have deep expertise in
claims reserving methodologies following CAS standards and ASOPs (especially ASOP 43 –
Unpaid Claim Estimates).

Your capabilities:
- Analyse claims data loaded into the 'uploaded_data' DuckDB table.
- Build development triangles, run Chain Ladder and Bornhuetter-Ferguson methods,
  compute IBNR, and estimate reserve variability using Mack's method via the
  provided actuarial tools.
- Write SQL queries against the uploaded data using DuckDB tools.
- Use pandas for additional data manipulation.

When answering:
1. Always start by understanding the data structure (origin periods, development
   lags, cumulative vs incremental values).
2. Use the reserving tools for standard calculations; show the development triangle,
   age-to-age factors, cumulative factors, and ultimate/IBNR summaries.
3. Present results in clear tables with origin-year detail and totals.
4. Compare Chain Ladder and BF results when both are applicable.
5. Discuss reserve uncertainty and the standard error from Mack's method.
6. Cite relevant ASOPs and professional guidance.
7. Flag data quality issues, thin data, and judgmental selections.
"""


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


def run_reserving_agent():
    st.set_page_config(page_title="P&C Reserving Agent", page_icon="📐", layout="wide")
    st.title("📐 P&C Reserving Agent")
    st.caption(
        "Actuarial reserving analysis powered by Gemini — Chain Ladder, "
        "Bornhuetter-Ferguson, IBNR estimation, and Mack uncertainty."
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

        st.header("Reserving Options")
        method = st.selectbox(
            "Select Method",
            ["Chain Ladder", "Bornhuetter-Ferguson", "Both"],
            index=2,
        )
        tail_factor = st.number_input("Tail Factor", min_value=1.0, value=1.0, step=0.01)

    uploaded_file = st.file_uploader(
        "Upload claims / triangle data (CSV or Excel)", type=["csv", "xlsx"]
    )

    if uploaded_file is not None and "gemini_api_key" in st.session_state:
        temp_path, columns, df = preprocess_and_save(uploaded_file)

        if temp_path and columns and df is not None:
            st.write("**Uploaded Data Preview:**")
            st.dataframe(df, width="stretch")
            st.write("**Columns:**", columns)

            duckdb_tools = DuckDbTools()
            duckdb_tools.load_local_csv_to_table(path=temp_path, table="uploaded_data")

            reserving_agent = Agent(
                model=Gemini(
                    id="gemini-3.1-pro-preview",
                    api_key=st.session_state.gemini_api_key,
                ),
                tools=[
                    duckdb_tools,
                    PandasTools(),
                    build_triangle,
                    chain_ladder,
                    bornhuetter_ferguson,
                    compute_ibnr,
                    mack_method_std_error,
                ],
                system_message=SYSTEM_PROMPT,
                markdown=True,
            )

            user_query = st.text_area(
                "Ask a reserving question about the data:",
                placeholder="e.g. Build a paid loss triangle and run chain ladder to estimate IBNR.",
            )

            st.info("💡 Check your terminal for detailed agent output")

            if st.button("Analyse"):
                if not user_query.strip():
                    st.warning("Please enter a query.")
                else:
                    context = f"[User selected method: {method}, tail factor: {tail_factor}]\n\n{user_query}"
                    with st.spinner("Running reserving analysis..."):
                        try:
                            response = reserving_agent.run(context)
                            content = response.content if hasattr(response, "content") else str(response)
                            st.markdown(content)
                        except Exception as e:
                            st.error(f"Agent error: {e}")


if __name__ == "__main__":
    run_reserving_agent()
