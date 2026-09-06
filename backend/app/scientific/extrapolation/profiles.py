"""Anchor-wise profile aggregation. No smoothing and no forced monotonicity."""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from app.scientific.surrogate.config import OUTPUT_NAMES

PRIMARY_METRIC = "median_relative_error_pct"


def _quantiles(values: np.ndarray) -> tuple[float, float, float]:
    q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75])
    return float(q1), float(median), float(q3)


def aggregate_profiles(observations: pa.Table) -> pa.Table:
    groups: dict[tuple[object, ...], dict[str, list[float]]] = defaultdict(
        lambda: {name: [] for name in OUTPUT_NAMES}
    )
    keys = ("model_id", "seed", "variable", "direction", "delta")
    columns = {name: observations.column(name).to_pylist() for name in observations.column_names}
    n = observations.num_rows
    for index in range(n):
        key = tuple(columns[name][index] for name in keys)
        for response in OUTPUT_NAMES:
            groups[key][response].append(float(columns[f"relative_{response}_error"][index]))
            groups[key].setdefault(f"abs_{response}", []).append(
                float(columns[f"absolute_{response}_error"][index])
            )
            groups[key].setdefault(f"signed_{response}", []).append(
                float(columns[f"signed_{response}_error"][index])
            )
    records: dict[str, list[object]] = {
        "model_id": [],
        "seed": [],
        "variable": [],
        "direction": [],
        "delta": [],
        "response": [],
        "n_anchors": [],
        "q1_relative_error_pct": [],
        "median_relative_error_pct": [],
        "q3_relative_error_pct": [],
        "mean_relative_error_pct": [],
        "median_absolute_error": [],
        "rmse": [],
        "mean_signed_error": [],
        "median_signed_error": [],
        "max_relative_error_pct": [],
        "primary_metric": [],
    }
    for key, payload in sorted(groups.items(), key=lambda item: str(item[0])):
        model_id, seed, variable, direction, delta = key
        for response in OUTPUT_NAMES:
            rel = np.asarray(payload[response], dtype=np.float64)
            abs_err = np.asarray(payload[f"abs_{response}"], dtype=np.float64)
            signed = np.asarray(payload[f"signed_{response}"], dtype=np.float64)
            q1, median, q3 = _quantiles(rel)
            records["model_id"].append(model_id)
            records["seed"].append(seed)
            records["variable"].append(variable)
            records["direction"].append(direction)
            records["delta"].append(delta)
            records["response"].append(response)
            records["n_anchors"].append(int(rel.size))
            records["q1_relative_error_pct"].append(q1)
            records["median_relative_error_pct"].append(median)
            records["q3_relative_error_pct"].append(q3)
            records["mean_relative_error_pct"].append(float(np.mean(rel)))
            records["median_absolute_error"].append(float(np.median(abs_err)))
            records["rmse"].append(float(np.sqrt(np.mean(signed**2))))
            records["mean_signed_error"].append(float(np.mean(signed)))
            records["median_signed_error"].append(float(np.median(signed)))
            records["max_relative_error_pct"].append(float(np.max(rel)))
            records["primary_metric"].append(PRIMARY_METRIC)
    return pa.table(records)


def write_profiles(table: pa.Table, path: object) -> None:
    pq.write_table(table, path, compression="zstd")


def asymmetry_table(profiles: pa.Table) -> pa.Table:
    rows = profiles.to_pylist()
    index = {
        (
            row["model_id"],
            row["seed"],
            row["variable"],
            row["response"],
            row["delta"],
            row["direction"],
        ): row
        for row in rows
    }
    records: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    for row in rows:
        key = (row["model_id"], row["seed"], row["variable"], row["response"], row["delta"])
        if key in seen:
            continue
        seen.add(key)
        lower = index.get((*key, "lower"))
        upper = index.get((*key, "upper"))
        if lower is None or upper is None:
            continue
        records.append(
            {
                "model_id": row["model_id"],
                "seed": row["seed"],
                "variable": row["variable"],
                "response": row["response"],
                "delta": row["delta"],
                "upper_median_relative_error_pct": upper["median_relative_error_pct"],
                "lower_median_relative_error_pct": lower["median_relative_error_pct"],
                "upper_minus_lower_median_relative_error_pct": (
                    float(upper["median_relative_error_pct"])
                    - float(lower["median_relative_error_pct"])
                ),
            }
        )
    return pa.Table.from_pylist(records) if records else pa.table({"empty": []})
