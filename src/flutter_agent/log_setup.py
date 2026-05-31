"""Logging configuration — supports plain text and structured JSON output.

Usage:
    from .log_setup import configure_logging
    configure_logging(settings)

Set ``LOG_FORMAT=json`` in .env to switch to JSON Lines output, suitable for
log aggregators (e.g. Datadog, Loki, CloudWatch).
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Settings


class _JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            obj["exception"] = self.formatException(record.exc_info)
        # Merge any extra fields attached via `logger.info("...", extra={...})`
        for key in ("run_id", "stage", "elapsed_ms", "tokens", "cost_usd"):
            val = getattr(record, key, None)
            if val is not None:
                obj[key] = val
        return json.dumps(obj, ensure_ascii=False)


_TEXT_FORMAT = "%(asctime)s %(levelname)-7s %(name)s | %(message)s"


def configure_logging(settings: Settings) -> None:
    """Call once during app startup to set the root logger format and level."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicate output
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    if settings.log_format.lower() == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(_TEXT_FORMAT))

    root.addHandler(handler)
