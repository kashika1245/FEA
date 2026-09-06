"""First observed empirical threshold crossings. No interpolation between deltas."""

from __future__ import annotations

from collections import defaultdict

import pyarrow as pa

NOT_REACHED = "not reached"


def first_observed_crossing(
    deltas: list[float],
    medians: list[float],
    threshold: float,
) -> str:
    ordered = sorted(zip(deltas, medians, strict=True), key=lambda item: item[0])
    for delta, median in ordered:
        if median >= threshold:
            return f"{delta:.2f}"
    return NOT_REACHED


def threshold_table(profiles: pa.Table, thresholds: tuple[float, ...]) -> pa.Table:
    groups: dict[tuple[object, ...], list[tuple[float, float]]] = defaultdict(list)
    for row in profiles.to_pylist():
        key = (row["model_id"], row["seed"], row["variable"], row["response"], row["direction"])
        groups[key].append((float(row["delta"]), float(row["median_relative_error_pct"])))
    records: list[dict[str, object]] = []
    for (model_id, seed, variable, response, direction), series in sorted(groups.items(), key=str):
        deltas = [item[0] for item in series]
        medians = [item[1] for item in series]
        record: dict[str, object] = {
            "model_id": model_id,
            "seed": seed,
            "variable": variable,
            "response": response,
            "direction": direction,
        }
        for threshold in thresholds:
            record[f"crossing_{int(threshold)}pct"] = first_observed_crossing(
                deltas, medians, threshold
            )
        records.append(record)
    return pa.Table.from_pylist(records)


def wide_threshold_table(thresholds_long: pa.Table, thresholds: tuple[float, ...]) -> pa.Table:
    rows = thresholds_long.to_pylist()
    grouped: dict[tuple[object, ...], dict[str, str]] = defaultdict(dict)
    for row in rows:
        key = (row["model_id"], row["seed"], row["variable"], row["response"])
        for threshold in thresholds:
            grouped[key][f"{row['direction']}_{int(threshold)}"] = str(
                row[f"crossing_{int(threshold)}pct"]
            )
    records = []
    for (model_id, seed, variable, response), crossings in sorted(grouped.items(), key=str):
        records.append(
            {
                "model_id": model_id,
                "seed": seed,
                "variable": variable,
                "response": response,
                "lower_5": crossings.get("lower_5", NOT_REACHED),
                "upper_5": crossings.get("upper_5", NOT_REACHED),
                "lower_10": crossings.get("lower_10", NOT_REACHED),
                "upper_10": crossings.get("upper_10", NOT_REACHED),
            }
        )
    return pa.Table.from_pylist(records)
