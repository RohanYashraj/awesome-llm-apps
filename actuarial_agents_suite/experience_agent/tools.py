"""Custom tools for actuarial experience studies and decrement analysis."""

from typing import Any, Dict, List, Optional

import json
import numpy as np


def actual_to_expected(
    actual_json: str,
    expected_json: str,
    segment_labels_json: str = "[]",
) -> Dict[str, Any]:
    """Compute Actual-to-Expected (A/E) ratios overall and by segment.

    Args:
        actual_json: JSON array of actual claim counts or amounts per segment.
        expected_json: JSON array of expected claim counts or amounts per segment.
        segment_labels_json: Optional JSON array of segment labels (e.g. age bands).

    Returns:
        Dictionary with overall A/E, segment-level A/E, and summary.
    """
    try:
        actual = np.array(json.loads(actual_json), dtype=float)
        expected = np.array(json.loads(expected_json), dtype=float)
    except Exception:
        return {"error": "Inputs must be valid JSON arrays of numbers."}

    if len(actual) != len(expected):
        return {"error": "Actual and expected arrays must have the same length."}

    try:
        labels = json.loads(segment_labels_json)
    except Exception:
        labels = []

    if not labels:
        labels = [f"Segment_{i+1}" for i in range(len(actual))]

    total_actual = float(np.sum(actual))
    total_expected = float(np.sum(expected))
    overall_ae = total_actual / total_expected if total_expected > 0 else None

    segments = []
    for i, (a, e) in enumerate(zip(actual, expected)):
        label = labels[i] if i < len(labels) else f"Segment_{i+1}"
        ae_ratio = float(a / e) if e > 0 else None
        segments.append({
            "segment": label,
            "actual": round(float(a), 4),
            "expected": round(float(e), 4),
            "ae_ratio": round(ae_ratio, 6) if ae_ratio is not None else "N/A",
        })

    return {
        "total_actual": round(total_actual, 4),
        "total_expected": round(total_expected, 4),
        "overall_ae_ratio": round(overall_ae, 6) if overall_ae is not None else "N/A",
        "segments": segments,
        "interpretation": (
            "A/E > 1.0 indicates actual experience is worse than expected; "
            "A/E < 1.0 indicates favorable experience."
        ),
    }


def credibility_weight(
    observed_claims: float,
    full_credibility_standard: float = 1082.0,
    method: str = "limited_fluctuation",
) -> Dict[str, Any]:
    """Compute credibility weight for an experience study.

    Supports limited fluctuation (classical) and Buhlmann credibility.

    Args:
        observed_claims: Number of observed claims in the study.
        full_credibility_standard: Number of claims needed for full (Z=1)
            credibility. For limited fluctuation with 90% confidence and
            5% margin, the standard is ~1,082.
        method: 'limited_fluctuation' or 'buhlmann'.

    Returns:
        Dictionary with credibility Z, interpretation.
    """
    if observed_claims < 0:
        return {"error": "Observed claims must be non-negative."}

    if method == "limited_fluctuation":
        z = min(1.0, np.sqrt(observed_claims / full_credibility_standard))
        desc = (
            f"Classical limited fluctuation credibility: Z = min(1, sqrt(n/n0)) "
            f"where n={observed_claims}, n0={full_credibility_standard}."
        )
    elif method == "buhlmann":
        k = full_credibility_standard
        z = observed_claims / (observed_claims + k) if (observed_claims + k) > 0 else 0.0
        desc = (
            f"Buhlmann credibility: Z = n / (n + k) "
            f"where n={observed_claims}, k={k}."
        )
    else:
        return {"error": f"Unknown method '{method}'. Use 'limited_fluctuation' or 'buhlmann'."}

    return {
        "method": method,
        "observed_claims": observed_claims,
        "full_credibility_standard": full_credibility_standard,
        "credibility_z": round(float(z), 6),
        "credibility_pct": f"{z * 100:.2f}%",
        "description": desc,
    }


def whittaker_henderson_graduation(
    raw_rates_json: str,
    smoothing_order: int = 3,
    smoothing_weight: float = 1.0,
) -> Dict[str, Any]:
    """Graduate (smooth) crude decrement rates using Whittaker-Henderson method.

    Minimises a weighted sum of fit (to raw rates) and smoothness (measured
    by differences of order h).

    Args:
        raw_rates_json: JSON array of crude rates, e.g. '[0.001, 0.0015, ...]'.
        smoothing_order: Order of differences for the smoothness penalty (2 or 3).
        smoothing_weight: Lambda weight controlling smoothness vs fit. Higher
            values produce smoother curves.

    Returns:
        Dictionary with raw rates, graduated rates, and smoothing diagnostics.
    """
    try:
        raw = np.array(json.loads(raw_rates_json), dtype=float)
    except Exception:
        return {"error": "raw_rates_json must be a valid JSON array of numbers."}

    n = len(raw)
    if n < smoothing_order + 1:
        return {"error": f"Need at least {smoothing_order + 1} data points for order-{smoothing_order} graduation."}

    I = np.eye(n)

    K = np.eye(n)
    for _ in range(smoothing_order):
        K = np.diff(K, axis=0)

    w = np.ones(n)
    W = np.diag(w)

    A = W + smoothing_weight * (K.T @ K)
    b = W @ raw

    graduated = np.linalg.solve(A, b)

    residuals = raw - graduated
    ss_residuals = float(np.sum(residuals ** 2))

    return {
        "n_rates": n,
        "smoothing_order": smoothing_order,
        "smoothing_weight": smoothing_weight,
        "raw_rates": [round(float(r), 8) for r in raw],
        "graduated_rates": [round(float(g), 8) for g in graduated],
        "residuals": [round(float(r), 8) for r in residuals],
        "sum_sq_residuals": round(ss_residuals, 10),
    }


def compute_decrement_rates(
    exposures_json: str,
    decrements_json: str,
    age_labels_json: str = "[]",
) -> Dict[str, Any]:
    """Compute crude decrement rates (qx, lapse, withdrawal) from exposures.

    Args:
        exposures_json: JSON array of exposure counts by age/duration.
        decrements_json: JSON array of decrement counts by age/duration.
        age_labels_json: Optional JSON array of age or duration labels.

    Returns:
        Dictionary with crude rates by age/duration band.
    """
    try:
        exposures = np.array(json.loads(exposures_json), dtype=float)
        decrements = np.array(json.loads(decrements_json), dtype=float)
    except Exception:
        return {"error": "Inputs must be valid JSON arrays of numbers."}

    if len(exposures) != len(decrements):
        return {"error": "Exposures and decrements must have the same length."}

    try:
        labels = json.loads(age_labels_json)
    except Exception:
        labels = []

    if not labels:
        labels = [f"Band_{i+1}" for i in range(len(exposures))]

    rows = []
    for i, (e, d) in enumerate(zip(exposures, decrements)):
        label = labels[i] if i < len(labels) else f"Band_{i+1}"
        rate = float(d / e) if e > 0 else 0.0
        rows.append({
            "label": label,
            "exposures": round(float(e), 2),
            "decrements": round(float(d), 2),
            "crude_rate": round(rate, 8),
        })

    total_exp = float(np.sum(exposures))
    total_dec = float(np.sum(decrements))
    overall_rate = total_dec / total_exp if total_exp > 0 else 0.0

    return {
        "rates_by_band": rows,
        "total_exposures": round(total_exp, 2),
        "total_decrements": round(total_dec, 2),
        "overall_crude_rate": round(overall_rate, 8),
    }


def trend_analysis(
    periods_json: str,
    rates_json: str,
    method: str = "linear",
) -> Dict[str, Any]:
    """Fit a trend line to decrement rates over time.

    Args:
        periods_json: JSON array of numeric period identifiers (e.g. years).
        rates_json: JSON array of observed rates corresponding to each period.
        method: 'linear' for linear regression, 'log_linear' for log-linear fit.

    Returns:
        Dictionary with trend parameters, fitted values, and R-squared.
    """
    try:
        periods = np.array(json.loads(periods_json), dtype=float)
        rates = np.array(json.loads(rates_json), dtype=float)
    except Exception:
        return {"error": "Inputs must be valid JSON arrays of numbers."}

    if len(periods) != len(rates):
        return {"error": "Periods and rates must have the same length."}

    if len(periods) < 2:
        return {"error": "Need at least 2 data points for trend fitting."}

    if method == "log_linear":
        if np.any(rates <= 0):
            return {"error": "All rates must be positive for log-linear fit."}
        y = np.log(rates)
    else:
        y = rates

    coeffs = np.polyfit(periods, y, 1)
    slope, intercept = float(coeffs[0]), float(coeffs[1])

    fitted = np.polyval(coeffs, periods)
    if method == "log_linear":
        fitted_rates = np.exp(fitted)
        annual_trend = float(np.exp(slope) - 1.0)
    else:
        fitted_rates = fitted
        mean_rate = np.mean(rates)
        annual_trend = slope / mean_rate if mean_rate != 0 else 0.0

    ss_res = float(np.sum((y - fitted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "method": method,
        "slope": round(slope, 8),
        "intercept": round(intercept, 8),
        "annual_trend_rate": round(annual_trend, 6),
        "r_squared": round(r_squared, 6),
        "fitted_values": [round(float(f), 8) for f in fitted_rates],
        "periods": [float(p) for p in periods],
        "observed_rates": [round(float(r), 8) for r in rates],
    }
