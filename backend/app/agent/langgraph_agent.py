from __future__ import annotations

from typing import Any, TypedDict

from sqlalchemy.orm import Session

from app.agent.tools import run_prism_engine_analysis, run_prism_ingestion, search_prism_memory


class PRISMState(TypedDict, total=False):
    query: str
    ingested: dict[str, Any]
    analyses: list[dict[str, Any]]
    memory_hits: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    iteration: int


class PRISMFallbackAgent:
    def run(self, db: Session, query: str, limit_per_source: int = 5, include_demo: bool = True) -> PRISMState:
        state: PRISMState = {"query": query, "iteration": 1}
        ingestion = run_prism_ingestion(db, query=query, limit_per_source=limit_per_source, include_demo=include_demo)
        state["ingested"] = ingestion.model_dump()
        state["analyses"] = run_prism_engine_analysis(db, limit=limit_per_source)
        state["memory_hits"] = [hit.model_dump() for hit in search_prism_memory(db, query=query, limit=10)]
        state["decisions"] = [self._decision(analysis) for analysis in state["analyses"]]
        return state

    def _decision(self, analysis: dict[str, Any]) -> dict[str, Any]:
        score = float(analysis.get("prism_score", 0.0))
        trust = float(analysis.get("trust_score", 0.0))
        if score >= 0.82 and trust >= 0.35:
            route = "alert"
        elif score >= 0.65:
            route = "daily_digest"
        elif score >= 0.45:
            route = "weekly_brief"
        else:
            route = "ignored_memory_update"
        return {"route": route, "item_id": analysis.get("item_id"), "reason": f"score={score:.2f}, trust={trust:.2f}"}


def build_prism_graph() -> PRISMFallbackAgent:
    try:
        import langgraph  # noqa: F401
    except Exception:
        return PRISMFallbackAgent()
    return PRISMFallbackAgent()
