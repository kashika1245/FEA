from __future__ import annotations

from pathlib import Path

from app.scientific.config import ScientificConfig
from app.scientific.dataset.generator import generate_dataset
from app.scientific.dataset.storage import read_parquet
from app.scientific.dataset.validation import validate_dataset_rows
from app.scientific.reproducibility import sha256_file


def test_n10_generation_and_quality(config: ScientificConfig, tmp_path: Path) -> None:
    data_repo = tmp_path
    (data_repo / "data").mkdir()
    result = generate_dataset(
        config,
        output_dir=data_repo / "data" / "datasets" / "n10",
        n_samples=10,
        resume=True,
        repo_root=data_repo,
        dataset_id="n10",
    )
    assert result.quality.ok
    assert result.quality.sample_count == 10
    assert result.metadata.sample_count == 10
    assert result.metadata.failed_fea_count == 0
    rows = read_parquet(result.parquet_path, repo_root=data_repo)
    assert [row.sample_id for row in rows] == list(range(1, 11))
    assert all(row.u_max > 0.0 and row.sigma_max > 0.0 and row.C > 0.0 for row in rows)


def test_checkpoint_resume(config: ScientificConfig, tmp_path: Path) -> None:
    data_repo = tmp_path
    (data_repo / "data").mkdir()
    directory = data_repo / "data" / "datasets" / "resume"
    first = generate_dataset(
        config,
        output_dir=directory,
        n_samples=8,
        resume=True,
        repo_root=data_repo,
        dataset_id="resume",
    )
    samples_path = directory / "samples.jsonl"
    lines = samples_path.read_text(encoding="utf-8").splitlines()
    samples_path.write_text("\n".join(lines[:5]) + "\n", encoding="utf-8")
    resumed = generate_dataset(
        config,
        output_dir=directory,
        n_samples=8,
        resume=True,
        repo_root=data_repo,
        dataset_id="resume",
    )
    assert resumed.quality.sample_count == 8
    assert resumed.metadata.dataset_hash == first.metadata.dataset_hash
    assert sha256_file(resumed.parquet_path) == first.metadata.dataset_hash


def test_reproducible_repeat(config: ScientificConfig, tmp_path: Path) -> None:
    data_repo = tmp_path
    (data_repo / "data").mkdir()
    a = generate_dataset(
        config,
        output_dir=data_repo / "data" / "datasets" / "a",
        n_samples=12,
        repo_root=data_repo,
        dataset_id="a",
    )
    b = generate_dataset(
        config,
        output_dir=data_repo / "data" / "datasets" / "b",
        n_samples=12,
        repo_root=data_repo,
        dataset_id="b",
    )
    assert a.metadata.dataset_hash == b.metadata.dataset_hash
    assert a.metadata.configuration_hash == b.metadata.configuration_hash
    rows_a = read_parquet(a.parquet_path, repo_root=data_repo)
    rows_b = read_parquet(b.parquet_path, repo_root=data_repo)
    assert rows_a == rows_b
    quality = validate_dataset_rows(
        rows_a,
        config.model_copy(update={"dataset": config.dataset.model_copy(update={"n_samples": 12})}),
        failed_fea_count=0,
    )
    assert quality.ok
