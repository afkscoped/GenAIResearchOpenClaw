# PRISM

PRISM is a lightweight hackathon MVP for a research intelligence platform that ingests research and innovation signals, links related entities, stores lightweight memory, and exposes stable APIs for trust scoring, contradiction mining, adoption-gap analysis, cross-domain discovery, and frontend reporting.

## Current Status

This repository currently contains a full-stack PRISM MVP:

- FastAPI backend
- SQLite persistence
- SQLAlchemy data models
- Pydantic API schemas
- arXiv, GitHub, Hugging Face, RSS/news, mock social, and mock jobs ingestion adapters
- Semantic Scholar, Crossref, optional Papers With Code, engineering blog RSS, and mock product launch adapters
- Normalization pipeline
- Entity linking
- Lightweight local vector-memory fallback
- Demo seed data
- Five intelligence engines and real fusion scoring
- Always-on lightweight research agent with APScheduler
- React/Vite/Tailwind command-center dashboard
- Markdown weekly report export

Future work should focus on channel delivery, richer source adapters, and optional OpenClaw-style orchestration.

## Repository Layout

```text
backend/
  app/
    api/
      routes_analysis.py
      routes_health.py
      routes_items.py
      routes_memory.py
      routes_pipeline.py
      routes_reports.py
    agent/
      channel_dispatcher.py
      heartbeat.py
      router.py
      soul_profile.py
      soul_profile.yaml
      state.py
      tools.py
    core/
      config.py
    db/
      init_db.py
      models.py
      session.py
    ingest/
      arxiv_adapter.py
      base.py
      crossref_adapter.py
      engineering_blog_adapter.py
      github_adapter.py
      huggingface_adapter.py
      mock_social_adapter.py
      news_adapter.py
      normalizer.py
      papers_with_code_adapter.py
      semantic_scholar_adapter.py
      pipeline.py
      seed_data.py
    memory/
      entity_linker.py
      vector_store.py
    engines/
      signal_engine.py
      trust_engine.py
      debate_engine.py
      gap_engine.py
      cross_domain_engine.py
      fusion_engine.py
    reports/
      markdown_report.py
    schemas/
      research.py
    main.py
  .env.example
  requirements.txt
frontend/
  src/
    App.tsx
    api/
    components/
  package.json
docs/
  TEAM_HANDOFF_AND_COMPLETION_PROMPT.md
  EXPANSION_OPENCLAW_PROMPTS.md
```

## Backend Setup

From the `backend` directory:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open:

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Frontend Setup

From the `frontend` directory:

```bash
npm install
copy .env.example .env
npm run dev
```

Open:

- Dashboard: `http://localhost:5173`

The frontend has fallback demo data, so it renders even if the backend is not running. Start the backend and click `Run PRISM` to use live SQLite/API data.

## First Demo Run

After starting the backend, call:

```bash
curl -X POST "http://localhost:8000/api/run-pipeline?query=multimodal%20agents&include_demo=true"
```

Then inspect:

- `GET /api/items`
- `GET /api/items/{item_id}`
- `GET /api/memory/search?q=multimodal%20agents`
- `GET /api/memory/links`
- `GET /api/analysis/fusion-reports`
- `GET /api/reports/weekly.md`

## OpenClaw-Style Agent

PRISM includes a lightweight OpenClaw-style agent layer. It uses PRISM's existing ingestion, memory, and engine modules as tools, then applies a SOUL profile for orchestration, alert thresholds, report routing, and channel delivery. It is disabled by default so local development stays quiet.

To enable it, set these values in `backend/.env`:

```bash
ENABLE_SCHEDULER=true
PRISM_HEARTBEAT_HOURS=6
PRISM_AGENT_QUERY=multimodal agents
PRISM_AGENT_LIMIT_PER_SOURCE=5
PRISM_AGENT_INCLUDE_DEMO=true
PRISM_SOUL_PROFILE_PATH=app/agent/soul_profile.yaml
DISCORD_WEBHOOK_URL=
```

Start the backend normally:

```bash
uvicorn app.main:app --reload
```

When enabled, APScheduler runs the heartbeat on startup and then every `PRISM_HEARTBEAT_HOURS` hours. Each heartbeat loads the SOUL profile, runs ingestion for monitored topics, performs entity linking and memory indexing through the existing ingestion pipeline, runs persisted engine analysis, routes each signal as `alert`, `daily_digest`, `weekly_brief`, or `ignored_memory_update`, and dispatches routed items to configured channels. It uses the FastAPI process only; no Celery, Redis, or worker service is required.

Agent endpoints:

- `GET /api/agent/status`: returns scheduler enabled state, current status, last run, next run, run count, details, and errors.
- `GET /api/agent/profile`: returns the loaded SOUL profile.
- `POST /api/agent/profile/reload`: reloads the YAML profile from disk.
- `POST /api/agent/run-once`: manually runs one heartbeat using the same env configuration.
- `GET /api/agent/alerts`: returns in-memory alerts, decisions, and delivery attempts.

Default SOUL profile:

```yaml
name: PRISM Research Agent
monitor_topics:
  - multimodal agents
  - AI evaluation
thresholds:
  alert_prism_score: 0.82
  digest_prism_score: 0.65
  weekly_brief_prism_score: 0.45
  min_trust_score: 0.35
channels:
  alerts:
    - mock
  daily_digest:
    - mock
  weekly_brief:
    - mock
report_frequency:
  daily_digest_hour_utc: 15
  weekly_brief_day: monday
  weekly_brief_hour_utc: 15
```

The `mock` channel records delivery attempts in memory. To enable Discord delivery, add `discord` to the relevant channel list in `backend/app/agent/soul_profile.yaml` and set `DISCORD_WEBHOOK_URL` in `.env`. Secrets are read only from environment configuration.

## Key API Contracts

### Normalized Research Item

```json
{
  "id": "string",
  "title": "string",
  "abstract": "string",
  "source": "arxiv|github|huggingface|news|mock_social|mock_jobs",
  "url": "string",
  "authors": ["string"],
  "organizations": ["string"],
  "topic": "string",
  "timestamp": "ISO datetime",
  "metadata": {}
}
```

### Fusion Report

```json
{
  "item_id": "string",
  "prism_score": 0.0,
  "novelty_score": 0.0,
  "trust_score": 0.0,
  "controversy_score": 0.0,
  "adoption_gap_score": 0.0,
  "transferability_score": 0.0,
  "verdict": "string",
  "evidence": ["string"]
}
```

## Environment Variables

See `backend/.env.example`.

Important variables:

- `DATABASE_URL`: defaults to local SQLite.
- `GITHUB_TOKEN`: optional, improves GitHub rate limit.
- `HUGGINGFACE_TOKEN`: optional.
- `NEWS_RSS_FEEDS`: comma-separated RSS feed list.
- `ENGINEERING_BLOG_RSS_FEEDS`: comma-separated engineering blog RSS feeds.
- `PAPERS_WITH_CODE_API_URL`: optional Papers With Code API base URL. The adapter fails safe and returns no items if the endpoint is unavailable.
- `CROSSREF_MAILTO`: optional email for Crossref polite-pool requests.
- `ENABLE_LLM`: reserved for future engine integration.
- `LLM_API_KEY`: reserved for future engine integration.
- `ENABLE_SCHEDULER`: set to `true` to start the APScheduler heartbeat.
- `PRISM_HEARTBEAT_HOURS`: heartbeat interval in hours, minimum effective value is 1.
- `PRISM_AGENT_QUERY`: research query used by scheduled and manual agent runs.
- `PRISM_AGENT_LIMIT_PER_SOURCE`: per-source ingestion limit for agent runs.
- `PRISM_AGENT_INCLUDE_DEMO`: include seeded demo data in agent runs.
- `PRISM_SOUL_PROFILE_PATH`: YAML profile path, relative to `backend/` unless absolute.
- `DISCORD_WEBHOOK_URL`: optional Discord webhook for agent delivery.

## Notes for the Team

- The backend works offline because seeded demo data is included.
- Every ingestion adapter fails safe and returns an empty list on network or parsing errors.
- Twitter/X and LinkedIn are intentionally mocked to avoid scraping/API issues.
- Product launches are mocked for demo mode, so no Product Hunt API key is required.
- `/api/analysis/fusion-reports` now uses the real Signal, Trust, Debate, Gap, Cross-Domain, and Fusion engines.
- `/api/agent/status` and `/api/agent/run-once` expose the always-on research loop.
- The frontend is a polished PRISM command center with pipeline trigger, ranked queue, score cards, source constellation, charts, detail panel, evidence trace, entity links, and Markdown report export.
- Expansion and OpenClaw integration prompts are in `docs/EXPANSION_OPENCLAW_PROMPTS.md`.
