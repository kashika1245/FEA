"""Dataset quality validation. Reports facts; it does not invent replacements."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.scientific.config import ScientificConfig
from app.scientific.dataset.schema import COLUMN_ORDER, DatasetRow
from app.scientific.exceptions import DatasetError


@dataclass(frozen=True, slots=True)
class DatasetQualityReport:
    sample_count: int
    column_count: int
    missing_value_count: int
    nan_count: int
    inf_count: int
    duplicate_id_count: int
    duplicate_input_count: int
    out_of_domain_count: int
    nonfinite_output_count: int
    min_values: dict[str, float]
    max_values: dict[str, float]
    failed_fea_count: int
    ok: bool
    notes: tuple[str, ...]


def validate_dataset_rows(
    rows: list[DatasetRow],
    config: ScientificConfig,
    failed_fea_count: int,
) -> DatasetQualityReport:
    expected = config.dataset.n_samples
    notes: list[str] = []
    if len(rows) != expected:
        notes.append(f"row count {len(rows)} != requested N={expected}")
    ids = [row.sample_id for row in rows]
    duplicate_id_count = len(ids) - len(set(ids))
    if duplicate_id_count:
        notes.append(f"duplicate sample_id count={duplicate_id_count}")
    numeric_names = [name for name in COLUMN_ORDER if name not in {"sample_id", "split"}]
    nan_count = 0
    inf_count = 0
    missing_value_count = 0
    out_of_domain_count = 0
    nonfinite_output_count = 0
    domain = config.parameter_domain
    input_keys: list[tuple[float, ...]] = []
    mins: dict[str, float] = {}
    maxs: dict[str, float] = {}
    for row in rows:
        payload = row.to_ordered_dict()
        areas = [float(payload[f"A{i}"]) for i in range(1, 11)]
        e_gpa = float(row.E)
        f_kn = float(row.F)
        input_keys.append(tuple([*areas, e_gpa, f_kn]))
        for name in numeric_names:
            value = float(payload[name])
            mins[name] = value if name not in mins else min(mins[name], value)
            maxs[name] = value if name not in maxs else max(maxs[name], value)
            if value != value:
                nan_count += 1
                missing_value_count += 1
            elif value in (float("inf"), float("-inf")):
                inf_count += 1
        for area in areas:
            if not (domain.area_mm2.min <= area <= domain.area_mm2.max):
                out_of_domain_count += 1
        if not (domain.youngs_modulus_gpa.min <= e_gpa <= domain.youngs_modulus_gpa.max):
            out_of_domain_count += 1
        if not (domain.load_kn.min <= f_kn <= domain.load_kn.max):
            out_of_domain_count += 1
        for name in ("u_max", "sigma_max", "C"):
            value = float(payload[name])
            if not np.isfinite(value):
                nonfinite_output_count += 1
            if name in {"u_max", "sigma_max"} and np.isfinite(value) and value < 0.0:
                notes.append(f"negative {name} on sample_id={row.sample_id}")
    unique_inputs = len(set(input_keys))
    duplicate_input_count = len(input_keys) - unique_inputs
    if out_of_domain_count:
        notes.append(f"out-of-domain values={out_of_domain_count}")
    if nan_count or inf_count or nonfinite_output_count:
        notes.append("non-finite scientific values present")
    if failed_fea_count:
        notes.append(f"failed FEA count={failed_fea_count}")
    ok = (
        len(rows) == expected
        and duplicate_id_count == 0
        and nan_count == 0
        and inf_count == 0
        and out_of_domain_count == 0
        and nonfinite_output_count == 0
        and failed_fea_count == 0
        and not any(note.startswith("negative") for note in notes)
    )
    if not ok and not notes:
        notes.append("dataset quality checks failed")
    return DatasetQualityReport(
        sample_count=len(rows),
        column_count=len(COLUMN_ORDER),
        missing_value_count=missing_value_count,
        nan_count=nan_count,
        inf_count=inf_count,
        duplicate_id_count=duplicate_id_count,
        duplicate_input_count=duplicate_input_count,
        out_of_domain_count=out_of_domain_count,
        nonfinite_output_count=nonfinite_output_count,
        min_values=mins,
        max_values=maxs,
        failed_fea_count=failed_fea_count,
        ok=ok,
        notes=tuple(notes),
    )


def require_quality(report: DatasetQualityReport) -> None:
    if not report.ok:
        raise DatasetError("dataset quality validation failed: " + "; ".join(report.notes))
