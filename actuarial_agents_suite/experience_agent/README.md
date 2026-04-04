# Experience Study Agent

An AI-powered actuarial experience study analyst that uses **Gemini** to compute A/E ratios, assess credibility, graduate rates, and analyse trends.

## Features

- **A/E Analysis** — actual-to-expected ratios overall and by segment
- **Credibility** — limited fluctuation and Buhlmann credibility weighting
- **Rate Graduation** — Whittaker-Henderson smoothing of crude rates
- **Decrement Rates** — crude qx, lapse, withdrawal rates from exposures
- **Trend Analysis** — linear and log-linear trend fitting with R-squared
- **SQL Analytics** — query uploaded data with DuckDB
- **Data Manipulation** — Pandas tools for transformations

## Usage

```bash
pip install -r ../requirements.txt
streamlit run experience_agent.py
```

1. Enter your Gemini API key in the sidebar.
2. Select the study type (Mortality, Lapse, Morbidity, etc.).
3. Upload a CSV or Excel file with experience data.
4. Ask experience study questions in the query box.

## Sample Questions

- "Compute A/E mortality ratios by 5-year age bands."
- "What is the credibility of our lapse experience with 500 observed lapses?"
- "Graduate the crude mortality rates using Whittaker-Henderson with order 3."
- "Show decrement rates by policy duration and test for a trend."
- "How does our experience compare if we blend 60% company / 40% industry?"

## Standards

Follows SOA experience study methodology, ASOP 25 (Credibility), and ASOP 35 (Selection of Demographic Assumptions).
