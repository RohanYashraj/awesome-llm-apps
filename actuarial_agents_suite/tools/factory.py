"""Shared tool factory for actuarial agents."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

from actuarial_utils.metrics import (
    actual_to_expected,
    frequency_severity,
    limited_fluctuation_credibility,
    loss_ratio_summary,
)
from actuarial_utils.triangle import (
    age_to_age_factors,
    bornhuetter_ferguson,
    cumulative_development_factor,
    triangle_diagnostics,
)
from actuarial_utils.validation import assumption_gaps, data_quality_summary, missing_required_columns

ToolRole = Literal["reserving", "pricing", "experience_study", "model_validation"]
ToolLogCallback = Callable[[str, dict[str, Any]], None]


@dataclass
class AgentTooling:
    tools: list[Any]
    duckdb: DuckDbTools | None = None


def build_duckdb_tools(csv_path: str, *, table_name: str = "uploaded_data") -> DuckDbTools:
    """Create a DuckDB toolkit and load one CSV into `table_name`."""
    duck = DuckDbTools()
    duck.load_local_csv_to_table(path=csv_path, table=table_name)
    return duck


def _record_tool_metric(
    callback: ToolLogCallback | None,
    tool_name: str,
    inputs: dict[str, Any],
    started_at: float,
    result: Any,
) -> None:
    if callback is None:
        return
    callback(
        tool_name,
        {
            "inputs_summary": json.dumps(inputs, default=str)[:300],
            "duration_ms": round((time.time() - started_at) * 1000, 2),
            "result_preview": str(result)[:500],
        },
    )


def make_triangle_factor_tool(callback: ToolLogCallback | None = None):
    """Build age-to-age and CDF estimates from a cumulative triangle."""

    def actuarial_triangle_factors(cumulative_triangle: list[list[float | int | None]]) -> dict[str, Any]:
        """Compute weighted age-to-age development factors and a cumulative development factor from a cumulative loss triangle. Each row is an origin period, each column a development period. Use None for missing cells."""
        start = time.time()
        diag = triangle_diagnostics(cumulative_triangle)
        factors = age_to_age_factors(cumulative_triangle)
        result = {
            "age_to_age_factors": factors,
            "cdf_from_latest_age": cumulative_development_factor(factors),
            "triangle_diagnostics": diag,
        }
        _record_tool_metric(callback, "actuarial_triangle_factors", {"rows": len(cumulative_triangle)}, start, result)
        return result

    actuarial_triangle_factors.__name__ = "actuarial_triangle_factors"
    return actuarial_triangle_factors


def make_bf_tool(callback: ToolLogCallback | None = None):
    """Bornhuetter-Ferguson IBNR and ultimate estimates."""

    def actuarial_bornhuetter_ferguson(
        earned_premium: list[float | int],
        a_priori_loss_ratio: float,
        cdfs: list[float | int],
    ) -> list[dict[str, float]]:
        """Compute Bornhuetter-Ferguson ultimate loss estimates. Provide earned premium per origin, an a priori loss ratio (decimal, e.g. 0.65), and cumulative development factors from latest diagonal to ultimate (one per origin; 1.0 = fully developed)."""
        start = time.time()
        result = bornhuetter_ferguson(earned_premium, a_priori_loss_ratio, cdfs)
        _record_tool_metric(callback, "actuarial_bornhuetter_ferguson", {"origins": len(earned_premium)}, start, result)
        return result

    actuarial_bornhuetter_ferguson.__name__ = "actuarial_bornhuetter_ferguson"
    return actuarial_bornhuetter_ferguson


def make_loss_ratio_tool(callback: ToolLogCallback | None = None):
    """Summarize aggregate and period loss ratio behavior."""

    def actuarial_loss_ratio_summary(
        earned_premium: list[float | int],
        incurred_loss: list[float | int],
    ) -> dict[str, float]:
        """Compute aggregate, latest, average, min, and max loss ratios from parallel lists of earned premium and incurred loss. Values returned as decimal ratios."""
        start = time.time()
        result = loss_ratio_summary(earned_premium, incurred_loss)
        _record_tool_metric(callback, "actuarial_loss_ratio_summary", {"n_points": len(earned_premium)}, start, result)
        return result

    actuarial_loss_ratio_summary.__name__ = "actuarial_loss_ratio_summary"
    return actuarial_loss_ratio_summary


def make_frequency_severity_tool(callback: ToolLogCallback | None = None):
    """Frequency, severity, and pure premium from claim-level aggregates."""

    def actuarial_frequency_severity(
        claim_count: list[int | float],
        incurred_loss: list[float | int],
        exposure: list[float | int],
    ) -> dict[str, float]:
        """Compute aggregate frequency, severity, and pure premium from parallel lists of claim counts, incurred losses, and exposure measures (e.g. earned premium or policy-years)."""
        start = time.time()
        result = frequency_severity(claim_count, incurred_loss, exposure)
        _record_tool_metric(callback, "actuarial_frequency_severity", {"periods": len(claim_count)}, start, result)
        return result

    actuarial_frequency_severity.__name__ = "actuarial_frequency_severity"
    return actuarial_frequency_severity


def make_credibility_tool(callback: ToolLogCallback | None = None):
    """Limited fluctuation credibility calculation."""

    def actuarial_credibility(
        observed_claims: int,
        full_credibility_standard: int = 1082,
    ) -> dict[str, float]:
        """Compute limited fluctuation (square-root rule) credibility Z-factor. Default full credibility standard is 1,082 claims (+/- 5% at 90% confidence, Poisson)."""
        start = time.time()
        result = limited_fluctuation_credibility(observed_claims, full_credibility_standard)
        _record_tool_metric(callback, "actuarial_credibility", {"claims": observed_claims}, start, result)
        return result

    actuarial_credibility.__name__ = "actuarial_credibility"
    return actuarial_credibility


def make_ae_tool(callback: ToolLogCallback | None = None):
    """Actual-to-expected ratio computation."""

    def actuarial_actual_to_expected(
        actual: list[float | int],
        expected: list[float | int],
    ) -> dict[str, float]:
        """Compute actual-to-expected (A/E) ratios: aggregate and per-period. Provide parallel lists of actual and expected values."""
        start = time.time()
        result = actual_to_expected(actual, expected)
        _record_tool_metric(callback, "actuarial_actual_to_expected", {"periods": len(actual)}, start, result)
        return result

    actuarial_actual_to_expected.__name__ = "actuarial_actual_to_expected"
    return actuarial_actual_to_expected


def make_validation_check_tool(callback: ToolLogCallback | None = None):
    """Check required fields and missing assumptions quickly."""

    def actuarial_validation_checks(
        required_columns: list[str],
        present_columns: list[str],
        assumptions: dict[str, str | None] | None = None,
    ) -> dict[str, Any]:
        """Verify that required data columns exist and flag missing assumptions. Pass required column names, present column names, and optionally a dict of assumption_name -> value (None or blank = missing)."""
        start = time.time()
        gaps = missing_required_columns(required_columns, present_columns)
        missing_assumptions = assumption_gaps(assumptions or {})
        result = {
            "missing_required_columns": gaps,
            "missing_assumptions": missing_assumptions,
        }
        _record_tool_metric(
            callback,
            "actuarial_validation_checks",
            {"required_count": len(required_columns), "present_count": len(present_columns)},
            start,
            result,
        )
        return result

    actuarial_validation_checks.__name__ = "actuarial_validation_checks"
    return actuarial_validation_checks


def make_data_quality_tool(callback: ToolLogCallback | None = None):
    """Quick data quality summary for upload validation."""

    def actuarial_data_quality(
        row_count: int,
        column_count: int,
        null_counts: dict[str, int] | None = None,
    ) -> dict[str, object]:
        """Assess uploaded data quality: flags low row counts, few columns, and columns with >30% nulls. Returns usability verdict and specific issues."""
        start = time.time()
        result = data_quality_summary(row_count, column_count, null_counts)
        _record_tool_metric(callback, "actuarial_data_quality", {"rows": row_count, "cols": column_count}, start, result)
        return result

    actuarial_data_quality.__name__ = "actuarial_data_quality"
    return actuarial_data_quality


def build_agent_tooling(
    *,
    role: ToolRole,
    csv_path: str | None = None,
    telemetry_callback: ToolLogCallback | None = None,
) -> AgentTooling:
    """Return the toolset for a role with consistent policy."""
    cb = telemetry_callback
    duckdb = build_duckdb_tools(csv_path) if csv_path else None
    tools: list[Any] = []

    if role in {"reserving", "pricing", "experience_study"} and duckdb is not None:
        tools.append(duckdb)

    if role in {"reserving", "pricing", "experience_study"}:
        tools.append(PandasTools())

    tools.append(make_validation_check_tool(cb))
    tools.append(make_data_quality_tool(cb))

    if role == "reserving":
        tools.append(make_triangle_factor_tool(cb))
        tools.append(make_bf_tool(cb))
        tools.append(make_loss_ratio_tool(cb))
    elif role == "pricing":
        tools.append(make_loss_ratio_tool(cb))
        tools.append(make_frequency_severity_tool(cb))
    elif role == "experience_study":
        tools.append(make_triangle_factor_tool(cb))
        tools.append(make_loss_ratio_tool(cb))
        tools.append(make_frequency_severity_tool(cb))
        tools.append(make_credibility_tool(cb))
        tools.append(make_ae_tool(cb))

    return AgentTooling(tools=tools, duckdb=duckdb)
