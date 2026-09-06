"""Independent Phase 5 forensic checks. Does not regenerate paper-a.phase2.v1."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.scientific.config import load_default_scientific_config
from app.scientific.extrapolation.coordinates import extrapolated_value
from app.scientific.extrapolation.thresholds import first_observed_crossing
from app.scientific.reproducibility import repo_root_from_package, sha256_file
from app.scientific.surrogate.dataset import (
    EXPECTED_DATASET_HASH,
    EXPECTED_SPLIT_COUNTS,
    inputs_of,
    load_and_validate_phase1_dataset,
    outputs_of,
)
from app.scientific.surrogate.normalization import (
    NormalizationBundle,
    fit_train_only_normalization,
)
from app.scientific.units import GPA_TO_N_PER_MM2, KN_TO_N

EXPECTED_NORM = "ff0c27f6faf4f812e49f8e165cb4584cd310d47b83c743c35280d75a97360327"
EXPECTED_VW = 132_000
EXPECTED_COMBINED = 242_000
EXPECTED_PROFILES = 3_960
EXPERIMENT_ID = "paper-a.phase2.v1"


def _fail(findings: list[str], message: str) -> None:
    findings.append(message)


def audit() -> dict[str, object]:
    root = repo_root_from_package()
    findings: list[str] = []
    notes: list[str] = []
    exp = root / "data" / "experiments" / EXPERIMENT_ID
    dataset = load_and_validate_phase1_dataset(repo_root=root)
    parquet_hash = sha256_file(dataset.parquet_path)
    if parquet_hash != EXPECTED_DATASET_HASH:
        _fail(findings, f"dataset file hash {parquet_hash} != {EXPECTED_DATASET_HASH}")
    if dataset.dataset_hash != EXPECTED_DATASET_HASH:
        _fail(findings, "loaded dataset_hash mismatch")
    if dataset.metadata.split_counts != EXPECTED_SPLIT_COUNTS:
        _fail(findings, f"split counts {dataset.metadata.split_counts}")
    train_ids = {row.sample_id for row in dataset.train}
    val_ids = {row.sample_id for row in dataset.validation}
    test_ids = {row.sample_id for row in dataset.interpolation_test}
    if train_ids & val_ids or train_ids & test_ids or val_ids & test_ids:
        _fail(findings, "split sample_id overlap")
    if len(train_ids) + len(val_ids) + len(test_ids) != 10_000:
        _fail(findings, "sample_id coverage is not 10000")

    recomputed = fit_train_only_normalization(
        inputs_of(dataset.train),
        outputs_of(dataset.train),
        dataset.dataset_hash,
    )
    stored_norm = NormalizationBundle.model_validate_json(
        (exp / "normalization.json").read_text(encoding="utf-8")
    )
    if recomputed.content_hash() != EXPECTED_NORM:
        _fail(findings, f"recomputed normalization hash {recomputed.content_hash()}")
    if stored_norm.content_hash() != EXPECTED_NORM:
        _fail(findings, f"stored normalization hash {stored_norm.content_hash()}")
    if stored_norm.inputs.training_sample_count != 7000:
        _fail(findings, "normalization was not fit on 7000 train rows")
    if stored_norm.dataset_hash != EXPECTED_DATASET_HASH:
        _fail(findings, "normalization dataset_hash drifted")

    forbidden_mean = inputs_of(dataset.interpolation_test).mean(axis=0)
    if np.allclose(np.asarray(stored_norm.inputs.mean), forbidden_mean):
        _fail(findings, "input means match interpolation_test — leakage")

    manifest = json.loads((exp / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("dataset_hash") != EXPECTED_DATASET_HASH:
        _fail(findings, "manifest dataset_hash mismatch")
    if manifest.get("normalization_hash") != EXPECTED_NORM:
        _fail(findings, "manifest normalization_hash mismatch")

    vw_path = exp / "extrapolation" / "observations.parquet"
    combined_path = exp / "combined" / "observations.parquet"
    profiles_path = exp / "profiles" / "profiles.parquet"
    thresholds_path = exp / "profiles" / "thresholds.parquet"
    asymmetry_path = exp / "profiles" / "asymmetry.parquet"
    counts = {
        "variable_wise": int(pq.ParquetFile(vw_path).metadata.num_rows),
        "combined": int(pq.ParquetFile(combined_path).metadata.num_rows),
        "profiles": int(pq.ParquetFile(profiles_path).metadata.num_rows),
        "thresholds": int(pq.ParquetFile(thresholds_path).metadata.num_rows),
        "asymmetry": int(pq.ParquetFile(asymmetry_path).metadata.num_rows),
    }
    if counts["variable_wise"] != EXPECTED_VW:
        _fail(findings, f"variable-wise rows {counts['variable_wise']}")
    if counts["combined"] != EXPECTED_COMBINED:
        _fail(findings, f"combined rows {counts['combined']}")
    if counts["profiles"] != EXPECTED_PROFILES:
        _fail(findings, f"profile rows {counts['profiles']}")

    profiles = pq.read_table(profiles_path)
    for name in (
        "median_relative_error_pct",
        "q1_relative_error_pct",
        "q3_relative_error_pct",
        "median_absolute_error",
    ):
        col = np.asarray(profiles[name].to_pylist(), dtype=np.float64)
        if not np.all(np.isfinite(col)):
            _fail(findings, f"non-finite values in profiles.{name}")

    n_anchors = set(profiles["n_anchors"].to_pylist())
    if n_anchors != {100}:
        _fail(findings, f"unexpected n_anchors values {n_anchors}")

    stored_thresholds = pq.read_table(thresholds_path).to_pylist()
    grouped: dict[tuple[object, ...], list[tuple[float, float]]] = defaultdict(list)
    for row in profiles.to_pylist():
        key = (row["seed"], row["variable"], row["response"], row["direction"])
        grouped[key].append((float(row["delta"]), float(row["median_relative_error_pct"])))
    mismatches = 0
    for row in stored_thresholds:
        for threshold, field in ((5.0, "lower_5"), (5.0, "upper_5"), (10.0, "lower_10"), (10.0, "upper_10")):
            direction = "lower" if field.startswith("lower") else "upper"
            series = grouped[(row["seed"], row["variable"], row["response"], direction)]
            deltas = [item[0] for item in series]
            medians = [item[1] for item in series]
            expected = first_observed_crossing(deltas, medians, threshold)
            if str(row[field]) != expected:
                mismatches += 1
    if mismatches:
        _fail(findings, f"{mismatches} threshold cells disagree with recomputed crossings")

    config = load_default_scientific_config()
    domain = config.parameter_domain
    anchors = pq.read_table(exp / "anchors" / "anchors.parquet").to_pylist()
    anchor_by_id = {int(row["anchor_id"]): row for row in anchors}
    if len(anchors) != 100:
        _fail(findings, f"anchor count {len(anchors)}")
    source_ids = {int(row["source_sample_id"]) for row in anchors}
    if not source_ids.issubset(test_ids):
        _fail(findings, "anchors include non-interpolation_test sample_ids")
    if source_ids & train_ids:
        _fail(findings, "anchors overlap the train split")

    combined = pq.read_table(
        combined_path,
        columns=[
            "anchor_id",
            "seed",
            "direction_a3",
            "direction_f",
            "delta_a3",
            "delta_f",
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "A7",
            "A8",
            "A9",
            "A10",
            "E",
            "F",
            "relative_sigma_max_error",
        ],
    )
    combined_cols = {name: combined[name].to_pylist() for name in combined.column_names}
    isolation_errors = 0
    for index in range(0, combined.num_rows, 2420):
        aid = int(combined_cols["anchor_id"][index])
        anchor = anchor_by_id[aid]
        expected_a3 = extrapolated_value(
            domain.area_mm2.min,
            domain.area_mm2.max,
            combined_cols["direction_a3"][index],
            float(combined_cols["delta_a3"][index]),
        )
        expected_f = extrapolated_value(
            domain.load_kn.min,
            domain.load_kn.max,
            combined_cols["direction_f"][index],
            float(combined_cols["delta_f"][index]),
        )
        if abs(float(combined_cols["A3"][index]) - expected_a3) > 1e-9:
            isolation_errors += 1
        if abs(float(combined_cols["F"][index]) - expected_f) > 1e-9:
            isolation_errors += 1
        for name in ("A1", "A2", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "E"):
            if abs(float(combined_cols[name][index]) - float(anchor[name])) > 1e-9:
                isolation_errors += 1
    if isolation_errors:
        _fail(findings, f"combined isolation errors: {isolation_errors}")

    units = {
        "gpa_to_n_per_mm2": GPA_TO_N_PER_MM2,
        "kn_to_n": KN_TO_N,
    }
    if GPA_TO_N_PER_MM2 != 1000.0 or KN_TO_N != 1000.0:
        _fail(findings, "unit conversion constants drifted")

    failures_dir = exp / "failures"
    failure_files = list(failures_dir.glob("*")) if failures_dir.is_dir() else []
    if failure_files:
        notes.append(f"{len(failure_files)} failure artefacts present")

    interpolation_dir = exp / "interpolation"
    interpolation = []
    for path in sorted(interpolation_dir.glob("seed-*.json")):
        interpolation.append(json.loads(path.read_text(encoding="utf-8")))
    if len(interpolation) != 5:
        _fail(findings, f"expected 5 interpolation seed files, got {len(interpolation)}")
    if not all(item.get("passed_gate") for item in interpolation):
        _fail(findings, "one or more seeds failed the interpolation competence gate")

    claim = _claim_evidence(profiles.to_pylist(), stored_thresholds, combined_cols)
    report = {
        "experiment_id": EXPERIMENT_ID,
        "dataset_hash": parquet_hash,
        "normalization_hash": stored_norm.content_hash(),
        "manifest_configuration_hash": manifest.get("configuration_hash"),
        "counts": counts,
        "units": units,
        "interpolation_gate": {
            "seeds": [item["seed"] for item in interpolation],
            "all_passed": all(item.get("passed_gate") for item in interpolation),
        },
        "claims": claim,
        "git_commit": None,
        "notes": notes,
        "findings": findings,
        "passed": not findings,
    }
    return report


def _claim_evidence(
    profiles: list[dict[str, object]],
    thresholds: list[dict[str, object]],
    combined_cols: dict[str, list[object]],
) -> dict[str, object]:
    seed = 20260905
    by_var: dict[str, list[float]] = defaultdict(list)
    by_resp: dict[str, list[float]] = defaultdict(list)
    for row in profiles:
        if int(row["seed"]) != seed or float(row["delta"]) != 0.5:
            continue
        by_var[str(row["variable"])].append(float(row["median_relative_error_pct"]))
        by_resp[str(row["response"])].append(float(row["median_relative_error_pct"]))
    var_medians = {name: float(np.median(values)) for name, values in by_var.items()}
    resp_medians = {name: float(np.median(values)) for name, values in by_resp.items()}
    asymmetric = 0
    for row in thresholds:
        if int(row["seed"]) != seed:
            continue
        if row["lower_5"] != row["upper_5"] or row["lower_10"] != row["upper_10"]:
            asymmetric += 1
    isolated = []
    combined = []
    for index, (d_a3, d_f) in enumerate(zip(combined_cols["delta_a3"], combined_cols["delta_f"], strict=True)):
        if int(combined_cols["seed"][index]) != seed:
            continue
        if combined_cols["direction_a3"][index] != "upper" or combined_cols["direction_f"][index] != "upper":
            continue
        value = float(combined_cols["relative_sigma_max_error"][index])
        if float(d_a3) == 0.5 and float(d_f) == 0.0:
            isolated.append(value)
        if float(d_a3) == 0.5 and float(d_f) == 0.5:
            combined.append(value)
    return {
        "variable_medians_at_delta_0_50_seed_20260905": var_medians,
        "response_medians_at_delta_0_50_seed_20260905": resp_medians,
        "variable_dependence_supported": len(set(round(v, 3) for v in var_medians.values())) > 1,
        "response_dependence_supported": len(set(round(v, 3) for v in resp_medians.values())) > 1,
        "asymmetric_threshold_rows_seed_20260905": asymmetric,
        "combined_upper_sigma_max_median_isolated_a3_0_50": float(np.median(isolated)) if isolated else None,
        "combined_upper_sigma_max_median_a3_f_0_50": float(np.median(combined)) if combined else None,
    }


def main() -> int:
    report = audit()
    out = repo_root_from_package() / "docs" / "audit" / "phase-5-audit-runtime.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
