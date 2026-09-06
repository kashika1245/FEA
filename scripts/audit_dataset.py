"""Write docs/audit/dataset-quality-report.md from a generated dataset artefact."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.scientific.config import load_scientific_config
from app.scientific.dataset.metadata import DatasetMetadata
from app.scientific.dataset.storage import read_parquet
from app.scientific.dataset.validation import validate_dataset_rows
from app.scientific.reproducibility import repo_root_from_package, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a generated FEM dataset")
    parser.add_argument("--config", type=Path, default=Path("configs/scientific.yaml"))
    parser.add_argument("--dataset-dir", type=Path, default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = load_scientific_config(args.config)
    root = repo_root_from_package()
    dataset_dir = args.dataset_dir
    if dataset_dir is None:
        dataset_id = (
            f"{config.dataset_version}-n{config.dataset.n_samples}-seed{config.dataset.random_seed}"
        )
        dataset_dir = root / "data" / "datasets" / dataset_id
    metadata_path = dataset_dir / "metadata.json"
    parquet_path = dataset_dir / "dataset.parquet"
    metadata = DatasetMetadata.model_validate_json(metadata_path.read_text(encoding="utf-8"))
    rows = read_parquet(parquet_path, repo_root=root)
    quality = validate_dataset_rows(rows, config, failed_fea_count=metadata.failed_fea_count)
    recomputed_hash = sha256_file(parquet_path)
    report_path = root / "docs" / "audit" / "dataset-quality-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    body = f"""# Dataset Quality Report

Generated programmatically by `scripts/audit_dataset.py`. Values are read from the artefact, not invented.

| Field | Value |
|-------|-------|
| dataset_id | `{metadata.dataset_id}` |
| sample_count | {quality.sample_count} |
| requested_sample_count | {metadata.requested_sample_count} |
| column_count | {quality.column_count} |
| missing_value_count | {quality.missing_value_count} |
| nan_count | {quality.nan_count} |
| inf_count | {quality.inf_count} |
| duplicate_id_count | {quality.duplicate_id_count} |
| duplicate_input_count | {quality.duplicate_input_count} |
| out_of_domain_count | {quality.out_of_domain_count} |
| nonfinite_output_count | {quality.nonfinite_output_count} |
| failed_fea_count | {quality.failed_fea_count} |
| random_seed | {metadata.random_seed} |
| geometry_version | `{metadata.geometry_version}` |
| solver_version | `{metadata.solver_version}` |
| software_version | `{metadata.software_version}` |
| git_commit | `{metadata.git_commit}` |
| dataset_hash | `{metadata.dataset_hash}` |
| dataset_hash_recomputed | `{recomputed_hash}` |
| configuration_hash | `{metadata.configuration_hash}` |
| quality_ok | {quality.ok} |

## Input and output ranges

```json
{json.dumps({"min": quality.min_values, "max": quality.max_values}, indent=2, sort_keys=True)}
```

## Notes

{chr(10).join(f"- {note}" for note in quality.notes) if quality.notes else "- none"}
"""
    report_path.write_text(body, encoding="utf-8")
    print(report_path)
    return 0 if quality.ok and recomputed_hash == metadata.dataset_hash else 1


if __name__ == "__main__":
    raise SystemExit(main())
