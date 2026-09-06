from __future__ import annotations

from pathlib import Path

from app.scientific.reproducibility import sha256_file
from app.scientific.surrogate.dataset import EXPECTED_DATASET_HASH
from app.scientific.surrogate.normalization import NormalizationBundle

REPO = Path(__file__).resolve().parents[2]
PHASE2 = REPO / "data" / "experiments" / "paper-a.phase2.v1"
DATASET = REPO / "data" / "datasets" / "paper-a.phase1.v1-n10000-seed20260905" / "dataset.parquet"
EXPECTED_NORM = "ff0c27f6faf4f812e49f8e165cb4584cd310d47b83c743c35280d75a97360327"


def test_phase1_dataset_hash_unchanged() -> None:
    assert sha256_file(DATASET) == EXPECTED_DATASET_HASH


def test_phase2_normalization_and_counts_unchanged() -> None:
    import json

    import pyarrow.parquet as pq

    manifest = json.loads((PHASE2 / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_hash"] == EXPECTED_DATASET_HASH
    assert manifest["normalization_hash"] == EXPECTED_NORM
    assert (
        pq.ParquetFile(PHASE2 / "extrapolation" / "observations.parquet").metadata.num_rows
        == 132000
    )
    assert pq.ParquetFile(PHASE2 / "combined" / "observations.parquet").metadata.num_rows == 242000
    assert pq.ParquetFile(PHASE2 / "profiles" / "profiles.parquet").metadata.num_rows == 3960
    stored = NormalizationBundle.model_validate_json(
        (PHASE2 / "normalization.json").read_text(encoding="utf-8")
    )
    assert stored.content_hash() == EXPECTED_NORM
