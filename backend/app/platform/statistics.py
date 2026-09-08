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
XBAR_S_CONSTANTS: dict[int, tuple[float, float, float]] = {
    2: (2.659, 0.000, 3.267),
    3: (1.954, 0.000, 2.568),
    4: (1.628, 0.000, 2.266),
    5: (1.427, 0.000, 2.089),
    6: (1.287, 0.848, 1.996),
    7: (1.182, 0.888, 1.924),
    8: (1.099, 0.902, 1.864),
    9: (1.032, 0.914, 1.816),
    10: (0.975, 0.921, 1.777),
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


def xbar_s(subgroups: Iterable[Iterable[float | int]]) -> dict[str, object]:
    groups = [finite_values(group) for group in subgroups]
    if len(groups) < 2:
        raise ValueError("At least two subgroups are required.")
    size = len(groups[0])
    if size not in XBAR_S_CONSTANTS or any(len(group) != size for group in groups):
        raise ValueError("Xbar-S requires equal subgroup sizes from 2 through 10.")
    means = [fmean(group) for group in groups]
    standard_deviations = [_sample_std(group) for group in groups]
    grand_mean = fmean(means)
    s_bar = fmean(standard_deviations)
    a3, b3, b4 = XBAR_S_CONSTANTS[size]
    return {
        "subgroup_size": size,
        "means": means,
        "standard_deviations": standard_deviations,
        "xbar_center": grand_mean,
        "xbar_lower": grand_mean - a3 * s_bar,
        "xbar_upper": grand_mean + a3 * s_bar,
        "sigma_center": s_bar,
        "sigma_lower": b3 * s_bar,
        "sigma_upper": b4 * s_bar,
        "out_of_control_mean_indexes": [index for index, value in enumerate(means) if value < grand_mean - a3 * s_bar or value > grand_mean + a3 * s_bar],
        "out_of_control_sigma_indexes": [index for index, value in enumerate(standard_deviations) if value < b3 * s_bar or value > b4 * s_bar],
    }


def _attribute_contract(defects: Iterable[float | int], samples: Iterable[float | int] | None = None) -> tuple[list[float], list[float]]:
    d = finite_values(defects)
    n = finite_values(samples if samples is not None else [1] * len(d))
    if len(d) != len(n) or any(sample <= 0 or defect < 0 or defect > sample for defect, sample in zip(d, n)):
        raise ValueError("Defects and sample sizes must be aligned and within valid bounds.")
    return d, n


def p_chart(defects: Iterable[float | int], samples: Iterable[float | int]) -> dict[str, object]:
    defects_values, sample_sizes = _attribute_contract(defects, samples)
    center = sum(defects_values) / sum(sample_sizes)
    limits = [3 * sqrt(center * (1 - center) / sample) for sample in sample_sizes]
    lower = [max(0.0, center - limit) for limit in limits]
    upper = [min(1.0, center + limit) for limit in limits]
    proportions = [defect / sample for defect, sample in zip(defects_values, sample_sizes)]
    return {"proportions": proportions, "center": center, "lower_control": lower, "upper_control": upper, "out_of_control_indexes": [index for index, value in enumerate(proportions) if value < lower[index] or value > upper[index]]}


def np_chart(defects: Iterable[float | int], sample_size: int) -> dict[str, object]:
    if sample_size <= 0:
        raise ValueError("Sample size must be positive.")
    raw = list(defects)
    values, _ = _attribute_contract(raw, [sample_size] * len(raw))
    center = sum(values) / len(values)
    p_bar = center / sample_size
    spread = 3 * sqrt(sample_size * p_bar * (1 - p_bar))
    lower, upper = max(0.0, center - spread), center + spread
    return {"counts": values, "center": center, "lower_control": lower, "upper_control": upper, "out_of_control_indexes": [index for index, value in enumerate(values) if value < lower or value > upper]}


def c_chart(defects: Iterable[float | int]) -> dict[str, object]:
    values = finite_values(defects)
    center = fmean(values)
    spread = 3 * sqrt(center)
    lower, upper = max(0.0, center - spread), center + spread
    return {"counts": values, "center": center, "lower_control": lower, "upper_control": upper, "out_of_control_indexes": [index for index, value in enumerate(values) if value < lower or value > upper]}


def u_chart(defects: Iterable[float | int], units: Iterable[float | int]) -> dict[str, object]:
    values, sample_sizes = _attribute_contract(defects, units)
    center = sum(values) / sum(sample_sizes)
    lower = [max(0.0, center - 3 * sqrt(center / sample)) for sample in sample_sizes]
    upper = [center + 3 * sqrt(center / sample) for sample in sample_sizes]
    rates = [defect / sample for defect, sample in zip(values, sample_sizes)]
    return {"rates": rates, "center": center, "lower_control": lower, "upper_control": upper, "out_of_control_indexes": [index for index, value in enumerate(rates) if value < lower[index] or value > upper[index]]}


def cusum(values: Iterable[float | int], *, target: float | None = None, allowance: float = 0.0, decision_interval: float = 5.0) -> dict[str, object]:
    xs = finite_values(values)
    midpoint = fmean(xs) if target is None else float(target)
    if not isfinite(midpoint) or allowance < 0 or decision_interval <= 0:
        raise ValueError("CUSUM target, allowance and decision interval are invalid.")
    positive = negative = 0.0
    positive_values: list[float] = []
    negative_values: list[float] = []
    for value in xs:
        positive = max(0.0, positive + value - midpoint - allowance)
        negative = min(0.0, negative + value - midpoint + allowance)
        positive_values.append(positive)
        negative_values.append(negative)
    return {"target": midpoint, "positive": positive_values, "negative": negative_values, "decision_interval": decision_interval, "positive_signal_indexes": [index for index, value in enumerate(positive_values) if value > decision_interval], "negative_signal_indexes": [index for index, value in enumerate(negative_values) if value < -decision_interval]}


def correlation(x_values: Iterable[float | int], y_values: Iterable[float | int]) -> float:
    xs, ys = finite_values(x_values), finite_values(y_values)
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("Correlation requires aligned pairs with at least two values.")
    x_mean, y_mean = fmean(xs), fmean(ys)
    denominator = sqrt(sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys))
    if denominator == 0:
        raise ValueError("Correlation is undefined for zero variance.")
    return sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator


def linear_regression(x_values: Iterable[float | int], y_values: Iterable[float | int]) -> dict[str, float]:
    xs, ys = finite_values(x_values), finite_values(y_values)
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("Regression requires aligned pairs with at least two values.")
    x_mean, y_mean = fmean(xs), fmean(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        raise ValueError("Regression is undefined for zero x variance.")
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
    intercept = y_mean - slope * x_mean
    predictions = [intercept + slope * x for x in xs]
    total = sum((y - y_mean) ** 2 for y in ys)
    residual = sum((y - prediction) ** 2 for y, prediction in zip(ys, predictions))
    return {"slope": slope, "intercept": intercept, "r_squared": 1.0 if total == 0 and residual == 0 else (1 - residual / total if total else 0.0)}


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
