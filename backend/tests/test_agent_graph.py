from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agent.langgraph_agent import build_prism_graph
from app.db.models import EngineRun, FusionReportRecord, MemoryDocument, ResearchItem, UserPersonaRecord
from app.db.session import get_db
from app.db.session import Base
from app.main import app


def _session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _seed_item(db):
    item = ResearchItem(
        id="paper-1",
        title="Reliable Evaluation for Multimodal Agents",
        abstract="A benchmark suite for multimodal agents and research evaluation.",
        source="arxiv",
        url="https://example.com/paper-1",
        authors=["Ada"],
        organizations=["Demo Lab"],
        topic="multimodal agents",
        timestamp=datetime.utcnow(),
        extra_metadata={},
    )
    db.add(item)
    db.flush()
    db.add(MemoryDocument(item_id=item.id, text=f"{item.title}\n{item.abstract}", embedding=[1.0], token_signature=["multimodal", "agents", "benchmark"]))
    engine_run = EngineRun(item_id=item.id, signal_score=0.8, trust_score=0.7, debate_score=0.1, gap_score=0.6, cross_domain_score=0.5)
    db.add(engine_run)
    db.flush()
    db.add(
        FusionReportRecord(
            item_id=item.id,
            engine_run_id=engine_run.id,
            prism_score=0.76,
            novelty_score=0.8,
            trust_score=0.7,
            controversy_score=0.1,
            adoption_gap_score=0.6,
            transferability_score=0.5,
            verdict="High-priority research candidate.",
            evidence=["seeded evidence"],
        )
    )
    db.commit()
    return item


class _UnavailableChroma:
    available = False

    def search(self, *args, **kwargs):
        raise AssertionError("Local fallback should be used when Chroma is unavailable")


class _UnavailableNeo4j:
    available = False


def test_existing_results_skip_ingestion_and_return_agent_run():
    db = _session()
    _seed_item(db)

    with patch("app.agent.langgraph_agent.ChromaVectorMemory", return_value=_UnavailableChroma()), \
         patch("app.agent.langgraph_agent.Neo4jStore", return_value=_UnavailableNeo4j()), \
         patch("app.agent.langgraph_agent.ask_llm_with_provider", return_value=(None, "heuristic")), \
         patch("app.agent.langgraph_agent.IngestionPipeline.run") as run_pipeline:
        response = build_prism_graph().run(db, query="multimodal agents", mode="discover", include_demo=False)

    assert run_pipeline.call_count == 0
    assert response.intent == "discover"
    assert response.provider_used == "heuristic"
    assert response.ranked_items
    assert response.ranked_items[0].item_id == "paper-1"


def test_empty_database_triggers_ingestion_path():
    db = _session()
    fake_ingestion = SimpleNamespace(
        item_ids=[],
        model_dump=lambda: {
            "ingested_items": 0,
            "stored_items": 0,
            "stored_signals": 0,
            "entity_links": 0,
            "memory_documents": 0,
            "sources": [],
            "item_ids": [],
        },
    )

    with patch("app.agent.langgraph_agent.ChromaVectorMemory", return_value=_UnavailableChroma()), \
         patch("app.agent.langgraph_agent.Neo4jStore", return_value=_UnavailableNeo4j()), \
         patch("app.agent.langgraph_agent.ask_llm_with_provider", return_value=(None, "heuristic")), \
         patch("app.agent.langgraph_agent.IngestionPipeline.run", return_value=fake_ingestion) as run_pipeline:
        response = build_prism_graph().run(db, query="new agent topic", mode="auto", include_demo=False)

    assert run_pipeline.call_count == 1
    assert response.plan["should_ingest"] is True
    assert response.ranked_items == []
    assert "No matching research items" in response.final_answer


def test_recommend_mode_applies_persona_weighting():
    db = _session()
    item = _seed_item(db)
    db.add(
        UserPersonaRecord(
            user_id="default",
            liked_topics={item.topic: 1.0},
            liked_sources={item.source: 1.0},
            favourite_paper_ids=[],
            interaction_history=[],
            domain_weights={item.topic: 1.0},
            last_updated=datetime.utcnow(),
        )
    )
    db.commit()

    with patch("app.agent.langgraph_agent.ChromaVectorMemory", return_value=_UnavailableChroma()), \
         patch("app.agent.langgraph_agent.Neo4jStore", return_value=_UnavailableNeo4j()), \
         patch("app.agent.langgraph_agent.ask_llm_with_provider", return_value=("brief", "ollama")):
        response = build_prism_graph().run(db, query="multimodal agents", mode="recommend", include_demo=False)

    assert response.intent == "recommend"
    assert response.provider_used == "ollama"
    assert response.ranked_items[0].personalised_score >= response.ranked_items[0].prism_score


def test_agent_research_api_and_run_replay():
    db = _session()
    _seed_item(db)

    def override_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_db
    try:
        with patch("app.agent.langgraph_agent.ChromaVectorMemory", return_value=_UnavailableChroma()), \
             patch("app.agent.langgraph_agent.Neo4jStore", return_value=_UnavailableNeo4j()), \
             patch("app.agent.langgraph_agent.ask_llm_with_provider", return_value=(None, "heuristic")):
            client = TestClient(app)
            response = client.post(
                "/api/agent/research",
                json={"query": "multimodal agents", "mode": "benchmark", "include_demo": False},
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["intent"] == "benchmark"
            assert payload["ranked_items"]

            replay = client.get(f"/api/agent/runs/{payload['run_id']}")
            assert replay.status_code == 200
            assert replay.json()["id"] == payload["run_id"]
    finally:
        app.dependency_overrides.clear()
