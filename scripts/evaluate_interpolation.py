"""Evaluate interpolation competence on the frozen interpolation_test split."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase2_common import add_common_args, build_runner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    runner = build_runner(args)
    runner.validate_phase1()
    runner.fit_normalization()
    runner.train_seeds()
    runner.evaluate_interpolation()
    runner.write_manifest("interpolation_evaluated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
