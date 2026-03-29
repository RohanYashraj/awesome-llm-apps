"""Smoke tests (no API calls). Run: `uv run pytest tests/test_smoke.py` from actuarial_agents_suite."""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def test_skills_root_is_bundled():
    from pathlib import Path

    from skills_loader import PACKAGE_DIR, SKILLS_ROOT

    assert SKILLS_ROOT == PACKAGE_DIR / "skills"
    assert (SKILLS_ROOT / "data-analyst" / "SKILL.md").is_file()


def test_actuarial_skills_exist():
    from skills_loader import skill_exists

    assert skill_exists("actuarial-reserving-pc")
    assert skill_exists("actuarial-model-validation")
    assert skill_exists("actuarial-life-health-pricing")


def test_compose_reserving_includes_domain_skill():
    from skills_loader import compose_reserving_system_prompt

    text = compose_reserving_system_prompt(extra_skill_dirs=["actuarial-reserving-pc"])
    assert len(text) > 5000
    assert "reserving" in text.lower() or "P&C" in text


def test_all_agent_factories_import():
    from agents.reserving_agent import create_reserving_agent
    from agents.pricing_agent import create_pricing_agent
    from agents.experience_study_agent import create_experience_study_agent
    from agents.validation_agent import create_validation_agent
    from agents.pension_agent import create_pension_agent
    from agents.ifrs_agent import create_ifrs_reporting_agent
    from agents.research_agent import create_regulatory_research_agent

    assert callable(create_reserving_agent)
    assert callable(create_pricing_agent)
    assert callable(create_experience_study_agent)
    assert callable(create_validation_agent)
    assert callable(create_pension_agent)
    assert callable(create_ifrs_reporting_agent)
    assert callable(create_regulatory_research_agent)


def test_build_run_pdf_bytes_non_empty():
    from agent_run_ui import build_run_pdf_bytes

    pdf = build_run_pdf_bytes(
        title="Test tab",
        query="What is IBNR?",
        output_text="**Draft** answer.",
        log_text="[tool] run_query ▶ args:\n{}",
    )
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 200


def test_format_stream_event_tool_started():
    from agno.models.response import ToolExecution
    from agno.run.agent import ToolCallStartedEvent

    from agent_run_ui import format_stream_event

    ev = ToolCallStartedEvent(
        tool=ToolExecution(tool_name="run_sql", tool_args={"query": "SELECT 1"}),
    )
    line = format_stream_event(ev)
    assert line is not None
    assert "run_sql" in line
    assert "SELECT 1" in line
