"""Pricing math is pure; we can verify it without any mocks."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402

from flutter_agent.pricing import (  # noqa: E402
    MODEL_PRICING,
    estimate_cost,
    load_pricing,
)


def test_estimate_cost_for_known_model() -> None:
    cost = estimate_cost(
        model="deepseek-chat", prompt_tokens=1_000_000, completion_tokens=1_000_000
    )
    assert cost.model == "deepseek-chat"
    assert cost.source == "deepseek-chat"
    assert cost.input_cost_usd == pytest.approx(0.27)
    assert cost.output_cost_usd == pytest.approx(1.10)
    assert cost.total_cost_usd == pytest.approx(1.37)
    assert cost.total_tokens == 2_000_000


def test_estimate_cost_falls_back_to_star() -> None:
    cost = estimate_cost(
        model="totally-made-up-model-xyz", prompt_tokens=1000, completion_tokens=500
    )
    assert cost.source == "*"
    # default fallback rate is 1.00 in / 3.00 out per 1M.
    assert cost.input_cost_usd == pytest.approx(1000 * 1.0 / 1_000_000)
    assert cost.output_cost_usd == pytest.approx(500 * 3.0 / 1_000_000)


def test_prefix_match_picks_longest_specific_key() -> None:
    cost = estimate_cost(
        model="gpt-4o-2024-08-06", prompt_tokens=10, completion_tokens=10
    )
    # Should match "gpt-4o" not "*".
    assert cost.source == "gpt-4o"
    assert cost.input_cost_usd > 0


def test_pricing_table_has_required_models() -> None:
    for required in ("deepseek-chat", "deepseek-reasoner", "deepseek-v4-pro", "*"):
        assert required in MODEL_PRICING, f"missing pricing entry for {required}"


def test_load_pricing_overrides_via_file(tmp_path) -> None:
    cfg = tmp_path / "pricing.json"
    cfg.write_text(
        '{"deepseek-v4-pro": {"input_per_million": 9.99, "output_per_million": 99.99}}',
        encoding="utf-8",
    )
    table = load_pricing(str(cfg))
    assert table["deepseek-v4-pro"]["input_per_million"] == 9.99
    assert table["deepseek-v4-pro"]["output_per_million"] == 99.99
    # Other entries untouched.
    assert table["deepseek-chat"]["input_per_million"] == MODEL_PRICING["deepseek-chat"]["input_per_million"]


def test_load_pricing_ignores_invalid_entries(tmp_path) -> None:
    cfg = tmp_path / "pricing.json"
    cfg.write_text('{"bad-entry": {"input_per_million": 1.0}}', encoding="utf-8")
    table = load_pricing(str(cfg))
    assert "bad-entry" not in table
