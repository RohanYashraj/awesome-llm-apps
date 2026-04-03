"""Agno-native orchestrator for routing actuarial prompts."""

from __future__ import annotations

import json
from typing import Literal

from agno.agent import Agent
from agno.models.google import Gemini
from pydantic import BaseModel, Field

from config import MODEL_FAST

AgentKey = Literal["reserving", "pricing", "experience_study", "model_validation"]

_AGENT_LABELS: dict[str, str] = {
    "reserving": "P&C Reserving",
    "pricing": "Pricing & rate",
    "experience_study": "Experience study",
    "model_validation": "Model validation",
}


class OrchestratorRoute(BaseModel):
    primary_agent: AgentKey
    additional_agents: list[AgentKey] = Field(default_factory=list)
    reroute_once: bool = False
    refined_query: str | None = None
    rationale: str = ""
    confidence: Literal["high", "medium", "low"] = "medium"

    @property
    def primary_label(self) -> str:
        return _AGENT_LABELS.get(self.primary_agent, self.primary_agent)

    @property
    def additional_labels(self) -> list[str]:
        return [_AGENT_LABELS.get(k, k) for k in self.additional_agents]

    def summary_lines(self) -> list[str]:
        lines = [
            f"[route] primary={self.primary_label} ({self.primary_agent})",
            f"[route] confidence={self.confidence}",
        ]
        if self.additional_agents:
            lines.append(f"[route] additional={', '.join(self.additional_labels)}")
        if self.reroute_once:
            lines.append("[route] quality_gate=reroute_once (under-specified request)")
        if self.rationale:
            lines.append(f"[route] rationale={self.rationale}")
        if self.refined_query:
            lines.append(f"[route] refined_query={self.refined_query[:200]}")
        return lines


_ROUTING_SYSTEM_MESSAGE = """
You are a senior actuarial routing coordinator. Classify the user's request and
pick the best specialist(s).

Available specialists:
- reserving: loss development, IBNR, reserve movement, triangle diagnostics, Mack SE, BF/Cape Cod
- pricing: rate adequacy, indication structure, trend/relativity, GLM concepts, filing narrative
- experience_study: segmentation, cohort analysis, frequency/severity diagnostics, credibility, A/E
- model_validation: model governance, testing, implementation controls, challenge review, code review

Rules:
1. Always choose exactly one primary_agent.
2. Use additional_agents only if the question clearly crosses domains (e.g. "validate the reserving model").
3. Set reroute_once=true if the user request is vague or missing key context (e.g. no LOB, no time horizon).
4. Set confidence to "high" when the match is obvious, "low" when ambiguous.
5. Keep rationale concise and auditable (1-2 sentences).
6. If useful, provide refined_query with clearer instructions for the specialist.
"""


def create_orchestrator_agent(api_key: str) -> Agent:
    """Create the routing agent that emits `OrchestratorRoute`."""
    return Agent(
        model=Gemini(id=MODEL_FAST, api_key=api_key),
        system_message=_ROUTING_SYSTEM_MESSAGE,
        output_schema=OrchestratorRoute,
        parse_response=True,
        markdown=False,
    )


def _keyword_fallback(query: str) -> OrchestratorRoute:
    q = query.lower()
    if any(k in q for k in ("reserve", "ibnr", "triangle", "development", "incurred")):
        return OrchestratorRoute(primary_agent="reserving", rationale="keyword fallback", confidence="low")
    if any(k in q for k in ("rate", "pricing", "adequacy", "premium", "glm", "indication")):
        return OrchestratorRoute(primary_agent="pricing", rationale="keyword fallback", confidence="low")
    if any(k in q for k in ("experience", "cohort", "segment", "mortality", "lapse", "credibility")):
        return OrchestratorRoute(primary_agent="experience_study", rationale="keyword fallback", confidence="low")
    return OrchestratorRoute(primary_agent="model_validation", rationale="default fallback", confidence="low")


def choose_route(api_key: str, query: str) -> OrchestratorRoute:
    """Route a user query to one or more specialists with structured fallback."""
    try:
        router = create_orchestrator_agent(api_key)
        out = router.run(query)
        content = out.content
        if isinstance(content, OrchestratorRoute):
            return content
        if isinstance(content, dict):
            return OrchestratorRoute.model_validate(content)
        if isinstance(content, str):
            payload = json.loads(content)
            return OrchestratorRoute.model_validate(payload)
    except Exception:
        pass
    return _keyword_fallback(query)
