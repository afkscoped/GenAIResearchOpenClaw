# PRISM Team Handoff and Completion Prompt

This document explains exactly what has been implemented, what remains, how to integrate the remaining work, and includes a large copy-paste prompt for teammates or AI agents to finish PRISM.

## 1. Project Goal

PRISM stands for Pre-publication Research Intelligence & Signal Machine. The MVP should behave like an always-on research intelligence copilot that detects emerging research signals, scores trustworthiness, finds contradictions, identifies adoption gaps, proposes cross-domain transfer ideas, and presents everything in a dashboard and weekly brief.

## 2. What Has Been Implemented

### Backend Foundation

A runnable Python FastAPI backend has been created under `backend/app`.

Implemented backend features:

- FastAPI app entrypoint at `backend/app/main.py`
- CORS configuration for local frontend development
- SQLite database support through SQLAlchemy
- Environment-based configuration through `pydantic-settings`
- Database initialization on app startup
- Health endpoint
- Item listing endpoint
- Item detail endpoint
- Pipeline run endpoint
- Memory search endpoint
- Entity link listing endpoint
- Placeholder fusion report endpoint
- Markdown weekly report endpoint

### Database Models

The following SQLAlchemy models are implemented in `backend/app/db/models.py`:

- `ResearchItem`
- `SourceSignal`
- `EntityLink`
- `MemoryDocument`

These give the rest of the team stable persistence for research items, source-level signals, item relationships, and lightweight memory search.

### API Schemas

The following Pydantic contracts are implemented in `backend/app/schemas/research.py`:

- `ResearchItemCreate`
- `ResearchItemRead`
- `SourceSignalCreate`
- `SourceSignalRead`
- `NormalizedItem`
- `EntityLinkRead`
- `PipelineRunResponse`
- `MemorySearchResult`
- `FusionReportRead`
- `HealthResponse`

The most important contracts for remaining teammates are `ResearchItemRead`, `NormalizedItem`, and `FusionReportRead`.

### Ingestion Layer

Implemented ingestion files:

- `backend/app/ingest/base.py`
- `backend/app/ingest/arxiv_adapter.py`
- `backend/app/ingest/github_adapter.py`
- `backend/app/ingest/huggingface_adapter.py`
- `backend/app/ingest/news_adapter.py`
- `backend/app/ingest/mock_social_adapter.py`
- `backend/app/ingest/normalizer.py`
- `backend/app/ingest/pipeline.py`
- `backend/app/ingest/seed_data.py`

Supported sources:

- arXiv through the `arxiv` Python package
- GitHub repository search through GitHub REST API
- Hugging Face model search through public HF API
- RSS/news through `feedparser`
- Mock Twitter/X-style social signal data
- Mock LinkedIn/job-style adoption signal data

Live adapters fail safely and return empty lists if packages, API access, network, or rate limits fail. The seeded demo data ensures the demo still works offline.

### Normalization

The normalizer converts different source payloads into one consistent `NormalizedItem` shape:

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
  "metadata": {},
  "signals": []
}
```

### Entity Linking

Implemented in `backend/app/memory/entity_linker.py`.

Current linking logic uses:

- Shared topic
- Title/abstract token overlap
- Metadata URL cross-references
- Shared authors
- Shared organizations

Supported relation labels:

- `paper_repo`
- `repo_model`
- `social_signal`
- `adoption_signal`
- `topic_similarity`

### Lightweight Memory Search

Implemented in `backend/app/memory/vector_store.py`.

This is intentionally simple and hardware-friendly. It creates a sparse token signature for each research item and performs cosine-like matching over query terms. It does not require GPU, ChromaDB, FAISS, or heavy embeddings.

Endpoint:

```text
GET /api/memory/search?q=multimodal agents&limit=10
```

### Demo Seed Data

Implemented in `backend/app/ingest/seed_data.py`.

Seed data covers a complete PRISM story:

- An emerging arXiv paper about sparse routing for multimodal agents
- A linked GitHub repository with stars/forks/commits
- A Hugging Face model upload
- A contradiction-style replication paper
- A news/adoption signal in healthcare
- A mock researcher teaser post
- A mock jobs trend signal
- A cross-domain graph-learning paper

This means the frontend and final demo do not depend on live APIs.

### Placeholder Fusion Reports

Implemented in `backend/app/api/routes_analysis.py`.

Endpoints:

```text
GET /api/analysis/fusion-reports
GET /api/analysis/fusion-reports/{item_id}
```

These currently return placeholder heuristic scores from stored metadata and signals. Teammate 3 should replace the internal logic with real engine outputs but preserve the response schema.

Current response contract:

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

### Markdown Report Export

Implemented in `backend/app/reports/markdown_report.py`.

Endpoint:

```text
GET /api/reports/weekly.md
```

It exports a Markdown report summarizing tracked signals, entity links, and integration notes.

## 3. How to Run the Backend

From the repository root:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open the API docs:

```text
http://localhost:8000/docs
```

Run the pipeline:

```bash
curl -X POST "http://localhost:8000/api/run-pipeline?query=multimodal%20agents&include_demo=true"
```

Then inspect:

```text
GET http://localhost:8000/api/items
GET http://localhost:8000/api/memory/search?q=multimodal%20agents
GET http://localhost:8000/api/memory/links
GET http://localhost:8000/api/analysis/fusion-reports
GET http://localhost:8000/api/reports/weekly.md
```

## 4. What Still Needs to Be Implemented

### Teammate 3: Intelligence Engines

Missing real engine layer:

- Signal Engine
- Trust Engine
- Debate Engine
- Gap Engine
- Cross-Domain Engine
- Fusion Engine

Recommended folder:

```text
backend/app/engines/
  __init__.py
  signal_engine.py
  trust_engine.py
  debate_engine.py
  gap_engine.py
  cross_domain_engine.py
  fusion_engine.py
```

Each engine should return:

- Numeric score from 0 to 1
- Verdict string
- Evidence strings
- Optional debug/details object

The Fusion Engine should eventually replace the placeholder logic inside `routes_analysis.py`.

### Teammate 4: Frontend and Demo

Missing frontend layer:

```text
frontend/
  src/
    api/client.ts
    pages/Dashboard.tsx
    pages/ItemDetail.tsx
    components/ScoreCard.tsx
    components/EvidencePanel.tsx
    components/ContradictionPanel.tsx
    components/OpportunityAtlas.tsx
    components/CrossDomainRadar.tsx
    components/TrendChart.tsx
```

The frontend should consume existing backend APIs and can start immediately using the placeholder fusion reports.

### Optional Integrations

Only if time remains:

- Telegram bot
- Discord bot
- PDF/DOCX export
- Scheduled APScheduler heartbeat
- OpenClaw-style multi-channel router
- LLM summarization through environment variable

## 5. Integration Strategy

### Step 1: Backend and Ingestion Baseline

Already done.

The backend can ingest data, store it, link it, search it, and expose placeholder analysis outputs.

### Step 2: Engine Integration

Teammate 3 should implement engine modules that accept SQLAlchemy records or normalized dictionaries.

Recommended engine function style:

```python
def score_item(item: ResearchItem, signals: list[SourceSignal]) -> EngineResult:
    ...
```

Recommended shared schema:

```python
class EngineResult(BaseModel):
    score: float
    verdict: str
    evidence: list[str]
    details: dict = {}
```

The real fusion endpoint should:

1. Query `ResearchItem`
2. Query related `SourceSignal`
3. Query related `EntityLink`
4. Run all five engines
5. Combine scores through Fusion Engine
6. Return `FusionReportRead`

### Step 3: Frontend Integration

Teammate 4 should build the UI against these endpoints:

```text
GET /health
POST /api/run-pipeline?query=multimodal agents&include_demo=true
GET /api/items
GET /api/items/{item_id}
GET /api/items/{item_id}/signals
GET /api/memory/search?q=multimodal agents
GET /api/memory/links
GET /api/analysis/fusion-reports
GET /api/analysis/fusion-reports/{item_id}
GET /api/reports/weekly.md
```

Recommended dashboard cards:

- Total tracked items
- Top PRISM Score
- Most controversial item
- Biggest adoption gap
- Best cross-domain transfer
- Source distribution

### Step 4: Final Demo Flow

1. Start backend.
2. Run pipeline with seeded demo data.
3. Start frontend.
4. Show dashboard with emerging topics.
5. Click sparse multimodal routing item.
6. Show source signals from arXiv, GitHub, HF, social mock data, jobs mock data, and news.
7. Show trust score and evidence.
8. Show contradiction battle with replication paper.
9. Show adoption gap in healthcare or enterprise deployment.
10. Show cross-domain graph-learning transfer idea.
11. Export weekly Markdown brief.

## 6. Suggested GitHub Workflow From Here

Branches:

```text
main
dev
feature/intelligence-engines
feature/frontend-dashboard
feature/report-polish
```

Rules:

- Merge this backend baseline into `dev` first.
- Teammate 3 branches from `dev` into `feature/intelligence-engines`.
- Teammate 4 branches from `dev` into `feature/frontend-dashboard`.
- Keep API response shapes stable.
- If an endpoint response must change, update this document and README in the same PR.
- Use seeded data for demos; do not depend only on live APIs.
- Do not commit `.env`, SQLite database files, or API keys.

## 7. Large Copy-Paste Prompt for Remaining Teammates or AI Agents

Use this prompt for another AI agent or teammate to finish the project from the current repository state:

```text
You are joining the PRISM hackathon project after the backend foundation and ingestion/memory layers have already been implemented.

PRISM means Pre-publication Research Intelligence & Signal Machine. It is a student-friendly research intelligence MVP that detects emerging papers/signals, scores trustworthiness, finds contradictions, maps adoption gaps, proposes cross-domain transfers, and shows everything in a dashboard and weekly brief.

Current repository state:
- Backend exists under backend/app.
- FastAPI app entrypoint: backend/app/main.py.
- SQLite + SQLAlchemy models exist in backend/app/db/models.py.
- Pydantic schemas exist in backend/app/schemas/research.py.
- Ingestion adapters exist for arXiv, GitHub, Hugging Face, RSS/news, mock social, and mock jobs.
- Normalization pipeline exists in backend/app/ingest/pipeline.py and backend/app/ingest/normalizer.py.
- Seed demo data exists in backend/app/ingest/seed_data.py.
- Entity linking exists in backend/app/memory/entity_linker.py.
- Lightweight memory search exists in backend/app/memory/vector_store.py.
- API routes already exist for health, items, pipeline, memory, placeholder analysis, and reports.
- Placeholder fusion reports exist in backend/app/api/routes_analysis.py and must be replaced with real engine outputs while preserving response contracts.

Run backend:
1. Go to backend directory.
2. Create virtualenv.
3. Install requirements.txt.
4. Copy .env.example to .env.
5. Run uvicorn app.main:app --reload.
6. Open http://localhost:8000/docs.
7. Run POST /api/run-pipeline?query=multimodal%20agents&include_demo=true.

Existing API endpoints:
- GET /health
- POST /api/run-pipeline?query=multimodal agents&include_demo=true
- GET /api/items
- GET /api/items/{item_id}
- GET /api/items/{item_id}/signals
- GET /api/memory/search?q=multimodal agents
- GET /api/memory/links
- GET /api/analysis/fusion-reports
- GET /api/analysis/fusion-reports/{item_id}
- GET /api/reports/weekly.md

Your task is to implement the remaining PRISM MVP work without breaking the existing API contracts.

Part A: Intelligence Engines
Create backend/app/engines with:
- __init__.py
- schemas.py
- signal_engine.py
- trust_engine.py
- debate_engine.py
- gap_engine.py
- cross_domain_engine.py
- fusion_engine.py

Implement an EngineResult schema with:
- score: float from 0 to 1
- verdict: string
- evidence: list of strings
- details: dictionary

Signal Engine requirements:
- Inputs: ResearchItem and related SourceSignal records.
- Use stars, forks, commits, model downloads, mentions, source type, and recency.
- Output novelty/early-signal score from 0 to 1.
- Evidence must mention the strongest source signals.

Trust Engine requirements:
- Inputs: ResearchItem and metadata.
- Score code availability, dataset availability, benchmark clarity, license availability, and reproducibility risk.
- Use metadata fields like code_url, dataset_url, benchmark, license, source.
- Output trust score from 0 to 1 and replication-risk details.

Debate Engine requirements:
- Inputs: Current item plus related items from same topic/entity links.
- Detect contradiction language such as contradicts, fails to reproduce, replication, lower than reported, distribution shift, not robust.
- Compare titles, abstracts, and metadata claim_language.
- Output controversy score from 0 to 1 and contested-claim evidence.

Gap Engine requirements:
- Inputs: Research item, signals, related news/mock_jobs items.
- Compare academic momentum against industry adoption.
- High academic signal plus low job/news/product signal should produce high adoption gap.
- Output opportunity/adoption-gap score and business-use-case evidence.

Cross-Domain Engine requirements:
- Inputs: item metadata, topic, text, and related items.
- Detect source_domain, target_domain, technique metadata if present.
- Also infer transfer from keywords like graph, biology, supply chain, optimization, healthcare, finance, robotics.
- Output transferability score, source domain, target domain, technique, and rationale.

Fusion Engine requirements:
- Combine engine outputs into FusionReportRead-compatible response:
  - item_id
  - prism_score
  - novelty_score
  - trust_score
  - controversy_score
  - adoption_gap_score
  - transferability_score
  - verdict
  - evidence
- Use an explainable weighted formula.
- Recommended formula:
  prism_score = 0.25*novelty + 0.25*trust + 0.15*(1 - controversy) + 0.20*adoption_gap + 0.15*transferability
- Preserve the endpoint shape expected by frontend.

Modify backend/app/api/routes_analysis.py:
- Replace placeholder scoring with real engine calls.
- Keep GET /api/analysis/fusion-reports and GET /api/analysis/fusion-reports/{item_id}.
- Do not break existing Pydantic response schema.

Part B: Frontend Dashboard
Create a React + Vite + TypeScript + Tailwind frontend under frontend/.

Frontend requirements:
- API client in frontend/src/api/client.ts.
- Dashboard page that calls backend APIs.
- Button to run pipeline.
- Cards for tracked items, PRISM score, trust, controversy, adoption gap, transferability.
- Item list sorted by PRISM score.
- Item detail page or modal showing:
  - research item metadata
  - source signals
  - entity links
  - fusion report
  - evidence list
- Components:
  - ScoreCard
  - EvidencePanel
  - ContradictionPanel
  - OpportunityAtlas
  - CrossDomainRadar
  - TrendChart or simple source distribution chart
- Add loading and error states.
- Add fallback mock JSON only if backend is unreachable.
- Add a report export button that links to /api/reports/weekly.md.

Frontend visual direction:
- Clean modern research intelligence dashboard.
- Dark or light theme is acceptable.
- Prioritize demo clarity over complex UI.
- Show the five PRISM engines clearly.
- Make evidence visible because judges need to understand why a score was produced.

Part C: Integration and Demo
After implementation:
1. Start backend.
2. Run pipeline with include_demo=true.
3. Start frontend.
4. Verify dashboard loads items and fusion reports.
5. Verify clicking an item shows evidence and source signals.
6. Verify weekly report export downloads Markdown.
7. Add or update README with frontend run instructions.
8. Keep all API keys in .env only.
9. Do not commit prism.db or .env.

Critical constraints:
- Keep it realistic for a one-week student hackathon.
- Do not add heavy GPU/model dependencies.
- Do not scrape Twitter/X or LinkedIn.
- Use mock social/job data for restricted platforms.
- Avoid breaking current backend endpoints.
- Use deterministic seed data so the demo works offline.
- Do not over-engineer authentication, deployment, or distributed jobs.

Expected final result:
A working PRISM MVP where a judge can run the pipeline, open a dashboard, see emerging research intelligence, inspect evidence for each score, view contradiction/adoption/cross-domain insights, and export a weekly brief.
```

## 8. Recommended Final README Additions After Teammates Finish

Once the engines and frontend are complete, update the README with:

- Full-stack setup instructions
- Frontend commands
- Backend commands
- Demo script
- Architecture diagram
- Screenshots
- Known limitations
- Future scope

## 9. Known Limitations in the Current Baseline

- Fusion reports are placeholders until Teammate 3 integrates real engines.
- Local memory search is sparse-token based, not semantic embeddings.
- Live APIs can fail due to network or rate limits.
- Twitter/X and LinkedIn are mocked intentionally.
- No frontend exists yet.
- No production authentication exists.
- No scheduled daemon exists yet.

## 10. Suggested Hackathon Pitch Framing

PRISM turns scattered weak signals from papers, repositories, models, social chatter, job posts, and news into one explainable research-intelligence workflow. It does not try to replace researchers. It helps them decide what to read first, what to trust, what is disputed, where industry is behind academia, and where an idea from one field may unlock progress in another.
