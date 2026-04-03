"""Experience studies: segmentation, credibility narrative, visualization plan."""

from agno.agent import Agent
from agno.models.google import Gemini

from config import MODEL_PRIMARY
from skills_loader import compose_prompt_for_role

_EXPERIENCE_WITH_DATA = """
## Session context
Uploaded data is in DuckDB table `uploaded_data`.
- Use DuckDB SQL tools first to inspect column names, row counts, and exposure totals.
- Use `actuarial_triangle_factors` if the data includes development triangles.
- Use `actuarial_loss_ratio_summary` for frequency/severity or loss ratio diagnostics.
- Use `actuarial_validation_checks` to verify expected columns before running analysis.
- Help with **credible segments**, **volume vs. volatility** trade-offs, and **visualization plans**.
- Do not claim a single "correct" segmentation without stating trade-offs and credibility implications.
- Structure output as: Study Design / Data Summary / A/E Results / Credibility / Segmentation / Recommendations / Limitations.
"""

_EXPERIENCE_NO_DATA = """
## Session context
No dataset is loaded in this session.
- Provide a conceptual study design with required data fields and their expected format.
- Discuss segmentation strategy, credibility standards, and expected basis selection.
- Structure output as: Study Objectives / Data Requirements / Methodology / Segmentation Strategy / Credibility Approach / Limitations.
"""


def create_experience_study_agent(api_key: str, tools: list | None = None, *, has_data: bool = True) -> Agent:
    context_block = _EXPERIENCE_WITH_DATA if has_data else _EXPERIENCE_NO_DATA
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=tools or [],
        system_message=compose_prompt_for_role(
            "experience_study",
            extra_block=context_block,
            missing_policy="skip",
        ),
        markdown=True,
    )
