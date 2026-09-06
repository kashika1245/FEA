# Phase 2 Reproducibility

## Executed checks

1. **Phase 1 artefact recovery.** `samples.jsonl` → Phase 1 `write_parquet` reproduced dataset hash `a78de261…e99e`.
2. **Normalization.** Independent pilots and the primary run produced the same train-only normalization hash `ff0c27f6…0327`.
3. **Single-seed training.** Seed `20260905` produced model hash `464496d4…da5e` in `paper-a.phase2.pilot-tiny`, `paper-a.phase2.pilot-10a`, and `paper-a.phase2.v1`.
4. **Tiny protocol twice.** `tests/integration/test_phase2_pipeline.py::test_reproducible_tiny_run` compared A3 coordinates, FEM `u_max`, and MLP `u_max` from two isolated experiment directories. They matched.
5. **Resume.** `tests/integration/test_phase2_pipeline.py::test_tiny_pilot_and_resume` deleted one chunk, resumed, and matched the clean observation column `predicted_u_max`.
6. **Deterministic anchors.** `tests/scientific/test_phase2_leakage.py::test_anchors_are_interpolation_test_and_error_independent` selected anchors twice; source `sample_id` lists were identical.

## Documented tolerance

Byte-identical NumPy/PyArrow tables are required for coordinates, FEM values, and stored errors when the software version, dataset hash, seed, and configuration hash match. Training uses `torch.use_deterministic_algorithms(True)` on CPU.

## What is not claimed

Cross-machine bit identity of PyTorch weights is not guaranteed if BLAS or PyTorch builds differ. On this machine, three independent trainings of seed `20260905` produced the same `model_hash`.
