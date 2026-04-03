# Actuarial Agents Suite

Self-contained practitioner **decision support** agents using [Agno](https://github.com/agno-agi/agno), **Google Gemini**, and bundled [Agent Skills](https://agentskills.io/specification) under [`skills/`](skills/README.md). **No dependency** on the parent repo's [`awesome_agent_skills/`](../awesome_agent_skills/) folder.

**This is not professional actuarial advice, legal advice, or filing-ready output.** All results require review by qualified staff and your governance process.

---

## Critical setup (read first)

| Step | Action |
|------|--------|
| **1. Python** | **3.11+** (`.python-version` pins **3.12** for [uv](https://docs.astral.sh/uv/); override if needed). |
| **2. Dependencies** | Use **[uv](https://docs.astral.sh/uv/)** only (`uv sync`). Do not rely on a sibling `awesome_agent_skills` checkout—skills live in [`skills/`](skills/). |
| **3. API key** | Get a **Google AI API key** from [Google AI Studio](https://aistudio.google.com/apikey). Copy [`.env.example`](.env.example) to **`.env`** in this folder and set **`GEMINI_API_KEY`** or **`GOOGLE_API_KEY`**, then restart the app. |
| **4. Model ID** | Default LLM is **`gemini-3.1-pro-preview`** in [`config.py`](config.py). Update `MODEL_PRIMARY` / `MODEL_FAST` if Google renames models. |
| **5. PDF export** | Uses **[Playwright](https://playwright.dev/python/)** + **headless Chromium** (Chrome's print-to-PDF). After `uv sync`, run **`uv run playwright install chromium`** once. See [PDF export](#pdf-export-playwright) below. |
| **6. Privacy** | Do **not** upload PHI, identifiable policyholder data, or confidential company figures. Prefer [`fixtures/sample_loss_triangle.csv`](fixtures/sample_loss_triangle.csv) for demos. |

---

## Install with uv

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed, then:

```bash
cd actuarial_agents_suite
uv sync
uv run playwright install chromium
```

The last line downloads the Chromium build used for **PDF export** (one-time per machine).

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

- Each **Run** opens an **Activity log** expander that updates **live** while the agent works. It shows **tool calls** (e.g. DuckDB / pandas / actuarial helpers) with arguments and results, plus **LLM request** start/completion (including token counts when the provider supplies them). A `[final_answer]` marker with wall-clock duration appears at the end.
- After at least one run, use **Download PDF (answer only)** or **Download activity log** in the **sidebar**. The PDF contains your **question** and the **agent answer** with Markdown rendered via CSS (headings, lists, tables, code). The PDF template includes **MaestrosAI** branding (header, [maestrosai.in](https://maestrosai.in) link, footer disclaimer) aligned with the app UI.

### PDF export (Playwright Chromium)

PDFs use the same **browser print pipeline** as Chrome ("Save as PDF" / print): Markdown → HTML + CSS → **headless Chromium** via [Playwright](https://playwright.dev/python/docs/api/class-page#page-pdf) `page.pdf()`. This matches how many production apps export rich HTML to PDF.

**One-time browser install** (after `uv sync`):

```bash
cd actuarial_agents_suite
uv run playwright install chromium
```

On Linux CI or minimal images you may need `uv run playwright install-deps chromium` (see [Playwright docs](https://playwright.dev/python/docs/intro#system-requirements)).

Smoke tests that generate a real PDF are **skipped** if Chromium is not installed (`pytest` reports them as skipped). Run `playwright install chromium` to enable them.

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

## Architecture

```
User question + optional data upload
            |
            v
  +---------------------+
  |  Orchestrator Agent  |  (Gemini Flash - fast routing)
  |  structured output   |
  +----------+----------+
             | OrchestratorRoute
             | primary / additional / reroute_once / confidence
             v
  +---------------------+    +---------------------+
  |  Specialist Agent    |--->|  Shared Tool Factory |
  |  (Gemini Pro)        |    |  DuckDB, Pandas,     |
  |  skills-composed     |    |  actuarial helpers    |
  |  system prompt       |    +---------------------+
  +----------+----------+
             | optional delegation to additional specialists
             | optional contradiction check via model_validation
             v
  +---------------------+
  |  Merged output +    |
  |  Activity log       |
  +---------------------+
```

### Key modules

| Module | Role |
|--------|------|
| `agents/orchestrator_agent.py` | Routes queries to specialists with confidence scoring and keyword fallback |
| `agent_profiles.py` | Declarative catalog of four specialists: tool policy, skill stack, display labels |
| `skills_loader.py` | Deterministic role-based skill stacks with senior-actuary base and supporting docs |
| `tools/factory.py` | Per-role tool sets: DuckDB/Pandas + actuarial helpers (triangle factors, BF, loss ratios, credibility, A/E, data quality) |
| `actuarial_utils/` | Pure utility functions consumed by tools and tests (no Streamlit coupling) |
| `agent_run_ui.py` | Streamed event formatting with phase labels, wall-clock timer, and `[final_answer]` marker |

### Specialists

| Agent | Skills | Tools | Data policy |
|-------|--------|-------|-------------|
| P&C Reserving | senior-practice, data-analyst, visualization, technical-writer, reserving-pc | DuckDB, Pandas, triangle factors, BF, loss ratios, validation, data quality | required |
| Pricing & rate | senior-practice, life-health-pricing, data-analyst, decision-helper, deep-research | DuckDB, Pandas, loss ratios, freq-severity, validation, data quality | optional |
| Experience study | senior-practice, experience-study, data-analyst, visualization, life-health-pricing | DuckDB, Pandas, triangle factors, loss ratios, freq-severity, credibility, A/E, validation, data quality | required |
| Model validation | senior-practice, model-validation, python-expert, code-reviewer | validation, data quality | text only |

## Layout

| Path | Purpose |
|------|---------|
| [`config.py`](config.py) | Model IDs, static reserving instructions, `.env` loading (`load_app_env`, `get_gemini_api_key_from_env`) |
| [`ui_branding.py`](ui_branding.py) | MaestrosAI-themed CSS and hero/header markup for Streamlit |
| [`skills/`](skills/) | Bundled Agent Skills (actuarial + supporting); see [`skills/README.md`](skills/README.md) |
| [`skills_loader.py`](skills_loader.py) | Central skills composer (role stacks, supporting docs, prompt assembly) |
| [`agent_profiles.py`](agent_profiles.py) | Four retained specialist profiles and tool policy |
| [`tools/factory.py`](tools/factory.py) | Shared tool construction + lightweight actuarial helper tools |
| [`actuarial_utils/`](actuarial_utils/) | Reusable pure utility functions for triangle, metrics, and validation tasks |
| [`data_utils.py`](data_utils.py) | CSV/XLSX preprocessing for DuckDB |
| [`agent_run_ui.py`](agent_run_ui.py) | Streamed Agno run events -> log text; re-exports PDF helper |
| [`pdf_export.py`](pdf_export.py) | Markdown -> HTML -> Playwright/Chromium PDF (question + answer only; no activity log) |
| [`agents/`](agents/) | Agent factories per workstream |
| [`app_streamlit.py`](app_streamlit.py) | Streamlit UI |
| [`fixtures/`](fixtures/) | Synthetic demo CSV/Markdown per tab; see [`fixtures/README.md`](fixtures/README.md) |
| [`pyproject.toml`](pyproject.toml) / [`uv.lock`](uv.lock) | Dependencies (uv) |

## Implementation notes

- Streamlit includes one **orchestrated copilot** entry tab plus direct specialist tabs for reserving, pricing, experience study, and model validation.
- The orchestrator uses `st.status()` for phased progress updates and renders a routing info card before the answer.
- Actuarial-specific skills were moved out of the shared [`awesome_agent_skills/`](../awesome_agent_skills/) catalog into this repo's **`skills/`** so this directory can be copied or published **standalone**.

---

## Troubleshooting

- **`FileNotFoundError` for a skill** — Confirm `skills/<skill-name>/SKILL.md` exists; reinstall from a clean clone if files are missing.
- **Gemini / model errors** — Check `MODEL_PRIMARY` in `config.py` against [AI Studio](https://aistudio.google.com/).
- **Excel upload fails** — `openpyxl` is included via `uv sync`.
- **PDF build failed / Chromium / Playwright** — Run **`uv run playwright install chromium`** from `actuarial_agents_suite` (see [PDF export (Playwright Chromium)](#pdf-export-playwright)). The sidebar surfaces a short hint if the browser is missing.

---

## License

Same as the parent [awesome-llm-apps](../LICENSE) repository unless you add a separate license here.
