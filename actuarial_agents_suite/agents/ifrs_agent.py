"""IFRS 17 / reporting narrative and high-level capital & risk communication."""

from agno.agent import Agent
from agno.models.google import Gemini

from config import MODEL_PRIMARY
from skills_loader import compose_agent_prompt

_IFRS_EXTRA = """
## Session context
Explain **concepts** and **questions for accounting / risk** teams. Never assert compliance, audit outcomes,
or firm-specific capital figures. For ORSA-style narrative, structure scenarios and governance discussion at a high level.
"""


def create_ifrs_reporting_agent(api_key: str) -> Agent:
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=[],
        system_message=compose_agent_prompt(
            [
                "actuarial-ifrs17-solvency",
                "technical-writer",
                "fact-checker",
                "strategy-advisor",
            ],
            _IFRS_EXTRA,
        ),
        markdown=True,
    )
