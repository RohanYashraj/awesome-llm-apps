"""Custom actuarial tools for P&C claims reserving and IBNR estimation."""

from typing import Any, Dict, List, Optional

import json
import numpy as np
import pandas as pd


def build_triangle(
    data_json: str,
    origin_col: str = "accident_year",
    development_col: str = "development_lag",
    value_col: str = "cumulative_paid",
) -> Dict[str, Any]:
    """Pivot claims data into a development triangle.

    Args:
        data_json: JSON string of records, each with origin, development, and
            value columns.  Example:
            '[{"accident_year":2018,"development_lag":1,"cumulative_paid":1000}, ...]'
        origin_col: Column name for the origin period (accident year).
        development_col: Column name for the development lag.
        value_col: Column name for the cumulative value.

    Returns:
        Dictionary containing the triangle as a nested dict (origin -> {dev -> value})
        and metadata.
    """
    try:
        records = json.loads(data_json)
        df = pd.DataFrame(records)
    except Exception:
        return {"error": "data_json must be a valid JSON array of records."}

    if not {origin_col, development_col, value_col}.issubset(df.columns):
        return {"error": f"Data must contain columns: {origin_col}, {development_col}, {value_col}"}

    triangle = df.pivot_table(
        index=origin_col, columns=development_col, values=value_col, aggfunc="sum"
    )
    triangle = triangle.sort_index(axis=0).sort_index(axis=1)

    return {
        "triangle": triangle.to_dict(),
        "origin_periods": triangle.index.tolist(),
        "development_lags": triangle.columns.tolist(),
        "shape": list(triangle.shape),
    }


def chain_ladder(
    triangle_json: str,
    tail_factor: float = 1.0,
) -> Dict[str, Any]:
    """Run the Chain Ladder (volume-weighted) method on a cumulative triangle.

    Args:
        triangle_json: JSON string representing the triangle as a dict of dicts:
            {"2018": {"1": 1000, "2": 1500, ...}, "2019": {...}, ...}
            Outer keys are origin periods, inner keys are development lags.
        tail_factor: Tail factor applied after the last observable development
            period. Defaults to 1.0 (no tail).

    Returns:
        Dictionary with age_to_age_factors, cumulative_development_factors,
        ultimate_losses, and ibnr by origin.
    """
    try:
        raw = json.loads(triangle_json)
        triangle = pd.DataFrame(raw).T.apply(pd.to_numeric, errors="coerce")
        triangle = triangle.sort_index(axis=0).sort_index(axis=1)
    except Exception:
        return {"error": "triangle_json must be a JSON dict-of-dicts representing the triangle."}

    origins = triangle.index.tolist()
    dev_periods = sorted(triangle.columns.tolist(), key=lambda x: float(x))

    ata_factors = {}
    for i in range(len(dev_periods) - 1):
        col_curr = dev_periods[i]
        col_next = dev_periods[i + 1]
        mask = triangle[[col_curr, col_next]].dropna()
        if mask[col_curr].sum() == 0:
            ata_factors[f"{col_curr}-{col_next}"] = None
            continue
        ldf = float(mask[col_next].sum() / mask[col_curr].sum())
        ata_factors[f"{col_curr}-{col_next}"] = round(ldf, 6)

    ldf_values = [v for v in ata_factors.values() if v is not None]
    cum_factors = []
    cum = tail_factor
    for ldf in reversed(ldf_values):
        cum *= ldf
        cum_factors.insert(0, round(cum, 6))
    cum_factors.append(round(tail_factor, 6))

    results = {}
    for idx, origin in enumerate(origins):
        row = triangle.loc[origin].dropna()
        if len(row) == 0:
            continue
        latest = float(row.iloc[-1])
        n_developed = len(row)
        cdf_index = len(dev_periods) - n_developed
        cdf = cum_factors[cdf_index] if cdf_index < len(cum_factors) else tail_factor
        ultimate = latest * cdf
        results[str(origin)] = {
            "latest_cumulative": round(latest, 2),
            "cdf_to_ultimate": round(cdf, 6),
            "ultimate_loss": round(ultimate, 2),
            "ibnr": round(ultimate - latest, 2),
        }

    total_ultimate = sum(r["ultimate_loss"] for r in results.values())
    total_ibnr = sum(r["ibnr"] for r in results.values())

    return {
        "age_to_age_factors": ata_factors,
        "cumulative_development_factors": cum_factors,
        "tail_factor": tail_factor,
        "results_by_origin": results,
        "total_ultimate": round(total_ultimate, 2),
        "total_ibnr": round(total_ibnr, 2),
    }


def bornhuetter_ferguson(
    triangle_json: str,
    expected_loss_ratios_json: str,
    earned_premiums_json: str,
    tail_factor: float = 1.0,
) -> Dict[str, Any]:
    """Run the Bornhuetter-Ferguson method.

    Combines chain-ladder development with a priori expected losses to
    produce a more stable IBNR estimate, especially for immature years.

    Args:
        triangle_json: JSON dict-of-dicts cumulative triangle.
        expected_loss_ratios_json: JSON dict mapping origin period to expected
            loss ratio, e.g. '{"2018": 0.65, "2019": 0.68}'.
        earned_premiums_json: JSON dict mapping origin period to earned premium,
            e.g. '{"2018": 5000000, "2019": 5200000}'.
        tail_factor: Tail factor (default 1.0).

    Returns:
        Dictionary with BF ultimates and IBNR by origin.
    """
    try:
        raw = json.loads(triangle_json)
        triangle = pd.DataFrame(raw).T.apply(pd.to_numeric, errors="coerce")
        triangle = triangle.sort_index(axis=0).sort_index(axis=1)
        elr_map = json.loads(expected_loss_ratios_json)
        ep_map = json.loads(earned_premiums_json)
    except Exception:
        return {"error": "Invalid JSON input. Check triangle, ELR, and premium data."}

    cl_result = chain_ladder(triangle_json, tail_factor)
    if "error" in cl_result:
        return cl_result

    cum_factors = cl_result["cumulative_development_factors"]
    dev_periods = sorted(triangle.columns.tolist(), key=lambda x: float(x))
    origins = triangle.index.tolist()

    results = {}
    for origin in origins:
        origin_str = str(origin)
        row = triangle.loc[origin].dropna()
        if len(row) == 0:
            continue

        latest = float(row.iloc[-1])
        n_developed = len(row)
        cdf_index = len(dev_periods) - n_developed
        cdf = cum_factors[cdf_index] if cdf_index < len(cum_factors) else tail_factor

        pct_developed = 1.0 / cdf if cdf != 0 else 1.0
        pct_unreported = 1.0 - pct_developed

        elr = float(elr_map.get(origin_str, 0.65))
        ep = float(ep_map.get(origin_str, 0))
        expected_ultimate = elr * ep

        bf_ibnr = expected_ultimate * pct_unreported
        bf_ultimate = latest + bf_ibnr

        results[origin_str] = {
            "latest_cumulative": round(latest, 2),
            "cdf_to_ultimate": round(cdf, 6),
            "pct_developed": round(pct_developed, 6),
            "expected_loss_ratio": elr,
            "earned_premium": ep,
            "a_priori_ultimate": round(expected_ultimate, 2),
            "bf_ibnr": round(bf_ibnr, 2),
            "bf_ultimate": round(bf_ultimate, 2),
        }

    total_bf_ultimate = sum(r["bf_ultimate"] for r in results.values())
    total_bf_ibnr = sum(r["bf_ibnr"] for r in results.values())

    return {
        "method": "Bornhuetter-Ferguson",
        "results_by_origin": results,
        "total_bf_ultimate": round(total_bf_ultimate, 2),
        "total_bf_ibnr": round(total_bf_ibnr, 2),
    }


def compute_ibnr(
    ultimate_losses: float,
    paid_to_date: float,
) -> Dict[str, float]:
    """Simple IBNR computation: Ultimate - Paid.

    Args:
        ultimate_losses: Estimated ultimate incurred losses.
        paid_to_date: Cumulative paid losses to date.

    Returns:
        Dictionary with ultimate, paid, case_reserves_plus_ibnr, ibnr.
    """
    ibnr = ultimate_losses - paid_to_date
    return {
        "ultimate_losses": round(ultimate_losses, 2),
        "paid_to_date": round(paid_to_date, 2),
        "total_reserves": round(ibnr, 2),
    }


def mack_method_std_error(
    triangle_json: str,
) -> Dict[str, Any]:
    """Estimate reserve variability using Mack's method.

    Computes the standard error of the IBNR reserve for each origin year
    based on the variance structure implied by the chain-ladder model.

    Args:
        triangle_json: JSON dict-of-dicts cumulative triangle.

    Returns:
        Dictionary with estimated standard errors by origin and overall.
    """
    try:
        raw = json.loads(triangle_json)
        triangle = pd.DataFrame(raw).T.apply(pd.to_numeric, errors="coerce")
        triangle = triangle.sort_index(axis=0).sort_index(axis=1)
    except Exception:
        return {"error": "triangle_json must be a valid JSON dict-of-dicts."}

    dev_periods = sorted(triangle.columns.tolist(), key=lambda x: float(x))
    n_dev = len(dev_periods)

    ldfs = []
    sigma_sq = []
    for k in range(n_dev - 1):
        col_k = dev_periods[k]
        col_k1 = dev_periods[k + 1]
        mask = triangle[[col_k, col_k1]].dropna()
        weights = mask[col_k]
        if weights.sum() == 0:
            ldfs.append(1.0)
            sigma_sq.append(0.0)
            continue
        f_k = float(mask[col_k1].sum() / mask[col_k].sum())
        ldfs.append(f_k)

        n_origins = len(mask)
        if n_origins <= 1:
            sigma_sq.append(0.0)
            continue
        residuals = mask[col_k] * ((mask[col_k1] / mask[col_k]) - f_k) ** 2
        s2 = float(residuals.sum() / max(n_origins - 1, 1))
        sigma_sq.append(s2)

    origins = triangle.index.tolist()
    se_results = {}
    for origin in origins:
        row = triangle.loc[origin].dropna()
        if len(row) <= 1:
            se_results[str(origin)] = {"standard_error": 0.0, "cv": 0.0}
            continue

        latest = float(row.iloc[-1])
        n_developed = len(row)
        start_k = n_developed - 1

        var_sum = 0.0
        c_current = latest
        for k in range(start_k, n_dev - 1):
            if k >= len(ldfs):
                break
            f_k = ldfs[k]
            s2_k = sigma_sq[k] if k < len(sigma_sq) else 0.0
            col_k = dev_periods[k]
            col_sum = float(triangle[col_k].dropna().sum())
            if col_sum == 0 or c_current == 0:
                continue
            var_sum += (s2_k / (f_k ** 2)) * (1.0 / c_current + 1.0 / col_sum)
            c_current *= f_k

        ibnr = c_current - latest
        se = float(np.sqrt(var_sum)) * latest if var_sum > 0 else 0.0
        cv = se / ibnr if ibnr > 0 else 0.0

        se_results[str(origin)] = {
            "ibnr": round(ibnr, 2),
            "standard_error": round(se, 2),
            "coefficient_of_variation": round(cv, 4),
        }

    return {
        "method": "Mack Chain-Ladder Standard Error",
        "results_by_origin": se_results,
    }
