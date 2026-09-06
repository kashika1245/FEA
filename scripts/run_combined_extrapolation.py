"""Run the A3 + F combined extrapolation case study."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase2_common import add_common_args, build_runner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    runner = build_runner(args)
    runner.validate_phase1()
    runner.fit_normalization()
    runner.train_seeds()
    runner.select_anchors()
    runner.run_combined(resume=not args.no_resume)
    runner.write_manifest("combined_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
