"""Local vector database: embedder, chunking, store, corpus build, search, API."""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))
os.environ.setdefault("DEEPSEEK_API_KEY", "")
os.environ.setdefault("LOCAL_API_KEY", "")

import pytest
from fastapi.testclient import TestClient

from flutter_agent.vector_store import (
    HashingEmbedder,
    VectorDoc,
    VectorStore,
    build_index,
    chunk_markdown,
    docs_from_memory,
    format_grounding,
    docs_from_knowledge,
    docs_from_skills,
)

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------

def test_embedder_is_deterministic_and_normalised():
    emb = HashingEmbedder(dim=128)
    a = emb.embed_one("全面思考 架构判断 offline sync")
    b = emb.embed_one("全面思考 架构判断 offline sync")
    assert a == b
    norm = math.sqrt(sum(v * v for v in a))
    assert abs(norm - 1.0) < 1e-6


def test_embedder_similar_texts_score_higher_than_unrelated():
    emb = HashingEmbedder()
    q = emb.embed_one("多数据源离线同步架构怎么选")
    near = emb.embed_one("离线同步与多数据源的架构选型")
    far = emb.embed_one("button color padding animation curve")
    dot = lambda x, y: sum(a * b for a, b in zip(x, y))
    assert dot(q, near) > dot(q, far)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def test_chunk_markdown_splits_on_headings_and_size():
    text = "# A\n" + "x" * 100 + "\n## B\n" + "y" * 4000
    chunks = chunk_markdown(text, max_chars=1600, overlap=160)
    assert len(chunks) >= 3
    assert chunks[0].startswith("# A")
    assert all(len(c) <= 1600 for c in chunks)


def test_chunk_markdown_empty():
    assert chunk_markdown("   \n  ") == []


# ---------------------------------------------------------------------------
# Store + search
# ---------------------------------------------------------------------------

def test_store_roundtrip_and_search(tmp_path):
    store = VectorStore(tmp_path / "v.sqlite3")
    store.add(
        [
            VectorDoc("doc-sync", "skill", "同步", "skills/a", 0,
                      "多数据源 离线同步 冲突解决 架构选型"),
            VectorDoc("doc-ui", "skill", "UI", "skills/b", 0,
                      "button padding color theme animation"),
            VectorDoc("doc-know", "knowledge", "知识", "knowledge/k.md", 0,
                      "模型能力演进的必要条件 蒸馏 验证闭环"),
        ]
    )
    assert store.count() == 3
    hits = store.search("离线同步架构", top_k=2)
    assert hits[0].doc_id == "doc-sync"
    only_knowledge = store.search("蒸馏 验证闭环", top_k=3, kind="knowledge")
    assert {h.kind for h in only_knowledge} == {"knowledge"}
    store.close()


def test_store_upsert_replaces(tmp_path):
    store = VectorStore(tmp_path / "v.sqlite3")
    doc = VectorDoc("d", "skill", "t", "s", 0, "first text")
    store.add([doc])
    store.add([VectorDoc("d", "skill", "t", "s", 0, "second text")])
    assert store.count() == 1
    store.close()


# ---------------------------------------------------------------------------
# Runtime memory notes + grounding
# ---------------------------------------------------------------------------

def test_memory_docs_survive_rebuild(tmp_path):
    store = VectorStore(tmp_path / "m.sqlite3")
    store.add(docs_from_memory("note-1", "偏好", "用户偏好 Riverpod 状态管理 离线优先"))
    assert store.count() >= 1
    build_index(store, skills_dir=ROOT / "skills", knowledge_dir=ROOT / "knowledge")
    hits = store.search("Riverpod 状态管理", top_k=3, kind="memory")
    assert hits and hits[0].doc_id == "note-1"
    listed = store.list_docs(kind="memory")
    assert [d["doc_id"] for d in listed] == ["note-1"]
    assert store.delete_doc("note-1") >= 1
    assert store.list_docs(kind="memory") == []
    store.close()


def test_format_grounding_filters_noise():
    from flutter_agent.vector_store import SearchHit

    good = SearchHit("d", "memory", "t", "memory:d", 0, 0.6, "离线同步要点")
    noise = SearchHit("n", "skill", "t", "skills/n", 0, 0.01, "无关")
    block = format_grounding([good, noise])
    assert "memory:d" in block and "无关" not in block
    assert format_grounding([noise]) == ""


def test_memory_api_write_list_delete(tmp_path):
    from flutter_agent.main import app

    store = VectorStore(tmp_path / "mem.sqlite3")
    app.state.vector_store = store
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/v1/vector/memory",
                json={"text": "项目约定: 提交信息用中文", "doc_id": "conv-1"},
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["doc_id"] == "conv-1" and body["chunks"] >= 1

            resp = client.get("/v1/vector/memory")
            assert resp.status_code == 200
            assert any(m["doc_id"] == "conv-1" for m in resp.json()["memories"])

            resp = client.post(
                "/v1/vector/search",
                json={"query": "提交信息 中文", "kind": "memory"},
            )
            assert resp.status_code == 200
            assert any(h["doc_id"] == "conv-1" for h in resp.json()["hits"])

            resp = client.delete("/v1/vector/memory/conv-1")
            assert resp.status_code == 200
            resp = client.delete("/v1/vector/memory/conv-1")
            assert resp.status_code == 404
    finally:
        store.close()
        del app.state.vector_store


# ---------------------------------------------------------------------------
# Corpus builders against the real repo
# ---------------------------------------------------------------------------

def test_docs_from_skills_covers_all_skills():
    docs = docs_from_skills(ROOT / "skills")
    ids = {d.doc_id for d in docs}
    assert "comprehensive-thinking" in ids
    assert "devin-ai-engineer-mindset" in ids
    assert len(ids) >= 61


def test_docs_from_knowledge_indexes_corpus():
    docs = docs_from_knowledge(ROOT / "knowledge")
    ids = {d.doc_id for d in docs}
    assert "claude-fable5-opus48" in ids
    assert "model-capability-evolution" in ids
    assert all(d.kind == "knowledge" for d in docs)


def test_flutter_corpus_docs_are_retrievable(tmp_path):
    store = VectorStore(tmp_path / "c.sqlite3")
    build_index(store, skills_dir=ROOT / "skills", knowledge_dir=ROOT / "knowledge")
    cases = {
        "状态管理选 riverpod 还是 bloc": "flutter-state-management",
        "离线同步 冲突解决 增量队列": "flutter-offline-sync",
        "掉帧 卡顿 着色器编译 profile": "flutter-performance",
        "widget 测试 pumpAndSettle 金字塔": "flutter-testing-strategy",
        "签名 上架 灰度发布 崩溃监控": "flutter-release-engineering",
        "项目结构分层 repository 单一事实源": "flutter-app-architecture",
        "go_router 深链 redirect 守卫": "flutter-navigation-deeplink",
        "dio 超时重试 幂等 json_serializable": "flutter-networking-api",
        "secure storage 证书锁定 混淆 keystore": "flutter-mobile-security",
        "国际化 arb 复数 读屏 无障碍 对比度": "flutter-i18n-accessibility",
        "isolate compute 不共享内存 消息深拷贝": "flutter-concurrency",
        "隐式动画 AnimationController Hero 转场": "flutter-animation-ux",
        "MethodChannel pigeon ffi PlatformView 原生": "flutter-platform-integration",
        "pubspec.lock 入库 fastlane match 可复现构建": "flutter-cicd-engineering",
        "Crashlytics onError 符号化 面包屑 慢帧": "flutter-observability",
        "三棵树 RenderObject 约束下行 raster 线程": "flutter-rendering-pipeline",
        "ValueKey GlobalKey canUpdate 状态串了": "flutter-element-keys",
        "sliver shrinkWrap unbounded height 吸顶": "flutter-sliver-scrolling",
        "内存泄漏 heap snapshot retaining path dispose": "flutter-memory-leaks",
        "进程死亡 RestorationMixin paused 落盘": "flutter-lifecycle-state-restoration",
    }
    for query, expected in cases.items():
        hit_ids = {h.doc_id for h in store.search(query, top_k=5, kind="knowledge")}
        assert expected in hit_ids, (query, hit_ids)
    store.close()


def test_build_index_and_semantic_search_end_to_end(tmp_path):
    store = VectorStore(tmp_path / "v.sqlite3")
    stats = build_index(
        store, skills_dir=ROOT / "skills", knowledge_dir=ROOT / "knowledge"
    )
    assert stats["documents"] >= 63  # 61 skills + 2 knowledge docs
    assert stats["chunks"] == store.count()

    hits = store.search("请全面思考这个架构判断", top_k=5, kind="skill")
    assert "comprehensive-thinking" in {h.doc_id for h in hits}

    hits = store.search("模型能力演进的必要条件 蒸馏", top_k=5, kind="knowledge")
    assert "model-capability-evolution" in {h.doc_id for h in hits}

    hits = store.search("Claude Fable 5 adaptive thinking effort", top_k=5)
    assert "claude-fable5-opus48" in {h.doc_id for h in hits}
    store.close()


# ---------------------------------------------------------------------------
# HTTP API
# ---------------------------------------------------------------------------

def test_vector_api_search_and_stats(tmp_path):
    from flutter_agent.main import app

    store = VectorStore(tmp_path / "api.sqlite3")
    app.state.vector_store = store
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/v1/vector/search",
                json={"query": "全面思考 架构判断", "top_k": 3, "kind": "skill"},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["query"] == "全面思考 架构判断"
            assert 1 <= len(body["hits"]) <= 3
            assert all(h["kind"] == "skill" for h in body["hits"])

            resp = client.get("/v1/vector/stats")
            assert resp.status_code == 200
            stats = resp.json()
            assert stats["chunks"] > 0 and stats["documents"] >= 63
    finally:
        store.close()
        del app.state.vector_store


# ---------------------------------------------------------------------------
# Semantic blending into the skill ranker
# ---------------------------------------------------------------------------

def test_semantic_skill_scores_and_ranker_blend(tmp_path):
    from flutter_agent.schemas import SkillDetail
    from flutter_agent.skill_ranker import SEMANTIC_WEIGHT, rank_skills
    from flutter_agent.vector_store import semantic_skill_scores

    store = VectorStore(tmp_path / "sem.sqlite3")
    build_index(
        store,
        skills_dir=_ROOT / "skills",
        knowledge_dir=_ROOT / "knowledge",
    )
    scores = semantic_skill_scores(store, "请全面思考这个架构判断")
    assert scores and all(v > 0 for v in scores.values())
    assert "comprehensive-thinking" in scores
    store.close()

    def mk(sid: str) -> SkillDetail:
        return SkillDetail(
            id=sid, name=sid, version="1.0", platforms=["all"],
            tags=[], applies_when="", stage_hints=[], body="x",
            path=f"skills/{sid}/SKILL.md",
        )

    a, b = mk("skill-a"), mk("skill-b")
    ranked = rank_skills("无关词", [a, b], [], semantic_scores={"skill-b": 0.4})
    assert ranked[0][0].id == "skill-b"
    assert ranked[0][1] - ranked[1][1] == pytest.approx(0.4 * SEMANTIC_WEIGHT)


def test_reload_endpoint_reindexes_vector_store(tmp_path):
    from flutter_agent.main import app

    store = VectorStore(tmp_path / "reload.sqlite3")
    app.state.vector_store = store
    try:
        with TestClient(app) as client:
            resp = client.post("/v1/skills/reload")
            assert resp.status_code == 200
            body = resp.json()
            assert body["loaded"] >= 61
            assert body["reindexed_chunks"] > 0
            assert store.doc_count() >= 63
    finally:
        store.close()
        del app.state.vector_store
