# Actuarial Agents Suite

A collection of **Gemini-powered AI agents** for actuarial work — P&C pricing, claims reserving, model validation, and experience studies.

There is **no shared package or lockfile** at this level: each agent folder is a complete mini-project (`pyproject.toml`, `uv.lock`, `requirements.txt`, `.python-version`, `skills/`, `tools.py`, Streamlit app).

## Agents

| Agent | Folder |
|-------|--------|
| P&C Pricing | [pc_pricing_agent/](pc_pricing_agent/) |
| P&C Reserving | [pc_reserving_agent/](pc_reserving_agent/) |
| Model Validation | [model_validation_agent/](model_validation_agent/) |
| Experience Study | [experience_agent/](experience_agent/) |

Each folder has its own **README** with features, standards, and run instructions.

## Quick start

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
2. Open the agent you want, install deps, run Streamlit:

```bash
cd actuarial_agents_suite/pc_pricing_agent   # or another agent folder
uv sync                                      # or: pip install -r requirements.txt
streamlit run pc_pricing_agent.py            # use that agent’s entry script name
```

Entry scripts: `pc_pricing_agent.py`, `pc_reserving_agent.py`, `model_validation_agent.py`, `experience_agent.py`.

From the **monorepo root** (after installing in the agent folder as above), you can still launch with a path:

```bash
streamlit run actuarial_agents_suite/pc_pricing_agent/pc_pricing_agent.py
```

Use the same pattern for the other three agents.

## Layout

```
actuarial_agents_suite/
├── README.md                 # This file — index only
├── pc_pricing_agent/         # Self-contained project
├── pc_reserving_agent/
├── model_validation_agent/
└── experience_agent/
```

Shared behavior across agents:

- **Gemini** (`gemini-3.1-pro-preview`) via `agno.models.google.Gemini`
- **DuckDB** + **Pandas** on uploaded CSV/Excel
- **Domain tools** in `tools.py`
- **`skills/<name>/SKILL.md`** merged into the system prompt at runtime

## Standards (summary)

CAS / SOA practice areas and ASOPs 13, 25, 30, 35, 43, 56; SR 11-7 where relevant — see each agent README.

## Disclaimer

For **education and analysis** only. Have a qualified actuary review outputs before filings or business use.
