"""Resumable Phase 2 experiment runner. Failures are logged, never fabricated."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from app.scientific.config import ScientificConfig
from app.scientific.dataset.storage import confine_under_data_root
from app.scientific.experiments.artifacts import ExperimentPaths
from app.scientific.experiments.manifest import ExperimentManifest, build_manifest, write_manifest
from app.scientific.extrapolation.anchors import Anchor, select_anchors
from app.scientific.extrapolation.combined import CombinedPoint, build_combined_points
from app.scientific.extrapolation.evaluator import (
    FemCache,
    evaluate_fem_matrix,
    evaluate_mlp_matrix,
    make_fem_cache,
    record_failure,
)
from app.scientific.extrapolation.profiles import (
    aggregate_profiles,
    asymmetry_table,
    write_profiles,
)
from app.scientific.extrapolation.sweeps import SweepPoint, build_variable_wise_points
from app.scientific.extrapolation.thresholds import threshold_table, wide_threshold_table
from app.scientific.phase2_errors import ExperimentError
from app.scientific.reproducibility import canonical_json_bytes, repo_root_from_package
from app.scientific.surrogate.checkpoints import restore_model, write_checkpoint
from app.scientific.surrogate.config import INPUT_NAMES, OUTPUT_NAMES, Phase2Config
from app.scientific.surrogate.dataset import (
    LoadedPhase1Dataset,
    inputs_of,
    load_and_validate_phase1_dataset,
    outputs_of,
)
from app.scientific.surrogate.evaluation import (
    evaluate_interpolation,
    require_interpolation_competence,
)
from app.scientific.surrogate.logging_util import get_logger, log_event
from app.scientific.surrogate.metrics import absolute_error, relative_error_pct, signed_error
from app.scientific.surrogate.model import StructuralMLP
from app.scientific.surrogate.normalization import NormalizationBundle, fit_train_only_normalization
from app.scientific.surrogate.training import (
    SeedTrainingResult,
    rank_by_validation_loss,
    train_one_seed,
)

LOGGER = get_logger()

VARIABLE_WISE_FIELDS: tuple[str, ...] = (
    "experiment_id",
    "model_id",
    "seed",
    "anchor_id",
    "source_sample_id",
    "variable",
    "direction",
    "delta",
    *INPUT_NAMES,
    "fea_u_max",
    "predicted_u_max",
    "signed_u_max_error",
    "absolute_u_max_error",
    "relative_u_max_error",
    "fea_sigma_max",
    "predicted_sigma_max",
    "signed_sigma_max_error",
    "absolute_sigma_max_error",
    "relative_sigma_max_error",
    "fea_C",
    "predicted_C",
    "signed_C_error",
    "absolute_C_error",
    "relative_C_error",
    "dataset_hash",
    "model_hash",
    "normalization_hash",
    "software_version",
)


@dataclass(frozen=True, slots=True)
class PreparedModels:
    normalization: NormalizationBundle
    results: tuple[SeedTrainingResult, ...]
    ranked: tuple[SeedTrainingResult, ...]


class Phase2Runner:
    def __init__(
        self,
        phase1: ScientificConfig,
        phase2: Phase2Config,
        *,
        experiment_id: str | None = None,
        n_anchors: int | None = None,
        seeds: tuple[int, ...] | None = None,
        variables: tuple[str, ...] | None = None,
        deltas: tuple[float, ...] | None = None,
        repo_root: Path | None = None,
    ) -> None:
        self.phase1 = phase1
        self.phase2 = phase2
        self.repo_root = repo_root if repo_root is not None else repo_root_from_package()
        self.experiment_id = experiment_id or phase2.phase2_version
        root = self.repo_root / "data" / "experiments" / self.experiment_id
        self.paths = ExperimentPaths(root, self.experiment_id, self.repo_root)
        self.n_anchors = n_anchors if n_anchors is not None else phase2.anchors.count
        self.seeds = seeds if seeds is not None else phase2.surrogate.seeds
        self.variables = variables if variables is not None else phase2.extrapolation.variables
        self.deltas = deltas if deltas is not None else phase2.extrapolation.deltas
        self.dataset: LoadedPhase1Dataset | None = None
        self.normalization: NormalizationBundle | None = None
        self.models: tuple[SeedTrainingResult, ...] = ()
        self.anchors: tuple[Anchor, ...] = ()
        self.fem_cache: FemCache | None = None

    def validate_phase1(self) -> LoadedPhase1Dataset:
        log_event(LOGGER, "phase1_validation_start", experiment_id=self.experiment_id)
        dataset = load_and_validate_phase1_dataset(config=self.phase1, repo_root=self.repo_root)
        self.dataset = dataset
        log_event(
            LOGGER,
            "phase1_validation_ok",
            dataset_hash=dataset.dataset_hash,
            n=len(dataset.rows),
        )
        return dataset

    def fit_normalization(self) -> NormalizationBundle:
        dataset = self._require_dataset()
        log_event(LOGGER, "normalization_start", n_train=len(dataset.train))
        bundle = fit_train_only_normalization(
            inputs_of(dataset.train),
            outputs_of(dataset.train),
            dataset.dataset_hash,
        )
        if bundle.inputs.training_sample_count != len(dataset.train):
            raise ExperimentError("normalization was not fitted on the train split alone")
        self.normalization = bundle
        path = self.paths.root / "normalization.json"
        path.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
        log_event(LOGGER, "normalization_complete", normalization_hash=bundle.content_hash())
        return bundle

    def train_seeds(self) -> PreparedModels:
        dataset = self._require_dataset()
        bundle = self._require_normalization()
        results: list[SeedTrainingResult] = []
        x_train = inputs_of(dataset.train)
        y_train = outputs_of(dataset.train)
        x_val = inputs_of(dataset.validation)
        y_val = outputs_of(dataset.validation)
        for seed in self.seeds:
            model_dir = self.paths.model_dir(seed)
            metadata_path = model_dir / "metadata.json"
            if metadata_path.is_file() and (model_dir / "weights.npz").is_file():
                log_event(LOGGER, "seed_restore", seed=seed)
                restored = restore_model(model_dir, self.repo_root)
                meta = json.loads(metadata_path.read_text(encoding="utf-8"))
                weights = {
                    key: value.detach().cpu().numpy()
                    for key, value in restored.state_dict().items()
                }
                results.append(
                    SeedTrainingResult(
                        seed=seed,
                        model_id=str(meta["model_id"]),
                        architecture=str(meta["architecture"]),
                        optimizer=str(meta["optimizer"]),
                        learning_rate=float(meta["learning_rate"]),
                        batch_size=int(meta["batch_size"]),
                        epoch_count=int(meta["epoch_count"]),
                        stopping_epoch=int(meta["stopping_epoch"]),
                        training_loss=float(meta["training_loss"]),
                        validation_loss=float(meta["validation_loss"]),
                        best_validation_loss=float(meta["best_validation_loss"]),
                        dataset_hash=str(meta["dataset_hash"]),
                        normalization_hash=str(meta["normalization_hash"]),
                        software_version=str(meta["software_version"]),
                        model_hash=str(meta["model_hash"]),
                        weights=weights,
                    )
                )
                continue
            log_event(LOGGER, "seed_train_start", seed=seed)
            result = train_one_seed(
                train_inputs=x_train,
                train_outputs=y_train,
                validation_inputs=x_val,
                validation_outputs=y_val,
                normalization=bundle,
                config=self.phase2,
                seed=seed,
                dataset_hash=dataset.dataset_hash,
            )
            metadata = {
                "seed": result.seed,
                "model_id": result.model_id,
                "architecture": result.architecture,
                "optimizer": result.optimizer,
                "learning_rate": result.learning_rate,
                "batch_size": result.batch_size,
                "epoch_count": result.epoch_count,
                "stopping_epoch": result.stopping_epoch,
                "training_loss": result.training_loss,
                "validation_loss": result.validation_loss,
                "best_validation_loss": result.best_validation_loss,
                "dataset_hash": result.dataset_hash,
                "normalization_hash": result.normalization_hash,
                "software_version": result.software_version,
                "model_hash": result.model_hash,
                "selection_rule": self.phase2.surrogate.model_selection_rule,
                "ranking_rule": self.phase2.surrogate.ranking_rule,
            }
            write_checkpoint(
                model_dir,
                seed=seed,
                weights=result.weights,
                metadata=metadata,
                normalization=bundle,
                repo_root=self.repo_root,
            )
            results.append(result)
            log_event(
                LOGGER,
                "seed_train_complete",
                seed=seed,
                stopping_epoch=result.stopping_epoch,
                validation_loss=result.validation_loss,
                model_hash=result.model_hash,
            )
        ranked = rank_by_validation_loss(tuple(results))
        ranking_path = self.paths.models / "validation_ranking.json"
        ranking_path.write_bytes(
            canonical_json_bytes(
                {
                    "rule": self.phase2.surrogate.ranking_rule,
                    "selection_rule": self.phase2.surrogate.model_selection_rule,
                    "order": [
                        {
                            "seed": item.seed,
                            "model_id": item.model_id,
                            "best_validation_loss": item.best_validation_loss,
                        }
                        for item in ranked
                    ],
                    "note": "All five seeds are retained. Ranking is validation-MSE only.",
                }
            )
        )
        self.models = tuple(results)
        return PreparedModels(normalization=bundle, results=tuple(results), ranked=ranked)

    def evaluate_interpolation(self) -> None:
        dataset = self._require_dataset()
        bundle = self._require_normalization()
        evaluations = []
        x_test = inputs_of(dataset.interpolation_test)
        y_test = outputs_of(dataset.interpolation_test)
        for result in self.models:
            model = self._load_model(result.seed)
            evaluation = evaluate_interpolation(
                model=model,
                inputs=x_test,
                references=y_test,
                normalization=bundle,
                config=self.phase2,
                seed=result.seed,
                model_id=result.model_id,
            )
            evaluations.append(evaluation)
            payload = {
                "seed": evaluation.seed,
                "model_id": evaluation.model_id,
                "passed_gate": evaluation.passed_gate,
                "gate_notes": evaluation.gate_notes,
                "metrics": [
                    {
                        "response": item.response,
                        "mae": item.mae,
                        "rmse": item.rmse,
                        "mean_relative_error_pct": item.mean_relative_error_pct,
                        "median_relative_error_pct": item.median_relative_error_pct,
                        "max_relative_error_pct": item.max_relative_error_pct,
                        "mean_signed_error": item.mean_signed_error,
                        "median_signed_error": item.median_signed_error,
                        "r2": item.r2,
                        "n": item.n,
                    }
                    for item in evaluation.metrics
                ],
            }
            path = self.paths.interpolation / f"seed-{result.seed}.json"
            path.write_bytes(canonical_json_bytes(payload))
            pred_path = self.paths.interpolation / f"seed-{result.seed}-predictions.parquet"
            table = pa.table(
                {
                    "sample_id": [row.sample_id for row in dataset.interpolation_test],
                    "fea_u_max": y_test[:, 0],
                    "fea_sigma_max": y_test[:, 1],
                    "fea_C": y_test[:, 2],
                    "predicted_u_max": evaluation.predictions[:, 0],
                    "predicted_sigma_max": evaluation.predictions[:, 1],
                    "predicted_C": evaluation.predictions[:, 2],
                }
            )
            pq.write_table(table, pred_path, compression="zstd")
            log_event(
                LOGGER,
                "interpolation_evaluated",
                seed=result.seed,
                passed=evaluation.passed_gate,
            )
        require_interpolation_competence(tuple(evaluations), self.phase2)
        log_event(LOGGER, "interpolation_gate_passed", n_seeds=len(evaluations))

    def select_anchors(self) -> tuple[Anchor, ...]:
        dataset = self._require_dataset()
        path = self.paths.anchors / "anchors.parquet"
        if path.is_file():
            table = pq.read_table(path)
            anchors = []
            for row in table.to_pylist():
                anchors.append(
                    Anchor(
                        anchor_id=int(row["anchor_id"]),
                        source_sample_id=int(row["source_sample_id"]),
                        values=tuple(float(row[name]) for name in INPUT_NAMES),
                        selection_method=str(row["selection_method"]),
                        selection_seed=int(row["selection_seed"]),
                        dataset_hash=str(row["dataset_hash"]),
                    )
                )
            self.anchors = tuple(anchors)[: self.n_anchors]
            log_event(LOGGER, "anchors_restored", n=len(self.anchors))
            return self.anchors
        selected = select_anchors(
            dataset.interpolation_test, self._anchor_config(), dataset.dataset_hash
        )
        self.anchors = selected[: self.n_anchors]
        records = []
        for anchor in self.anchors:
            record = {
                "anchor_id": anchor.anchor_id,
                "source_sample_id": anchor.source_sample_id,
                "selection_method": anchor.selection_method,
                "selection_seed": anchor.selection_seed,
                "dataset_hash": anchor.dataset_hash,
            }
            record.update(anchor.as_mapping())
            records.append(record)
        pq.write_table(pa.Table.from_pylist(records), path, compression="zstd")
        (self.paths.anchors / "anchors.json").write_bytes(
            canonical_json_bytes({"anchors": records})
        )
        log_event(
            LOGGER,
            "anchors_selected",
            n=len(self.anchors),
            method=self.phase2.anchors.selection_method,
        )
        return self.anchors

    def run_variable_wise(self, resume: bool = True) -> Path:
        dataset = self._require_dataset()
        bundle = self._require_normalization()
        anchors = self.anchors or self.select_anchors()
        cache = self._fem_cache()
        points = build_variable_wise_points(
            anchors,
            self.phase2,
            self.phase1.parameter_domain,
            variables=self.variables,
            deltas=self.deltas,
        )
        expected = len(self.seeds) * len(points)
        log_event(LOGGER, "variable_wise_start", expected=expected)
        for result in self.models:
            model = self._load_model(result.seed)
            for variable in self.variables:
                for direction in self.phase2.extrapolation.directions:
                    chunk = self.paths.chunk_path(result.seed, variable, direction)
                    if resume and chunk.is_file():
                        existing = pq.read_table(chunk)
                        expected_rows = self.n_anchors * len(self.deltas)
                        if existing.num_rows == expected_rows:
                            continue
                        raise ExperimentError(
                            f"incomplete chunk {chunk} has {existing.num_rows} rows, expected {expected_rows}"
                        )
                    subset = [
                        point
                        for point in points
                        if point.variable == variable and point.direction == direction
                    ]
                    table = self._evaluate_points(
                        subset,
                        model=model,
                        result=result,
                        normalization=bundle,
                        cache=cache,
                        dataset_hash=dataset.dataset_hash,
                    )
                    _atomic_write_table(chunk, table, self.repo_root)
                    log_event(
                        LOGGER,
                        "chunk_complete",
                        seed=result.seed,
                        variable=variable,
                        direction=direction,
                        n=table.num_rows,
                    )
        merged = self._merge_chunks(
            self.paths.chunks, self.paths.extrapolation / "observations.parquet"
        )
        log_event(LOGGER, "variable_wise_complete", n=merged.num_rows, expected=expected)
        if merged.num_rows != expected:
            raise ExperimentError(f"variable-wise rows {merged.num_rows} != expected {expected}")
        return self.paths.extrapolation / "observations.parquet"

    def build_profiles(self) -> None:
        observations = pq.read_table(self.paths.extrapolation / "observations.parquet")
        profiles = aggregate_profiles(observations)
        write_profiles(profiles, self.paths.profiles / "profiles.parquet")
        thresholds = threshold_table(profiles, self.phase2.extrapolation.threshold_pct)
        wide = wide_threshold_table(thresholds, self.phase2.extrapolation.threshold_pct)
        pq.write_table(
            thresholds, self.paths.profiles / "thresholds_long.parquet", compression="zstd"
        )
        pq.write_table(wide, self.paths.profiles / "thresholds.parquet", compression="zstd")
        pq.write_table(
            asymmetry_table(profiles), self.paths.profiles / "asymmetry.parquet", compression="zstd"
        )
        log_event(LOGGER, "profiles_complete", n=profiles.num_rows)

    def run_combined(self, resume: bool = True) -> Path:
        dataset = self._require_dataset()
        bundle = self._require_normalization()
        anchors = self.anchors or self.select_anchors()
        cache = self._fem_cache()
        points = build_combined_points(anchors, self.phase2, self.phase1.parameter_domain)
        # If this runner reduced anchors, rebuild with the selected prefix.
        if len(anchors) != self.phase2.anchors.count:
            points = tuple(point for point in points if point.anchor_id <= self.n_anchors)
        expected = len(self.seeds) * len(points)
        log_event(LOGGER, "combined_start", expected=expected)
        for result in self.models:
            model = self._load_model(result.seed)
            for direction_a3 in self.phase2.combined.directions_a3:
                for direction_f in self.phase2.combined.directions_f:
                    chunk = self.paths.combined_chunk_path(result.seed, direction_a3, direction_f)
                    subset = [
                        point
                        for point in points
                        if point.direction_a3 == direction_a3 and point.direction_f == direction_f
                    ]
                    if resume and chunk.is_file():
                        existing = pq.read_table(chunk)
                        if existing.num_rows == len(subset):
                            continue
                        raise ExperimentError(
                            f"incomplete combined chunk {chunk} has {existing.num_rows} rows"
                        )
                    table = self._evaluate_combined(
                        subset,
                        model=model,
                        result=result,
                        normalization=bundle,
                        cache=cache,
                        dataset_hash=dataset.dataset_hash,
                    )
                    _atomic_write_table(chunk, table, self.repo_root)
                    log_event(
                        LOGGER,
                        "combined_chunk_complete",
                        seed=result.seed,
                        direction_a3=direction_a3,
                        direction_f=direction_f,
                        n=table.num_rows,
                    )
        merged = self._merge_chunks(
            self.paths.combined_chunks, self.paths.combined / "observations.parquet"
        )
        log_event(LOGGER, "combined_complete", n=merged.num_rows, expected=expected)
        if merged.num_rows != expected:
            raise ExperimentError(f"combined rows {merged.num_rows} != expected {expected}")
        return self.paths.combined / "observations.parquet"

    def write_manifest(self, status: str) -> ExperimentManifest:
        dataset = self._require_dataset()
        bundle = self._require_normalization()
        manifest = build_manifest(
            self.phase2,
            dataset_id=dataset.metadata.dataset_id,
            dataset_hash=dataset.dataset_hash,
            geometry_version=dataset.metadata.geometry_version,
            solver_version=dataset.metadata.solver_version,
            normalization_hash=bundle.content_hash(),
            n_models=len(self.seeds),
            n_anchors=self.n_anchors,
            status=status,
        )
        write_manifest(self.paths.root / "manifest.json", manifest)
        return manifest

    def _evaluate_points(
        self,
        points: list[SweepPoint],
        *,
        model: StructuralMLP,
        result: SeedTrainingResult,
        normalization: NormalizationBundle,
        cache: FemCache,
        dataset_hash: str,
    ) -> pa.Table:
        inputs = np.asarray([point.inputs for point in points], dtype=np.float64)
        try:
            fea = evaluate_fem_matrix(inputs, cache)
            pred = evaluate_mlp_matrix(
                inputs, model, normalization, self.phase2.performance.mlp_batch_size
            )
        except Exception as exc:
            payload = record_failure(
                experiment_id=self.experiment_id,
                observation_id=f"{result.model_id}:{points[0].variable}:{points[0].direction}",
                stage="variable_wise",
                exc=exc,
            )
            self._append_failure(payload)
            raise
        return self._observation_table(points, fea, pred, result, dataset_hash, normalization)

    def _evaluate_combined(
        self,
        points: tuple[CombinedPoint, ...] | list[CombinedPoint],
        *,
        model: StructuralMLP,
        result: SeedTrainingResult,
        normalization: NormalizationBundle,
        cache: FemCache,
        dataset_hash: str,
    ) -> pa.Table:
        inputs = np.asarray([point.inputs for point in points], dtype=np.float64)
        try:
            fea = evaluate_fem_matrix(inputs, cache)
            pred = evaluate_mlp_matrix(
                inputs, model, normalization, self.phase2.performance.mlp_batch_size
            )
        except Exception as exc:
            payload = record_failure(
                experiment_id=self.experiment_id,
                observation_id=f"{result.model_id}:A3+F",
                stage="combined",
                exc=exc,
            )
            self._append_failure(payload)
            raise
        records: dict[str, list[object]] = {
            name: []
            for name in (
                "experiment_id",
                "model_id",
                "seed",
                "anchor_id",
                "source_sample_id",
                "direction_a3",
                "direction_f",
                "delta_a3",
                "delta_f",
                *INPUT_NAMES,
                "fea_u_max",
                "predicted_u_max",
                "signed_u_max_error",
                "absolute_u_max_error",
                "relative_u_max_error",
                "fea_sigma_max",
                "predicted_sigma_max",
                "signed_sigma_max_error",
                "absolute_sigma_max_error",
                "relative_sigma_max_error",
                "fea_C",
                "predicted_C",
                "signed_C_error",
                "absolute_C_error",
                "relative_C_error",
                "dataset_hash",
                "model_hash",
                "normalization_hash",
                "software_version",
            )
        }
        epsilon = self.phase2.relative_error_epsilon
        for index, point in enumerate(points):
            records["experiment_id"].append(self.experiment_id)
            records["model_id"].append(result.model_id)
            records["seed"].append(result.seed)
            records["anchor_id"].append(point.anchor_id)
            records["source_sample_id"].append(point.source_sample_id)
            records["direction_a3"].append(point.direction_a3)
            records["direction_f"].append(point.direction_f)
            records["delta_a3"].append(point.delta_a3)
            records["delta_f"].append(point.delta_f)
            for name, value in zip(INPUT_NAMES, point.inputs, strict=True):
                records[name].append(value)
            self._fill_errors(records, fea[index], pred[index], epsilon)
            records["dataset_hash"].append(dataset_hash)
            records["model_hash"].append(result.model_hash)
            records["normalization_hash"].append(normalization.content_hash())
            records["software_version"].append(self.phase2.software_version)
        return pa.table(records)

    def _observation_table(
        self,
        points: list[SweepPoint],
        fea: np.ndarray,
        pred: np.ndarray,
        result: SeedTrainingResult,
        dataset_hash: str,
        normalization: NormalizationBundle,
    ) -> pa.Table:
        records: dict[str, list[object]] = {name: [] for name in VARIABLE_WISE_FIELDS}
        epsilon = self.phase2.relative_error_epsilon
        for index, point in enumerate(points):
            records["experiment_id"].append(self.experiment_id)
            records["model_id"].append(result.model_id)
            records["seed"].append(result.seed)
            records["anchor_id"].append(point.anchor_id)
            records["source_sample_id"].append(point.source_sample_id)
            records["variable"].append(point.variable)
            records["direction"].append(point.direction)
            records["delta"].append(point.delta)
            for name, value in zip(INPUT_NAMES, point.inputs, strict=True):
                records[name].append(value)
            self._fill_errors(records, fea[index], pred[index], epsilon)
            records["dataset_hash"].append(dataset_hash)
            records["model_hash"].append(result.model_hash)
            records["normalization_hash"].append(normalization.content_hash())
            records["software_version"].append(self.phase2.software_version)
        return pa.table(records)

    def _fill_errors(
        self,
        records: dict[str, list[object]],
        fea_row: np.ndarray,
        pred_row: np.ndarray,
        epsilon: float,
    ) -> None:
        for response, fea_value, pred_value in zip(OUTPUT_NAMES, fea_row, pred_row, strict=True):
            fea_arr = np.asarray([fea_value], dtype=np.float64)
            pred_arr = np.asarray([pred_value], dtype=np.float64)
            if not np.isfinite(fea_value) or not np.isfinite(pred_value):
                raise ExperimentError(f"non-finite {response} value encountered")
            records[f"fea_{response}"].append(float(fea_value))
            records[f"predicted_{response}"].append(float(pred_value))
            records[f"signed_{response}_error"].append(float(signed_error(pred_arr, fea_arr)[0]))
            records[f"absolute_{response}_error"].append(
                float(absolute_error(pred_arr, fea_arr)[0])
            )
            records[f"relative_{response}_error"].append(
                float(relative_error_pct(pred_arr, fea_arr, epsilon)[0])
            )

    def _merge_chunks(self, chunk_dir: Path, destination: Path) -> pa.Table:
        files = sorted(chunk_dir.glob("*.parquet"))
        if not files:
            raise ExperimentError(f"no parquet chunks in {chunk_dir}")
        tables = [pq.read_table(path) for path in files]
        merged = pa.concat_tables(tables)
        _atomic_write_table(destination, merged, self.repo_root)
        return merged

    def _append_failure(self, payload: dict[str, str]) -> None:
        path = self.paths.failures / "failures.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def _load_model(self, seed: int) -> StructuralMLP:
        return restore_model(self.paths.model_dir(seed), self.repo_root)

    def _require_dataset(self) -> LoadedPhase1Dataset:
        if self.dataset is None:
            return self.validate_phase1()
        return self.dataset

    def _require_normalization(self) -> NormalizationBundle:
        if self.normalization is None:
            stored = self.paths.root / "normalization.json"
            if stored.is_file():
                self.normalization = NormalizationBundle.model_validate_json(
                    stored.read_text(encoding="utf-8")
                )
                return self.normalization
            return self.fit_normalization()
        return self.normalization

    def _fem_cache(self) -> FemCache:
        if self.fem_cache is None:
            self.fem_cache = make_fem_cache(self.phase1, self.phase2.performance.fem_cache)
        return self.fem_cache

    def _anchor_config(self) -> Phase2Config:
        if self.n_anchors == self.phase2.anchors.count:
            return self.phase2
        return self.phase2.model_copy(
            update={"anchors": self.phase2.anchors.model_copy(update={"count": self.n_anchors})}
        )


def _atomic_write_table(path: Path, table: pa.Table, repo_root: Path) -> None:
    target = confine_under_data_root(path, repo_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    pq.write_table(table, tmp, compression="zstd")
    tmp.replace(target)
