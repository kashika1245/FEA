"""Aggregate median/IQR profiles and empirical threshold crossings."""

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
    runner.build_profiles()
    runner.write_manifest("profiles_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
