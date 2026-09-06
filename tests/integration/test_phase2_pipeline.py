from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from app.scientific.config import load_default_scientific_config
from app.scientific.experiments.runner import Phase2Runner
from app.scientific.surrogate.config import load_default_phase2_config
from app.scientific.surrogate.dataset import inputs_of, load_and_validate_phase1_dataset, outputs_of
from app.scientific.surrogate.normalization import fit_train_only_normalization

DATASET_ID = "paper-a.phase1.v1-n10000-seed20260905"


def _prepare_repo(tmp_path: Path) -> Path:
    source = Path(__file__).resolve().parents[2]
    src = source / "data" / "datasets" / DATASET_ID
    dst = tmp_path / "data" / "datasets" / DATASET_ID
    dst.mkdir(parents=True)
    shutil.copy2(src / "dataset.parquet", dst / "dataset.parquet")
    shutil.copy2(src / "metadata.json", dst / "metadata.json")
    return tmp_path


def _runner(tmp_path: Path, experiment_id: str, deltas: tuple[float, ...]) -> Phase2Runner:
    phase1 = load_default_scientific_config()
    phase2 = load_default_phase2_config()
    return Phase2Runner(
        phase1,
        phase2,
        experiment_id=experiment_id,
        n_anchors=2,
        seeds=(20260905,),
        variables=("A3",),
        deltas=deltas,
        repo_root=tmp_path,
    )


def test_tiny_pilot_and_resume(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    runner = _runner(root, "phase2-resume-a", (0.0, 0.25, 0.50))
    runner.validate_phase1()
    runner.fit_normalization()
    runner.train_seeds()
    runner.evaluate_interpolation()
    runner.select_anchors()
    runner.run_variable_wise(resume=False)
    observations = root / "data/experiments/phase2-resume-a/extrapolation/observations.parquet"
    table = pq.read_table(observations)
    assert table.num_rows == 2 * 1 * 2 * 3 * 1
    chunk = next((root / "data/experiments/phase2-resume-a/extrapolation/chunks").glob("*.parquet"))
    chunk.unlink()
    runner.run_variable_wise(resume=True)
    resumed = pq.read_table(observations)
    assert resumed.num_rows == table.num_rows
    assert np.allclose(
        resumed.column("predicted_u_max").to_numpy(),
        table.column("predicted_u_max").to_numpy(),
    )


def test_reproducible_tiny_run(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    hashes = []
    for name in ("phase2-repro-a", "phase2-repro-b"):
        runner = _runner(root, name, (0.0, 0.50))
        runner.validate_phase1()
        runner.fit_normalization()
        runner.train_seeds()
        runner.select_anchors()
        runner.run_variable_wise(resume=False)
        table = pq.read_table(
            root / "data/experiments" / name / "extrapolation/observations.parquet"
        )
        hashes.append(
            (
                table.column("A3").to_pylist(),
                table.column("fea_u_max").to_pylist(),
                table.column("predicted_u_max").to_pylist(),
            )
        )
    assert hashes[0] == hashes[1]


def test_train_only_normalization_count() -> None:
    dataset = load_and_validate_phase1_dataset()
    bundle = fit_train_only_normalization(
        inputs_of(dataset.train), outputs_of(dataset.train), dataset.dataset_hash
    )
    assert bundle.inputs.training_sample_count == 7000
    assert bundle.outputs.training_sample_count == 7000
