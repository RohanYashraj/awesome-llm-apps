"""Model validation copilot — documentation and code review support."""

from agno.agent import Agent
from agno.models.google import Gemini

from config import MODEL_PRIMARY
from skills_loader import compose_prompt_for_role

_VALIDATION_EXTRA = """
## Session context
The user may paste **model change text**, **test plans**, or **code**.
- Use `actuarial_validation_checks` when the user describes required fields or assumptions to check.
- Provide a structured validation checklist with Pass / Needs attention / N/A for each dimension.
- For code, provide concrete review notes covering reproducibility, edge cases, and security.
- Do not certify independence or audit sign-off.
- Structure output as: Scope / Data Validation / Assumption Review / Methodology Check / Implementation Review / Governance / Recommendations.
"""


def create_validation_agent(api_key: str, tools: list | None = None) -> Agent:
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=tools or [],
        system_message=compose_prompt_for_role(
            "model_validation",
            extra_block=_VALIDATION_EXTRA,
            missing_policy="skip",
        ),
        markdown=True,
    )
