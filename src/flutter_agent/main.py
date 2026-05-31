"""FastAPI entry point.

Mounts:
  * GET  /                       quick HTML index
  * GET  /healthz                liveness + skill count
  * GET  /openapi.json           machine-readable OpenAPI 3.x spec
  * GET  /docs                   Swagger UI
  * GET  /redoc                  ReDoc
  * GET  /v1/skills              list loaded skills
  * GET  /v1/skills/{id}         fetch one skill (incl. markdown body)
  * POST /v1/skills/reload       hot-reload skills from disk
  * POST /v1/refine              run the refinement pipeline (canonical)
  * POST /v1/chat/completions    OpenAI-compatible facade
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from . import __version__
from .cache import RunCache
from .config import get_settings
from .log_setup import configure_logging
from .deepseek_client import DeepSeekClient
from .pipeline import RefinementPipeline
from .pub_validator import PubValidator
from .routes import metrics, openai_compat, refine, runs, skills
from .run_store import RunStore
from .schemas import HealthResponse
from .skill_loader import SkillRegistry

logger = logging.getLogger("flutter_agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    registry = SkillRegistry(settings.skills_path)
    registry.reload()
    client = DeepSeekClient(settings)
    run_store = RunStore(settings.runs_log_file)
    run_cache = RunCache(settings.runs_log_file)
    run_cache.load()
    pub_validator = PubValidator()
    pipeline = RefinementPipeline(
        settings,
        client,
        registry,
        cache=run_cache,
        pub_validator=pub_validator,
        run_store=run_store,
    )

    app.state.settings = settings
    app.state.registry = registry
    app.state.client = client
    app.state.pipeline = pipeline
    app.state.run_store = run_store
    app.state.run_cache = run_cache
    app.state.pub_validator = pub_validator

    logger.info(
        "flutter-agent ready: model=%s base=%s skills=%d cache_entries=%d",
        settings.deepseek_model,
        settings.deepseek_base_url,
        len(registry),
        len(run_cache),
    )
    try:
        yield
    finally:
        await client.aclose()
        await pub_validator.aclose()


app = FastAPI(
    title="flutter-agent",
    version=__version__,
    summary=(
        "Local Flutter requirement refinement service: turns one-liners into "
        "spec / architecture / task breakdowns using DeepSeek (or any "
        "OpenAI-compatible model) plus Markdown skill files."
    ),
    description=(
        "Two ways to call:\n\n"
        "* **Canonical**: `POST /v1/refine` returns a strongly-typed "
        "`RefineResponse` (classify / spec / architecture / breakdown / "
        "acceptance + final markdown PRD).\n"
        "* **OpenAI-compatible**: `POST /v1/chat/completions` accepts the "
        "standard OpenAI chat format. Use `model=\"flutter-agent\"` to run "
        "the refinement pipeline, or any other model name to passthrough to "
        "the upstream provider."
    ),
    contact={"name": "flutter-agent", "url": "http://127.0.0.1:8765/docs"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Top-level routes
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def index() -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>flutter-agent</title>
<style>body{{font-family:system-ui,-apple-system,sans-serif;max-width:780px;margin:3rem auto;padding:0 1rem;line-height:1.55}}
code{{background:#f4f4f5;padding:2px 6px;border-radius:4px}}
a{{color:#2563eb}}</style></head>
<body>
<h1>flutter-agent <small style="color:#6b7280">v{__version__}</small></h1>
<p>Local Flutter requirement refinement service.</p>
<ul>
  <li><a href="/docs">Swagger UI</a> &middot; <a href="/redoc">ReDoc</a> &middot; <a href="/openapi.json">openapi.json</a></li>
  <li><code>POST /v1/refine</code> — full pipeline, typed JSON response</li>
  <li><code>POST /v1/chat/completions</code> — OpenAI-compatible (supports <code>stream=true</code> SSE; use <code>model=&quot;flutter-agent&quot;</code>)</li>
  <li><code>GET  /v1/skills</code> — list loaded skill docs</li>
  <li><code>POST /v1/skills/reload</code> — hot-reload <code>SKILL.md</code> files</li>
  <li><code>GET  /v1/runs</code> &middot; <code>GET /v1/runs/{{id}}</code> — audit log of past pipelines</li>
  <li><code>GET  /v1/metrics</code> — aggregate run statistics (tokens, cost, success rate)</li>
  <li><code>GET  /healthz</code> — health</li>
</ul>
</body></html>"""


@app.get("/healthz", response_model=HealthResponse, tags=["meta"])
async def healthz() -> HealthResponse:
    settings = app.state.settings
    registry: SkillRegistry = app.state.registry
    return HealthResponse(
        version=__version__,
        skills_loaded=len(registry),
        upstream_base_url=settings.deepseek_base_url,
        upstream_model=settings.deepseek_model,
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(skills.router)
app.include_router(refine.router)
app.include_router(runs.router)
app.include_router(openai_compat.router)
app.include_router(metrics.router)
