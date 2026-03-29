"""Pension and OPEB communication assistant."""

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

from config import MODEL_PRIMARY
from skills_loader import compose_agent_prompt

_PENSION_EXTRA = """
## Session context
If liability or member data is uploaded, it is in `uploaded_data`. Otherwise answer conceptually.
Emphasize **assumption sensitivities** and clear definitions—avoid jurisdiction-specific assertions without sources.
"""


def create_pension_agent(api_key: str, duckdb_tools: DuckDbTools | None) -> Agent:
    tools = [duckdb_tools, PandasTools()] if duckdb_tools is not None else []
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=tools,
        system_message=compose_agent_prompt(
            ["actuarial-pension-benefits", "visualization-expert", "decision-helper"],
            _PENSION_EXTRA,
        ),
        markdown=True,
    )
