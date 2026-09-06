# Phase 3 reproducibility

## What Phase 3 must not change

Phase 3 does not alter `configs/scientific.yaml`, `configs/phase2.yaml`, the Phase 1 dataset, or completed `paper-a.phase2.*` trees.

## Job execution

API jobs construct `Phase2Runner` with the same Phase 1/2 configs used by the CLI. Tiny IDs (`*.tiny*` / `*-pilot-tiny`) use the existing pilot reductions (2 anchors, one seed, A3, three deltas, skip combined). That is an execution profile, not a change to the frozen protocol for `paper-a.phase2.v1`.

## Restart

On process start, `running` jobs become `failed` with `STALE_AFTER_RESTART`. `cancel_requested` jobs become `cancelled`. Completed/failed/queued rows are left as stored. Progress is not fabricated after restart.

## Resume

Scientific resume remains inside `Phase2Runner` (chunk files). The application layer does not rewrite observation Parquet to invent missing rows.
