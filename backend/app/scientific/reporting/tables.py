"""Generate scientific tables from stored artefacts only."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from app.scientific.experiments.artifacts import ExperimentPaths
from app.scientific.reporting.serialization import markdown_table, write_json
from app.scientific.surrogate.config import OUTPUT_NAMES


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def write_interpolation_table(paths: ExperimentPaths) -> Path:
    rows: list[list[object]] = []
    records: list[dict[str, object]] = []
    for path in sorted(paths.interpolation.glob("seed-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for metric in payload["metrics"]:
            records.append({"seed": payload["seed"], **metric})
            rows.append(
                [
                    payload["seed"],
                    metric["response"],
                    _fmt(metric["mae"]),
                    _fmt(metric["rmse"]),
                    _fmt(metric["median_relative_error_pct"]),
                    _fmt(metric["mean_relative_error_pct"]),
                    _fmt(metric["r2"]),
                    _fmt(metric["mean_signed_error"]),
                ]
            )
    text = markdown_table(
        ["seed", "response", "MAE", "RMSE", "median RE %", "mean RE %", "R2", "mean signed"],
        rows,
    )
    out = paths.reports / "interpolation_table.md"
    out.write_text(text + "\n", encoding="utf-8")
    write_json(paths.reports / "interpolation_table.json", {"rows": records})
    return out


def write_threshold_markdown(paths: ExperimentPaths) -> Path:
    table = pq.read_table(paths.profiles / "thresholds.parquet")
    rows = [
        [
            row["variable"],
            row["response"],
            row["lower_5"],
            row["upper_5"],
            row["lower_10"],
            row["upper_10"],
            row["seed"],
        ]
        for row in table.to_pylist()
    ]
    text = markdown_table(
        ["Variable", "Response", "Lower 5%", "Upper 5%", "Lower 10%", "Upper 10%", "seed"],
        rows,
    )
    out = paths.reports / "threshold_table.md"
    out.write_text(text + "\n", encoding="utf-8")
    return out


def write_profile_table(paths: ExperimentPaths) -> Path:
    table = pq.read_table(paths.profiles / "profiles.parquet")
    rows = [
        [
            row["variable"],
            row["response"],
            row["direction"],
            row["delta"],
            _fmt(row["median_relative_error_pct"]),
            _fmt(row["q1_relative_error_pct"]),
            _fmt(row["q3_relative_error_pct"]),
            row["seed"],
        ]
        for row in table.to_pylist()
    ]
    text = markdown_table(
        ["variable", "response", "direction", "delta", "median RE %", "Q1", "Q3", "seed"],
        rows,
    )
    out = paths.reports / "profile_table.md"
    out.write_text(text + "\n", encoding="utf-8")
    return out


def write_asymmetry_table(paths: ExperimentPaths) -> Path:
    table = pq.read_table(paths.profiles / "asymmetry.parquet")
    rows = [
        [
            row["variable"],
            row["response"],
            row["delta"],
            _fmt(row["upper_minus_lower_median_relative_error_pct"]),
            row["seed"],
        ]
        for row in table.to_pylist()
    ]
    text = markdown_table(
        ["variable", "response", "delta", "upper-minus-lower median RE %", "seed"],
        rows,
    )
    out = paths.reports / "asymmetry_table.md"
    out.write_text(text + "\n", encoding="utf-8")
    return out


def write_seed_variability_table(paths: ExperimentPaths) -> Path:
    table = pq.read_table(paths.profiles / "profiles.parquet")
    groups: dict[tuple[object, ...], list[float]] = {}
    for row in table.to_pylist():
        key = (row["variable"], row["response"], row["direction"], row["delta"])
        groups.setdefault(key, []).append(float(row["median_relative_error_pct"]))
    rows = []
    records = []
    for group_key, values in sorted(groups.items(), key=str):
        records.append(
            {
                "variable": group_key[0],
                "response": group_key[1],
                "direction": group_key[2],
                "delta": group_key[3],
                "n_seeds": len(values),
                "min_seed_median_re": min(values),
                "max_seed_median_re": max(values),
                "range_seed_median_re": max(values) - min(values),
            }
        )
        rows.append(
            [
                group_key[0],
                group_key[1],
                group_key[2],
                group_key[3],
                len(values),
                _fmt(min(values)),
                _fmt(max(values)),
                _fmt(max(values) - min(values)),
            ]
        )
    text = markdown_table(
        [
            "variable",
            "response",
            "direction",
            "delta",
            "n_seeds",
            "min seed median",
            "max seed median",
            "range",
        ],
        rows,
    )
    out = paths.reports / "seed_variability_table.md"
    out.write_text(text + "\n", encoding="utf-8")
    write_json(paths.reports / "seed_variability_table.json", {"rows": records})
    return out


def write_combined_table(paths: ExperimentPaths) -> Path:
    table = pq.read_table(paths.combined / "observations.parquet")
    groups: dict[tuple[object, ...], dict[str, list[float]]] = {}
    for row in table.to_pylist():
        key = (
            row["direction_a3"],
            row["direction_f"],
            row["delta_a3"],
            row["delta_f"],
            row["seed"],
        )
        bucket = groups.setdefault(key, {name: [] for name in OUTPUT_NAMES})
        for name in OUTPUT_NAMES:
            bucket[name].append(float(row[f"relative_{name}_error"]))
    rows = []
    for group_key, payload in sorted(groups.items(), key=str):
        import numpy as np

        rows.append(
            [
                group_key[0],
                group_key[1],
                group_key[2],
                group_key[3],
                group_key[4],
                *[f"{float(np.median(payload[name])):.6g}" for name in OUTPUT_NAMES],
            ]
        )
    text = markdown_table(
        [
            "dir A3",
            "dir F",
            "delta A3",
            "delta F",
            "seed",
            "median RE u_max",
            "median RE sigma_max",
            "median RE C",
        ],
        rows,
    )
    out = paths.reports / "combined_table.md"
    out.write_text(text + "\n", encoding="utf-8")
    return out
