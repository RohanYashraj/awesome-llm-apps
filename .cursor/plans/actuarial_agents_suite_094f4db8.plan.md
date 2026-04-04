---
name: Actuarial Agents Suite
overview: Create a standalone `actuarial_agents_suite/` directory containing four Gemini-powered actuarial agents (P&C Pricing, P&C Reserving, Model Validation, Experience Study) with custom domain tools, Streamlit UI, and actuarial-specific SKILL.md files, following the patterns established across the repository.
todos:
  - id: create-structure
    content: Create actuarial_agents_suite/ directory structure with all subdirectories and __init__.py files
    status: completed
  - id: requirements
    content: Create shared requirements.txt with Gemini/Agno/Streamlit/Pandas/NumPy/SciPy dependencies
    status: completed
  - id: pc-pricing-tools
    content: Build pc_pricing_agent/tools.py with loss ratio, rate indication, trending, pure premium, large loss tools
    status: completed
  - id: pc-pricing-agent
    content: Build pc_pricing_agent/pc_pricing_agent.py -- Agno+Gemini agent with Streamlit UI, DuckDB/Pandas + custom pricing tools
    status: completed
  - id: pc-reserving-tools
    content: Build pc_reserving_agent/tools.py with chain ladder, BF, IBNR, triangle, Mack std error tools
    status: completed
  - id: pc-reserving-agent
    content: Build pc_reserving_agent/pc_reserving_agent.py -- Agno+Gemini agent with Streamlit UI for triangle analysis
    status: completed
  - id: model-validation-tools
    content: Build model_validation_agent/tools.py with back-test, sensitivity, residual, assumption check tools
    status: completed
  - id: model-validation-agent
    content: Build model_validation_agent/model_validation_agent.py -- Agno+Gemini agent with Streamlit UI for model validation
    status: completed
  - id: experience-tools
    content: Build experience_agent/tools.py with A/E ratio, credibility, graduation, decrement, trend tools
    status: completed
  - id: experience-agent
    content: Build experience_agent/experience_agent.py -- Agno+Gemini agent with Streamlit UI for experience studies
    status: completed
  - id: skills
    content: Create 4 SKILL.md files under skills/ for pc-pricing, pc-reserving, model-validation, experience-study
    status: completed
  - id: hub-app
    content: Build app_streamlit.py -- unified multi-page Streamlit hub navigating to all 4 agents
    status: completed
  - id: readme
    content: Create suite-level README.md and per-agent README.md files
    status: completed
  - id: update-refs
    content: Update awesome_agent_skills/README.md links if needed to point to the new suite
    status: completed
isProject: false
---

# Actuarial Agents Suite

## Context and Repository Patterns

The repository is organized as a monorepo of ~100+ LLM app projects grouped by category. The dominant patterns are:

- **Framework**: Agno (`agno.agent.Agent`, `agno.team.Team`) -- used in ~70% of projects
- **LLM**: Gemini via `agno.models.google.Gemini` -- already used in `ai_data_analysis_agent`, `gemini_agentic_rag`, `agentic_rag_with_reasoning`, `ai_medical_imaging_agent`, etc.
- **UI**: Streamlit -- used in nearly all projects
- **Data tools**: `agno.tools.duckdb.DuckDbTools` + `agno.tools.pandas.PandasTools` for tabular work
- **Alternative**: Google ADK (`google.adk.agents.LlmAgent`, `SequentialAgent`) -- used in `ai_vc_due_diligence_agent_team`, `ai_financial_coach_agent`, `ai_consultant_agent`
- **Skills**: `SKILL.md` files with YAML frontmatter in `awesome_agent_skills/`

Key reference implementations for this work:
- [`starter_ai_agents/ai_data_analysis_agent/ai_data_analyst.py`](starter_ai_agents/ai_data_analysis_agent/ai_data_analyst.py) -- Agno + Gemini + DuckDB/Pandas + Streamlit (closest template for data-heavy agents)
- [`starter_ai_agents/ai_life_insurance_advisor_agent/life_insurance_advisor_agent.py`](starter_ai_agents/ai_life_insurance_advisor_agent/life_insurance_advisor_agent.py) -- Insurance domain agent with E2B code execution + custom math
- [`advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent/ai_financial_coach_agent.py`](advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent/ai_financial_coach_agent.py) -- Google ADK SequentialAgent with Pydantic models, CSV upload, Plotly charts
- [`advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team/agent.py`](advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team/agent.py) -- ADK multi-stage pipeline with custom tools and chart generation

The `actuarial_agents_suite/` directory is already referenced in [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json) (line 9, 22) and [`awesome_agent_skills/README.md`](awesome_agent_skills/README.md) (line 58) but does not yet exist on disk.

## Architecture Decision

Use **Agno + Gemini** (not Google ADK) because:
- It is the dominant pattern in the repo for Gemini-based agents
- Simpler, more consistent with the existing project style
- Built-in DuckDB/Pandas tools for tabular actuarial data
- Streamlit integration is straightforward
- Each agent gets custom Python tool functions for domain-specific calculations

## Directory Structure

```
actuarial_agents_suite/
├── README.md                         # Suite overview, setup, usage
├── requirements.txt                  # Shared dependencies
├── app_streamlit.py                  # Unified hub app (multi-page nav)
├── pc_pricing_agent/
│   ├── pc_pricing_agent.py           # Streamlit app + Agno agent
│   ├── tools.py                      # Loss ratio, rate adequacy, exposure tools
│   └── README.md
├── pc_reserving_agent/
│   ├── pc_reserving_agent.py         # Streamlit app + Agno agent
│   ├── tools.py                      # Chain ladder, BF, IBNR, triangle tools
│   └── README.md
├── model_validation_agent/
│   ├── model_validation_agent.py     # Streamlit app + Agno agent
│   ├── tools.py                      # Back-testing, sensitivity, residual tools
│   └── README.md
├── experience_agent/
│   ├── experience_agent.py           # Streamlit app + Agno agent
│   ├── tools.py                      # A/E ratio, credibility, graduation tools
│   └── README.md
└── skills/
    ├── pc-pricing/SKILL.md
    ├── pc-reserving/SKILL.md
    ├── model-validation/SKILL.md
    └── experience-study/SKILL.md
```

## Agent Specifications

### 1. P&C Pricing Agent (`pc_pricing_agent/`)

**Purpose**: Property & Casualty insurance pricing analysis -- loss ratio analysis, rate adequacy testing, indicated rate changes, exposure/premium trending, class plan relativities.

**Model**: `Gemini(id="gemini-3.1-flash-lite-preview")`

**Tools**:
- `DuckDbTools` + `PandasTools` (from Agno) for data exploration
- Custom `tools.py`:
  - `compute_loss_ratio(earned_premium, incurred_losses, lae)` -- basic/adjusted loss ratios
  - `compute_indicated_rate_change(target_lr, actual_lr, expense_ratio, profit_margin)` -- (actual / target - 1) rate indication
  - `trending_factors(annual_trend_rate, months_from_avg_written, months_from_avg_earned)` -- on-level / trend factors
  - `compute_pure_premium(losses, exposures)` -- pure premium by class
  - `large_loss_cap_analysis(losses_df, threshold_percentile)` -- cap/truncate large losses

**UI**: Streamlit -- upload loss/premium CSV/Excel, sidebar for API key, query box to ask pricing questions, results as tables + markdown.

**Pattern base**: Adapted from `ai_data_analysis_agent` with actuarial system prompt and custom pricing tools.

### 2. P&C Reserving Agent (`pc_reserving_agent/`)

**Purpose**: Claims reserving -- development triangle analysis, chain ladder method, Bornhuetter-Ferguson method, IBNR estimation, reserve adequacy assessment.

**Model**: `Gemini(id="gemini-3.1-flash-lite-preview")`

**Tools**:
- `DuckDbTools` + `PandasTools` for triangle data
- Custom `tools.py`:
  - `build_triangle(claims_df, origin_col, dev_col, value_col)` -- pivot claims data into development triangle
  - `chain_ladder(triangle, tail_factor)` -- weighted-average LDFs, cumulative development, ultimate losses
  - `bornhuetter_ferguson(triangle, expected_loss_ratios, earned_premiums)` -- BF method ultimates
  - `compute_ibnr(ultimate_losses, paid_to_date)` -- IBNR = ultimate - paid
  - `mack_method_std_error(triangle)` -- Mack's standard error for reserve uncertainty

**UI**: Streamlit -- upload triangle CSV, select method (chain ladder / BF / both), display development factors table, ultimate losses, IBNR summary, optional plot of triangle development.

**Pattern base**: Adapted from `ai_data_analysis_agent` with reserving-specific system prompt and triangle tools.

### 3. Model Validation Agent (`model_validation_agent/`)

**Purpose**: Validate actuarial models -- back-testing, assumption validation, sensitivity analysis, residual diagnostics, regulatory compliance checks, model governance documentation.

**Model**: `Gemini(id="gemini-3.1-flash-lite-preview")`

**Tools**:
- `DuckDbTools` + `PandasTools`
- `DuckDuckGoTools` for regulatory/standards research
- Custom `tools.py`:
  - `back_test(predicted, actual)` -- compute error metrics (MAE, RMSE, MAPE, bias)
  - `sensitivity_analysis(base_result, parameter_name, perturbations)` -- vary parameters +/- X% and measure output change
  - `residual_diagnostics(predicted, actual)` -- mean residual, std, normality test (Shapiro-Wilk), auto-correlation
  - `assumption_reasonableness_check(assumption_name, value, industry_range)` -- flag assumptions outside industry norms
  - `generate_validation_report(results_dict)` -- structured JSON/markdown validation report

**UI**: Streamlit -- upload model predictions vs actuals CSV, sidebar options for validation type, results in tabs (Back-testing, Sensitivity, Residuals, Report).

**Pattern base**: Hybrid of `ai_consultant_agent` (structured analysis + report generation) and `ai_data_analysis_agent` (data tools).

### 4. Experience Agent (`experience_agent/`)

**Purpose**: Experience studies -- actual-to-expected (A/E) analysis, mortality/morbidity/lapse rate studies, credibility weighting, experience graduation, trend analysis.

**Model**: `Gemini(id="gemini-3.1-flash-lite-preview")`

**Tools**:
- `DuckDbTools` + `PandasTools`
- Custom `tools.py`:
  - `actual_to_expected(actual_claims, expected_claims)` -- A/E ratio overall and by segment
  - `credibility_weight(observed_claims, full_credibility_standard, method)` -- limited fluctuation or Buhlmann credibility
  - `whittaker_henderson_graduation(raw_rates, smoothing_order, smoothing_weight)` -- graduated rates
  - `compute_decrement_rates(exposures, decrements)` -- qx/lapse/withdrawal rates
  - `trend_analysis(rates_by_period)` -- linear/log-linear fit for trend detection

**UI**: Streamlit -- upload experience data CSV, select study type (mortality/lapse/morbidity), display A/E ratios, credibility measures, graduated rates, trend charts.

**Pattern base**: Adapted from `ai_data_analysis_agent` with experience study system prompt and tools.

### 5. Unified Hub App (`app_streamlit.py`)

A top-level Streamlit multi-page app that provides navigation to all four agents. Uses `st.navigation` or a sidebar selector to route to individual agent pages.

### 6. Actuarial Skills (`skills/`)

Four `SKILL.md` files following the same YAML frontmatter + markdown format used in `awesome_agent_skills/`:
- `pc-pricing/SKILL.md` -- P&C pricing expertise, triggers, competencies
- `pc-reserving/SKILL.md` -- Reserving methods, triangle analysis, IBNR
- `model-validation/SKILL.md` -- Validation frameworks, back-testing, regulatory
- `experience-study/SKILL.md` -- A/E analysis, credibility, graduation

### 7. Cross-cutting Concerns

- **All agents** use `agno.models.google.Gemini` -- no OpenAI/Anthropic dependencies
- **requirements.txt** shared at suite root: `streamlit`, `agno>=2.2.10`, `pandas`, `numpy`, `scipy` (for statistical tests), `duckduckgo-search`
- **System prompts** are actuarial-domain-specific, instructing the agent about insurance terminology, regulatory context, and professional standards (CAS, SOA, ASOP)
- **README.md** documents setup, API key requirements (Google AI Studio), and per-agent usage
