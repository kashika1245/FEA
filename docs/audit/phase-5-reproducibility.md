# Phase 5 reproducibility

## Dataset generator — Verified

`make verify-reproducibility` (n=20):

- Repeat with the same seed: identical hash `67e5e7d5a32806b3f7ad48f5f640d7a34d4432b50f4aafb3afbff1faae655506` and identical rows
- Seed+1: different hash
- Configuration hash `449e9b7cfd50bcce39c9293bb5f12b63724d49ae44cc0cd427290b3e998e4752`

RNG: `numpy.random.PCG64` with `SeedSequence(seed).spawn(n_samples)` per sample; split RNG is `SeedSequence([seed, 1])`.

The 10,000-row artefact hash was independently recomputed from the file (not taken from the manifest alone).

## Models

Phase 5 did **not** retrain the five MLPs. Weight archives are NumPy `.npz` + JSON (no pickle). Bit-identical training across machines is **Assumed**, not re-verified end-to-end in this phase. Stored interpolation metrics and profile hashes are the frozen evidence.

## Clean-environment reproduction

A full new venv + `npm ci` was **not** executed in this session (the existing `.venv` and `frontend/node_modules` were reused). Commands that *were* executed against that environment are listed in `phase-5-testing.md`. Treat “clean machine from zero” as **partially verified**.

## Git identity

No commit hash exists. Reproduction must use the working tree plus the frozen artefact directories.
