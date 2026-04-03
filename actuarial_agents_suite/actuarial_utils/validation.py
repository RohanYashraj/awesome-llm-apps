"""Validation helpers for actuarial data and assumptions."""

from __future__ import annotations


def missing_required_columns(required: list[str], present: list[str]) -> list[str]:
    """Return required column names that are missing from present columns."""
    present_lc = {c.strip().lower() for c in present}
    return [c for c in required if c.strip().lower() not in present_lc]


def assumption_gaps(assumptions: dict[str, str | None]) -> list[str]:
    """Return assumption keys with missing or blank values."""
    gaps: list[str] = []
    for k, v in assumptions.items():
        if v is None or not str(v).strip():
            gaps.append(k)
    return gaps


_CONTRADICTION_PAIRS = [
    ("adequate", "inadequate"),
    ("pass", "fail"),
    ("sufficient", "insufficient"),
    ("favorable", "unfavorable"),
    ("increase", "decrease"),
]


def has_contradictory_conclusion(text: str) -> bool:
    """
    Lightweight contradiction detector for final narrative checks.

    Scans for common opposing conclusion pairs within the same text.
    """
    if not text:
        return False
    t = text.lower()
    for a, b in _CONTRADICTION_PAIRS:
        if a in t and b in t:
            return True
    return False


def data_quality_summary(
    row_count: int,
    column_count: int,
    null_counts: dict[str, int] | None = None,
    expected_row_min: int = 10,
) -> dict[str, object]:
    """
    Quick data quality summary for upload validation.

    Returns a dict with quality flags and a list of issues.
    """
    issues: list[str] = []
    if row_count < expected_row_min:
        issues.append(f"Low row count ({row_count}); results may lack credibility")
    if column_count < 2:
        issues.append("Very few columns; verify data structure")
    high_null_cols: list[str] = []
    if null_counts:
        for col, nc in null_counts.items():
            if row_count > 0 and nc / row_count > 0.3:
                high_null_cols.append(col)
    if high_null_cols:
        issues.append(f"High null rate (>30%): {', '.join(high_null_cols)}")
    return {
        "row_count": row_count,
        "column_count": column_count,
        "high_null_columns": high_null_cols,
        "issues": issues,
        "usable": len(issues) == 0,
    }
