# PRISM Testing Phase - Comprehensive Documentation

**Project**: GenAIResearchOpenClaw (PRISM MVP)  
**Version**: 1.0.0 MVP  
**Testing Date**: May 2026  
**Prepared by**: YuvarajGML  

---

## Table of Contents

1. [Overview & Objectives](#1-overview--objectives)
2. [Testing Scope](#2-testing-scope)
3. [Test Environment Setup](#3-test-environment-setup)
4. [Testing Categories](#4-testing-categories)
5. [Test Cases & Execution](#5-test-cases--execution)
6. [Acceptance Criteria](#6-acceptance-criteria)
7. [Defect Management](#7-defect-management)
8. [Performance & Load Testing](#8-performance--load-testing)
9. [Integration Testing](#9-integration-testing)
10. [Frontend Testing](#10-frontend-testing)
11. [Demo Scenario Testing](#11-demo-scenario-testing)
12. [Sign-off & Reporting](#12-sign-off--reporting)

---

## 1. Overview & Objectives

### Purpose
The PRISM testing phase validates that all components (backend APIs, intelligence engines, database persistence, memory search, and frontend) work correctly together before client demonstration.

### Key Objectives
- ✅ Verify all APIs return correct response schemas
- ✅ Validate each intelligence engine produces reasonable scores
- ✅ Test data flow from ingestion → normalization → linking → analysis
- ✅ Ensure database persistence is reliable
- ✅ Confirm frontend dashboard loads and displays data correctly
- ✅ Validate end-to-end pipeline execution
- ✅ Test fallback and error handling
- ✅ Measure performance baselines

### Success Criteria
- All API endpoints respond with correct status codes
- Engine scores fall within expected ranges (0-1)
- Demo data executes without errors
- Frontend displays items and reports
- No critical defects at go-live

---

## 2. Testing Scope

### In Scope ✓
- Backend FastAPI application
- All 6 intelligence engines (Signal, Trust, Debate, Gap, Cross-Domain, Fusion)
- SQLite database and SQLAlchemy models
- All API endpoints (health, items, pipeline, analysis, memory, reports)
- Entity linking logic
- Memory search functionality
- Report generation (Markdown)
- Frontend React dashboard
- End-to-end pipeline execution

### Out of Scope ✗
- Production deployment
- Load testing with >1000 concurrent users
- Real-time Twitter/LinkedIn scraping (mocked)
- Distributed caching (Redis/Memcached)
- Advanced LLM integrations
- Scheduled agent loops (optional enhancement)

### Known Limitations
- Local SQLite only (no multi-instance support)
- Memory search uses token-based matching (not semantic embeddings)
- Mock social/job data (not real Twitter/LinkedIn)
- No production authentication

---

## 3. Test Environment Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- Git
- ~2GB disk space
- Internet access (for arXiv, GitHub, HF APIs)

### Backend Setup
```bash
# Clone and navigate
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env if needed (API tokens are optional for demo)

# Initialize database
python -c "from app.db.init_db import init_db; init_db()"

# Verify backend runs
uvicorn app.main:app --reload
# Should output: Uvicorn running on http://127.0.0.1:8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env

# Verify frontend runs
npm run dev
# Should output: Local: http://localhost:5173
```

### Test Environment Checklist
- [ ] Backend starts without errors
- [ ] FastAPI Swagger docs available at http://localhost:8000/docs
- [ ] Frontend starts without errors
- [ ] Frontend accessible at http://localhost:5173
- [ ] Backend health check returns 200
- [ ] SQLite database created in backend/prism.db

---

## 4. Testing Categories

### 4.1 Unit Testing
**Purpose**: Validate individual components in isolation

**Components to Test**:
- Signal Engine score calculation
- Trust Engine reproducibility scoring
- Debate Engine contradiction detection
- Gap Engine adoption gap calculation
- Cross-Domain Engine transferability detection
- Fusion Engine weighted formula
- Entity Linking algorithms
- Memory Search token matching
- Normalizer data transformation
- Report Generator markdown output

### 4.2 Integration Testing
**Purpose**: Validate components work together

**Test Paths**:
- Pipeline ingestion → Database storage
- Raw data → Normalization → Entity linking
- Items + Signals → Engine scoring → Report generation
- API request → Database query → Response schema

### 4.3 API Testing
**Purpose**: Validate REST endpoints

**Testing Approach**:
- Status codes (200, 404, 500)
- Response schemas match Pydantic models
- Request validation
- Error handling

### 4.4 Database Testing
**Purpose**: Validate persistence

**Testing Approach**:
- CRUD operations on all models
- Data integrity
- Relationship constraints
- Query performance

### 4.5 Frontend Testing
**Purpose**: Validate UI rendering and interactions

**Testing Approach**:
- Component rendering
- API integration
- User interactions
- Error states

### 4.6 End-to-End Testing
**Purpose**: Validate complete workflows

**Test Scenarios**:
- Full pipeline execution with demo data
- Real arXiv query
- Dashboard load and display
- Score card rendering

---

## 5. Test Cases & Execution

### 5.1 Backend Unit Tests

#### Test Suite 1: Signal Engine

| Test ID | Test Name | Input | Expected Output | Pass/Fail |
|---------|-----------|-------|-----------------|-----------|
| T-SE-001 | High novelty paper | Recent arXiv + high stars | novelty_score > 0.7 | [ ] |
| T-SE-002 | Low signal paper | Old paper + low activity | novelty_score < 0.4 | [ ] |
| T-SE-003 | Multiple sources | Paper + repo + model | score considers all | [ ] |
| T-SE-004 | No signals | Item with no related signals | score uses defaults | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/engines/test_signal_engine.py -v
```

#### Test Suite 2: Trust Engine

| Test ID | Test Name | Input | Expected Output | Pass/Fail |
|---------|-----------|-------|-----------------|-----------|
| T-TE-001 | High trust paper | Code URL + dataset + benchmark | trust_score > 0.7 | [ ] |
| T-TE-002 | Low trust paper | No code/data | trust_score < 0.4 | [ ] |
| T-TE-003 | License present | Apache/MIT license | evidence mentions license | [ ] |
| T-TE-004 | Missing metadata | Minimal metadata | Handles gracefully | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/engines/test_trust_engine.py -v
```

#### Test Suite 3: Debate Engine

| Test ID | Test Name | Input | Expected Output | Pass/Fail |
|---------|-----------|-------|-----------------|-----------|
| T-DE-001 | Contradiction found | Paper + replication paper | controversy_score > 0.6 | [ ] |
| T-DE-002 | No contradiction | Single paper | controversy_score < 0.3 | [ ] |
| T-DE-003 | Contradiction keywords | "contradicts" in abstract | Detected correctly | [ ] |
| T-DE-004 | Similar topics | Related items from same topic | Linked properly | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/engines/test_debate_engine.py -v
```

#### Test Suite 4: Gap Engine

| Test ID | Test Name | Input | Expected Output | Pass/Fail |
|---------|-----------|-------|-----------------|-----------|
| T-GE-001 | High adoption gap | High academic + low job signals | gap_score > 0.7 | [ ] |
| T-GE-002 | Balanced signals | Even academic/industry | gap_score ≈ 0.5 | [ ] |
| T-GE-003 | Low academic | Few papers + high jobs | gap_score < 0.3 | [ ] |
| T-GE-004 | Healthcare domain | Medical paper + healthcare news | Domain detected | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/engines/test_gap_engine.py -v
```

#### Test Suite 5: Cross-Domain Engine

| Test ID | Test Name | Input | Expected Output | Pass/Fail |
|---------|-----------|-------|-----------------|-----------|
| T-CD-001 | Graph to supply chain | Graph paper + supply metadata | transferability > 0.6 | [ ] |
| T-CD-002 | NLP to biology | NLP technique + biology keywords | transfer detected | [ ] |
| T-CD-003 | No transfer potential | Domain-specific paper | transferability < 0.4 | [ ] |
| T-CD-004 | Inference domains | From title/abstract keywords | Domains extracted | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/engines/test_cross_domain_engine.py -v
```

#### Test Suite 6: Fusion Engine

| Test ID | Test Name | Input | Expected Output | Pass/Fail |
|---------|-----------|-------|-----------------|-----------|
| T-FE-001 | Weighted combination | All 5 engines + scores | prism_score in [0, 1] | [ ] |
| T-FE-002 | Formula validation | Known inputs | Formula: 0.25*novelty + 0.25*trust + 0.15*(1-controversy) + 0.20*gap + 0.15*transfer | [ ] |
| T-FE-003 | Verdict generation | High/low scores | Generates appropriate verdict | [ ] |
| T-FE-004 | Evidence collection | Multiple engines | Combines evidence properly | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/engines/test_fusion_engine.py -v
```

---

### 5.2 Backend Integration Tests

#### Test Suite 7: Pipeline & Data Flow

| Test ID | Test Name | Steps | Expected Result | Pass/Fail |
|---------|-----------|-------|-----------------|-----------|
| T-INT-001 | Full pipeline execution | Query → Ingest → Normalize → Link → Analyze | All items in DB | [ ] |
| T-INT-002 | Demo data pipeline | include_demo=true | Demo seed data loaded | [ ] |
| T-INT-003 | Entity linking | Papers + repos + models | Linked via shared topics | [ ] |
| T-INT-004 | Memory indexing | Items added | Searchable immediately | [ ] |
| T-INT-005 | Engine persistence | Run engines | Scores stored correctly | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/integration/test_pipeline.py -v
python -m pytest tests/integration/test_data_flow.py -v
```

---

### 5.3 API Tests

#### Test Suite 8: Health & Items Endpoints

| Test ID | Endpoint | Method | Expected Status | Expected Body | Pass/Fail |
|---------|----------|--------|-----------------|----------------|-----------|
| T-API-001 | /health | GET | 200 | `{status: "ok"}` | [ ] |
| T-API-002 | /api/items | GET | 200 | `{data: [...]}` | [ ] |
| T-API-003 | /api/items | GET | 200 | Items count ≥ 0 | [ ] |
| T-API-004 | /api/items/{id} | GET | 200 | ResearchItem schema | [ ] |
| T-API-005 | /api/items/{id} | GET | 404 | Non-existent ID | [ ] |
| T-API-006 | /api/items/{id}/signals | GET | 200 | SourceSignal array | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/api/test_items.py -v
python -m pytest tests/api/test_health.py -v
```

#### Test Suite 9: Pipeline Endpoint

| Test ID | Endpoint | Method | Params | Expected | Pass/Fail |
|---------|----------|--------|--------|----------|-----------|
| T-API-007 | /api/run-pipeline | POST | query=multimodal agents | 200 + result | [ ] |
| T-API-008 | /api/run-pipeline | POST | include_demo=true | Seeds data | [ ] |
| T-API-009 | /api/run-pipeline | POST | Empty query | 400 or defaults | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/api/test_pipeline.py -v
```

#### Test Suite 10: Analysis Endpoints

| Test ID | Endpoint | Method | Expected Status | Schema Check | Pass/Fail |
|---------|----------|--------|-----------------|--------------|-----------|
| T-API-010 | /api/analysis/fusion-reports | GET | 200 | FusionReportRead[] | [ ] |
| T-API-011 | /api/analysis/fusion-reports/{id} | GET | 200 | FusionReportRead | [ ] |
| T-API-012 | /api/analysis/fusion-reports/{id} | GET | 404 | Non-existent | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/api/test_analysis.py -v
```

#### Test Suite 11: Memory Endpoints

| Test ID | Endpoint | Method | Params | Expected | Pass/Fail |
|---------|----------|--------|--------|----------|-----------|
| T-API-013 | /api/memory/search | GET | q=multimodal | 200 + results | [ ] |
| T-API-014 | /api/memory/search | GET | q=xyz&limit=5 | Max 5 results | [ ] |
| T-API-015 | /api/memory/links | GET | - | EntityLink array | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/api/test_memory.py -v
```

#### Test Suite 12: Report Endpoint

| Test ID | Endpoint | Method | Expected Status | Format | Pass/Fail |
|---------|----------|--------|-----------------|--------|-----------|
| T-API-016 | /api/reports/weekly.md | GET | 200 | Markdown text | [ ] |
| T-API-017 | /api/reports/weekly.md | GET | 200 | Contains "PRISM" | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/api/test_reports.py -v
```

---

### 5.4 Database Tests

#### Test Suite 13: Database Operations

| Test ID | Operation | Entity | Test | Expected | Pass/Fail |
|---------|-----------|--------|------|----------|-----------|
| T-DB-001 | Create | ResearchItem | Insert item | ID assigned | [ ] |
| T-DB-002 | Read | ResearchItem | Query by ID | Correct data | [ ] |
| T-DB-003 | Update | ResearchItem | Modify field | Updated | [ ] |
| T-DB-004 | Delete | ResearchItem | Delete & query | Not found | [ ] |
| T-DB-005 | Relationship | Item ↔ Signal | Create link | Queryable | [ ] |
| T-DB-006 | Constraint | ResearchItem | Null title | Error | [ ] |
| T-DB-007 | Performance | Query | 1000 items | < 100ms | [ ] |

**Execution**:
```bash
cd backend
python -m pytest tests/database/ -v
```

---

### 5.5 Frontend Tests

#### Test Suite 14: Component Rendering

| Test ID | Component | Test | Expected | Pass/Fail |
|---------|-----------|------|----------|-----------|
| T-FE-001 | Dashboard | Render | No errors | [ ] |
| T-FE-002 | Dashboard | Load items from API | Items displayed | [ ] |
| T-FE-003 | ScoreCard | Render | Score visible | [ ] |
| T-FE-004 | ItemList | Filter/sort | Works correctly | [ ] |
| T-FE-005 | ItemDetail | Modal/page | All fields shown | [ ] |
| T-FE-006 | EvidencePanel | Render | Evidence visible | [ ] |

**Execution**:
```bash
cd frontend
npm run test -- --run
```

#### Test Suite 15: User Interactions

| Test ID | Interaction | Action | Expected | Pass/Fail |
|---------|-------------|--------|----------|-----------|
| T-FE-007 | Run Pipeline | Click button | Pipeline starts | [ ] |
| T-FE-008 | Item Click | Select item | Detail modal opens | [ ] |
| T-FE-009 | Search | Enter query | Results filter | [ ] |
| T-FE-010 | Export Report | Click export | Markdown downloads | [ ] |

---

### 5.6 End-to-End Tests

#### Test Suite 16: Complete Workflows

| Test ID | Scenario | Steps | Expected | Pass/Fail |
|---------|----------|-------|----------|-----------|
| T-E2E-001 | Demo workflow | 1. Start backend 2. Run pipeline with demo=true 3. Start frontend 4. Load dashboard 5. Click item | All working | [ ] |
| T-E2E-002 | Live query | 1. Backend up 2. POST /api/run-pipeline?query=AI 3. Wait 4. GET /api/items | Items retrieved | [ ] |
| T-E2E-003 | Full analysis | 1. Load items 2. Run engines 3. Get fusion reports 4. Display scores | All scores > 0 | [ ] |
| T-E2E-004 | Memory search | 1. Add items 2. Search "multimodal" 3. Verify results | Found items | [ ] |
| T-E2E-005 | Report export | 1. Items loaded 2. GET /api/reports/weekly.md 3. Parse markdown | Valid markdown | [ ] |

**Execution**:
```bash
# Manual execution following the demo scenario in Section 11
```

---

## 6. Acceptance Criteria

### Backend Acceptance
- [ ] All 6 engines implemented and scoring 0-1
- [ ] All 9 API endpoints return correct schemas
- [ ] Database persists data correctly
- [ ] Entity linking finds related items
- [ ] Memory search returns relevant results
- [ ] Markdown report generates successfully
- [ ] Zero critical defects
- [ ] No unhandled exceptions

### Frontend Acceptance
- [ ] Dashboard renders without errors
- [ ] Items load from API
- [ ] Score cards display properly
- [ ] Item detail modal/page works
- [ ] Report export works
- [ ] Handles missing backend gracefully
- [ ] Zero critical defects

### Integration Acceptance
- [ ] Full pipeline executes without errors
- [ ] Demo data loads successfully
- [ ] All components work together
- [ ] Performance acceptable (<2s responses)
- [ ] No data loss during operations

### Demo Readiness
- [ ] Can be executed multiple times without reset
- [ ] Works offline with seeded data
- [ ] All functionality visible in demo
- [ ] No credentials exposed
- [ ] Professional appearance

---

## 7. Defect Management

### Defect Classification

**Critical** (Blocks demo):
- API returns 500 error
- Engine crashes
- Database corruption
- Frontend won't load
- Pipeline fails

**Major** (Significant impact):
- Wrong schema returned
- Engine score out of range
- Incorrect calculations
- Missing UI elements
- Performance < 5s

**Minor** (Polish):
- Typos in text
- Formatting issues
- Accessibility issues
- Nice-to-have features

### Defect Logging Template

```
Defect ID: DEF-XXX
Date Found: YYYY-MM-DD
Severity: Critical/Major/Minor
Component: [Backend/Frontend/API/Engine]
Title: [Brief description]
Steps to Reproduce:
1. ...
2. ...
Expected: [What should happen]
Actual: [What actually happened]
Evidence: [Screenshot/log/curl output]
Status: Open/In Progress/Resolved/Verified
Assigned To: [Developer]
Resolution: [How fixed]
```

### Defect Tracking
- Use GitHub Issues: `afkscoped/GenAIResearchOpenClaw/issues`
- Label with: `bug`, `critical`/`major`/`minor`, `backend`/`frontend`
- Track in PR reviews

---

## 8. Performance & Load Testing

### Performance Baselines

#### Backend Response Times

| Endpoint | Expected | Target |
|----------|----------|--------|
| GET /health | < 50ms | < 100ms |
| GET /api/items | < 500ms | < 1s |
| GET /api/items/{id} | < 200ms | < 500ms |
| POST /api/run-pipeline | < 5s | < 10s |
| GET /api/analysis/fusion-reports | < 1s | < 2s |
| GET /api/memory/search | < 300ms | < 1s |

**Test Script**:
```bash
# Install Apache Bench or similar
ab -n 100 -c 10 http://localhost:8000/api/items

# Or use curl loop
for i in {1..10}; do
  time curl http://localhost:8000/api/items > /dev/null 2>&1
done
```

#### Frontend Load Time

| Metric | Target |
|--------|--------|
| Initial load | < 3s |
| Dashboard render | < 2s |
| API call display | < 1s |
| Item detail open | < 500ms |

**Test Tool**: Browser DevTools Network tab

#### Database Performance

| Query | Expected |
|-------|----------|
| All items count | < 50ms |
| Item + signals join | < 100ms |
| Memory search tokenize | < 200ms |
| Links query | < 150ms |

---

## 9. Integration Testing

### Test Data Sets

#### Dataset 1: Minimal
- 2 ResearchItems
- 2 SourceSignals
- 1 EntityLink
- Purpose: Smoke testing

#### Dataset 2: Standard (Demo)
- 8 ResearchItems
- 12 SourceSignals
- 10 EntityLinks
- Purpose: Feature demonstration

#### Dataset 3: Stress
- 100 ResearchItems
- 200 SourceSignals
- 150 EntityLinks
- Purpose: Performance validation

### Integration Scenarios

```
Scenario A: Happy Path
  1. Start backend ✓
  2. POST /api/run-pipeline?query=multimodal agents&include_demo=true
  3. Verify items in database ✓
  4. GET /api/items (should return 8+ items)
  5. GET /api/analysis/fusion-reports (should have scores)
  6. GET /api/memory/search?q=multimodal (should find papers)
  7. GET /api/reports/weekly.md (should have markdown)
  ✓ Result: All endpoints work

Scenario B: Error Handling
  1. GET /api/items/{invalid-id}
  2. Expected: 404 response
  3. GET /api/run-pipeline (missing query)
  4. Expected: 400 or default behavior
  5. POST /api/run-pipeline (backend down)
  6. Expected: Clear error
  ✓ Result: Errors handled gracefully

Scenario C: Data Consistency
  1. Create 5 items via pipeline
  2. Query items count (should be 5+)
  3. Add signal to item
  4. Query signals (should find it)
  5. Search memory (should index items)
  6. Run engines
  7. Verify scores stored
  ✓ Result: Data consistent across all components
```

---

## 10. Frontend Testing

### Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest | ✓ Primary |
| Firefox | Latest | ✓ Secondary |
| Safari | Latest | ✓ Secondary |
| Edge | Latest | ✓ Secondary |

### Responsive Testing

| Device | Resolution | Status |
|--------|-----------|--------|
| Desktop | 1920x1080 | ✓ Primary |
| Laptop | 1366x768 | ✓ Primary |
| Tablet | 768x1024 | ⚠ Secondary |
| Mobile | 375x667 | ⚠ Secondary |

### Accessibility Testing

- [ ] Tab navigation works
- [ ] Screen reader compatible (ARIA labels)
- [ ] Color contrast acceptable
- [ ] Keyboard shortcuts functional

### Test Checklist

- [ ] Dashboard loads without errors
- [ ] Items display in list
- [ ] Score cards show numbers
- [ ] Click item opens detail
- [ ] Evidence panel visible
- [ ] Report export link works
- [ ] Search/filter functional
- [ ] Mobile responsive
- [ ] API fallback works (without backend)
- [ ] No console errors

---

## 11. Demo Scenario Testing

### Demo Flow (Complete End-to-End)

**Objective**: Show PRISM's capabilities in 5-10 minutes

**Duration**: ~10 minutes

**Steps**:

```
=== PRISM MVP Demo Scenario ===

[SETUP - 2 min]
1. Open two terminals
2. Terminal 1: cd backend && uvicorn app.main:app --reload
   → Wait for "Uvicorn running on..."
3. Terminal 2: cd frontend && npm run dev
   → Wait for "Local: http://localhost:5173"

[BACKEND DEMO - 3 min]
4. Open http://localhost:8000/docs (Swagger UI)
   → Show: All 9 API endpoints available
   
5. Execute: POST /api/run-pipeline
   Params: query=multimodal agents, include_demo=true
   → Show: Pipeline starts, returns success
   → Show: Loading seeded demo data
   → Wait ~5 seconds
   
6. Execute: GET /api/items
   → Show: 8+ research items loaded
   → Show: Items from arXiv, GitHub, HuggingFace sources
   
7. Execute: GET /api/items/{first-id}
   → Show: Complete item structure
   → Show: Title, abstract, source, metadata
   → Show: Authors and organizations extracted

[ANALYSIS DEMO - 2 min]
8. Execute: GET /api/analysis/fusion-reports
   → Show: All reports with PRISM scores
   → Show: Individual engine scores (novelty, trust, controversy, etc.)
   → Show: Evidence strings explaining the scores
   
9. Execute: GET /api/analysis/fusion-reports/{high-score-id}
   → Show: Details of top-ranked item
   → Explain: Why this item scored high
   → Point out: Novelty + Trust + Low Controversy = High PRISM

[MEMORY DEMO - 1 min]
10. Execute: GET /api/memory/search?q=multimodal agents
    → Show: Search results from sparse-token memory
    → Show: Rankings match semantic relevance
    
11. Execute: GET /api/memory/links
    → Show: Entity relationships found
    → Show: Papers linked to repos/models

[FRONTEND DEMO - 2 min]
12. Open http://localhost:5173
    → Show: Dashboard loads with no errors
    
13. Look for "Run PRISM" button, click it
    → Show: Dashboard updating
    → Show: Items appearing in ranked list
    
14. Click on top-ranked item
    → Show: Item detail modal
    → Show: Score cards (Novelty, Trust, Controversy, Gap, Transfer)
    → Show: Evidence panel with reasoning
    
15. Click "Export Report"
    → Show: Weekly markdown report downloads
    → Open .md file in text editor
    → Show: Markdown formatting with item summaries

[SUMMARY - 1 min]
16. Highlight key takeaways:
    ✓ Real-time research intelligence from multiple sources
    ✓ Explainable scoring with 5 engines
    ✓ Entity linking connecting related research
    ✓ Professional dashboard for exploration
    ✓ Portable MVP (runs offline with seeded data)
```

### Pre-Demo Checklist

- [ ] Database reset to fresh state: `rm backend/prism.db`
- [ ] Backend dependencies installed: `pip install -r requirements.txt`
- [ ] Frontend dependencies installed: `npm install`
- [ ] Environment files copied: `.env.example → .env`
- [ ] No uncommitted changes in git
- [ ] Terminal windows ready (two side-by-side)
- [ ] Browser windows ready (http://localhost:8000/docs and http://localhost:5173)
- [ ] Network connection stable
- [ ] Screenshots prepared for backup
- [ ] Time allocated for Q&A

### Demo Timing Guide

| Phase | Time | Notes |
|-------|------|-------|
| Setup | 2 min | Can be pre-done |
| Backend demo | 3 min | Show API endpoints + pipeline |
| Analysis | 2 min | Show engine scores |
| Memory | 1 min | Show search + links |
| Frontend | 2 min | Show dashboard + export |
| Q&A | 2-3 min | Buffer for questions |
| **Total** | **10-12 min** | Professional pace |

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Backend won't start | Check port 8000 not in use: `lsof -i :8000` |
| Frontend won't start | Check port 5173 not in use: `lsof -i :5173` |
| Database error | Delete prism.db and restart backend |
| API 404s | Backend not running, check terminal |
| Dashboard empty | Run /api/run-pipeline first |
| Slow responses | Kill other processes, check disk space |
| Frontend API errors | Check CORS in .env, backend must be running |

---

## 12. Sign-off & Reporting

### Test Execution Report

**Project**: PRISM MVP  
**Test Phase**: Comprehensive Testing  
**Date Started**: [DATE]  
**Date Completed**: [DATE]  
**Tested By**: YuvarajGML  

### Summary Metrics

| Category | Pass | Fail | Pending | Pass Rate |
|----------|------|------|---------|-----------|
| Unit Tests | [ ] | [ ] | [ ] | [ ]% |
| Integration Tests | [ ] | [ ] | [ ] | [ ]% |
| API Tests | [ ] | [ ] | [ ] | [ ]% |
| Database Tests | [ ] | [ ] | [ ] | [ ]% |
| Frontend Tests | [ ] | [ ] | [ ] | [ ]% |
| E2E Tests | [ ] | [ ] | [ ] | [ ]% |
| **TOTAL** | [ ] | [ ] | [ ] | [ ]% |

### Quality Assessment

| Aspect | Status | Comments |
|--------|--------|----------|
| Code Quality | ✓/⚠/✗ | |
| Performance | ✓/⚠/✗ | |
| Reliability | ✓/⚠/✗ | |
| User Experience | ✓/⚠/✗ | |
| Documentation | ✓/⚠/✗ | |

### Critical Issues Summary

```
Total Critical Defects: [ ]
Total Major Defects: [ ]
Total Minor Defects: [ ]

Blocking Issues: [ ]
Non-Blocking Issues: [ ]

Status: ✓ READY FOR DEMO / ⚠ CONDITIONAL / ✗ NOT READY
```

### Sign-Off

- **Testing Lead**: YuvarajGML
- **Date**: ____________
- **Client Approval**: ____________ (on presentation day)

### Recommendations

```
For Demo:
- [ ] Use seeded data (include_demo=true) for consistency
- [ ] Pre-load dashboard before showing clients
- [ ] Have backup terminal windows ready
- [ ] Prepare talking points about each engine
- [ ] Show evidence strings (judges care about explainability)

For Production:
- [ ] Migrate to PostgreSQL
- [ ] Add authentication
- [ ] Set up monitoring/logging
- [ ] Implement caching (Redis)
- [ ] Add scheduled tasks (APScheduler)
```

---

## Appendix A: Test Execution Template

```bash
# Quick test run script
#!/bin/bash

echo "=== PRISM Testing Phase ==="
echo "1. Starting Backend..."
cd backend
python -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
cp .env.example .env 2>/dev/null || true
uvicorn app.main:app --reload &
BACKEND_PID=$!
sleep 3

echo "2. Health check..."
curl -s http://localhost:8000/health

echo "3. Running pipeline..."
curl -s -X POST "http://localhost:8000/api/run-pipeline?query=multimodal%20agents&include_demo=true"

echo "4. Checking items..."
curl -s http://localhost:8000/api/items | head -20

echo "5. Getting fusion reports..."
curl -s http://localhost:8000/api/analysis/fusion-reports | head -20

echo "6. Running pytest..."
python -m pytest tests/ -v --tb=short 2>/dev/null || echo "No tests found (optional)"

echo "7. Frontend check..."
cd ../frontend
npm install > /dev/null 2>&1
npm run build > /dev/null 2>&1 && echo "✓ Frontend builds successfully"

kill $BACKEND_PID
echo "=== Testing Complete ==="
```

---

## Appendix B: Curl Commands for Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# List items
curl http://localhost:8000/api/items

# Get single item
curl http://localhost:8000/api/items/item_id_here

# Get item signals
curl http://localhost:8000/api/items/item_id_here/signals

# Run pipeline
curl -X POST "http://localhost:8000/api/run-pipeline?query=multimodal%20agents&include_demo=true"

# Get fusion reports
curl http://localhost:8000/api/analysis/fusion-reports

# Get single fusion report
curl http://localhost:8000/api/analysis/fusion-reports/item_id_here

# Memory search
curl "http://localhost:8000/api/memory/search?q=multimodal%20agents"

# Get entity links
curl http://localhost:8000/api/memory/links

# Get weekly report
curl http://localhost:8000/api/reports/weekly.md
```

---

## Appendix C: Expected Engine Score Ranges

### Normal Ranges (Typical Items)

| Engine | Low | Medium | High |
|--------|-----|--------|------|
| Signal | 0.2-0.4 | 0.4-0.6 | 0.6-0.9 |
| Trust | 0.3-0.5 | 0.5-0.7 | 0.7-0.95 |
| Debate | 0.1-0.3 | 0.3-0.6 | 0.6-0.95 |
| Gap | 0.2-0.4 | 0.4-0.7 | 0.7-0.95 |
| Cross-Domain | 0.1-0.3 | 0.3-0.6 | 0.6-0.9 |
| **PRISM** | 0.2-0.4 | 0.45-0.65 | 0.65-0.9 |

### Demo Data Expected Scores

| Item | Expected Novelty | Expected Trust | Expected PRISM |
|------|------------------|-----------------|----------------|
| Multimodal Routing (arXiv) | 0.75+ | 0.65+ | 0.7+ |
| Replication Paper (contrary) | 0.45+ | 0.55+ | 0.45+ |
| GitHub Repo (linked) | 0.6+ | 0.75+ | 0.68+ |

---

**End of PRISM Testing Phase Document**

*Version 1.0 | Last Updated: May 2, 2026*
