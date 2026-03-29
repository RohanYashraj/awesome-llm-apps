"""Regulatory and methodology research with web search."""

from __future__ import annotations

import json
import os
from typing import Any

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools

from config import MODEL_PRIMARY
from skills_loader import compose_agent_prompt

_RESEARCH_EXTRA = """
## Session context
Use the search tool to find **current** primary sources where possible (regulators, standard setters, professional bodies).
Cite URLs and publication dates. Synthesize—do not copy long passages.
If the tool returns JSON with `search_failed`, explain that to the user and answer from general knowledge with clear caveats (no fabricated URLs).
"""


def _ddgs_timeout() -> int:
    raw = os.environ.get("DDGS_TIMEOUT", "25")
    try:
        return max(5, int(raw.strip() or "25"))
    except ValueError:
        return 25


def _verify_ssl_from_env() -> bool:
    return os.environ.get("DDGS_VERIFY_SSL", "true").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


class RegulatoryWebSearchTools(DuckDuckGoTools):
    """
    Metasearch for the research tab: uses ddgs backend ``auto`` (rotates engines),
    disables news by default (fewer failure modes), longer timeout, env overrides.
    """

    def __init__(self, **kwargs: Any) -> None:
        merged: dict[str, Any] = {
            "backend": "auto",
            "enable_news": False,
            "timeout": _ddgs_timeout(),
            "verify_ssl": _verify_ssl_from_env(),
        }
        merged.update(kwargs)
        super().__init__(**merged)

    def web_search(self, query: str, max_results: int = 5) -> str:
        try:
            return super().web_search(query, max_results=max_results)
        except Exception as e:
            return json.dumps(
                {
                    "search_failed": True,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "hint": "ddgs rotates multiple providers; intermittent failures are common. "
                    "Retry, shorten the query, set DDGS_PROXY or HTTPS_PROXY if required, "
                    "or DDGS_VERIFY_SSL=false only if corporate SSL inspection breaks HTTPS.",
                },
                indent=2,
            )


def create_regulatory_research_agent(api_key: str) -> Agent:
    return Agent(
        model=Gemini(id=MODEL_PRIMARY, api_key=api_key),
        tools=[RegulatoryWebSearchTools()],
        system_message=compose_agent_prompt(
            ["deep-research", "academic-researcher", "fact-checker"],
            _RESEARCH_EXTRA,
        ),
        markdown=True,
    )
