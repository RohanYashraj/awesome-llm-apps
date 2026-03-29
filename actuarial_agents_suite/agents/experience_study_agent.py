"""Experience studies: segmentation, credibility narrative, visualization plan."""

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

from config import MODEL_PRIMARY
from skills_loader import compose_agent_prompt

_EXPERIENCE_EXTRA = """
## Session context
Uploaded data is in `uploaded_data`. Help with **credible segments**, **volume vs. volatility** trade-offs,
and **charts** to diagnose experience—without claiming a single “correct” segmentation without business judgment.
"""


def create_experience_study_agent(api_key: str, duckdb_tools: DuckDbTools) -> Agent:
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=[duckdb_tools, PandasTools()],
        system_message=compose_agent_prompt(
            ["data-analyst", "visualization-expert", "actuarial-life-health-pricing"],
            _EXPERIENCE_EXTRA,
        ),
        markdown=True,
    )
