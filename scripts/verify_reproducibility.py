"""Generate a small dataset twice and compare content hashes and rows."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.scientific.config import load_scientific_config
from app.scientific.dataset.generator import generate_dataset
from app.scientific.dataset.storage import read_parquet
from app.scientific.reproducibility import repo_root_from_package


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify dataset reproducibility")
    parser.add_argument("--config", type=Path, default=Path("configs/scientific.yaml"))
    parser.add_argument("--n-samples", type=int, default=20)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = load_scientific_config(args.config)
    root = repo_root_from_package()
    a = generate_dataset(
        config,
        output_dir=root / "data" / "validation" / "repro-a",
        n_samples=args.n_samples,
        dataset_id="repro-a",
        repo_root=root,
    )
    b = generate_dataset(
        config,
        output_dir=root / "data" / "validation" / "repro-b",
        n_samples=args.n_samples,
        dataset_id="repro-b",
        repo_root=root,
    )
    alt = config.model_copy(
        update={
            "dataset": config.dataset.model_copy(
                update={"random_seed": config.dataset.random_seed + 1}
            )
        }
    )
    c = generate_dataset(
        alt,
        output_dir=root / "data" / "validation" / "repro-c",
        n_samples=args.n_samples,
        dataset_id="repro-c",
        repo_root=root,
    )
    rows_a = read_parquet(a.parquet_path, repo_root=root)
    rows_b = read_parquet(b.parquet_path, repo_root=root)
    identical = a.metadata.dataset_hash == b.metadata.dataset_hash and rows_a == rows_b
    seed_changes = a.metadata.dataset_hash != c.metadata.dataset_hash
    report = {
        "n_samples": args.n_samples,
        "hash_a": a.metadata.dataset_hash,
        "hash_b": b.metadata.dataset_hash,
        "hash_alt_seed": c.metadata.dataset_hash,
        "configuration_hash": a.metadata.configuration_hash,
        "identical_repeat": identical,
        "different_seed_changes_hash": seed_changes,
        "passed": identical and seed_changes,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
