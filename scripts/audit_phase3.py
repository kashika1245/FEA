#!/usr/bin/env python3
"""Forensic scan of Phase 3 application code. Does not mutate scientific artefacts."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "backend" / "app" / "api",
    ROOT / "backend" / "app" / "application",
    ROOT / "backend" / "app" / "infrastructure",
    ROOT / "backend" / "app" / "main.py",
)
FORBIDDEN_CALLS = {"eval", "exec", "os.system"}
FINDINGS: list[str] = []


def scan_file(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in FORBIDDEN_CALLS
        ):
            FINDINGS.append(f"{path}:{node.lineno}: forbidden call {node.func.id}")
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "system"
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
        ):
            FINDINGS.append(f"{path}:{node.lineno}: os.system")
        if (
            isinstance(node, ast.keyword)
            and node.arg == "shell"
            and isinstance(node.value, ast.Constant)
            and node.value.value is True
        ):
            FINDINGS.append(f"{path}:{node.lineno}: shell=True")
        if (
            isinstance(node, ast.Attribute)
            and node.attr in {"load", "unsafe_load"}
            and isinstance(node.value, ast.Name)
            and node.value.id == "yaml"
        ):
            FINDINGS.append(f"{path}:{node.lineno}: yaml.{node.attr}")


def scientific_imports_web() -> None:
    scientific = ROOT / "backend" / "app" / "scientific"
    banned = ("fastapi", "starlette", "uvicorn", "app.api", "app.application", "app.infrastructure")
    for path in scientific.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if f"import {token}" in text or f"from {token}" in text:
                FINDINGS.append(f"{path}: scientific module imports {token}")


def main() -> int:
    for target in TARGETS:
        paths = [target] if target.is_file() else list(target.rglob("*.py"))
        for path in paths:
            scan_file(path)
    scientific_imports_web()
    if FINDINGS:
        print("PHASE 3 AUDIT FINDINGS")
        for item in FINDINGS:
            print(item)
        return 1
    print("phase-3 source scan: no forbidden execution, unsafe YAML, or layer-boundary imports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
