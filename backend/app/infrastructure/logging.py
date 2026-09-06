"""Structured JSON application logs. No secrets, weights, or Parquet dumps."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any


def get_app_logger() -> logging.Logger:
    logger = logging.getLogger("paper_a.app")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_app(logger: logging.Logger, event: str, **fields: Any) -> None:
    payload = {"timestamp": datetime.now(UTC).isoformat(), "event": event, **fields}
    logger.info(json.dumps(payload, sort_keys=True, default=str))
