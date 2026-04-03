"""Central profile catalog for retained actuarial agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ToolPolicy = Literal["required_data", "optional_data", "text_only"]


@dataclass(frozen=True)
class AgentProfile:
    key: str
    label: str
    description: str
    role_id: str
    tool_policy: ToolPolicy


AGENT_PROFILES: dict[str, AgentProfile] = {
    "reserving": AgentProfile(
        key="reserving",
        label="P&C Reserving",
        description="Loss development, reserve rationale, and assumption framing.",
        role_id="reserving",
        tool_policy="required_data",
    ),
    "pricing": AgentProfile(
        key="pricing",
        label="Pricing & rate",
        description="Rate adequacy and pricing structure with documented assumptions.",
        role_id="pricing",
        tool_policy="optional_data",
    ),
    "experience_study": AgentProfile(
        key="experience_study",
        label="Experience study",
        description="Segment diagnostics, volatility, and credibility tradeoffs.",
        role_id="experience_study",
        tool_policy="required_data",
    ),
    "model_validation": AgentProfile(
        key="model_validation",
        label="Model validation",
        description="Checklist-based model governance and technical review.",
        role_id="model_validation",
        tool_policy="text_only",
    ),
}

DIRECT_TAB_ORDER = [
    "reserving",
    "pricing",
    "experience_study",
    "model_validation",
]
