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
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.pandas import PandasTools

from tools import (
    assumption_reasonableness_check,
    back_test,
    generate_validation_report,
    residual_diagnostics,
    sensitivity_analysis,
)

SYSTEM_PROMPT = """You are a senior actuarial model validation specialist. You follow the
principles of ASOP 56 (Modeling), SR 11-7 (Federal Reserve model risk management
guidance), and industry best practices for independent model validation.

Your capabilities:
- Analyse model output data loaded into the 'uploaded_data' DuckDB table.
- Back-test model predictions against actuals, run sensitivity analyses, perform
  residual diagnostics, check assumption reasonableness, and compile structured
  validation reports using the provided tools.
- Search the web (DuckDuckGo) for regulatory guidance and industry benchmarks.

When validating a model:
1. **Conceptual Soundness**: Assess whether the methodology is appropriate for
   the risk being modelled.
2. **Back-testing**: Compare predictions to actuals using MAE, RMSE, MAPE, bias.
3. **Sensitivity Analysis**: Test key assumptions under stress scenarios.
4. **Residual Diagnostics**: Check for bias, non-normality, autocorrelation.
5. **Assumption Review**: Verify assumptions against industry ranges.
6. **Report**: Produce a structured findings report with PASS / NEEDS REVIEW status.

Always present results in organised tables and clearly state whether the model
passes or requires remediation. Reference relevant standards.
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


def run_model_validation_agent():
    st.set_page_config(page_title="Model Validation Agent", page_icon="✅", layout="wide")
    st.title("✅ Actuarial Model Validation Agent")
    st.caption(
        "Independent model validation powered by Gemini — back-testing, sensitivity "
        "analysis, residual diagnostics, and assumption review."
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

        st.header("Validation Options")
        validation_type = st.selectbox(
            "Validation Focus",
            [
                "Full Validation",
                "Back-testing Only",
                "Sensitivity Analysis",
                "Residual Diagnostics",
                "Assumption Review",
            ],
        )

    uploaded_file = st.file_uploader(
        "Upload model predictions vs actuals (CSV or Excel)", type=["csv", "xlsx"]
    )

    if uploaded_file is not None and "gemini_api_key" in st.session_state:
        temp_path, columns, df = preprocess_and_save(uploaded_file)

        if temp_path and columns and df is not None:
            st.write("**Uploaded Data Preview:**")
            st.dataframe(df, width="stretch")
            st.write("**Columns:**", columns)

            duckdb_tools = DuckDbTools()
            duckdb_tools.load_local_csv_to_table(path=temp_path, table="uploaded_data")

            validation_agent = Agent(
                model=Gemini(
                    id="gemini-3.1-pro-preview",
                    api_key=st.session_state.gemini_api_key,
                ),
                tools=[
                    duckdb_tools,
                    PandasTools(),
                    DuckDuckGoTools(),
                    back_test,
                    sensitivity_analysis,
                    residual_diagnostics,
                    assumption_reasonableness_check,
                    generate_validation_report,
                ],
                system_message=SYSTEM_PROMPT,
                markdown=True,
            )

            user_query = st.text_area(
                "Describe the validation you need:",
                placeholder="e.g. Back-test the predicted vs actual loss ratios and check residual normality.",
            )

            st.info("💡 Check your terminal for detailed agent output")

            if st.button("Validate"):
                if not user_query.strip():
                    st.warning("Please enter a query.")
                else:
                    context = f"[Validation focus: {validation_type}]\n\n{user_query}"
                    with st.spinner("Running model validation..."):
                        try:
                            response = validation_agent.run(context)
                            content = response.content if hasattr(response, "content") else str(response)
                            st.markdown(content)
                        except Exception as e:
                            st.error(f"Agent error: {e}")


if __name__ == "__main__":
    run_model_validation_agent()
