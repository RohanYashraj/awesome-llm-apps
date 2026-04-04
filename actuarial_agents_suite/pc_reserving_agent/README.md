# P&C Reserving Agent

An AI-powered P&C claims reserving specialist that uses **Gemini** to build development triangles, estimate IBNR, and assess reserve adequacy.

This folder is **self-contained**: `pyproject.toml`, `requirements.txt`, `.python-version`, `skills/pc-reserving/SKILL.md`, `agent_utils.py`, `tools.py`, and the Streamlit app.

## Features

- **Triangle Construction** — pivot claims data into cumulative development triangles
- **Chain Ladder** — volume-weighted age-to-age factors, CDFs, ultimates
- **Bornhuetter-Ferguson** — a-priori expected losses blended with development
- **IBNR Estimation** — ultimate minus paid/incurred
- **Mack Standard Error** — reserve variability by origin year
- **SQL Analytics** — query uploaded data with DuckDB
- **Bundled skill** — `skills/pc-reserving/SKILL.md`

## Usage

From **this directory**:

```bash
uv sync
# or: pip install -r requirements.txt
streamlit run pc_reserving_agent.py
```

From the **monorepo root** (after installing deps in **this** folder):

```bash
streamlit run actuarial_agents_suite/pc_reserving_agent/pc_reserving_agent.py
```

1. Enter your Gemini API key in the sidebar.
2. Select the reserving method and tail factor.
3. Upload a CSV or Excel file with claims data.
4. Ask reserving questions in the query box.

## Sample Questions

- "Build a paid loss triangle and run chain ladder to estimate IBNR."
- "Compare Chain Ladder and BF ultimates for the last 5 accident years."
- "What is the Mack standard error for the total reserve?"
- "Show the age-to-age factors and identify any unusual development patterns."

## Standards

Follows ASOP 43 (Unpaid Claim Estimates) and the CAS Statement of Principles on Loss Reserving.
