"""Custom actuarial tools for P&C insurance pricing analysis."""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def compute_loss_ratio(
    earned_premium: float,
    incurred_losses: float,
    lae: float = 0.0,
    ulae: float = 0.0,
) -> Dict[str, float]:
    """Compute basic and adjusted loss ratios for a P&C insurance book.

    Args:
        earned_premium: Total earned premium for the period.
        incurred_losses: Total incurred losses (paid + reserves).
        lae: Allocated loss adjustment expenses (ALAE).
        ulae: Unallocated loss adjustment expenses (ULAE).

    Returns:
        Dictionary with basic_loss_ratio, lae_ratio, combined_loss_and_lae_ratio.
    """
    if earned_premium <= 0:
        return {"error": "Earned premium must be positive."}

    basic_lr = incurred_losses / earned_premium
    lae_ratio = (lae + ulae) / earned_premium
    combined = (incurred_losses + lae + ulae) / earned_premium

    return {
        "earned_premium": earned_premium,
        "incurred_losses": incurred_losses,
        "lae": lae + ulae,
        "basic_loss_ratio": round(basic_lr, 6),
        "lae_ratio": round(lae_ratio, 6),
        "combined_loss_and_lae_ratio": round(combined, 6),
    }


def compute_indicated_rate_change(
    target_loss_ratio: float,
    actual_loss_ratio: float,
    expense_ratio: float = 0.0,
    profit_and_contingency_margin: float = 0.0,
) -> Dict[str, float]:
    """Compute the indicated overall rate change using the loss-ratio method.

    The permissible loss ratio = 1 - expense_ratio - profit_margin.
    Indicated change = (actual_loss_ratio / permissible_loss_ratio) - 1.

    If a target_loss_ratio is supplied directly (> 0), it overrides the
    permissible derivation.

    Args:
        target_loss_ratio: Target / permissible loss ratio (0–1).
        actual_loss_ratio: Observed loss ratio (0–1+).
        expense_ratio: Fixed + variable expense ratio (0–1).
        profit_and_contingency_margin: Desired underwriting profit margin (0–1).

    Returns:
        Dictionary with permissible_lr, actual_lr, indicated_change_pct.
    """
    if target_loss_ratio > 0:
        permissible = target_loss_ratio
    else:
        permissible = 1.0 - expense_ratio - profit_and_contingency_margin

    if permissible <= 0:
        return {"error": "Permissible loss ratio must be positive."}

    indicated_change = (actual_loss_ratio / permissible) - 1.0

    return {
        "permissible_loss_ratio": round(permissible, 6),
        "actual_loss_ratio": round(actual_loss_ratio, 6),
        "indicated_rate_change": round(indicated_change, 6),
        "indicated_rate_change_pct": f"{indicated_change * 100:.2f}%",
    }


def trending_factors(
    annual_trend_rate: float,
    months_from_avg_written_to_future: float,
    months_from_avg_earned_to_future: float = 0.0,
) -> Dict[str, float]:
    """Compute loss and premium trending (on-level) factors.

    Args:
        annual_trend_rate: Annual loss trend rate (e.g. 0.05 for 5%).
        months_from_avg_written_to_future: Months between average written
            date of historical period and the midpoint of the future policy period.
        months_from_avg_earned_to_future: Months between average earned
            date of historical period and the midpoint of the future policy period.

    Returns:
        Dictionary with trend_factor_written, trend_factor_earned.
    """
    tf_written = (1.0 + annual_trend_rate) ** (months_from_avg_written_to_future / 12.0)
    tf_earned = (1.0 + annual_trend_rate) ** (months_from_avg_earned_to_future / 12.0) if months_from_avg_earned_to_future else 1.0

    return {
        "annual_trend_rate": annual_trend_rate,
        "months_written": months_from_avg_written_to_future,
        "months_earned": months_from_avg_earned_to_future,
        "trend_factor_written": round(tf_written, 6),
        "trend_factor_earned": round(tf_earned, 6),
    }


def compute_pure_premium(
    total_losses: float,
    total_exposures: float,
) -> Dict[str, float]:
    """Compute the pure premium (frequency x severity proxy).

    Args:
        total_losses: Total incurred losses.
        total_exposures: Exposure base (e.g. earned car-years, house-years).

    Returns:
        Dictionary with pure_premium, losses, exposures.
    """
    if total_exposures <= 0:
        return {"error": "Exposures must be positive."}

    pp = total_losses / total_exposures
    return {
        "total_losses": total_losses,
        "total_exposures": total_exposures,
        "pure_premium": round(pp, 4),
    }


def large_loss_cap_analysis(
    losses_json: str,
    cap_threshold: float,
) -> Dict[str, Any]:
    """Analyse the impact of capping individual large losses.

    Reads a JSON array of loss amounts, caps each at the threshold, and
    returns summary statistics before and after capping.

    Args:
        losses_json: JSON string representing a list of individual loss amounts,
            e.g. '[10000, 250000, 50000, 1200000]'.
        cap_threshold: Dollar threshold above which individual losses are capped.

    Returns:
        Dictionary with before/after totals, count of capped losses, and
        excess amount removed.
    """
    try:
        import json
        losses = json.loads(losses_json)
    except Exception:
        return {"error": "losses_json must be a valid JSON array of numbers."}

    arr = np.array(losses, dtype=float)
    capped = np.minimum(arr, cap_threshold)

    n_capped = int(np.sum(arr > cap_threshold))
    total_before = float(np.sum(arr))
    total_after = float(np.sum(capped))

    return {
        "num_losses": len(losses),
        "cap_threshold": cap_threshold,
        "num_capped": n_capped,
        "total_losses_before_cap": round(total_before, 2),
        "total_losses_after_cap": round(total_after, 2),
        "excess_removed": round(total_before - total_after, 2),
        "avg_loss_before": round(total_before / len(losses), 2) if losses else 0,
        "avg_loss_after": round(total_after / len(losses), 2) if losses else 0,
    }
