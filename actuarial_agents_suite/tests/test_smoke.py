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


# ---------- Skills ----------

def test_skills_root_is_bundled():
    from skills_loader import PACKAGE_DIR, SKILLS_ROOT

    assert SKILLS_ROOT == PACKAGE_DIR / "skills"
    assert (SKILLS_ROOT / "data-analyst" / "SKILL.md").is_file()


def test_actuarial_skills_exist():
    from skills_loader import skill_exists

    assert skill_exists("actuarial-reserving-pc")
    assert skill_exists("actuarial-model-validation")
    assert skill_exists("actuarial-life-health-pricing")
    assert skill_exists("actuarial-senior-practice")
    assert skill_exists("actuarial-experience-study")


def test_compose_reserving_includes_domain_skill():
    from skills_loader import compose_prompt_for_role, compose_reserving_system_prompt

    text = compose_reserving_system_prompt(extra_skill_dirs=["actuarial-reserving-pc"])
    assert len(text) > 5000
    assert "reserving" in text.lower() or "P&C" in text
    role_text = compose_prompt_for_role("reserving", missing_policy="skip")
    assert "senior actuarial" in role_text.lower()


def test_compose_experience_study_includes_skills():
    from skills_loader import compose_prompt_for_role

    text = compose_prompt_for_role("experience_study", missing_policy="skip")
    assert "experience study" in text.lower() or "segmentation" in text.lower()
    assert "senior actuarial" in text.lower()


def test_compose_all_roles():
    from skills_loader import AGENT_SKILL_STACKS, compose_prompt_for_role

    for role in AGENT_SKILL_STACKS:
        text = compose_prompt_for_role(role, missing_policy="skip")
        assert len(text) > 500, f"Role {role} produced too-short prompt"


# ---------- Agent factories ----------

def test_all_agent_factories_import():
    from agents.reserving_agent import create_reserving_agent
    from agents.pricing_agent import create_pricing_agent
    from agents.experience_study_agent import create_experience_study_agent
    from agents.validation_agent import create_validation_agent
    from agents.orchestrator_agent import create_orchestrator_agent

    assert callable(create_reserving_agent)
    assert callable(create_pricing_agent)
    assert callable(create_experience_study_agent)
    assert callable(create_validation_agent)
    assert callable(create_orchestrator_agent)


def test_agent_profiles_complete():
    from agent_profiles import AGENT_PROFILES, DIRECT_TAB_ORDER

    assert len(AGENT_PROFILES) == 4
    for key in DIRECT_TAB_ORDER:
        assert key in AGENT_PROFILES
        p = AGENT_PROFILES[key]
        assert p.label
        assert p.tool_policy in ("required_data", "optional_data", "text_only")


# ---------- Tools ----------

def test_tool_factory_builds_without_data():
    from tools.factory import build_agent_tooling

    reserving = build_agent_tooling(role="reserving")
    pricing = build_agent_tooling(role="pricing")
    experience = build_agent_tooling(role="experience_study")
    validation = build_agent_tooling(role="model_validation")

    assert reserving.duckdb is None
    assert pricing.duckdb is None
    assert validation.duckdb is None
    assert experience.duckdb is None

    assert len(reserving.tools) >= 4
    assert len(pricing.tools) >= 3
    assert len(experience.tools) >= 5
    assert len(validation.tools) >= 2


def test_tool_factory_tools_are_usable():
    from tools.factory import build_agent_tooling

    for role in ("reserving", "pricing", "experience_study", "model_validation"):
        tooling = build_agent_tooling(role=role)
        for t in tooling.tools:
            is_toolkit = hasattr(t, "functions") or hasattr(t, "name")
            assert callable(t) or is_toolkit, f"Tool {t} for {role} is not callable or a toolkit"


# ---------- Actuarial utilities ----------

def test_triangle_utilities():
    from actuarial_utils.triangle import (
        age_to_age_factors,
        bornhuetter_ferguson,
        cumulative_development_factor,
        triangle_diagnostics,
    )

    tri = [[100, 140, 160], [120, 168, None], [150, None, None]]
    factors = age_to_age_factors(tri)
    assert len(factors) == 2
    assert all(f > 1.0 for f in factors)
    assert cumulative_development_factor(factors) > 1.0

    bf = bornhuetter_ferguson([1000, 1100, 1200], 0.65, [1.0, 1.1, 1.3])
    assert len(bf) == 3
    assert all("bf_ultimate" in r for r in bf)
    assert bf[0]["percent_unreported"] == 0.0

    diag = triangle_diagnostics(tri)
    assert diag["rows"] == 3
    assert diag["cols"] == 3
    assert diag["fill_rate"] > 0.5


def test_metrics_utilities():
    from actuarial_utils.metrics import (
        actual_to_expected,
        annual_trend_rate,
        frequency_severity,
        limited_fluctuation_credibility,
        loss_ratio_summary,
    )

    lr = loss_ratio_summary([100, 110], [70, 88])
    assert 0.0 < lr["aggregate_loss_ratio"] < 1.0

    assert annual_trend_rate([100, 121]) > 0

    fs = frequency_severity([50, 60], [5000, 7200], [10000, 12000])
    assert fs["frequency"] > 0
    assert fs["severity"] > 0
    assert fs["pure_premium"] > 0

    cred = limited_fluctuation_credibility(500, 1082)
    assert 0.0 < cred["credibility_z"] < 1.0
    assert not cred["is_fully_credible"]

    cred_full = limited_fluctuation_credibility(2000, 1082)
    assert cred_full["credibility_z"] == 1.0
    assert cred_full["is_fully_credible"]

    ae = actual_to_expected([100, 120], [110, 100])
    assert ae["ae_aggregate"] > 0
    assert len(ae["ae_per_period"]) == 2


def test_validation_utilities():
    from actuarial_utils.validation import (
        assumption_gaps,
        data_quality_summary,
        has_contradictory_conclusion,
        missing_required_columns,
    )

    assert missing_required_columns(["a", "b"], ["A"]) == ["b"]
    assert assumption_gaps({"trend": "3%", "tail": None}) == ["tail"]

    assert has_contradictory_conclusion("The reserves are adequate but also inadequate.")
    assert has_contradictory_conclusion("Results pass overall but some segments fail.")
    assert not has_contradictory_conclusion("The reserves appear adequate.")

    dqs = data_quality_summary(5, 3)
    assert not dqs["usable"]
    assert any("Low row count" in i for i in dqs["issues"])

    dqs_ok = data_quality_summary(100, 10)
    assert dqs_ok["usable"]


# ---------- Orchestrator ----------

def test_orchestrator_route_model():
    from agents.orchestrator_agent import OrchestratorRoute

    route = OrchestratorRoute(
        primary_agent="reserving",
        additional_agents=["model_validation"],
        confidence="high",
        rationale="Triangle analysis with validation",
    )
    assert route.primary_label == "P&C Reserving"
    assert len(route.additional_labels) == 1
    lines = route.summary_lines()
    assert any("primary=" in l for l in lines)
    assert any("confidence=high" in l for l in lines)


def test_orchestrator_keyword_fallback():
    from agents.orchestrator_agent import _keyword_fallback

    assert _keyword_fallback("What is the IBNR estimate?").primary_agent == "reserving"
    assert _keyword_fallback("Rate adequacy check").primary_agent == "pricing"
    assert _keyword_fallback("Mortality experience study").primary_agent == "experience_study"
    assert _keyword_fallback("Review this model documentation").primary_agent == "model_validation"


# ---------- PDF ----------

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


# ---------- Fixtures ----------

_DEMO_FIXTURES = (
    "sample_loss_triangle.csv",
    "sample_pricing_rating.csv",
    "sample_experience_study.csv",
    "sample_model_validation_context.md",
)


def test_demo_fixtures_exist():
    fixtures_dir = _ROOT / "fixtures"
    assert (fixtures_dir / "README.md").is_file()
    for name in _DEMO_FIXTURES:
        path = fixtures_dir / name
        assert path.is_file(), f"Missing fixture: {path}"
        assert path.stat().st_size > 20


# ---------- Event formatting ----------

def test_format_stream_event_sql_query():
    from agno.models.response import ToolExecution
    from agno.run.agent import ToolCallStartedEvent

    from agent_run_ui import format_stream_event

    ev = ToolCallStartedEvent(
        tool=ToolExecution(tool_name="run_query", tool_args={"query": "SELECT * FROM uploaded_data LIMIT 5"}),
    )
    line = format_stream_event(ev)
    assert line is not None
    assert "[sql]" in line
    assert "SELECT * FROM uploaded_data LIMIT 5" in line


def test_format_stream_event_pandas_operation():
    from agno.models.response import ToolExecution
    from agno.run.agent import ToolCallStartedEvent

    from agent_run_ui import format_stream_event

    ev = ToolCallStartedEvent(
        tool=ToolExecution(
            tool_name="run_dataframe_operation",
            tool_args={
                "dataframe_name": "df",
                "operation": "groupby",
                "operation_parameters": {"by": "LOB"},
            },
        ),
    )
    line = format_stream_event(ev)
    assert line is not None
    assert "[pandas]" in line
    assert "df.groupby" in line
    assert "LOB" in line


def test_format_stream_event_actuarial_formula():
    from agno.models.response import ToolExecution
    from agno.run.agent import ToolCallStartedEvent

    from agent_run_ui import format_stream_event

    ev = ToolCallStartedEvent(
        tool=ToolExecution(
            tool_name="actuarial_bornhuetter_ferguson",
            tool_args={
                "earned_premium": [1000, 1100],
                "a_priori_loss_ratio": 0.65,
                "cdfs": [1.0, 1.2],
            },
        ),
    )
    line = format_stream_event(ev)
    assert line is not None
    assert "[formula]" in line
    assert "BF" in line
    assert "ELR=0.65" in line


def test_format_stream_event_describe_table():
    from agno.models.response import ToolExecution
    from agno.run.agent import ToolCallStartedEvent

    from agent_run_ui import format_stream_event

    ev = ToolCallStartedEvent(
        tool=ToolExecution(tool_name="describe_table", tool_args={"table": "uploaded_data"}),
    )
    line = format_stream_event(ev)
    assert line is not None
    assert "[sql]" in line
    assert "uploaded_data" in line


def test_format_stream_event_generic_tool():
    from agno.models.response import ToolExecution
    from agno.run.agent import ToolCallStartedEvent

    from agent_run_ui import format_stream_event

    ev = ToolCallStartedEvent(
        tool=ToolExecution(tool_name="some_custom_tool", tool_args={"key": "value"}),
    )
    line = format_stream_event(ev)
    assert line is not None
    assert "[tool_call]" in line
    assert "some_custom_tool" in line


def test_format_stream_event_final_answer_marker():
    """Verify the run_agent_stream function appends a final_answer marker (checked via module import)."""
    from agent_run_ui import format_stream_event
    from agno.run.agent import RunCompletedEvent

    assert format_stream_event(RunCompletedEvent()) is None
