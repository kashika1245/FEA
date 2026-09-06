"""Build Phase 2 tables, plots, and report stubs from stored artefacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.scientific.reporting.plots import (
    write_combined_heatmaps,
    write_interpolation_plots,
    write_profile_plots,
)
from app.scientific.reporting.tables import (
    write_asymmetry_table,
    write_combined_table,
    write_interpolation_table,
    write_profile_table,
    write_seed_variability_table,
    write_threshold_markdown,
)
from phase2_common import add_common_args, build_runner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    runner = build_runner(args)
    runner.validate_phase1()
    paths = runner.paths
    write_interpolation_table(paths)
    write_interpolation_plots(paths)
    write_profile_table(paths)
    write_threshold_markdown(paths)
    write_asymmetry_table(paths)
    write_seed_variability_table(paths)
    write_profile_plots(paths)
    write_combined_table(paths)
    write_combined_heatmaps(paths)
    runner.write_manifest("reports_written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
