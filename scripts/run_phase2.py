"""Execute the complete Phase 2 scientific pipeline."""

from __future__ import annotations

import argparse
import sys
import time
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
from app.scientific.surrogate.logging_util import get_logger, log_event
from phase2_common import add_common_args, build_runner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--skip-combined", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    started = time.perf_counter()
    runner = build_runner(args)
    logger = get_logger()
    log_event(logger, "experiment_start", experiment_id=runner.experiment_id)
    runner.validate_phase1()
    runner.fit_normalization()
    runner.train_seeds()
    runner.evaluate_interpolation()
    runner.select_anchors()
    runner.run_variable_wise(resume=not args.no_resume)
    runner.build_profiles()
    if not args.skip_combined:
        runner.run_combined(resume=not args.no_resume)
    write_interpolation_table(runner.paths)
    write_interpolation_plots(runner.paths)
    write_profile_table(runner.paths)
    write_threshold_markdown(runner.paths)
    write_asymmetry_table(runner.paths)
    write_seed_variability_table(runner.paths)
    write_profile_plots(runner.paths)
    if (runner.paths.combined / "observations.parquet").is_file():
        write_combined_table(runner.paths)
        write_combined_heatmaps(runner.paths)
    runner.write_manifest("completed")
    log_event(
        logger,
        "experiment_complete",
        experiment_id=runner.experiment_id,
        elapsed_s=time.perf_counter() - started,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
