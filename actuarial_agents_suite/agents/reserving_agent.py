"""P&C reserving assistant — DuckDB + Pandas tools, Gemini Pro."""

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

from config import MODEL_PRIMARY
from skills_loader import compose_reserving_system_prompt


def create_reserving_agent(
    api_key: str,
    duckdb_tools: DuckDbTools,
    *,
    extra_skills: list[str] | None = None,
) -> Agent:
    """Build the reserving agent. Optional `extra_skills` are skill directory names under awesome_agent_skills."""
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=[duckdb_tools, PandasTools()],
        system_message=compose_reserving_system_prompt(extra_skill_dirs=extra_skills),
        markdown=True,
    )
