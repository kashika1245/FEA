from __future__ import annotations

from pathlib import Path

from app.scientific.config import ScientificConfig
from app.scientific.dataset.generator import generate_dataset
from app.scientific.dataset.sampling import draw_paper_unit_sample
from app.scientific.dataset.storage import read_parquet
from app.scientific.reproducibility import sha256_file


def test_dataset_hash_changes_with_content(config: ScientificConfig, tmp_path: Path) -> None:
    data_repo = tmp_path
    (data_repo / "data").mkdir()
    first = generate_dataset(
        config,
        output_dir=data_repo / "data" / "datasets" / "h1",
        n_samples=10,
        repo_root=data_repo,
        dataset_id="h1",
    )
    alt_seed = config.model_copy(
        update={
            "dataset": config.dataset.model_copy(
                update={"random_seed": config.dataset.random_seed + 7}
            )
        }
    )
    second = generate_dataset(
        alt_seed,
        output_dir=data_repo / "data" / "datasets" / "h2",
        n_samples=10,
        repo_root=data_repo,
        dataset_id="h2",
    )
    assert first.metadata.dataset_hash != second.metadata.dataset_hash
    assert sha256_file(first.parquet_path) == first.metadata.dataset_hash
    rows = read_parquet(first.parquet_path, repo_root=data_repo)
    assert len(rows) == 10
    sample = draw_paper_unit_sample(1, 10, config.dataset.random_seed, config.parameter_domain)
    assert sample.areas_mm2[0] == rows[0].A1
    assert sample.e_gpa == rows[0].E
    assert sample.f_kn == rows[0].F
