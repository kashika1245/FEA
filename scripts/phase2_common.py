"""Shared Phase 2 script bootstrap."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.scientific.config import load_scientific_config
from app.scientific.experiments.runner import Phase2Runner
from app.scientific.surrogate.config import load_phase2_config


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--phase1-config", type=Path, default=Path("configs/scientific.yaml"))
    parser.add_argument("--phase2-config", type=Path, default=Path("configs/phase2.yaml"))
    parser.add_argument("--experiment-id", type=str, default=None)
    parser.add_argument("--n-anchors", type=int, default=None)
    parser.add_argument("--seeds", type=int, nargs="*", default=None)
    parser.add_argument("--variables", type=str, nargs="*", default=None)
    parser.add_argument("--deltas", type=float, nargs="*", default=None)


def build_runner(args: argparse.Namespace) -> Phase2Runner:
    logging.basicConfig(level=logging.INFO)
    phase1 = load_scientific_config(args.phase1_config)
    phase2 = load_phase2_config(args.phase2_config)
    return Phase2Runner(
        phase1,
        phase2,
        experiment_id=args.experiment_id,
        n_anchors=args.n_anchors,
        seeds=tuple(args.seeds) if args.seeds else None,
        variables=tuple(args.variables) if args.variables else None,
        deltas=tuple(args.deltas) if args.deltas else None,
    )
