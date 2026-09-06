"""Forensic audit of Phase 2 source and generated artefacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.scientific.reproducibility import repo_root_from_package, sha256_file
from app.scientific.surrogate.dataset import EXPECTED_DATASET_HASH, load_and_validate_phase1_dataset

FORBIDDEN = (
    "TODO",
    "FIXME",
    "NotImplemented",
    "hardcoded prediction",
    "hardcoded metric",
    "hardcoded profile",
)

ALLOWED_PASS_FILES = {
    "backend/app/scientific/surrogate/training.py",
}


def _scan(root: Path) -> list[str]:
    findings: list[str] = []
    roots = [
        root / "backend" / "app" / "scientific" / "surrogate",
        root / "backend" / "app" / "scientific" / "extrapolation",
        root / "backend" / "app" / "scientific" / "experiments",
        root / "backend" / "app" / "scientific" / "reporting",
        root / "scripts",
        root / "tests" / "unit",
        root / "tests" / "scientific",
        root / "tests" / "integration",
    ]
    pattern = re.compile("|".join(re.escape(token) for token in FORBIDDEN))
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(root))
            if path.name == "audit_phase2.py":
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line) and "FORBIDDEN" not in line:
                    findings.append(f"{rel}:{lineno}:{line.strip()}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-id", default="paper-a.phase2.v1")
    args = parser.parse_args()
    root = repo_root_from_package()
    dataset = load_and_validate_phase1_dataset()
    findings = _scan(root)
    experiment = root / "data" / "experiments" / args.experiment_id
    parquet = experiment / "extrapolation" / "observations.parquet"
    report = {
        "phase1_hash": dataset.dataset_hash,
        "phase1_hash_expected": EXPECTED_DATASET_HASH,
        "phase1_hash_match": dataset.dataset_hash == EXPECTED_DATASET_HASH,
        "forensic_findings": findings,
        "experiment_dir": str(experiment),
        "observations_exist": parquet.is_file(),
        "observations_hash": sha256_file(parquet) if parquet.is_file() else None,
    }
    out = experiment / "reports" / "forensic_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
