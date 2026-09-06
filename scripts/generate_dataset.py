"""Generate or resume a Paper A FEM dataset."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.scientific.config import load_scientific_config
from app.scientific.dataset.generator import generate_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Paper A FEM dataset")
    parser.add_argument("--config", type=Path, default=Path("configs/scientific.yaml"))
    parser.add_argument("--n-samples", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--dataset-id", type=str, default=None)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    config = load_scientific_config(args.config)
    result = generate_dataset(
        config,
        output_dir=args.output_dir,
        n_samples=args.n_samples,
        resume=not args.no_resume,
        dataset_id=args.dataset_id,
    )
    print(result.metadata.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
