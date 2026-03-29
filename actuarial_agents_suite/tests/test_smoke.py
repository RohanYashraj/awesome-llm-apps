"""Smoke tests (no API calls). Run: `uv run pytest tests/test_smoke.py` from actuarial_agents_suite."""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _playwright_chromium_available() -> bool:
    """PDF uses Playwright + Chromium; skip if browser not installed."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception:
        return False


requires_playwright_pdf = pytest.mark.skipif(
    not _playwright_chromium_available(),
    reason="Run: uv run playwright install chromium (see README PDF export)",
)


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


def test_regulatory_web_search_tools_config():
    from agents.research_agent import RegulatoryWebSearchTools

    t = RegulatoryWebSearchTools()
    assert t.backend == "auto"
    assert t.timeout >= 5


@requires_playwright_pdf
def test_build_run_pdf_bytes_non_empty():
    from agent_run_ui import build_run_pdf_bytes

    pdf = build_run_pdf_bytes(
        title="Test tab",
        query="What is IBNR?",
        output_text="**Draft** answer.",
    )
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 200
    assert b"[tool]" not in pdf
    assert b"Run log" not in pdf


@requires_playwright_pdf
def test_pdf_export_markdown_list_builds():
    """List-heavy Markdown (including definition-style colons) should produce a valid PDF."""
    from agent_run_ui import build_run_pdf_bytes

    md = """- **Personal Auto**

    :

    High Credibility. Text here.
"""
    pdf = build_run_pdf_bytes(title="Tab", query="q", output_text=md)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


_DEMO_FIXTURES = (
    "sample_loss_triangle.csv",
    "sample_pricing_rating.csv",
    "sample_experience_study.csv",
    "sample_pension_plan.csv",
    "sample_model_validation_context.md",
    "sample_ifrs_questions.md",
    "sample_research_questions.txt",
)


def test_demo_fixtures_exist():
    fixtures_dir = _ROOT / "fixtures"
    assert (fixtures_dir / "README.md").is_file()
    for name in _DEMO_FIXTURES:
        path = fixtures_dir / name
        assert path.is_file(), f"Missing fixture: {path}"
        assert path.stat().st_size > 20


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
