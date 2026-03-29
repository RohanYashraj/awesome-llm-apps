"""Life / health / P&C pricing and rate review."""

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

from config import MODEL_PRIMARY
from skills_loader import compose_agent_prompt

_PRICING_EXTRA = """
## Session context
The user's data (if uploaded) is in DuckDB table `uploaded_data`. Use SQL via DuckDB tools and pandas as needed.
Focus on rate indication **structure**, assumption **reasonableness**, and **documentation**—not regulatory approval.
"""

_PRICING_NO_DATA = _PRICING_EXTRA + """
**No dataset loaded:** answer conceptually only—do not query table `uploaded_data`.
"""


def create_pricing_agent(api_key: str, duckdb_tools: DuckDbTools | None) -> Agent:
    if duckdb_tools is not None:
        tools = [duckdb_tools, PandasTools()]
        block = _PRICING_EXTRA
    else:
        tools = [PandasTools()]
        block = _PRICING_NO_DATA
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=tools,
        system_message=compose_agent_prompt(
            ["actuarial-life-health-pricing", "decision-helper", "deep-research"],
            block,
        ),
        markdown=True,
    )
