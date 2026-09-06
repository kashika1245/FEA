# Phase 2 Performance

Measured on this machine during the executed runs. Not estimates.

| Run | Wall time | Command / log |
|-----|----------:|---------------|
| Tiny pilot (1 seed, 2 anchors, A3, 3 deltas, skip combined) | 11.78 s | `experiment_complete` in `paper-a.phase2.pilot-tiny` |
| 10-anchor pilot (1 seed, 12×2×11, skip combined) | 14.90 s | `paper-a.phase2.pilot-10a` |
| Primary experiment (5 seeds, 100 anchors, variable-wise + A3+F + plots) | 89.21 s | `paper-a.phase2.v1` `elapsed_s` |
| Full pytest (unit + scientific + integration) | 31.66 s | terminal `pytest` |

Phase 1 `analyze()` remains ~0.21 ms (Phase 1 performance audit). 132,000 + 242,000 FEM evaluations are consistent with an 89 s pipeline that also trains five MLPs.

Optimizations used without changing science:

- train-once / restore checkpoints
- train-only normalization persisted once
- batched MLP prediction (`mlp_batch_size = 1024`)
- optional exact-tuple FEM cache
- chunk-level Parquet persistence
- deterministic chunk keys for resume

Correctness was not traded for speed: every observation still calls Phase 1 `analyze()` unless that exact 12-vector was already solved in the same process.
