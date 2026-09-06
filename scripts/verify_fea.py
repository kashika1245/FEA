"""Run a canonical FEA analysis and print scalar diagnostics."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.scientific.canonical import canonical_ten_bar_truss
from app.scientific.config import load_scientific_config
from app.scientific.fem.solver import analyze
from app.scientific.parameters import StructuralParameters


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the canonical 10-bar FEM oracle")
    parser.add_argument("--config", type=Path, default=Path("configs/scientific.yaml"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = load_scientific_config(args.config)
    model = canonical_ten_bar_truss(config=config)
    parameters = StructuralParameters.uniform(model, 75.0, 200.0, 5.0)
    result = analyze(model, parameters, config)
    payload = {
        "validated": result.validated,
        "geometry_version": result.geometry_version,
        "solver_version": result.solver_version,
        "u_max_mm": result.u_max_mm,
        "u_max_node_id": result.u_max_node_id,
        "sigma_max_n_per_mm2": result.sigma_max_n_per_mm2,
        "sigma_max_member_id": result.sigma_max_member_id,
        "compliance_nmm": result.compliance_nmm,
        "condition_number": result.diagnostics.condition_number,
        "stiffness_symmetry_residual": result.diagnostics.stiffness_symmetry_residual,
        "reduced_residual_norm": result.diagnostics.reduced_residual_norm,
        "equilibrium_sum_fx_n": result.diagnostics.equilibrium_sum_fx_n,
        "equilibrium_sum_fy_n": result.diagnostics.equilibrium_sum_fy_n,
        "equilibrium_sum_mz_nmm": result.diagnostics.equilibrium_sum_mz_nmm,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
