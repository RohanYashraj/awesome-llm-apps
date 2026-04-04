# Model Validation Agent

An AI-powered actuarial model validation specialist that uses **Gemini** to back-test models, run sensitivity analyses, and produce structured validation reports.

## Features

- **Back-testing** — MAE, RMSE, MAPE, bias between predicted and actual
- **Sensitivity Analysis** — one-way parameter perturbation with impact measurement
- **Residual Diagnostics** — normality (Shapiro-Wilk), autocorrelation, skewness/kurtosis
- **Assumption Review** — compare assumptions to industry ranges
- **Validation Reports** — structured PASS / NEEDS REVIEW output
- **Regulatory Search** — DuckDuckGo for standards and benchmarks
- **SQL Analytics** — query uploaded data with DuckDB

## Usage

```bash
pip install -r ../requirements.txt
streamlit run model_validation_agent.py
```

1. Enter your Gemini API key in the sidebar.
2. Select the validation focus area.
3. Upload a CSV or Excel file with model predictions vs actuals.
4. Describe the validation you need in the query box.

## Sample Questions

- "Back-test the predicted vs actual loss ratios and report all error metrics."
- "Run sensitivity analysis on the discount rate assumption from 2% to 6%."
- "Check residual normality and autocorrelation for the mortality model."
- "Is a 5% annual loss trend reasonable for commercial auto?"
- "Produce a full validation report for the pricing model."

## Standards

Follows ASOP 56 (Modeling), SR 11-7 (Model Risk Management), and ORSA principles.
