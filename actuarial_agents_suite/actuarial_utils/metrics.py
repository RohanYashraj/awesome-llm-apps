"""General-purpose pricing and experience metrics."""

from __future__ import annotations

import math


def loss_ratio_summary(earned_premium: list[float | int], incurred_loss: list[float | int]) -> dict[str, float]:
    """
    Return aggregate and point-in-time loss ratio statistics.

    Values are expressed as decimal ratios (e.g., 0.72).
    """
    prem = [float(v) for v in earned_premium]
    loss = [float(v) for v in incurred_loss]
    if len(prem) != len(loss):
        raise ValueError("earned_premium and incurred_loss must be the same length")
    if not prem:
        raise ValueError("At least one period is required")

    total_premium = sum(prem)
    total_loss = sum(loss)
    agg_lr = total_loss / total_premium if total_premium else 0.0
    point = [(l / p) if p else 0.0 for p, l in zip(prem, loss)]
    return {
        "aggregate_loss_ratio": agg_lr,
        "latest_loss_ratio": point[-1],
        "average_loss_ratio": sum(point) / len(point),
        "max_loss_ratio": max(point),
        "min_loss_ratio": min(point),
    }


def annual_trend_rate(values: list[float | int]) -> float:
    """Estimate simple annual trend from first and last point."""
    seq = [float(v) for v in values]
    if len(seq) < 2:
        return 0.0
    first = seq[0]
    last = seq[-1]
    if first <= 0:
        return 0.0
    years = len(seq) - 1
    return (last / first) ** (1 / years) - 1


def frequency_severity(
    claim_count: list[int | float],
    incurred_loss: list[float | int],
    exposure: list[float | int],
) -> dict[str, float]:
    """
    Compute aggregate frequency, severity, and pure premium.

    Parameters
    ----------
    claim_count : per-period claim counts
    incurred_loss : per-period incurred losses
    exposure : per-period exposure (e.g. earned premiums, policy-years)
    """
    if not (len(claim_count) == len(incurred_loss) == len(exposure)):
        raise ValueError("All input lists must have the same length")
    if not claim_count:
        raise ValueError("At least one period is required")

    total_claims = sum(float(c) for c in claim_count)
    total_loss = sum(float(l) for l in incurred_loss)
    total_exposure = sum(float(e) for e in exposure)

    freq = total_claims / total_exposure if total_exposure else 0.0
    sev = total_loss / total_claims if total_claims else 0.0
    pure_premium = total_loss / total_exposure if total_exposure else 0.0
    return {
        "frequency": freq,
        "severity": sev,
        "pure_premium": pure_premium,
        "total_claims": total_claims,
        "total_loss": total_loss,
        "total_exposure": total_exposure,
    }


def limited_fluctuation_credibility(
    observed_claims: int,
    full_credibility_standard: int = 1082,
) -> dict[str, float]:
    """
    Classical limited fluctuation (square-root rule) credibility.

    Parameters
    ----------
    observed_claims
        Number of observed claims in the study.
    full_credibility_standard
        Claims needed for full credibility. Default 1,082 corresponds to
        +/- 5% at 90% confidence for a Poisson process.
    """
    if observed_claims < 0:
        raise ValueError("observed_claims must be non-negative")
    if full_credibility_standard <= 0:
        raise ValueError("full_credibility_standard must be positive")
    z = min(1.0, math.sqrt(observed_claims / full_credibility_standard))
    return {
        "credibility_z": round(z, 6),
        "is_fully_credible": z >= 1.0,
        "observed_claims": observed_claims,
        "full_credibility_standard": full_credibility_standard,
    }


def actual_to_expected(
    actual: list[float | int],
    expected: list[float | int],
) -> dict[str, float]:
    """
    Compute actual-to-expected (A/E) ratio with aggregate and per-period detail.
    """
    if len(actual) != len(expected):
        raise ValueError("actual and expected must have the same length")
    if not actual:
        raise ValueError("At least one period is required")

    total_actual = sum(float(a) for a in actual)
    total_expected = sum(float(e) for e in expected)
    ae_aggregate = total_actual / total_expected if total_expected else 0.0
    per_period = [
        float(a) / float(e) if float(e) > 0 else 0.0
        for a, e in zip(actual, expected)
    ]
    return {
        "ae_aggregate": ae_aggregate,
        "ae_per_period": per_period,
        "total_actual": total_actual,
        "total_expected": total_expected,
    }
