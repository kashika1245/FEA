# Phase 3 data integrity

## Source of truth

Scientific numbers come from stored Parquet/JSON artefacts or from a real `Phase2Runner` execution. SQLite stores only application state (jobs, locks, schema version).

## Verified frozen hashes (executed)

| Artefact | Value |
|----------|--------|
| Phase 1 dataset SHA-256 | `a78de261b1686363ed6d830cd370b763800da657bce0991047fe43fb9504e99e` |
| Phase 2 normalization | `ff0c27f6faf4f812e49f8e165cb4584cd310d47b83c743c35280d75a97360327` |
| Variable-wise rows | 132000 |
| Combined rows | 242000 |
| Profile rows | 3960 |

The API research routes for `paper-a.phase2.v1` returned these same counts and the same dataset hash. Phase 1 Parquet was not rewritten.

## Artifact metadata

Inventory records experiment id, relative path, media type, size, and SHA-256 for files ≤ 50 MB. Incomplete job trees are not advertised as completed unless the job state is `completed` and a manifest exists.

## Retention

Authoritative Phase 1/2 trees are never auto-deleted. Incomplete Phase 3 directories remain for audit until an operator removes them.
