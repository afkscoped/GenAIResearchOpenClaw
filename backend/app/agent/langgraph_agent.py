from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any, Literal, TypedDict

from sqlalchemy.orm import Session

from app.api.query_filters import apply_item_search_filter
from app.db.models import AgentRunRecord, EntityLink, FusionReportRecord, ResearchItem
from app.engines.llm_client import ask_llm_with_provider
from app.ingest.pipeline import IngestionPipeline
from app.memory.chroma_store import ChromaVectorMemory
from app.memory.neo4j_store import Neo4jStore
from app.memory.vector_store import LocalVectorMemory
from app.schemas.agent import AgentRunResponse
from app.services.engine_runner import run_and_persist_engines
from app.services.persona_service import get_or_create_persona, suggestions


Intent = Literal["discover", "compare", "benchmark", "summarize", "recommend"]


class PRISMState(TypedDict, total=False):
    run_id: str
    query: str
    user_id: str
    mode: str
    intent: Intent
    plan: dict[str, Any]
    ingestion_result: dict[str, Any]
    memory_hits: list[dict[str, Any]]
    graph_context: list[dict[str, Any]]
    engine_reports: list[dict[str, Any]]
    ranked_recommendations: list[dict[str, Any]]
    persona_snapshot: dict[str, Any]
    final_answer: str
    llm_provider: str
    errors: list[str]
    timings: dict[str, float]
    chroma_available: bool
    neo4j_available: bool
    created_at: str


class PRISMLangGraphAgent:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def run(
        self,
        db: Session,
        query: str,
        user_id: str = "default",
        mode: str = "auto",
        limit_per_source: int = 5,
        include_demo: bool = True,
    ) -> AgentRunResponse:
        state: PRISMState = {
            "run_id": uuid.uuid4().hex,
            "query": query.strip(),
            "user_id": user_id or "default",
            "mode": mode,
            "plan": {
                "limit_per_source": limit_per_source,
                "include_demo": include_demo,
            },
            "errors": [],
            "timings": {},
            "llm_provider": "heuristic",
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self.graph.invoke({"db": db, **state})
        return self._response_from_state(result)

    def _build_graph(self) -> Any:
        from langgraph.graph import END, StateGraph

        graph = StateGraph(dict)
        graph.add_node("classify_intent", self._timed("classify_intent", self.classify_intent))
        graph.add_node("plan_research", self._timed("plan_research", self.plan_research))
        graph.add_node("ingest_sources", self._timed("ingest_sources", self.ingest_sources))
        graph.add_node("retrieve_memory", self._timed("retrieve_memory", self.retrieve_memory))
        graph.add_node("expand_graph", self._timed("expand_graph", self.expand_graph))
        graph.add_node("run_engines", self._timed("run_engines", self.run_engines))
        graph.add_node("rank_and_personalize", self._timed("rank_and_personalize", self.rank_and_personalize))
        graph.add_node("synthesize", self._timed("synthesize", self.synthesize))
        graph.add_node("persist_agent_run", self._timed("persist_agent_run", self.persist_agent_run))

        graph.set_entry_point("classify_intent")
        graph.add_edge("classify_intent", "plan_research")
        graph.add_conditional_edges(
            "plan_research",
            self._ingestion_route,
            {
                "ingest": "ingest_sources",
                "skip": "retrieve_memory",
            },
        )
        graph.add_edge("ingest_sources", "retrieve_memory")
        graph.add_edge("retrieve_memory", "expand_graph")
        graph.add_edge("expand_graph", "run_engines")
        graph.add_edge("run_engines", "rank_and_personalize")
        graph.add_edge("rank_and_personalize", "synthesize")
        graph.add_edge("synthesize", "persist_agent_run")
        graph.add_edge("persist_agent_run", END)
        return graph.compile()

    def _timed(self, name: str, fn: Any) -> Any:
        def wrapper(state: dict[str, Any]) -> dict[str, Any]:
            started = time.perf_counter()
            try:
                return fn(state)
            except Exception as exc:
                errors = list(state.get("errors", []))
                errors.append(f"{name}: {exc}")
                state["errors"] = errors
                return state
            finally:
                timings = dict(state.get("timings", {}))
                timings[name] = round(time.perf_counter() - started, 4)
                state["timings"] = timings

        return wrapper

    def classify_intent(self, state: dict[str, Any]) -> dict[str, Any]:
        mode = state.get("mode", "auto")
        query = str(state.get("query", "")).lower()
        if mode != "auto":
            state["intent"] = "summarize" if mode == "summarize" else mode
            return state
        if any(term in query for term in ["compare", "versus", " vs ", "tradeoff"]):
            intent: Intent = "compare"
        elif any(term in query for term in ["benchmark", "metric", "score", "evaluate"]):
            intent = "benchmark"
        elif any(term in query for term in ["recommend", "suggest", "next reads", "personal"]):
            intent = "recommend"
        elif any(term in query for term in ["summarize", "summary", "brief"]):
            intent = "summarize"
        else:
            intent = "discover"
        state["intent"] = intent
        return state

    def plan_research(self, state: dict[str, Any]) -> dict[str, Any]:
        db: Session = state["db"]
        query = state["query"]
        plan = dict(state.get("plan", {}))
        existing_count = apply_item_search_filter(db.query(ResearchItem), query).limit(6).count()
        plan.update(
            {
                "existing_results": existing_count,
                "should_ingest": existing_count == 0,
                "use_chroma": True,
                "use_graph": state.get("intent") in {"discover", "compare", "recommend", "benchmark"},
                "ranking": "persona_weighted" if state.get("intent") == "recommend" else "prism_weighted",
            }
        )
        state["plan"] = plan
        return state

    def ingest_sources(self, state: dict[str, Any]) -> dict[str, Any]:
        db: Session = state["db"]
        plan = state["plan"]
        result = IngestionPipeline().run(
            db=db,
            query=state["query"],
            limit_per_source=int(plan.get("limit_per_source", 5)),
            include_demo=bool(plan.get("include_demo", True)),
        )
        state["ingestion_result"] = result.model_dump()
        self._mirror_to_neo4j(db, result.item_ids)
        return state

    def retrieve_memory(self, state: dict[str, Any]) -> dict[str, Any]:
        db: Session = state["db"]
        chroma = ChromaVectorMemory()
        state["chroma_available"] = chroma.available
        memory = chroma if chroma.available else LocalVectorMemory()
        hits = memory.search(db=db, query=state["query"], limit=10)
        state["memory_hits"] = [hit.model_dump() for hit in hits]
        return state

    def expand_graph(self, state: dict[str, Any]) -> dict[str, Any]:
        db: Session = state["db"]
        neo4j = Neo4jStore()
        state["neo4j_available"] = neo4j.available
        item_ids = [hit["item_id"] for hit in state.get("memory_hits", [])[:5]]
        context: list[dict[str, Any]] = []
        if neo4j.available:
            for item_id in item_ids:
                for related in neo4j.find_related(item_id, depth=2, limit=10):
                    context.append({"source": "neo4j", "seed_item_id": item_id, "related": related})
        if not context:
            context = self._sqlite_graph_context(db, item_ids)
        state["graph_context"] = context[:40]
        return state

    def run_engines(self, state: dict[str, Any]) -> dict[str, Any]:
        db: Session = state["db"]
        item_query = apply_item_search_filter(
            db.query(ResearchItem).order_by(ResearchItem.timestamp.desc()),
            state["query"],
        )
        items = item_query.limit(25).all()
        if not items:
            items = db.query(ResearchItem).order_by(ResearchItem.timestamp.desc()).limit(25).all()

        reports: list[dict[str, Any]] = []
        for item in items:
            cached = (
                db.query(FusionReportRecord)
                .filter(FusionReportRecord.item_id == item.id)
                .order_by(FusionReportRecord.created_at.desc())
                .first()
            )
            if cached is None:
                _engine_run, cached = run_and_persist_engines(db, item)
                db.commit()
                db.refresh(cached)
            reports.append(self._report_dict(item, cached))
        state["engine_reports"] = reports
        return state

    def rank_and_personalize(self, state: dict[str, Any]) -> dict[str, Any]:
        db: Session = state["db"]
        user_id = state.get("user_id", "default")
        persona = get_or_create_persona(db, user_id)
        db.commit()
        state["persona_snapshot"] = {
            "user_id": persona.user_id,
            "liked_topics": persona.liked_topics or {},
            "liked_sources": persona.liked_sources or {},
            "favourite_paper_ids": persona.favourite_paper_ids or [],
            "interaction_history": persona.interaction_history or [],
        }

        memory_scores = {hit["item_id"]: float(hit.get("score", 0.0)) for hit in state.get("memory_hits", [])}
        graph_scores = self._graph_scores(state.get("graph_context", []))
        persona_suggestions = {entry.item_id: entry for entry in suggestions(db, user_id=user_id, limit=200)}
        ranked: list[dict[str, Any]] = []
        for report in state.get("engine_reports", []):
            base = float(report["prism_score"])
            memory_score = memory_scores.get(report["item_id"], 0.0)
            graph_score = graph_scores.get(report["item_id"], 0.0)
            persona_score = persona_suggestions.get(report["item_id"]).personalised_score if report["item_id"] in persona_suggestions else base
            if state.get("intent") == "recommend":
                final_score = self._weighted_score(base, persona_score, memory_score, graph_score, weights=(0.55, 0.25, 0.12, 0.08))
            else:
                final_score = self._weighted_score(base, persona_score, memory_score, graph_score, weights=(0.72, 0.10, 0.10, 0.08))
            ranked.append(
                {
                    **report,
                    "personalised_score": round(float(persona_score), 4),
                    "memory_score": round(memory_score, 4),
                    "graph_score": round(graph_score, 4),
                    "final_score": round(final_score, 4),
                    "reason": self._ranking_reason(base, persona_score, memory_score, graph_score),
                }
            )
        state["ranked_recommendations"] = sorted(ranked, key=lambda entry: entry["final_score"], reverse=True)[:10]
        return state

    def synthesize(self, state: dict[str, Any]) -> dict[str, Any]:
        ranked = state.get("ranked_recommendations", [])
        if not ranked:
            state["final_answer"] = "No matching research items were found yet. Run ingestion with demo data enabled or broaden the query."
            state["llm_provider"] = "heuristic"
            return state

        compact = "\n".join(
            f"{index + 1}. {item['title']} | score={item['final_score']:.2f} | trust={item['trust_score']:.2f} | {item['verdict']}"
            for index, item in enumerate(ranked[:6])
        )
        system = (
            "You are PRISM's core research agent. Produce a concise, actionable research brief. "
            "Do not mention Discord, Telegram, Reddit, or webhooks."
        )
        prompt = (
            f"Intent: {state.get('intent')}\n"
            f"Query: {state.get('query')}\n"
            f"Top ranked items:\n{compact}\n\n"
            "Return 2 short paragraphs plus 3 bullet recommendations."
        )
        text, provider = ask_llm_with_provider(system, prompt, max_tokens=420, temperature=0.25)
        state["llm_provider"] = provider
        state["final_answer"] = text or self._heuristic_answer(state)
        return state

    def persist_agent_run(self, state: dict[str, Any]) -> dict[str, Any]:
        db: Session = state["db"]
        record = AgentRunRecord(
            id=state["run_id"],
            query=state["query"],
            user_id=state.get("user_id", "default"),
            mode=state.get("mode", "auto"),
            intent=state.get("intent", "discover"),
            llm_provider=state.get("llm_provider", "heuristic"),
            status="error" if state.get("errors") else "ok",
            final_answer=state.get("final_answer", ""),
            payload=self._payload(state),
            errors=state.get("errors", []),
            timings=state.get("timings", {}),
        )
        db.add(record)
        db.commit()
        state["created_at"] = record.created_at.isoformat()
        return state

    def _ingestion_route(self, state: dict[str, Any]) -> str:
        return "ingest" if state.get("plan", {}).get("should_ingest") else "skip"

    def _sqlite_graph_context(self, db: Session, item_ids: list[str]) -> list[dict[str, Any]]:
        if not item_ids:
            return []
        links = (
            db.query(EntityLink)
            .filter((EntityLink.source_item_id.in_(item_ids)) | (EntityLink.target_item_id.in_(item_ids)))
            .order_by(EntityLink.confidence.desc())
            .limit(40)
            .all()
        )
        return [
            {
                "source": "sqlite",
                "source_item_id": link.source_item_id,
                "target_item_id": link.target_item_id,
                "relation_type": link.relation_type,
                "confidence": link.confidence,
                "evidence": link.evidence,
            }
            for link in links
        ]

    def _mirror_to_neo4j(self, db: Session, item_ids: list[str]) -> None:
        neo4j = Neo4jStore()
        if not neo4j.available or not item_ids:
            return
        items = db.query(ResearchItem).filter(ResearchItem.id.in_(item_ids)).all()
        for item in items:
            neo4j.upsert_item(item)
        links = db.query(EntityLink).filter((EntityLink.source_item_id.in_(item_ids)) | (EntityLink.target_item_id.in_(item_ids))).all()
        for link in links:
            neo4j.upsert_link(link.source_item_id, link.target_item_id, link.relation_type, link.confidence)

    def _graph_scores(self, graph_context: list[dict[str, Any]]) -> dict[str, float]:
        scores: dict[str, float] = {}
        for entry in graph_context:
            for key in ["source_item_id", "target_item_id", "seed_item_id"]:
                item_id = entry.get(key)
                if item_id:
                    scores[item_id] = min(1.0, scores.get(item_id, 0.0) + float(entry.get("confidence", 0.25)))
        return scores

    def _report_dict(self, item: ResearchItem, record: FusionReportRecord) -> dict[str, Any]:
        return {
            "item_id": item.id,
            "title": item.title,
            "topic": item.topic,
            "source": item.source,
            "url": item.url,
            "prism_score": record.prism_score,
            "novelty_score": record.novelty_score,
            "trust_score": record.trust_score,
            "controversy_score": record.controversy_score,
            "adoption_gap_score": record.adoption_gap_score,
            "transferability_score": record.transferability_score,
            "verdict": record.verdict,
            "evidence": record.evidence,
        }

    def _ranking_reason(self, base: float, persona: float, memory: float, graph: float) -> str:
        return f"prism={base:.2f}, persona={persona:.2f}, memory={memory:.2f}, graph={graph:.2f}"

    def _weighted_score(
        self,
        prism_score: float,
        persona_score: float,
        memory_score: float,
        graph_score: float,
        *,
        weights: tuple[float, float, float, float],
    ) -> float:
        score = (
            weights[0] * prism_score
            + weights[1] * persona_score
            + weights[2] * memory_score
            + weights[3] * graph_score
        )
        return max(0.0, min(1.0, score))

    def _heuristic_answer(self, state: dict[str, Any]) -> str:
        top = state.get("ranked_recommendations", [])[:3]
        lines = [
            f"PRISM found {len(state.get('ranked_recommendations', []))} strong candidates for '{state.get('query')}'.",
            "The ranking combines fusion score, memory similarity, graph proximity, and persona fit.",
        ]
        for item in top:
            lines.append(f"- {item['title']} ({item['final_score']:.2f}): {item['verdict']}")
        return "\n".join(lines)

    def _payload(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "plan": state.get("plan", {}),
            "ingestion_result": state.get("ingestion_result", {}),
            "memory_hits": state.get("memory_hits", []),
            "graph_context": state.get("graph_context", []),
            "engine_summaries": state.get("engine_reports", []),
            "ranked_items": state.get("ranked_recommendations", []),
            "persona_snapshot": state.get("persona_snapshot", {}),
            "chroma_available": state.get("chroma_available", False),
            "neo4j_available": state.get("neo4j_available", False),
        }

    def _response_from_state(self, state: dict[str, Any]) -> AgentRunResponse:
        return AgentRunResponse(
            run_id=state["run_id"],
            query=state["query"],
            user_id=state.get("user_id", "default"),
            mode=state.get("mode", "auto"),
            intent=state.get("intent", "discover"),
            plan=state.get("plan", {}),
            final_answer=state.get("final_answer", ""),
            ranked_items=state.get("ranked_recommendations", []),
            memory_hits=state.get("memory_hits", []),
            graph_context=state.get("graph_context", []),
            engine_summaries=state.get("engine_reports", []),
            provider_used=state.get("llm_provider", "heuristic"),
            chroma_available=bool(state.get("chroma_available", False)),
            neo4j_available=bool(state.get("neo4j_available", False)),
            timings=state.get("timings", {}),
            errors=state.get("errors", []),
            created_at=datetime.fromisoformat(state["created_at"]) if state.get("created_at") else None,
        )


def build_prism_graph() -> PRISMLangGraphAgent:
    return PRISMLangGraphAgent()
