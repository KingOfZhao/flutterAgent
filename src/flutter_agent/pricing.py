"""Token-to-USD cost estimator.

Pricing follows the per-million-token model used by every OpenAI-compatible
provider. The defaults below are pinned to DeepSeek's published price list
(https://api-docs.deepseek.com/quick_start/pricing as of 2025-01); update them
in `MODEL_PRICING` or via a JSON file pointed to by the `PRICING_CONFIG`
environment variable when prices change.

Design notes:
  * We accept the model name verbatim and look up exact, then prefix, then
    fall back to ``"*"``. This avoids silent miscosting when a new model name
    is introduced.
  * Cache pricing (DeepSeek differentiates cache-hit vs cache-miss for input
    tokens) is not modeled here because our upstream client doesn't yet
    receive the cache hit metadata. We report a worst-case (cache-miss) cost
    so the estimator never under-counts.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# USD per 1,000,000 tokens. Worst-case (no-cache) input prices.
# Sources:
#   * DeepSeek pricing page (https://api-docs.deepseek.com/quick_start/pricing)
#   * OpenAI pricing page (https://openai.com/api/pricing/)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # DeepSeek
    "deepseek-chat":     {"input_per_million": 0.27,  "output_per_million": 1.10},
    "deepseek-reasoner": {"input_per_million": 0.55,  "output_per_million": 2.19},
    # "deepseek-v4-pro" is the model name requested by the user; not part of
    # DeepSeek's currently published model line. We default it to the V3 chat
    # rate as a placeholder. Override via PRICING_CONFIG when the real price
    # is known.
    "deepseek-v4-pro":   {"input_per_million": 0.27,  "output_per_million": 1.10},
    # OpenAI (selected, for the passthrough mode)
    "gpt-4o":            {"input_per_million": 2.50,  "output_per_million": 10.00},
    "gpt-4o-mini":       {"input_per_million": 0.15,  "output_per_million": 0.60},
    "o1-mini":           {"input_per_million": 3.00,  "output_per_million": 12.00},
    # Safe fallback for anything else.
    "*":                 {"input_per_million": 1.00,  "output_per_million": 3.00},
}


@dataclass(frozen=True)
class CostBreakdown:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    model: str
    source: str  # which key in the pricing table we hit

    def to_dict(self) -> Dict[str, object]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "input_cost_usd": round(self.input_cost_usd, 6),
            "output_cost_usd": round(self.output_cost_usd, 6),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "model": self.model,
            "pricing_source": self.source,
        }


def load_pricing(path: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """Merge the built-in table with an optional JSON file at ``path``.

    The file at ``path`` (or ``PRICING_CONFIG`` env var) must be a mapping of
    model name → {"input_per_million": float, "output_per_million": float}.
    Anything else is ignored with a warning.
    """
    table = dict(MODEL_PRICING)
    cfg_path = path or os.environ.get("PRICING_CONFIG")
    if not cfg_path:
        return table
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning("PRICING_CONFIG=%s not found, using defaults", cfg_path)
        return table
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("failed to read PRICING_CONFIG=%s: %s", cfg_path, exc)
        return table

    if not isinstance(data, dict):
        logger.warning("PRICING_CONFIG must be a JSON object; got %s", type(data))
        return table

    for name, rate in data.items():
        if (
            isinstance(rate, dict)
            and "input_per_million" in rate
            and "output_per_million" in rate
        ):
            table[str(name)] = {
                "input_per_million": float(rate["input_per_million"]),
                "output_per_million": float(rate["output_per_million"]),
            }
        else:
            logger.warning("ignoring invalid pricing entry for %s: %s", name, rate)
    return table


def _resolve(table: Dict[str, Dict[str, float]], model: str) -> tuple[Dict[str, float], str]:
    """Pick the most specific pricing entry for ``model``."""
    if model in table:
        return table[model], model
    # prefix match: e.g. "gpt-4o-2024-08-06" -> "gpt-4o"
    for key in sorted(table.keys(), key=len, reverse=True):
        if key != "*" and model.startswith(key):
            return table[key], key
    return table.get("*", {"input_per_million": 0.0, "output_per_million": 0.0}), "*"


def estimate_cost(
    *,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    pricing: Optional[Dict[str, Dict[str, float]]] = None,
) -> CostBreakdown:
    """Compute the USD cost for a single completion."""
    table = pricing if pricing is not None else load_pricing()
    rates, source = _resolve(table, model)
    input_cost = prompt_tokens * rates["input_per_million"] / 1_000_000.0
    output_cost = completion_tokens * rates["output_per_million"] / 1_000_000.0
    return CostBreakdown(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
        total_cost_usd=input_cost + output_cost,
        model=model,
        source=source,
    )
