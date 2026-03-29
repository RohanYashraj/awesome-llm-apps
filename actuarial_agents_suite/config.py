"""Central configuration for models and static instruction blocks.

Change `MODEL_PRIMARY` here if Google renames preview models in AI Studio.
"""

from __future__ import annotations

import os
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent


def load_app_env() -> None:
    """Load `.env` from the actuarial_agents_suite directory (optional)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(_APP_DIR / ".env", override=False)


def get_gemini_api_key_from_env() -> str | None:
    """First non-empty value among common env var names (Google AI / Gemini)."""
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_AI_API_KEY"):
        v = os.environ.get(name, "").strip()
        if v:
            return v
    return None


# Gemini model IDs (see https://aistudio.google.com/ for current names)
MODEL_PRIMARY = "gemini-3.1-pro-preview"
MODEL_FAST = "gemini-3-flash-preview"

# Core reserving instructions used until / alongside loaded Agent Skills (see skills_loader).
RESERVING_CORE_INSTRUCTIONS = """
## Actuarial reserving context (P&C)

You support **property and casualty actuaries** analyzing **loss triangles** and related data.
The user's data is loaded as DuckDB table `uploaded_data` (from their CSV/Excel).

**Your role**
- Help interpret development patterns, suggest appropriate **deterministic** methods conceptually
  (e.g. chain ladder, Bornhuetter–Ferguson, Cape Cod, Mack standard errors) and explain **assumptions**.
- Use DuckDB tools to query aggregates and Pandas tools when vectorized manipulation helps.
- Recommend **visualizations** (e.g. loss development by period, heatmaps of link ratios) and describe what to look for.
- Draft **assumption language** and **reconciliation narrative** to prior estimates when the user asks—clearly label
  anything that requires **sign-off by a qualified actuary** and **company governance**.

**Guardrails**
- Do not claim regulatory, audit, or statutory filing approval. Outputs are **decision support** only.
- If data is incomplete or ambiguous (missing tail, mixed lines, salvage/subro not separated), **say so** and list options.
- Never invent numeric ultimate reserves without running tools on the user's data; show reasoning and cite which columns you used.
"""
