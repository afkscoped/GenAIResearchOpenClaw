# PRISM Expansion, Robustness, and OpenClaw Integration Prompts

This document is for teammates who will extend PRISM after the current full-stack MVP baseline. It explains how to make the system more robust, more agentic, more scalable, and more aligned with an OpenClaw-style always-on research copilot.

## Current MVP Baseline

The current project includes:

- FastAPI backend with SQLite persistence.
- Public/mock ingestion for arXiv, GitHub, Hugging Face, RSS/news, mock social, and mock jobs.
- Normalized research item contract.
- Entity linking.
- Lightweight token-memory search.
- Five real intelligence engines:
  - Signal Engine
  - Trust Engine
  - Debate Engine
  - Gap Engine
  - Cross-Domain Engine
- Fusion Engine returning PRISM scores.
- React/Vite/Tailwind dashboard.
- Markdown weekly report export.

## Immediate Robustness Upgrades

### 1. Add Persistent Engine Output Tables

Currently, fusion reports are computed dynamically from stored items/signals/links. Add tables for cached engine results:

```text
EngineRun
  id
  item_id
  engine_name
  score
  verdict
  evidence
  details
  created_at

FusionReportRecord
  id
  item_id
  prism_score
  novelty_score
  trust_score
  controversy_score
  adoption_gap_score
  transferability_score
  verdict
  evidence
  created_at
```

Benefits:

- Faster dashboard loading.
- Historical score evolution.
- Easy weekly trend charts.
- Easier debugging of engine decisions.

### 2. Add Background Scheduler

Use APScheduler for a lightweight always-on loop:

```text
Every 6 hours:
  run ingestion pipeline
  normalize items
  update memory
  update links
  run engines
  cache fusion reports
  generate digest
```

Do not build Celery/Redis unless the hackathon specifically needs distributed workers.

### 3. Add Caching and API Resilience

Add:

- Request timeouts per adapter.
- Per-source error logs.
- Cached raw API payloads.
- Rate-limit backoff.
- Adapter health endpoint.

Recommended endpoint:

```text
GET /api/sources/health
```

### 4. Upgrade Memory from Sparse Tokens to Real Embeddings

Current memory is intentionally lightweight. A realistic upgrade:

- Use `sentence-transformers/all-MiniLM-L6-v2` if laptop can handle it.
- Store vectors in ChromaDB.
- Keep sparse-token fallback if ChromaDB is unavailable.

Do not remove the current fallback.

### 5. Add Evaluation Test Set

Create `backend/tests/fixtures/demo_cases.json` with known expected outcomes:

- A strong emerging paper.
- A low-trust teaser.
- A contradiction cluster.
- An adoption-gap opportunity.
- A cross-domain transfer case.

Then write tests asserting approximate score ranges.

## OpenClaw-Style Integration Plan

Treat OpenClaw as an orchestration and delivery layer, not as a mandatory dependency for the core MVP.

### OpenClaw Mapping

```text
OpenClaw heartbeat daemon
  -> PRISM scheduled ingestion and analysis loop

SOUL.md / agent memory
  -> PRISM persistent research memory and engine preferences

Multi-channel router
  -> PRISM Telegram/Slack/Discord/Email delivery

Tool calling
  -> PRISM adapters for arXiv, GitHub, HF, news, and reports

Document delivery
  -> PRISM weekly Markdown/PDF/DOCX brief
```

### Suggested Folder for OpenClaw Integration

```text
backend/app/agent/
  __init__.py
  heartbeat.py
  router.py
  soul_profile.py
  channel_dispatcher.py
  tools.py
```

### Agent Loop Design

```text
1. Wake up on schedule.
2. Read SOUL/profile configuration.
3. Select topics to monitor.
4. Run ingestion adapters.
5. Normalize and link entities.
6. Update memory.
7. Run PRISM engines.
8. Generate fusion reports.
9. Decide if alert threshold is crossed.
10. Dispatch alert/report to configured channels.
```

### Alert Threshold Rules

Send alert if any condition is true:

- `prism_score >= 0.75`
- `novelty_score >= 0.80 and trust_score >= 0.55`
- `controversy_score >= 0.75`
- `adoption_gap_score >= 0.75`
- `transferability_score >= 0.80`

### SOUL/Profile Example

```yaml
agent_name: PRISM
monitor_topics:
  - multimodal agents
  - AI evaluation
  - scientific discovery
  - healthcare AI
  - graph learning
alert_thresholds:
  prism_score: 0.75
  controversy_score: 0.75
  transferability_score: 0.80
delivery_channels:
  - email
  - discord
report_frequency: weekly
risk_tolerance: medium
```

## Prompt 1: Robust Engine Persistence Agent

```text
You are extending PRISM, a FastAPI + React research intelligence MVP. Your task is to add persistent storage for engine outputs without breaking existing endpoints.

Current backend has SQLAlchemy models for ResearchItem, SourceSignal, EntityLink, and MemoryDocument. Current engine modules exist under backend/app/engines and routes_analysis.py computes FusionReportRead dynamically.

Implement:
1. EngineRun SQLAlchemy model.
2. FusionReportRecord SQLAlchemy model.
3. Pydantic read schemas for both.
4. A service that runs all engines and stores their outputs.
5. Endpoints:
   - POST /api/analysis/run-engines
   - GET /api/analysis/engine-runs/{item_id}
   - GET /api/analysis/fusion-history/{item_id}
6. Keep existing /api/analysis/fusion-reports response shape unchanged.
7. Add tests or a script that runs the pipeline and then runs engines.
8. Do not remove the dynamic scoring fallback.
```

## Prompt 2: Scheduler and Agent Loop Agent

```text
You are extending PRISM into an always-on research intelligence agent. Add a lightweight scheduler using APScheduler.

Current backend has an ingestion pipeline and analysis engines. Your task is to create backend/app/agent with heartbeat.py, router.py, and configurable scheduled jobs.

Implement:
1. APScheduler setup that can be enabled with ENABLE_SCHEDULER=true.
2. A heartbeat job that runs every N hours from env variable PRISM_HEARTBEAT_HOURS.
3. The heartbeat should run ingestion, entity linking, memory indexing, and engine analysis.
4. Add /api/agent/status showing last run, next run, status, and errors.
5. Add /api/agent/run-once for manual triggering.
6. Keep it simple and laptop-friendly. Do not add Celery or Redis.
7. Add clear README instructions.
```

## Prompt 3: OpenClaw Integration Agent

```text
You are integrating PRISM with an OpenClaw-style agent architecture. Treat OpenClaw as orchestration, memory profile, and multi-channel delivery. Do not rewrite the core ingestion or engine modules.

Create backend/app/agent with:
- soul_profile.py for loading YAML configuration.
- tools.py exposing PRISM functions as tool-like callables.
- heartbeat.py for always-on loop orchestration.
- channel_dispatcher.py for delivery adapters.
- router.py for deciding whether a signal should become an alert, daily digest, weekly brief, or ignored memory update.

Implement a SOUL/profile YAML format with monitor topics, thresholds, channels, and report frequency.

Add endpoints:
- GET /api/agent/profile
- POST /api/agent/profile/reload
- POST /api/agent/run-once
- GET /api/agent/alerts

Create a mock channel dispatcher first. If time remains, implement Discord webhook delivery using DISCORD_WEBHOOK_URL from .env. Never hardcode secrets.

Preserve all existing PRISM endpoints and frontend compatibility.
```

## Prompt 4: Advanced Frontend Expansion Agent

```text
You are extending the PRISM React/Vite/Tailwind dashboard. The current frontend already has a polished command-center dashboard, source constellation, score cards, ranked queue, charts, detail panel, evidence panel, entity links, pipeline button, and Markdown report export.

Add advanced views without breaking the existing dashboard:
1. Topic Explorer page.
2. Contradiction Battle page.
3. Adoption Gap Atlas page.
4. Cross-Domain Radar page.
5. Memory Search command palette.
6. Engine History chart if backend history endpoints exist.
7. Alert Center page for OpenClaw-style agent alerts.

Use React state or simple routing. Keep design consistent: dark glassmorphism, cyan/violet gradients, evidence-first UX. Add graceful fallback data if backend endpoints are unavailable.
```

## Prompt 5: Multi-Source Ingestion Expansion Agent

```text
You are improving PRISM ingestion. Add more robust source adapters while preserving the NormalizedItem contract.

Add adapters for:
- Semantic Scholar API
- Crossref API
- Papers With Code if available
- Product Hunt or mock product launches
- Company engineering blogs through RSS

Rules:
1. Every adapter must fail safely and return [] on errors.
2. Every adapter must output raw dictionaries accepted by normalize_raw_item.
3. Add source-specific evidence strings.
4. Add tests or sample fixtures.
5. Do not scrape restricted websites.
6. Do not require paid API keys for demo mode.
```

## Long-Term Architecture Target

```text
Sources
  -> Adapter Layer
  -> Normalizer
  -> Entity Resolver
  -> Raw Store + ResearchItem Store
  -> Vector Memory
  -> Engine Runner
  -> Fusion Cache
  -> Alert Router
  -> Dashboard + Weekly Brief + Channels
```

## Final Hackathon Upgrade Priorities

If only a few hours remain, prioritize in this order:

1. Make the demo run end-to-end reliably.
2. Add engine persistence only if current dynamic scoring feels slow.
3. Add scheduler only if you can show it safely in demo.
4. Add one channel integration, preferably Discord webhook.
5. Add more frontend pages only after backend is stable.

## Important Constraints

- Keep seeded fallback data.
- Keep SQLite default.
- Keep mock social/job sources.
- Do not scrape Twitter/X or LinkedIn.
- Do not require GPU.
- Do not hardcode API keys.
- Preserve current API contracts for the dashboard.
