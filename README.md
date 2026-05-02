# PRISM

PRISM is a lightweight hackathon MVP for a research intelligence platform that ingests research and innovation signals, links related entities, stores lightweight memory, and exposes stable APIs for trust scoring, contradiction mining, adoption-gap analysis, cross-domain discovery, and frontend reporting.

## Current Status

This repository currently contains a full-stack PRISM MVP:

- FastAPI backend
- SQLite persistence
- SQLAlchemy data models
- Pydantic API schemas
- arXiv, GitHub, Hugging Face, RSS/news, mock social, and mock jobs ingestion adapters
- Normalization pipeline
- Entity linking
- Lightweight local vector-memory fallback
- Demo seed data
- Five intelligence engines and real fusion scoring
- React/Vite/Tailwind command-center dashboard
- Markdown weekly report export

Future work should focus on engine persistence, scheduled agent loops, channel delivery, richer source adapters, and optional OpenClaw-style orchestration.

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
    core/
      config.py
    db/
      init_db.py
      models.py
      session.py
    ingest/
      arxiv_adapter.py
      base.py
      github_adapter.py
      huggingface_adapter.py
      mock_social_adapter.py
      news_adapter.py
      normalizer.py
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
- `ENABLE_LLM`: reserved for future engine integration.
- `LLM_API_KEY`: reserved for future engine integration.

## Notes for the Team

- The backend works offline because seeded demo data is included.
- Twitter/X and LinkedIn are intentionally mocked to avoid scraping/API issues.
- `/api/analysis/fusion-reports` now uses the real Signal, Trust, Debate, Gap, Cross-Domain, and Fusion engines.
- The frontend is a polished PRISM command center with pipeline trigger, ranked queue, score cards, source constellation, charts, detail panel, evidence trace, entity links, and Markdown report export.
- Expansion and OpenClaw integration prompts are in `docs/EXPANSION_OPENCLAW_PROMPTS.md`.
