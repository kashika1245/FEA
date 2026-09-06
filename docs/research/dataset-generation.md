# Dataset Generation

## Sampling

Each sample \(i = 1\ldots N\) is drawn from an independent `numpy.random.Generator(PCG64)` whose seed is

```
SeedSequence(master_seed).spawn(N)[i-1]
```

Master seed (frozen): `20260905`.

Twelve independent uniforms are drawn, in order: \(A_1\ldots A_{10}\), then \(E\), then \(F\), using `Generator.uniform(low, high)` which is the half-open interval `[low, high)`. Domain validation still requires the closed interval of the specification.

Split labels are assigned by a separate generator `PCG64(SeedSequence([master_seed, 1]))` permuting IDs `1…N` into 70% / 15% / 15% using `int(N*fraction)` for train and validation, with the remainder going to interpolation test. For \(N=10000\) this is exactly 7000 / 1500 / 1500.

## FEM pipeline per sample

1. Draw paper-unit parameters.
2. Reject if outside the training domain (should not happen for the sampler).
3. Convert \(E\) and \(F\) into internal units.
4. `analyze(canonical_ten_bar_truss(), parameters)`.
5. Persist a `DatasetRow` in paper units.

In-domain FEM failure is a job failure. NaN/zero/fake rows are not written to the primary dataset. The failure is recorded in `failures.jsonl` and generation stops.

## Checkpointing

Directory: `data/datasets/<dataset_id>/`

| File | Role |
|------|------|
| `samples.jsonl` | append-only complete rows, `fsync` after each write |
| `checkpoint.json` | completed count, IDs, status (`in_progress` / `completed` / `failed`) |
| `failures.jsonl` | structured FEM failures |
| `dataset.parquet` | final artefact (written only after all rows exist) |
| `metadata.json` | provenance + hashes |

A line without a trailing newline is treated as incomplete and is not loaded. Complete JSONL lines that fail to parse raise `CheckpointError` (they are corrupt, not truncated).

Resume skips sample IDs already present. Because RNGs are per-sample, skipped IDs do not alter later draws.

## Storage

Parquet (zstd), non-nullable columns, unit metadata on fields. Chosen for numerical fidelity, portable reads, and content hashing of file bytes. Phase 1 does not duplicate the table into PostgreSQL.

## Hashing

- `configuration_hash`: SHA-256 of canonical JSON of `ScientificConfig.model_dump()` plus the frozen geometry payload (nodes, members, supports, loads, DOF map). No timestamps.
- `dataset_hash`: SHA-256 of the Parquet file bytes.

## Reproducibility

The same geometry, configuration, seed, software, and algorithm must reproduce bit-identical Parquet hashes on the same platform numpy build. Tests generate small \(N\) twice and compare rows and hashes, then confirm a different seed changes the hash.
