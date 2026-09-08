"""Deterministic statistical engineering primitives used by analytics workspaces.

The functions intentionally avoid third-party numerical dependencies so the company
profile remains lightweight and reproducible. They operate on finite numeric inputs
and raise ValueError for invalid analysis contracts rather than silently coercing.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite, sqrt
from statistics import fmean, stdev
from typing import Iterable, Sequence

D2_INDIVIDUAL = 1.128
D4_INDIVIDUAL = 3.267
XBAR_R_CONSTANTS: dict[int, tuple[float, float, float]] = {
    2: (1.880, 0.000, 3.267),
    3: (1.023, 0.000, 2.574),
    4: (0.729, 0.000, 2.282),
    5: (0.577, 0.000, 2.114),
    6: (0.483, 0.000, 2.004),
    7: (0.419, 0.076, 1.924),
    8: (0.373, 0.136, 1.864),
    9: (0.337, 0.184, 1.816),
    10: (0.308, 0.223, 1.777),
}


def finite_values(values: Iterable[float | int]) -> list[float]:
    result = [float(value) for value in values]
    if not result:
        raise ValueError("At least one value is required.")
    if any(not isfinite(value) for value in result):
        raise ValueError("Analysis values must be finite numbers.")
    return result


def _sample_std(values: Sequence[float]) -> float:
    return stdev(values) if len(values) >= 2 else 0.0


def descriptive(values: Iterable[float | int]) -> dict[str, float | int]:
    xs = finite_values(values)
    mean = fmean(xs)
    return {
        "count": len(xs),
        "mean": mean,
        "minimum": min(xs),
        "maximum": max(xs),
        "range": max(xs) - min(xs),
        "sample_std": _sample_std(xs),
    }


def imr(values: Iterable[float | int]) -> dict[str, object]:
    xs = finite_values(values)
    center = fmean(xs)
    moving_ranges = [abs(right - left) for left, right in zip(xs, xs[1:])]
    mr_bar = fmean(moving_ranges) if moving_ranges else 0.0
    sigma_within = mr_bar / D2_INDIVIDUAL if mr_bar else 0.0
    spread = 3.0 * sigma_within
    lower = center - spread
    upper = center + spread
    flags = [index for index, value in enumerate(xs) if value < lower or value > upper]
    return {
        "center": center,
        "lower_control": lower,
        "upper_control": upper,
        "moving_ranges": moving_ranges,
        "moving_range_center": mr_bar,
        "moving_range_lower": 0.0,
        "moving_range_upper": mr_bar * D4_INDIVIDUAL,
        "sigma_within": sigma_within,
        "out_of_control_indexes": flags,
    }


def xbar_r(subgroups: Iterable[Iterable[float | int]]) -> dict[str, object]:
    groups = [finite_values(group) for group in subgroups]
    if len(groups) < 2:
        raise ValueError("At least two subgroups are required.")
    size = len(groups[0])
    if size not in XBAR_R_CONSTANTS or any(len(group) != size for group in groups):
        raise ValueError("Xbar-R requires equal subgroup sizes from 2 through 10.")
    means = [fmean(group) for group in groups]
    ranges = [max(group) - min(group) for group in groups]
    grand_mean = fmean(means)
    r_bar = fmean(ranges)
    a2, d3, d4 = XBAR_R_CONSTANTS[size]
    xbar_lower = grand_mean - a2 * r_bar
    xbar_upper = grand_mean + a2 * r_bar
    r_lower = d3 * r_bar
    r_upper = d4 * r_bar
    return {
        "subgroup_size": size,
        "means": means,
        "ranges": ranges,
        "xbar_center": grand_mean,
        "xbar_lower": xbar_lower,
        "xbar_upper": xbar_upper,
        "range_center": r_bar,
        "range_lower": r_lower,
        "range_upper": r_upper,
        "out_of_control_mean_indexes": [index for index, value in enumerate(means) if value < xbar_lower or value > xbar_upper],
        "out_of_control_range_indexes": [index for index, value in enumerate(ranges) if value < r_lower or value > r_upper],
    }


def capability(values: Iterable[float | int], *, lower_spec: float | None = None, upper_spec: float | None = None) -> dict[str, float | None]:
    xs = finite_values(values)
    if lower_spec is None and upper_spec is None:
        raise ValueError("At least one specification limit is required.")
    if lower_spec is not None and upper_spec is not None and lower_spec >= upper_spec:
        raise ValueError("Lower specification limit must be below upper specification limit.")
    mean = fmean(xs)
    overall_sigma = _sample_std(xs)
    imr_result = imr(xs)
    within_sigma = float(imr_result["sigma_within"])

    def indices(sigma: float) -> tuple[float | None, float | None, float | None]:
        if sigma <= 0:
            return None, None, None
        lower_index = (mean - float(lower_spec)) / (3 * sigma) if lower_spec is not None else None
        upper_index = (float(upper_spec) - mean) / (3 * sigma) if upper_spec is not None else None
        candidates = [value for value in (lower_index, upper_index) if value is not None]
        centered = (float(upper_spec) - float(lower_spec)) / (6 * sigma) if lower_spec is not None and upper_spec is not None else None
        return centered, min(candidates) if candidates else None, lower_index if lower_index is not None else upper_index

    cp, cpk, _ = indices(within_sigma)
    pp, ppk, _ = indices(overall_sigma)
    return {
        "mean": mean,
        "within_sigma": within_sigma,
        "overall_sigma": overall_sigma,
        "cp": cp,
        "cpk": cpk,
        "pp": pp,
        "ppk": ppk,
    }


def ewma(values: Iterable[float | int], *, alpha: float = 0.2, target: float | None = None) -> list[float]:
    xs = finite_values(values)
    if not 0 < alpha <= 1:
        raise ValueError("EWMA alpha must be greater than 0 and at most 1.")
    current = float(target) if target is not None else xs[0]
    if not isfinite(current):
        raise ValueError("EWMA target must be finite.")
    result: list[float] = []
    for value in xs:
        current = alpha * value + (1 - alpha) * current
        result.append(current)
    return result


def pareto(categories: Iterable[str]) -> list[dict[str, float | int | str]]:
    counts: dict[str, int] = {}
    total = 0
    for raw in categories:
        key = str(raw).strip() or "Unspecified"
        counts[key] = counts.get(key, 0) + 1
        total += 1
    if not total:
        return []
    running = 0
    result: list[dict[str, float | int | str]] = []
    for label, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        running += count
        result.append({"category": label, "count": count, "cumulative_percent": running / total * 100.0})
    return result


def run_rule_flags(values: Iterable[float | int], *, center: float | None = None) -> dict[str, list[int]]:
    """Small deterministic Western-Electric-style subset.

    Reports 8 consecutive observations on one side of center and 6-point strictly
    increasing/decreasing trends. Indexes identify the final point of each signal.
    """
    xs = finite_values(values)
    midpoint = fmean(xs) if center is None else float(center)
    if not isfinite(midpoint):
        raise ValueError("Run-rule center must be finite.")
    one_side: list[int] = []
    trend: list[int] = []
    for end in range(7, len(xs)):
        window = xs[end - 7 : end + 1]
        if all(value > midpoint for value in window) or all(value < midpoint for value in window):
            one_side.append(end)
    for end in range(5, len(xs)):
        window = xs[end - 5 : end + 1]
        if all(left < right for left, right in zip(window, window[1:])) or all(left > right for left, right in zip(window, window[1:])):
            trend.append(end)
    return {"eight_on_one_side": one_side, "six_point_trend": trend}
