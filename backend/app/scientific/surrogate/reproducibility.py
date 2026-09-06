"""Deterministic RNG and hashing for Phase 2 artefacts."""

from __future__ import annotations

import os
import random
from collections.abc import Mapping
from typing import Any

import numpy as np
import torch

from app.scientific.reproducibility import canonical_json_bytes, sha256_bytes


def configure_deterministic_runtime(seed: int) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)


def pcg64(seed: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))


def hash_mapping(payload: Mapping[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(payload))


def hash_weight_map(weights: Mapping[str, np.ndarray]) -> str:
    digest_payload = {
        name: np.asarray(array, dtype=np.float32).tobytes().hex()
        for name, array in sorted(weights.items())
    }
    return hash_mapping(digest_payload)
