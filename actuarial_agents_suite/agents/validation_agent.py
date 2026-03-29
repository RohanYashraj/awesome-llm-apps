"""Model validation copilot — documentation and code review support."""

from agno.agent import Agent
from agno.models.google import Gemini

from config import MODEL_PRIMARY
from skills_loader import compose_agent_prompt

_VALIDATION_EXTRA = """
## Session context
The user may paste **model change text**, **test plans**, or **code**. Provide structured validation checklists
and concrete code review notes. Do not certify independence or audit sign-off.
"""


def create_validation_agent(api_key: str) -> Agent:
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=[],
        system_message=compose_agent_prompt(
            ["actuarial-model-validation", "python-expert", "code-reviewer"],
            _VALIDATION_EXTRA,
        ),
        markdown=True,
    )
