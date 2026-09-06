# Performance Audit

All numbers below were measured on this machine on 2026-09-05 with Python 3.14.6 and the installed numpy 2.5.2 wheel. They are not estimates.

## FEM `analyze()` (canonical 10-bar, uniform A=75 mm², E=200 GPa, F=5 kN)

300 timed calls after one warmup:

| Statistic | Wall time |
|-----------|-----------|
| mean | 0.212 ms |
| median | 0.210 ms |
| p95 | 0.222 ms |
| min | 0.206 ms |
| max | 0.275 ms |

Condition number of that case (from `scripts/verify_fea.py`): 74.61. The 8×8 reduced system is not a performance problem.

## Staged dataset generation (includes JSONL+fsync checkpointing and Parquet finalize)

| N | Wall (`time -p` real) | Notes |
|---|----------------------:|-------|
| 10 | 0.57 s | includes interpreter startup |
| 50 | 0.31 s | |
| 500 | 1.34 s | |
| 1000 | 3.92 s | |
| 10000 | **302.63 s** | primary artefact; see I/O note |
| 200 (after checkpoint fix) | 0.52 s | same FEM, smaller checkpoint JSON |

## I/O note (root cause, not FEM)

During the 10,000-sample run, `checkpoint.json` rewrote the full `completed_ids` list on every sample. That is O(N²) JSON serialization and dominated the 302.63 s wall time. FEM itself at 0.21 ms × 10000 ≈ 2.1 s.

After that run completed, checkpoint status was reduced to counts only. `samples.jsonl` remains the recovery source of truth. A subsequent N=200 generation took 0.52 s. The 10,000-row Parquet artefact was **not** regenerated; its scientific content does not depend on the checkpoint JSON shape.

## Conclusion

Correctness was not traded for speed. The remaining generation cost is durable per-row `fsync` of JSONL, which is required for crash recovery. Parallel FEM is unnecessary at 0.21 ms/solve.
