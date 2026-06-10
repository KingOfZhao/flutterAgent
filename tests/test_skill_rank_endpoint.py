"""Tests for POST /v1/skills/rank — the skill selection dry-run endpoint."""
from __future__ import annotations

import os

os.environ.setdefault("DEEPSEEK_API_KEY", "")
os.environ.setdefault("LOCAL_API_KEY", "")

from fastapi.testclient import TestClient

from flutter_agent.main import app


def _rank(payload):
    with TestClient(app) as client:
        resp = client.post("/v1/skills/rank", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_rank_returns_all_skills_scored():
    data = _rank({"requirement": "做一个移动端电商应用,需要状态管理和导航"})
    assert data["requirement"]
    assert data["token_budget"] == 40_000
    assert len(data["ranked"]) >= 50  # all loaded skills appear
    assert data["selected"]
    # ranked is sorted by descending score
    scores = [item["score"] for item in data["ranked"]]
    assert scores == sorted(scores, reverse=True)
    # selected ids must be a subset of ranked ids
    ranked_ids = {item["id"] for item in data["ranked"]}
    assert set(data["selected"]).issubset(ranked_ids)
    # selected flags agree with the selected list
    flagged = {item["id"] for item in data["ranked"] if item["selected"]}
    assert flagged == set(data["selected"])


def test_rank_pins_foundational_for_state_requirement():
    data = _rank({"requirement": "登录表单的状态管理怎么设计"})
    assert "state-management" in data["foundational"]
    assert "state-management" in data["selected"]
    pinned = [i for i in data["ranked"] if i["id"] == "state-management"][0]
    assert pinned["foundational"] is True
    assert pinned["score"] >= 100.0


def test_rank_ops_task_pins_nothing():
    data = _rank({"requirement": "Android 打包签名", "platforms": ["mobile"]})
    assert data["foundational"] == []


def test_rank_respects_token_budget_override():
    big = _rank({"requirement": "做一个跨端记账应用"})
    small = _rank({"requirement": "做一个跨端记账应用", "token_budget": 1})
    assert len(small["selected"]) <= len(big["selected"])
    assert small["token_budget"] == 1


def test_rank_family_dedup_marks_family():
    data = _rank({"requirement": "优化 CI 流水线缓存与产物归档"})
    by_id = {i["id"]: i for i in data["ranked"]}
    # flutter-cicd-pipelines extends flutter-ci-cd -> child carries family root
    child = by_id.get("flutter-cicd-pipelines")
    assert child is not None
    assert child["family"] == "flutter-ci-cd"
    # only one member of the family may be selected (no always-include here)
    fam_selected = [
        i for i in data["ranked"]
        if i["selected"] and i["id"] in ("flutter-ci-cd", "flutter-cicd-pipelines")
    ]
    assert len(fam_selected) <= 1


def test_rank_rejects_too_short_requirement():
    with TestClient(app) as client:
        resp = client.post("/v1/skills/rank", json={"requirement": "x"})
    assert resp.status_code == 422
