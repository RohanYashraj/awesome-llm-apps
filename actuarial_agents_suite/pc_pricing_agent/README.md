# P&C Pricing Agent

An AI-powered P&C insurance pricing analyst that uses **Gemini** to analyse loss and premium data, compute rate indications, and support ratemaking workflows.

## Features

- **Loss Ratio Analysis** — basic, adjusted, and combined loss-and-LAE ratios
- **Indicated Rate Changes** — loss-ratio method with permissible LR derivation
- **Trending** — on-level and trend factors for written/earned periods
- **Pure Premium** — frequency-times-severity proxy by class
- **Large-Loss Treatment** — cap individual losses and measure excess removed
- **SQL Analytics** — query uploaded data with DuckDB
- **Data Manipulation** — Pandas tools for transformations

## Usage

```bash
pip install -r ../requirements.txt
streamlit run pc_pricing_agent.py
```

1. Enter your Gemini API key in the sidebar.
2. Upload a CSV or Excel file with loss/premium data.
3. Ask pricing questions in the query box.

## Sample Questions

- "Compute the loss ratio by accident year and show the indicated overall rate change."
- "What is the pure premium by line of business?"
- "Cap individual losses at $500K and show the impact on the loss ratio."
- "Trend the losses forward 24 months at 5% annual and recompute the indication."

## Standards

Follows CAS ratemaking principles, ASOP 13 (Trending), ASOP 25 (Credibility), ASOP 30 (Profit and Contingency).
