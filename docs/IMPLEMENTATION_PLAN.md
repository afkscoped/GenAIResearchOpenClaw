# PRISM v2 — Full Implementation Plan
**Project**: GenAIResearchOpenClaw / PRISM  
**Date**: May 2026  
**Status**: Planning Phase

---

## 1. Current System Overview

PRISM v1 is a research intelligence platform that:
- Scrapes ArXiv, GitHub, HuggingFace, Semantic Scholar, Crossref, PapersWithCode, RSS news/blogs
- Normalises raw items into a SQLite database via SQLAlchemy
- Runs 5 heuristic scoring engines (Signal, Trust, Debate, Gap, Cross-Domain) combined by FusionEngine
- Uses a sparse token-based LocalVectorMemory (NOT real semantic embeddings)
- Has a SOUL profile YAML for scheduling agent heartbeats (APScheduler)
- Dispatches alerts to Discord webhook or mock channel
- Has `openclaw_service.py` — a standalone FastAPI microservice that calls Groq LLM to refine heuristic scores
- Serves a React/Vite/Tailwind dashboard (port 5173)

### What is MISSING / Weak
| Gap | Impact |
|-----|--------|
| No LLM calls in main pipeline engines — all scoring is pure heuristics | Low intelligence quality |
| Vector memory uses sparse token matching, not real embeddings | Weak semantic search |
| No graph database (Neo4j) — entity links stored flat in SQLite | No relationship traversal |
| OpenClaw social integrations are all mocked | No real signal from Discord/Telegram/Reddit |
| No user persona / preference model | No personalisation |
| No RL-based recommendation engine | No proactive suggestions |
| No LangGraph agent — heartbeat loop is simple APScheduler, not agentic | No multi-step reasoning |
| ChromaDB not integrated | Missing hybrid RAG |

---

## 2. Team Roles & Responsibilities

| Member | Role | Owns |
|--------|------|------|
| Member A | Backend Lead | LLM Engine Integration, Groq calls in all 5 engines, LangGraph agent, FastAPI new routes |
| Member B | Data & Memory Lead | ChromaDB integration, hybrid RAG, Neo4j graph, sentence-transformers embeddings |
| Member C | OpenClaw & Social Lead | Real OpenClaw social connectors (Discord, Telegram, Reddit), RL persona model, frontend OpenClaw tab |

---

## 3. Phase 1 — LLM-Enhanced Engines via Groq (Member A)

### 3.1 What to change
Wire `llm_client.py`'s `enhance_verdict()` into ALL five engines. Currently only the client exists but is not called by most engines.

**Files to modify:**
- `backend/app/engines/signal_engine.py`
- `backend/app/engines/trust_engine.py`
- `backend/app/engines/debate_engine.py`
- `backend/app/engines/gap_engine.py`
- `backend/app/engines/cross_domain_engine.py`

### 3.2 Pseudocode — LLM Enhancement Pattern
```python
# In each engine's .score() method, after computing heuristic score:
from app.engines.llm_client import enhance_verdict

enhanced_verdict, enhanced_evidence = enhance_verdict(
    engine_name="TrustEngine",
    heuristic_verdict=verdict,
    heuristic_score=score,
    item_title=item.title,
    item_abstract=item.abstract or "",
    evidence_points=evidence,
    extra_context=f"source={item.source}, authors={item.authors[:3]}"
)
return EngineResult(score=score, verdict=enhanced_verdict, evidence=enhanced_evidence, details=...)
```

### 3.3 Enable in .env
```
ENABLE_LLM=true
LLM_API_KEY=gsk_your_groq_key_here
LLM_MODEL=llama-3.3-70b-versatile
```

### 3.4 New Route: `/api/openclaw/analyze`
Connect main pipeline to `openclaw_service.py` via HTTP call after FusionEngine scores each item. If openclaw service is unreachable, fall back to heuristic score (already implemented in `openclaw_service.py`).

```python
# backend/app/services/openclaw_client.py  (NEW FILE)
import httpx
OPENCLAW_URL = os.getenv("OPENCLAW_URL", "http://localhost:9000")

def refine_with_openclaw(title, abstract, scores) -> dict | None:
    try:
        resp = httpx.post(f"{OPENCLAW_URL}/analyze", json={...}, timeout=10)
        return resp.json()
    except Exception:
        return None  # fallback to heuristic
```

---

## 4. Phase 2 — LangGraph Agentic Research Loop (Member A)

Replace the simple APScheduler heartbeat with a proper LangGraph StateGraph agent.

### 4.1 Architecture
```
State: { query, ingested_items, engine_results, memory_hits, decisions, iteration }

Nodes:
  ingest_node       → runs IngestionPipeline
  analyze_node      → runs FusionEngine + OpenClaw refinement
  memory_node       → queries ChromaDB for related past items
  reason_node       → Groq LLM decides: escalate / store / ignore
  dispatch_node     → sends to real channels
  reflect_node      → updates user persona model
```

### 4.2 New File: `backend/app/agent/langgraph_agent.py`
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class PRISMState(TypedDict):
    query: str
    ingested: list
    analyses: list
    memory_hits: list
    decisions: list
    persona: dict

def build_prism_graph():
    g = StateGraph(PRISMState)
    g.add_node("ingest", ingest_node)
    g.add_node("analyze", analyze_node)
    g.add_node("memory_lookup", memory_node)
    g.add_node("reason", reason_node)   # LLM decides routing
    g.add_node("dispatch", dispatch_node)
    g.add_node("reflect", reflect_node) # update persona
    
    g.set_entry_point("ingest")
    g.add_edge("ingest", "analyze")
    g.add_edge("analyze", "memory_lookup")
    g.add_edge("memory_lookup", "reason")
    g.add_conditional_edges("reason", route_decision, {
        "dispatch": "dispatch",
        "reflect": "reflect",
    })
    g.add_edge("dispatch", "reflect")
    g.add_edge("reflect", END)
    return g.compile()
```

### 4.3 Fallback
If LangGraph agent fails or `ENABLE_SCHEDULER=false`, fall back to existing `heartbeat.py` (keep it intact).

---

## 5. Phase 3 — ChromaDB + Hybrid RAG Memory (Member B)

### 5.1 Replace LocalVectorMemory
Create `backend/app/memory/chroma_store.py` using `sentence-transformers` for real embeddings.

```python
# backend/app/memory/chroma_store.py  (NEW FILE)
import chromadb
from sentence_transformers import SentenceTransformer

MODEL = SentenceTransformer("all-MiniLM-L6-v2")  # lightweight, fast

class ChromaVectorMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection("prism_research")

    def index_items(self, items: list) -> int:
        docs, ids, metas, embeds = [], [], [], []
        for item in items:
            text = f"{item.title}\n{item.abstract}\n{item.topic}"
            embedding = MODEL.encode(text).tolist()
            docs.append(text)
            ids.append(item.id)
            metas.append({"source": item.source, "url": item.url, "topic": item.topic})
            embeds.append(embedding)
        self.collection.upsert(documents=docs, ids=ids, metadatas=metas, embeddings=embeds)
        return len(docs)

    def search(self, query: str, limit: int = 10) -> list:
        q_embed = MODEL.encode(query).tolist()
        results = self.collection.query(query_embeddings=[q_embed], n_results=limit)
        return results  # hybrid: also run BM25 sparse search, merge results
```

### 5.2 Hybrid RAG Pipeline
```
User Query
  ├── Dense retrieval  → ChromaDB semantic search (sentence-transformers)
  ├── Sparse retrieval → existing LocalVectorMemory BM25-style token search
  └── Merge + Rerank   → Groq LLM re-ranks top 20 combined results → returns top 5
```

### 5.3 .env additions
```
CHROMA_PERSIST_PATH=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## 6. Phase 4 — Neo4j Knowledge Graph (Member B)

### 6.1 Purpose
Replace SQLite EntityLink table with a real graph DB. Enables queries like:
- "Find all papers citing the same technique as X"
- "Which authors cluster around topic Y?"
- "What is the shortest path from paper A to paper B?"

### 6.2 New File: `backend/app/memory/neo4j_store.py`
```python
from neo4j import GraphDatabase

class Neo4jStore:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def upsert_item(self, item):
        with self.driver.session() as s:
            s.run("""
                MERGE (p:Paper {id: $id})
                SET p.title=$title, p.source=$source, p.topic=$topic, p.url=$url
            """, **item.__dict__)

    def upsert_link(self, source_id, target_id, relation, confidence):
        with self.driver.session() as s:
            s.run("""
                MATCH (a:Paper {id:$src}), (b:Paper {id:$tgt})
                MERGE (a)-[r:RELATES {type:$rel}]->(b)
                SET r.confidence=$conf
            """, src=source_id, tgt=target_id, rel=relation, conf=confidence)

    def find_related(self, item_id, depth=2):
        with self.driver.session() as s:
            result = s.run("""
                MATCH (p:Paper {id:$id})-[*1..$depth]-(related)
                RETURN related LIMIT 20
            """, id=item_id, depth=depth)
            return [r["related"] for r in result]
```

### 6.3 .env additions
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
ENABLE_NEO4J=false  # false = fall back to SQLite EntityLink
```

---

## 7. Phase 5 — OpenClaw Social Integrations (Member C)

### 7.1 Credential Onboarding API
New endpoint: `POST /api/openclaw/credentials`

```python
class OpenClawCredentials(BaseModel):
    discord_bot_token: str | None = None
    discord_webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_username: str | None = None
    reddit_password: str | None = None
```

Credentials are stored encrypted (Fernet) in `backend/creds.enc`, never in plain .env.

### 7.2 Real Channel Adapters

**New files:**
- `backend/app/agent/adapters/discord_adapter.py`
- `backend/app/agent/adapters/telegram_adapter.py`
- `backend/app/agent/adapters/reddit_adapter.py`

```python
# discord_adapter.py
import discord
from discord.ext import commands

class DiscordAdapter:
    """Listens to DMs/channels, extracts research queries, dispatches papers."""
    
    async def on_message(self, message):
        if message.content.startswith("!research"):
            query = message.content[9:].strip()
            results = await run_prism_query(query)
            await message.reply(format_results(results))
    
    async def send_alert(self, channel_id, item):
        channel = self.bot.get_channel(channel_id)
        embed = discord.Embed(title=item["title"], url=item["url"])
        embed.add_field(name="PRISM Score", value=f"{item['prism_score']:.2f}")
        await channel.send(embed=embed)
```

```python
# telegram_adapter.py
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler

class TelegramAdapter:
    async def handle_message(self, update: Update, context):
        text = update.message.text
        if "/research" in text:
            query = text.replace("/research", "").strip()
            results = await run_prism_query(query)
            await update.message.reply_text(format_results(results))
```

```python
# reddit_adapter.py  — monitors subreddits, extracts signals
import praw

class RedditAdapter:
    def __init__(self, creds):
        self.reddit = praw.Reddit(
            client_id=creds.reddit_client_id,
            client_secret=creds.reddit_client_secret,
            username=creds.reddit_username,
            password=creds.reddit_password,
            user_agent="PRISM/2.0"
        )
    
    def monitor_subreddits(self, subs=["MachineLearning","LocalLLaMA","artificial"]):
        for post in self.reddit.subreddit("+".join(subs)).stream.submissions():
            yield {
                "title": post.title,
                "url": post.url,
                "score": post.score,
                "source": "reddit"
            }
```

### 7.3 SOUL Profile Updates
```yaml
# soul_profile.yaml — new fields
social_sources:
  discord:
    enabled: true
    listen_channels: ["1234567890"]   # channel IDs
    command_prefix: "!research"
  telegram:
    enabled: true
    chat_ids: ["-1001234567890"]
  reddit:
    enabled: true
    subreddits: ["MachineLearning", "LocalLLaMA"]
    min_score: 50

openclaw:
  credentials_file: backend/creds.enc
  fallback_to_langgraph: true   # if OpenClaw fails, use LangGraph agent
```

---

## 8. Phase 6 — User Persona & RL Recommendation Engine (Member C)

### 8.1 User Persona Model
Track per-user interactions to build a preference profile.

```python
# backend/app/persona/persona_model.py  (NEW FILE)
class UserPersona(BaseModel):
    user_id: str
    liked_topics: dict[str, float]       # topic -> weight
    liked_sources: dict[str, float]      # source -> weight
    min_trust_threshold: float = 0.4
    favourite_paper_ids: list[str] = []
    interaction_history: list[dict] = [] # {item_id, action, timestamp}
    domain_weights: dict[str, float] = {}
    last_updated: datetime

class PersonaEngine:
    def update(self, persona: UserPersona, item_id: str, action: str):
        # action: "liked", "starred", "dismissed", "shared"
        weight = {"liked":+0.3, "starred":+0.5, "dismissed":-0.2, "shared":+0.4}
        item = get_item(item_id)
        persona.liked_topics[item.topic] = persona.liked_topics.get(item.topic, 0.5)
        persona.liked_topics[item.topic] += weight.get(action, 0)
        persona.liked_topics[item.topic] = max(0.0, min(1.0, persona.liked_topics[item.topic]))

    def personalise_score(self, persona: UserPersona, item, base_prism_score: float) -> float:
        topic_boost = persona.liked_topics.get(item.topic, 0.5) * 0.2
        source_boost = persona.liked_sources.get(item.source, 0.5) * 0.1
        return min(1.0, base_prism_score + topic_boost + source_boost)
```

### 8.2 RL-based Proactive Suggestion Engine
Use a lightweight contextual bandit model (no heavy RL framework needed).

```python
# backend/app/persona/rl_recommender.py  (NEW FILE)
import numpy as np

class ContextualBanditRecommender:
    """
    Multi-armed bandit per topic domain.
    Arms = research topics. Reward = user engagement (like/star/share).
    Algorithm: Upper Confidence Bound (UCB1)
    """
    def __init__(self, topics: list[str]):
        self.topics = topics
        self.counts = {t: 0 for t in topics}     # times recommended
        self.rewards = {t: 0.0 for t in topics}  # cumulative reward

    def select_topic(self) -> str:
        total = sum(self.counts.values()) + 1
        ucb_scores = {
            t: (self.rewards[t] / max(self.counts[t], 1))
               + np.sqrt(2 * np.log(total) / max(self.counts[t], 1))
            for t in self.topics
        }
        return max(ucb_scores, key=ucb_scores.get)

    def update(self, topic: str, reward: float):
        self.counts[topic] += 1
        self.rewards[topic] += reward

    def proactive_suggestions(self, persona: UserPersona, all_items: list) -> list:
        best_topic = self.select_topic()
        return [i for i in all_items if i.topic == best_topic][:5]
```

### 8.3 New API Routes
```
POST /api/persona/feedback          # record like/star/dismiss
GET  /api/persona/{user_id}         # get persona profile
GET  /api/persona/{user_id}/suggest # RL-powered proactive suggestions
POST /api/persona/{user_id}/reset   # reset preferences
```

### 8.4 Paper Rating System
```python
class PaperRating(BaseModel):
    item_id: str
    user_id: str
    rating: int       # 1-5 stars
    tags: list[str]   # e.g. ["must-read", "reproduced", "applied"]
    notes: str = ""
    is_favourite: bool = False
```

New routes:
```
POST /api/items/{id}/rate
GET  /api/items/{id}/ratings
GET  /api/persona/{user_id}/favourites
```

---

## 9. Phase 7 — LangGraph Fallback Agent (Member A/B)

This agent activates when OpenClaw social connectors fail or are disabled.

### 9.1 Architecture
```
PRISMFallbackAgent (LangGraph):
  ├── query_understanding_node  → LLM parses intent from user message
  ├── memory_retrieval_node     → ChromaDB + Neo4j search
  ├── web_ingest_node           → runs IngestionPipeline for query
  ├── synthesis_node            → LLM summarises findings
  ├── persona_update_node       → updates user model
  └── response_format_node      → formats for target channel (Discord/Telegram/API)
```

### 9.2 Trigger Conditions
```python
# In channel_dispatcher.py
def dispatch(self, decision, profile):
    if not self._openclaw_available():
        logger.warning("OpenClaw unavailable, routing to LangGraph fallback agent")
        return self._dispatch_langgraph(decision, profile)
    return self._dispatch_openclaw(decision, profile)
```

---

## 10. Frontend Additions (Member C)

### 10.1 New Views to Add
| View | Description |
|------|-------------|
| `VIII. OpenClaw` | Credential setup form + connection status for Discord/Telegram/Reddit |
| `IX. Persona` | User taste profile visualisation, favourite papers, domain radar |
| `X. Suggest` | RL-powered proactive suggestions feed |

### 10.2 OpenClaw Credentials UI
- Simple form to enter tokens (masked input)
- Test connection button per platform
- Live status indicators (green/red dot)
- Shows last message received from each platform

### 10.3 Persona Dashboard
- Radar chart of domain weights
- Starred/favourite papers list
- Engagement history timeline
- "Reset my preferences" button

---

## 11. New File Structure

```
backend/app/
  agent/
    langgraph_agent.py        NEW — LangGraph StateGraph agent
    adapters/
      discord_adapter.py      NEW — real Discord bot/webhook
      telegram_adapter.py     NEW — real Telegram bot
      reddit_adapter.py       NEW — PRAW Reddit monitor
  memory/
    chroma_store.py           NEW — ChromaDB semantic memory
    neo4j_store.py            NEW — Neo4j knowledge graph
  persona/
    persona_model.py          NEW — user preference tracking
    rl_recommender.py         NEW — contextual bandit recommender
  services/
    openclaw_client.py        NEW — HTTP client for openclaw_service
    persona_service.py        NEW — CRUD for personas + ratings
  api/
    routes_persona.py         NEW — /api/persona/* endpoints
    routes_openclaw.py        NEW — /api/openclaw/* endpoints

frontend/src/
  components/
    OpenClawPanel.tsx          NEW
    PersonaDashboard.tsx       NEW
    SuggestionFeed.tsx         NEW
    PaperRatingWidget.tsx      NEW
```

---

## 12. New Dependencies

```
# Add to backend/requirements.txt
langchain>=0.2
langchain-groq>=0.1
langgraph>=0.1
chromadb>=0.5
sentence-transformers>=3.0
neo4j>=5.0
praw>=7.7         # Reddit API
python-telegram-bot>=21.0
discord.py>=2.3
cryptography>=42  # Fernet for credential encryption
torch>=2.6        # GPU-accelerated embeddings
```

---

## 13. Environment Variables Summary

```bash
# Existing
ENABLE_LLM=true
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile
ENABLE_SCHEDULER=true

# Phase 3 — ChromaDB
CHROMA_PERSIST_PATH=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Phase 4 — Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_pass
ENABLE_NEO4J=false

# Phase 5 — Social
DISCORD_BOT_TOKEN=
DISCORD_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=

# Phase 6 — Persona
ENABLE_PERSONA=true
PERSONA_DB_PATH=./persona.db

# OpenClaw Microservice
OPENCLAW_URL=http://localhost:9000
ENABLE_OPENCLAW=true
OPENCLAW_FALLBACK=langgraph
```

---

## 14. Implementation Sequence

```
Week 1:
  [A] Wire LLM calls into all 5 engines (ENABLE_LLM guard)
  [A] Create openclaw_client.py HTTP bridge
  [B] Integrate ChromaDB + sentence-transformers (replace LocalVectorMemory)
  [C] Build credential onboarding API + encryption

Week 2:
  [A] Build LangGraph PRISMAgent (ingest→analyze→reason→dispatch)
  [B] Neo4j integration (optional, ENABLE_NEO4J flag)
  [C] Discord + Telegram bot adapters with !research command

Week 3:
  [C] Reddit monitor adapter
  [C] PersonaEngine + PaperRating routes
  [C] RL ContextualBanditRecommender
  [A] LangGraph fallback agent wiring in ChannelDispatcher

Week 4:
  [A+B+C] Frontend: OpenClaw panel, Persona dashboard, Suggestions feed
  [A+B+C] Integration testing, fix regressions
  [A] Push final build, tag v2.0
```

---

## 15. Unique / Novel Ideas

1. **Cross-platform Research Persona** — your Discord DM history, Reddit upvotes, and Telegram forwards are unified into a single research taste profile that gets smarter every week.

2. **Bandit-powered topic discovery** — UCB1 bandit proactively suggests topics you haven't explored but statistically should love, breaking filter bubbles.

3. **Paper Debate Arena** — two papers on the same topic get a Groq-powered structured debate: pros, cons, reproducibility gaps — displayed as a head-to-head scorecard in the frontend.

4. **Signal Graph Walk** — Neo4j enables "6 degrees of separation" between papers: given a paper you starred, find the chain of citations/techniques leading to 5 other papers you'd never have found.

5. **Community Radar** — aggregate all users' persona models (anonymised) to surface emerging trends before they hit mainstream — a crowd-sourced early warning system.

6. **Discord Research Bot Commands**
   - `!research <query>` → runs PRISM pipeline, returns top 3 papers
   - `!star <url>` → adds paper to your PRISM favourites
   - `!suggest` → RL model picks your next recommended topic
   - `!debate <paper_a> vs <paper_b>` → Groq debate engine

7. **Multimodal RAG** — ingest paper PDFs (via arxiv PDF URLs), chunk + embed with sentence-transformers, store in ChromaDB. Users can ask "find papers that use diagrams of attention maps" and get image-caption-aware results.

---

*End of PRISM v2 Implementation Plan*
