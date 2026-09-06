"""Path confinement and Parquet I/O. No pickle."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from app.scientific.dataset.schema import COLUMN_ORDER, COLUMN_UNITS, DatasetRow
from app.scientific.exceptions import DatasetError, StorageSecurityError
from app.scientific.reproducibility import repo_root_from_package


def data_root(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else repo_root_from_package()
    return (root / "data").resolve()


def confine_under_data_root(path: Path, repo_root: Path | None = None) -> Path:
    resolved = path.expanduser().resolve()
    root = data_root(repo_root)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise StorageSecurityError(f"path {resolved} is outside data root {root}") from exc
    return resolved


def write_parquet(rows: list[DatasetRow], path: Path, repo_root: Path | None = None) -> Path:
    target = confine_under_data_root(path, repo_root)
    if not rows:
        raise DatasetError("refusing to write an empty parquet dataset")
    target.parent.mkdir(parents=True, exist_ok=True)
    arrays: dict[str, list[object]] = {name: [] for name in COLUMN_ORDER}
    for row in rows:
        payload = row.to_ordered_dict()
        for name in COLUMN_ORDER:
            arrays[name].append(payload[name])
    fields = []
    for name in COLUMN_ORDER:
        if name == "sample_id":
            pa_type: pa.DataType = pa.int64()
        elif name == "split":
            pa_type = pa.string()
        else:
            pa_type = pa.float64()
        fields.append(
            pa.field(name, pa_type, nullable=False, metadata={"unit": COLUMN_UNITS[name]})
        )
    table = pa.table(arrays, schema=pa.schema(fields))
    tmp = target.with_suffix(target.suffix + ".tmp")
    pq.write_table(table, tmp, compression="zstd")
    tmp.replace(target)
    return target


def read_parquet(path: Path, repo_root: Path | None = None) -> list[DatasetRow]:
    target = confine_under_data_root(path, repo_root)
    if not target.is_file():
        raise DatasetError(f"parquet file does not exist: {target}")
    table = pq.read_table(target)
    names = table.column_names
    if names != list(COLUMN_ORDER):
        raise DatasetError(f"unexpected parquet columns {names}, expected {list(COLUMN_ORDER)}")
    rows: list[DatasetRow] = []
    for index in range(table.num_rows):
        payload = {name: table.column(name)[index].as_py() for name in COLUMN_ORDER}
        rows.append(DatasetRow.model_validate(payload))
    return rows
