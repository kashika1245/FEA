"""Append-only JSONL checkpointing with fsync. Incomplete last lines are not treated as rows."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from app.scientific.dataset.schema import DatasetRow
from app.scientific.dataset.storage import confine_under_data_root
from app.scientific.exceptions import CheckpointError
from app.scientific.reproducibility import canonical_json_bytes


@dataclass(frozen=True, slots=True)
class CheckpointState:
    dataset_id: str
    n_samples: int
    seed: int
    completed_ids: frozenset[int]
    status: str


class CheckpointStore:
    def __init__(self, directory: Path, dataset_id: str, repo_root: Path | None = None) -> None:
        self.directory = confine_under_data_root(directory, repo_root)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.dataset_id = dataset_id
        self.samples_path = self.directory / "samples.jsonl"
        self.failures_path = self.directory / "failures.jsonl"
        self.checkpoint_path = self.directory / "checkpoint.json"

    def load_completed_rows(self) -> list[DatasetRow]:
        if not self.samples_path.is_file():
            return []
        rows: list[DatasetRow] = []
        seen: set[int] = set()
        try:
            text = self.samples_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CheckpointError(f"cannot read checkpoint samples: {exc}") from exc
        if not text:
            return []
        lines = text.split("\n")
        complete_lines = lines[:-1] if not text.endswith("\n") else lines
        for line in complete_lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                row = DatasetRow.model_validate(payload)
            except (json.JSONDecodeError, ValueError) as exc:
                raise CheckpointError(f"corrupt complete checkpoint line: {exc}") from exc
            if row.sample_id in seen:
                raise CheckpointError(f"duplicate sample_id {row.sample_id} in checkpoint")
            seen.add(row.sample_id)
            rows.append(row)
        return rows

    def append_row(self, row: DatasetRow) -> None:
        payload = row.to_ordered_dict()
        line = canonical_json_bytes(payload).decode("ascii") + "\n"
        self._append_line(self.samples_path, line)

    def append_failure(self, payload: dict[str, object]) -> None:
        line = canonical_json_bytes(payload).decode("ascii") + "\n"
        self._append_line(self.failures_path, line)

    def write_status(self, n_samples: int, seed: int, completed_ids: set[int], status: str) -> None:
        body = {
            "dataset_id": self.dataset_id,
            "n_samples": n_samples,
            "seed": seed,
            "completed_count": len(completed_ids),
            "status": status,
        }
        encoded = canonical_json_bytes(body)
        tmp = self.checkpoint_path.with_suffix(".json.tmp")
        tmp.write_bytes(encoded)
        with tmp.open("rb") as handle:
            os.fsync(handle.fileno())
        tmp.replace(self.checkpoint_path)

    def _append_line(self, path: Path, line: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
