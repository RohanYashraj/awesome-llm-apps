"""Custom tools for actuarial model validation, back-testing, and diagnostics."""

from typing import Any, Dict, List, Optional

import json
import numpy as np


def back_test(
    predicted_json: str,
    actual_json: str,
) -> Dict[str, Any]:
    """Compute back-testing error metrics between predicted and actual values.

    Args:
        predicted_json: JSON array of predicted values, e.g. '[100, 110, 95]'.
        actual_json: JSON array of corresponding actual values.

    Returns:
        Dictionary with MAE, RMSE, MAPE, bias, and count.
    """
    try:
        predicted = np.array(json.loads(predicted_json), dtype=float)
        actual = np.array(json.loads(actual_json), dtype=float)
    except Exception:
        return {"error": "Inputs must be valid JSON arrays of numbers."}

    if len(predicted) != len(actual):
        return {"error": "Predicted and actual arrays must have the same length."}

    n = len(predicted)
    errors = actual - predicted
    abs_errors = np.abs(errors)

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    bias = float(np.mean(errors))

    nonzero_mask = actual != 0
    if nonzero_mask.any():
        mape = float(np.mean(np.abs(errors[nonzero_mask] / actual[nonzero_mask])))
    else:
        mape = None

    return {
        "n": n,
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "mape": round(mape, 6) if mape is not None else "N/A (zeros in actuals)",
        "bias": round(bias, 6),
        "max_absolute_error": round(float(np.max(abs_errors)), 6),
        "min_absolute_error": round(float(np.min(abs_errors)), 6),
    }


def sensitivity_analysis(
    base_result: float,
    parameter_name: str,
    base_value: float,
    perturbation_pcts_json: str = "[-20, -10, -5, 5, 10, 20]",
) -> Dict[str, Any]:
    """Perform one-way sensitivity analysis by perturbing a parameter.

    For each perturbation percentage, computes the new parameter value and
    the proportional change in the result (assuming linear relationship
    as a first approximation).

    Args:
        base_result: The model output at the base parameter value.
        parameter_name: Name of the parameter being varied.
        base_value: The base / central value of the parameter.
        perturbation_pcts_json: JSON array of perturbation percentages,
            e.g. '[-20, -10, 10, 20]'.

    Returns:
        Dictionary with sensitivity table rows.
    """
    try:
        pcts = json.loads(perturbation_pcts_json)
    except Exception:
        return {"error": "perturbation_pcts_json must be a valid JSON array."}

    if base_value == 0:
        return {"error": "base_value cannot be zero for percentage perturbations."}

    rows = []
    for pct in pcts:
        new_value = base_value * (1.0 + pct / 100.0)
        ratio = new_value / base_value
        new_result = base_result * ratio
        change = new_result - base_result
        rows.append({
            "perturbation_pct": pct,
            "parameter_value": round(new_value, 6),
            "result": round(new_result, 2),
            "change_from_base": round(change, 2),
            "change_pct": round((change / base_result) * 100, 4) if base_result != 0 else 0,
        })

    return {
        "parameter": parameter_name,
        "base_value": base_value,
        "base_result": base_result,
        "sensitivity_table": rows,
    }


def residual_diagnostics(
    predicted_json: str,
    actual_json: str,
) -> Dict[str, Any]:
    """Compute residual diagnostic statistics for model validation.

    Includes mean residual, standard deviation, skewness, kurtosis,
    and a Shapiro-Wilk normality test (for samples up to 5000).

    Args:
        predicted_json: JSON array of predicted values.
        actual_json: JSON array of actual values.

    Returns:
        Dictionary with residual statistics and normality test result.
    """
    try:
        predicted = np.array(json.loads(predicted_json), dtype=float)
        actual = np.array(json.loads(actual_json), dtype=float)
    except Exception:
        return {"error": "Inputs must be valid JSON arrays of numbers."}

    if len(predicted) != len(actual):
        return {"error": "Arrays must have the same length."}

    residuals = actual - predicted
    n = len(residuals)

    result = {
        "n": n,
        "mean_residual": round(float(np.mean(residuals)), 6),
        "std_residual": round(float(np.std(residuals, ddof=1)), 6) if n > 1 else 0,
        "min_residual": round(float(np.min(residuals)), 6),
        "max_residual": round(float(np.max(residuals)), 6),
        "median_residual": round(float(np.median(residuals)), 6),
    }

    if n >= 3:
        from scipy import stats as sp_stats

        result["skewness"] = round(float(sp_stats.skew(residuals)), 6)
        result["kurtosis"] = round(float(sp_stats.kurtosis(residuals)), 6)

        if n <= 5000:
            stat, p_value = sp_stats.shapiro(residuals)
            result["shapiro_wilk_statistic"] = round(float(stat), 6)
            result["shapiro_wilk_p_value"] = round(float(p_value), 6)
            result["normality_conclusion"] = (
                "Residuals appear normally distributed (p >= 0.05)"
                if p_value >= 0.05
                else "Residuals deviate from normality (p < 0.05)"
            )

    lag1 = np.corrcoef(residuals[:-1], residuals[1:])[0, 1] if n > 2 else 0
    result["lag1_autocorrelation"] = round(float(lag1), 6)

    return result


def assumption_reasonableness_check(
    assumption_name: str,
    value: float,
    industry_low: float,
    industry_high: float,
    industry_median: float = 0.0,
) -> Dict[str, Any]:
    """Check whether an actuarial assumption falls within an industry range.

    Args:
        assumption_name: Name of the assumption (e.g. 'loss_trend', 'discount_rate').
        value: The assumed value used in the model.
        industry_low: Lower bound of acceptable industry range.
        industry_high: Upper bound of acceptable industry range.
        industry_median: Median industry value (informational).

    Returns:
        Dictionary with pass/fail flag, deviation from median, and commentary.
    """
    within_range = industry_low <= value <= industry_high

    deviation_from_median = 0.0
    if industry_median != 0:
        deviation_from_median = (value - industry_median) / industry_median

    if within_range:
        status = "PASS"
        commentary = f"{assumption_name} = {value} is within the industry range [{industry_low}, {industry_high}]."
    else:
        status = "FAIL"
        if value < industry_low:
            commentary = f"{assumption_name} = {value} is BELOW the industry range [{industry_low}, {industry_high}]. Review for potential under-estimation."
        else:
            commentary = f"{assumption_name} = {value} is ABOVE the industry range [{industry_low}, {industry_high}]. Review for potential over-estimation."

    return {
        "assumption": assumption_name,
        "value": value,
        "industry_range": [industry_low, industry_high],
        "industry_median": industry_median,
        "status": status,
        "deviation_from_median": round(deviation_from_median, 6),
        "commentary": commentary,
    }


def generate_validation_report(
    model_name: str,
    validation_date: str,
    back_test_results_json: str = "{}",
    sensitivity_results_json: str = "{}",
    residual_results_json: str = "{}",
    assumption_checks_json: str = "[]",
) -> Dict[str, Any]:
    """Assemble a structured model validation report from component results.

    Args:
        model_name: Name of the actuarial model being validated.
        validation_date: Date of the validation exercise (ISO format).
        back_test_results_json: JSON string of back-test results dict.
        sensitivity_results_json: JSON string of sensitivity analysis dict.
        residual_results_json: JSON string of residual diagnostics dict.
        assumption_checks_json: JSON array of assumption check dicts.

    Returns:
        Structured validation report dictionary.
    """
    try:
        bt = json.loads(back_test_results_json)
        sens = json.loads(sensitivity_results_json)
        resid = json.loads(residual_results_json)
        assumptions = json.loads(assumption_checks_json)
    except Exception:
        return {"error": "One or more JSON inputs are invalid."}

    issues = []
    if isinstance(bt, dict) and bt.get("bias", 0) != 0:
        if abs(bt.get("bias", 0)) > 0.1 * abs(bt.get("mae", 1)):
            issues.append(f"Significant bias detected in back-test: {bt.get('bias')}")

    if isinstance(resid, dict):
        p_val = resid.get("shapiro_wilk_p_value")
        if p_val is not None and p_val < 0.05:
            issues.append("Residuals fail normality test (Shapiro-Wilk p < 0.05)")
        ac = resid.get("lag1_autocorrelation", 0)
        if abs(ac) > 0.3:
            issues.append(f"Residual autocorrelation detected: lag-1 = {ac}")

    if isinstance(assumptions, list):
        for check in assumptions:
            if isinstance(check, dict) and check.get("status") == "FAIL":
                issues.append(f"Assumption '{check.get('assumption')}' outside industry range")

    overall_status = "PASS" if not issues else "NEEDS REVIEW"

    return {
        "report_title": f"Model Validation Report: {model_name}",
        "validation_date": validation_date,
        "overall_status": overall_status,
        "issues_found": len(issues),
        "issues": issues,
        "sections": {
            "back_testing": bt,
            "sensitivity_analysis": sens,
            "residual_diagnostics": resid,
            "assumption_checks": assumptions,
        },
    }
