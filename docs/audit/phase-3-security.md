# Phase 3 security

## Authorization

Phase 3 is research infrastructure. It assumes a trusted network boundary. Mutating routes are not separately authenticated. Authentication can be added at the reverse proxy without changing scientific code.

## Path confinement

- Experiment IDs are token-shaped; `..` and separators are rejected.
- Artifact relative paths reject leading `/`, `\`, `:`, `..` segments, and encoded traversal after decode.
- Artifact IDs are opaque base64 tokens; `GET /file?path=` does not exist.
- Resolved paths must stay under `data/experiments/{id}`.
- Symlink hops under the experiment root are rejected before serve.

Executed tests include `../../etc/passwd`, `..\\..\\`, `%2e%2e/`, absolute paths, and symlink escape.

## Execution

No `shell=True`, `os.system`, `eval`, `exec`, or `yaml.load` in application code. Jobs call `Phase2Runner` in-process. Models are `npz` + JSON, not pickle.

## Input validation

Pydantic `extra=forbid` on request bodies. Experiment create is restricted to `paper-a.phase3.*`. Pagination limits cap list size. Unknown job types cannot be invented beyond the `JobType` enum.

## Resource protection

- `max_running_jobs = 1`
- Experiment write lock in SQLite
- Mutating request counter (`mutate_rate_limit = 30` per process)
- Artifact hashing bounded to 50 MB files

## Disposition of scan

`scripts/audit_phase3.py` reported no forbidden execution, unsafe YAML, or scientific→web imports.

`model.eval()` hits in scientific training/evaluation are PyTorch inference mode, not Python `eval`.
