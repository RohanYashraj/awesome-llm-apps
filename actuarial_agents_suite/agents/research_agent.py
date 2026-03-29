"""Regulatory and methodology research with web search."""

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

from config import MODEL_PRIMARY
from skills_loader import compose_agent_prompt

_RESEARCH_EXTRA = """
## Session context
Use the search tool to find **current** primary sources where possible (regulators, standard setters, professional bodies).
Cite URLs and publication dates. Synthesize—do not copy long passages.
"""


def create_regulatory_research_agent(api_key: str) -> Agent:
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=[DuckDuckGoTools()],
        system_message=compose_agent_prompt(
            ["deep-research", "academic-researcher", "fact-checker"],
            _RESEARCH_EXTRA,
        ),
        markdown=True,
    )
