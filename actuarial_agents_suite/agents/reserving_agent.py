"""P&C reserving assistant."""

from agno.agent import Agent
from agno.models.google import Gemini

from config import MODEL_PRIMARY
from skills_loader import compose_prompt_for_role

_RESERVING_WITH_DATA = """
## Session context
Uploaded data is available in DuckDB table `uploaded_data`.
- Use DuckDB SQL tools first to inspect column names and row counts before analysis.
- Use the `actuarial_triangle_factors` tool when the user provides or asks about cumulative triangles.
- Use `actuarial_validation_checks` to verify required columns exist before running queries.
- Always cite specific columns and filters used in any numeric conclusion.
- Structure output as: Data Summary / Diagnostics / Method Options / Assumptions / Limitations / Next Steps.
"""

_RESERVING_NO_DATA = """
## Session context
No dataset is loaded in this run.
- Provide conceptual reserving guidance grounded in industry practice.
- Explicitly list required data fields and their expected format for implementation.
- When discussing methods, state the data requirements for each (e.g. BF needs an a priori loss ratio and earned premium).
- Structure output as: Approach / Data Requirements / Method Options / Key Assumptions / Limitations.
"""


def create_reserving_agent(
    api_key: str,
    tools: list | None = None,
    has_data: bool = False,
) -> Agent:
    """Build the reserving agent."""
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=tools or [],
        system_message=compose_prompt_for_role(
            "reserving",
            extra_block=_RESERVING_WITH_DATA if has_data else _RESERVING_NO_DATA,
            missing_policy="skip",
        ),
        markdown=True,
    )
