"""Triangle-oriented actuarial helpers."""

from __future__ import annotations

from collections.abc import Iterable


def age_to_age_factors(cumulative_triangle: list[list[float | int | None]]) -> list[float]:
    """
    Compute weighted age-to-age factors from a cumulative triangle.

    Each row is an origin period and each column is a development period.
    Missing cells are represented by ``None``.
    """
    if not cumulative_triangle:
        return []

    n_cols = max((len(row) for row in cumulative_triangle), default=0)
    factors: list[float] = []
    for dev in range(n_cols - 1):
        num = 0.0
        den = 0.0
        for row in cumulative_triangle:
            if dev + 1 >= len(row):
                continue
            a = row[dev]
            b = row[dev + 1]
            if a is None or b is None:
                continue
            a_f = float(a)
            b_f = float(b)
            if a_f <= 0:
                continue
            den += a_f
            num += b_f
        factors.append((num / den) if den > 0 else 1.0)
    return factors


def cumulative_development_factor(age_to_age: Iterable[float | int]) -> float:
    """Multiply age-to-age factors to return a CDF from latest observed age."""
    cdf = 1.0
    for f in age_to_age:
        cdf *= float(f)
    return cdf


def bornhuetter_ferguson(
    earned_premium: list[float | int],
    a_priori_loss_ratio: float,
    cdfs: list[float | int],
) -> list[dict[str, float]]:
    """
    Bornhuetter-Ferguson ultimate estimates per origin period.

    Parameters
    ----------
    earned_premium
        Earned premium by origin period.
    a_priori_loss_ratio
        Expected loss ratio (decimal, e.g. 0.65).
    cdfs
        Cumulative development factors from latest diagonal to ultimate, one per origin.
        A CDF of 1.0 means fully developed.

    Returns a list of dicts with ``expected_loss``, ``percent_unreported``, ``ibnr``,
    and ``bf_ultimate`` per origin period.
    """
    if len(earned_premium) != len(cdfs):
        raise ValueError("earned_premium and cdfs must have the same length")
    results: list[dict[str, float]] = []
    for prem, cdf in zip(earned_premium, cdfs):
        p = float(prem)
        c = float(cdf)
        expected_loss = p * a_priori_loss_ratio
        pct_unreported = 1.0 - (1.0 / c) if c > 0 else 0.0
        ibnr = expected_loss * pct_unreported
        results.append({
            "expected_loss": round(expected_loss, 2),
            "percent_unreported": round(pct_unreported, 6),
            "ibnr": round(ibnr, 2),
            "bf_ultimate": round(expected_loss * (1.0 / c) + ibnr, 2) if c > 0 else round(expected_loss, 2),
        })
    return results


def triangle_diagnostics(cumulative_triangle: list[list[float | int | None]]) -> dict[str, object]:
    """
    Quick health-check diagnostics for a cumulative triangle.

    Returns row count, column count, fill rate, and any negative or zero diagonal values.
    """
    if not cumulative_triangle:
        return {"rows": 0, "cols": 0, "fill_rate": 0.0, "issues": ["empty triangle"]}

    n_rows = len(cumulative_triangle)
    n_cols = max((len(row) for row in cumulative_triangle), default=0)
    total_cells = 0
    filled_cells = 0
    issues: list[str] = []
    for r, row in enumerate(cumulative_triangle):
        for c, val in enumerate(row):
            total_cells += 1
            if val is not None:
                filled_cells += 1
                if float(val) <= 0:
                    issues.append(f"row {r} col {c}: non-positive value {val}")
    fill_rate = filled_cells / total_cells if total_cells else 0.0
    return {
        "rows": n_rows,
        "cols": n_cols,
        "fill_rate": round(fill_rate, 4),
        "issues": issues,
    }
