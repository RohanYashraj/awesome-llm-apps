# Actuarial Agents Suite

A collection of **Gemini-powered AI agents** purpose-built for actuarial work — P&C pricing, claims reserving, model validation, and experience studies.

Each agent combines Google's Gemini LLM with domain-specific actuarial tools, DuckDB for SQL analytics, Pandas for data manipulation, and a Streamlit UI for interactive analysis.

## Agents

| Agent | Description | Key Tools |
|-------|-------------|-----------|
| [P&C Pricing](pc_pricing_agent/) | Loss ratios, indicated rate changes, trending, pure premiums, large-loss caps | `compute_loss_ratio`, `compute_indicated_rate_change`, `trending_factors`, `compute_pure_premium`, `large_loss_cap_analysis` |
| [P&C Reserving](pc_reserving_agent/) | Development triangles, Chain Ladder, Bornhuetter-Ferguson, IBNR, Mack uncertainty | `build_triangle`, `chain_ladder`, `bornhuetter_ferguson`, `compute_ibnr`, `mack_method_std_error` |
| [Model Validation](model_validation_agent/) | Back-testing, sensitivity analysis, residual diagnostics, assumption review, validation reports | `back_test`, `sensitivity_analysis`, `residual_diagnostics`, `assumption_reasonableness_check`, `generate_validation_report` |
| [Experience Study](experience_agent/) | A/E ratios, credibility, rate graduation, decrement rates, trend analysis | `actual_to_expected`, `credibility_weight`, `whittaker_henderson_graduation`, `compute_decrement_rates`, `trend_analysis` |

## Quick Start

### 1. Install dependencies

```bash
pip install -r actuarial_agents_suite/requirements.txt
```

### 2. Get a Gemini API key

Sign up at [Google AI Studio](https://aistudio.google.com/apikey) and copy your API key.

### 3. Launch an agent

```bash
# Hub page (overview and navigation)
streamlit run actuarial_agents_suite/app_streamlit.py

# Individual agents
streamlit run actuarial_agents_suite/pc_pricing_agent/pc_pricing_agent.py
streamlit run actuarial_agents_suite/pc_reserving_agent/pc_reserving_agent.py
streamlit run actuarial_agents_suite/model_validation_agent/model_validation_agent.py
streamlit run actuarial_agents_suite/experience_agent/experience_agent.py
```

### 4. Upload data and ask questions

Each agent accepts CSV or Excel files. Enter your Gemini API key in the sidebar, upload your data, and type a question in the query box.

## Architecture

```
actuarial_agents_suite/
├── app_streamlit.py              # Hub page
├── requirements.txt              # Shared dependencies
├── pc_pricing_agent/
│   ├── pc_pricing_agent.py       # Streamlit + Agno agent
│   └── tools.py                  # Actuarial pricing tools
├── pc_reserving_agent/
│   ├── pc_reserving_agent.py
│   └── tools.py                  # Reserving tools (chain ladder, BF, etc.)
├── model_validation_agent/
│   ├── model_validation_agent.py
│   └── tools.py                  # Validation tools (back-test, sensitivity, etc.)
├── experience_agent/
│   ├── experience_agent.py
│   └── tools.py                  # Experience study tools (A/E, credibility, etc.)
└── skills/
    ├── pc-pricing/SKILL.md       # Agent skill definitions
    ├── pc-reserving/SKILL.md
    ├── model-validation/SKILL.md
    └── experience-study/SKILL.md
```

All agents use:
- **Gemini** (`gemini-3.1-pro-preview`) via `agno.models.google.Gemini`
- **DuckDB** for SQL queries on uploaded data
- **Pandas** for data manipulation
- **Custom Python tools** for domain-specific actuarial calculations
- **Streamlit** for the interactive UI

## Standards and References

These agents are informed by actuarial professional standards:

- **CAS** — Casualty Actuarial Society ratemaking and reserving principles
- **SOA** — Society of Actuaries experience study methodology
- **ASOP 13** — Trending Procedures in Property/Casualty Insurance
- **ASOP 25** — Credibility Procedures
- **ASOP 30** — Treatment of Profit and Contingency Provisions
- **ASOP 35** — Selection of Demographic Assumptions
- **ASOP 43** — Unpaid Claim Estimates
- **ASOP 56** — Modeling
- **SR 11-7** — Federal Reserve model risk management guidance

## Disclaimer

This suite is for **educational and analytical purposes**. All outputs should be reviewed by a qualified actuary before use in regulatory filings, financial reporting, or business decisions.
