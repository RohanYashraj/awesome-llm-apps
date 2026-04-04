"""Actuarial Agents Suite — unified Streamlit hub.

Run with:
    streamlit run actuarial_agents_suite/app_streamlit.py
"""

import streamlit as st

st.set_page_config(
    page_title="Actuarial Agents Suite",
    page_icon="🧮",
    layout="wide",
)

st.title("🧮 Actuarial Agents Suite")
st.markdown(
    "A collection of **Gemini-powered actuarial AI agents** for P&C pricing, "
    "reserving, model validation, and experience studies."
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("💲 P&C Pricing Agent")
    st.markdown(
        "Loss ratio analysis, indicated rate changes, loss trending, "
        "pure premiums, and large-loss treatment."
    )
    st.code("streamlit run actuarial_agents_suite/pc_pricing_agent/pc_pricing_agent.py", language="bash")

    st.subheader("📐 P&C Reserving Agent")
    st.markdown(
        "Development triangles, Chain Ladder, Bornhuetter-Ferguson, "
        "IBNR estimation, and Mack uncertainty."
    )
    st.code("streamlit run actuarial_agents_suite/pc_reserving_agent/pc_reserving_agent.py", language="bash")

with col2:
    st.subheader("✅ Model Validation Agent")
    st.markdown(
        "Back-testing, sensitivity analysis, residual diagnostics, "
        "assumption review, and structured validation reports."
    )
    st.code("streamlit run actuarial_agents_suite/model_validation_agent/model_validation_agent.py", language="bash")

    st.subheader("📊 Experience Study Agent")
    st.markdown(
        "A/E ratios, credibility weighting, rate graduation, "
        "decrement rates, and trend analysis."
    )
    st.code("streamlit run actuarial_agents_suite/experience_agent/experience_agent.py", language="bash")

st.divider()

st.markdown("### Quick Start")
st.markdown(
    """
1. **Get a Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey).
2. **Install dependencies**:
   ```bash
   pip install -r actuarial_agents_suite/requirements.txt
   ```
3. **Launch any agent** using the commands above, or select one below.
"""
)

st.divider()

agent_choice = st.selectbox(
    "Select an agent to learn more:",
    [
        "-- Select --",
        "P&C Pricing Agent",
        "P&C Reserving Agent",
        "Model Validation Agent",
        "Experience Study Agent",
    ],
)

if agent_choice == "P&C Pricing Agent":
    st.markdown(
        """
**Purpose**: Analyse P&C insurance pricing data — loss ratios, rate
indications, trending, pure premiums, and large-loss caps.

**Tools**: DuckDB (SQL), Pandas, plus custom actuarial pricing functions
(loss ratio, indicated rate change, trending factors, pure premium,
large-loss cap analysis).

**Standards**: CAS ratemaking, ASOP 13, ASOP 25, ASOP 30.

**Data**: Upload a CSV/Excel with columns like `accident_year`,
`earned_premium`, `incurred_losses`, `lae`, `exposures`, etc.
"""
    )

elif agent_choice == "P&C Reserving Agent":
    st.markdown(
        """
**Purpose**: Estimate unpaid claims using development triangles —
Chain Ladder, Bornhuetter-Ferguson, IBNR, and Mack standard error.

**Tools**: DuckDB (SQL), Pandas, plus custom reserving functions
(triangle builder, chain ladder, BF, IBNR, Mack method).

**Standards**: ASOP 43, CAS Statement of Principles on Loss Reserving.

**Data**: Upload a CSV/Excel with columns like `accident_year`,
`development_lag`, `cumulative_paid` (or `cumulative_incurred`).
"""
    )

elif agent_choice == "Model Validation Agent":
    st.markdown(
        """
**Purpose**: Independently validate actuarial models — back-test,
stress-test, check residuals, review assumptions, produce reports.

**Tools**: DuckDB (SQL), Pandas, DuckDuckGo (regulatory search),
plus custom validation functions (back-test, sensitivity, residual
diagnostics, assumption check, report generator).

**Standards**: ASOP 56, SR 11-7, ORSA.

**Data**: Upload a CSV/Excel with columns like `predicted`, `actual`,
or any model-output columns you want to validate.
"""
    )

elif agent_choice == "Experience Study Agent":
    st.markdown(
        """
**Purpose**: Conduct experience studies — A/E ratios, credibility,
graduated rates, decrement analysis, and trend fitting.

**Tools**: DuckDB (SQL), Pandas, plus custom experience study functions
(A/E ratios, credibility weighting, Whittaker-Henderson graduation,
decrement rates, trend analysis).

**Standards**: ASOP 25, ASOP 35, SOA experience study methodology.

**Data**: Upload a CSV/Excel with columns like `age`, `exposures`,
`actual_claims`, `expected_claims`, `study_year`, etc.
"""
    )

st.divider()
st.caption(
    "Actuarial Agents Suite is for educational and analytical purposes. "
    "All outputs should be reviewed by a qualified actuary before use in "
    "regulatory filings or business decisions."
)
