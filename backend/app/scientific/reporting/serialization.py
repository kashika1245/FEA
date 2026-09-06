"""JSON/Markdown writers for generated scientific tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pyarrow as pa

from app.scientific.reproducibility import canonical_json_bytes


def table_to_records(table: pa.Table) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], table.to_pylist())


def write_json(path: Path, payload: Any) -> None:
    if isinstance(payload, dict):
        path.write_bytes(canonical_json_bytes(payload))
        return
    path.write_text(
        __import__("json").dumps(payload, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join([head, sep, body])
