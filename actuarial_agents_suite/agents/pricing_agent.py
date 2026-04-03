"""Life / health / P&C pricing and rate review."""

from agno.agent import Agent
from agno.models.google import Gemini

from config import MODEL_PRIMARY
from skills_loader import compose_prompt_for_role

_PRICING_EXTRA = """
## Session context
The user's data (if uploaded) is in DuckDB table `uploaded_data`.
- Use DuckDB SQL tools to inspect and query the data before drawing conclusions.
- Use `actuarial_loss_ratio_summary` when the user asks about loss ratios or rate adequacy.
- Use `actuarial_validation_checks` to verify required columns before analysis.
- Focus on rate indication **structure**, assumption **reasonableness**, and **documentation** — not regulatory approval.
- Structure output as: Objective / Data Summary / Method / Rate Indication / Key Assumptions / Limitations / Next Steps.
"""

_PRICING_NO_DATA = """
## Session context
No dataset is loaded in this session.
- Answer conceptually only — do not query table `uploaded_data`.
- When discussing rate indications, state required data fields and their expected format.
- Use `actuarial_loss_ratio_summary` only if the user provides inline numeric data.
- Structure output as: Approach / Data Requirements / Hypothetical Framework / Key Assumptions / Limitations.
"""


def create_pricing_agent(api_key: str, tools: list | None = None, *, has_data: bool = False) -> Agent:
    block = _PRICING_EXTRA if has_data else _PRICING_NO_DATA
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=tools or [],
        system_message=compose_prompt_for_role(
            "pricing",
            extra_block=block,
            missing_policy="skip",
        ),
        markdown=True,
    )
