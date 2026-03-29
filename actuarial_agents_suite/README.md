# Actuarial Agents Suite

Self-contained practitioner **decision support** agents using [Agno](https://github.com/agno-agi/agno), **Google Gemini**, and bundled [Agent Skills](https://agentskills.io/specification) under [`skills/`](skills/README.md). **No dependency** on the parent repo’s [`awesome_agent_skills/`](../awesome_agent_skills/) folder.

**This is not professional actuarial advice, legal advice, or filing-ready output.** All results require review by qualified staff and your governance process.

---

## Critical setup (read first)

| Step | Action |
|------|--------|
| **1. Python** | **3.11+** (`.python-version` pins **3.12** for [uv](https://docs.astral.sh/uv/); override if needed). |
| **2. Dependencies** | Use **[uv](https://docs.astral.sh/uv/)** only (`uv sync`). Do not rely on a sibling `awesome_agent_skills` checkout—skills live in [`skills/`](skills/). |
| **3. API key** | Get a **Google AI API key** from [Google AI Studio](https://aistudio.google.com/apikey). Paste in the Streamlit sidebar (session only) or set `GOOGLE_API_KEY` if your tooling reads it. |
| **4. Model ID** | Default LLM is **`gemini-3.1-pro-preview`** in [`config.py`](config.py). Update `MODEL_PRIMARY` / `MODEL_FAST` if Google renames models. |
| **5. Regulatory research tab** | Requires the **`ddgs`** package (declared in `pyproject.toml`) for DuckDuckGo search via Agno. |
| **6. Privacy** | Do **not** upload PHI, identifiable policyholder data, or confidential company figures. Prefer [`fixtures/sample_loss_triangle.csv`](fixtures/sample_loss_triangle.csv) for demos. |

---

## Install with uv

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed, then:

```bash
cd actuarial_agents_suite
uv sync
```

Include dev tools (e.g. pytest):

```bash
uv sync --group dev
```

This creates/uses `.venv` in this directory and installs from **`pyproject.toml`** + **`uv.lock`**.

---

## Run the app

```bash
cd actuarial_agents_suite
uv run streamlit run app_streamlit.py
```

Or activate the venv uv created:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
streamlit run app_streamlit.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

### Activity log and PDF export

- Each **Run** opens an **Activity log** expander that updates **live** while the agent works. It shows **tool calls** (e.g. DuckDB / pandas) with arguments and results, plus **LLM request** start/completion (including token counts when the provider supplies them).
- After at least one run, use **Download PDF (answer + activity log)** at the **bottom of the sidebar** (scroll down; it appears there after your run completes).

---

## Verify install (no API call)

```bash
cd actuarial_agents_suite
uv run python -c "from skills_loader import compose_reserving_system_prompt; print('OK, prompt length:', len(compose_reserving_system_prompt()))"
```

You should see a large prompt length. Skills are read from **`skills/`** inside this folder.

### Automated smoke tests

```bash
cd actuarial_agents_suite
uv sync --group dev
uv run pytest tests/test_smoke.py -q
```

---

## Layout

| Path | Purpose |
|------|---------|
| [`config.py`](config.py) | Model IDs and static reserving instructions |
| [`skills/`](skills/) | Bundled Agent Skills (actuarial + supporting); see [`skills/README.md`](skills/README.md) |
| [`skills_loader.py`](skills_loader.py) | Loads `skills/<name>/SKILL.md` |
| [`data_utils.py`](data_utils.py) | CSV/XLSX preprocessing for DuckDB |
| [`agent_run_ui.py`](agent_run_ui.py) | Streamed Agno run events → log text; PDF export |
| [`agents/`](agents/) | Agent factories per workstream |
| [`app_streamlit.py`](app_streamlit.py) | Streamlit UI |
| [`fixtures/`](fixtures/) | Sample non-sensitive data |
| [`pyproject.toml`](pyproject.toml) / [`uv.lock`](uv.lock) | Dependencies (uv) |

---

## Implementation notes

- **Phase 1–3:** Streamlit tabs for reserving, pricing, experience study, model validation, pension, IFRS/risk narrative, regulatory research—see [`agents/`](agents/).
- Actuarial-specific skills were moved out of the shared [`awesome_agent_skills/`](../awesome_agent_skills/) catalog into this repo’s **`skills/`** so this directory can be copied or published **standalone**.

---

## Troubleshooting

- **`FileNotFoundError` for a skill** — Confirm `skills/<skill-name>/SKILL.md` exists; reinstall from a clean clone if files are missing.
- **Gemini / model errors** — Check `MODEL_PRIMARY` in `config.py` against [AI Studio](https://aistudio.google.com/).
- **Excel upload fails** — `openpyxl` is included via `uv sync`.

---

## License

Same as the parent [awesome-llm-apps](../LICENSE) repository unless you add a separate license here.
