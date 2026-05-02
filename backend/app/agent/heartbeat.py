"""
OpenClaw-style PRISM heartbeat orchestration.

This module treats PRISM's existing ingestion, memory, and engine services as
tools. The SOUL profile controls monitored topics, thresholds, channels, and
report cadence metadata.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any

from app.agent.channel_dispatcher import ChannelDispatcher
from app.agent.router import decide_signal_route
from app.agent.soul_profile import get_soul_profile
from app.agent.state import AgentState
from app.agent.tools import run_prism_engine_analysis, run_prism_ingestion
from app.db.session import SessionLocal

logger = logging.getLogger("prism.agent.heartbeat")


def heartbeat_job(
    query: str = "multimodal agents",
    limit_per_source: int = 5,
    include_demo: bool = True,
) -> dict[str, Any]:
    """Run one agent cycle."""

    if not AgentState.begin_run():
        logger.info("PRISM heartbeat skipped because another run is active.")
        return {"skipped": True, "reason": "already_running"}

    logger.info("PRISM OpenClaw-style heartbeat starting.")
    db = SessionLocal()

    try:
        profile = get_soul_profile()
        dispatcher = ChannelDispatcher()
        topics = _monitor_topics(profile.monitor_topics, query)

        ingestion_results = []
        for index, topic in enumerate(topics):
            result = run_prism_ingestion(
                db=db,
                query=topic,
                limit_per_source=limit_per_source,
                include_demo=include_demo and index == 0,
            )
            ingestion_results.append(
                {
                    "query": topic,
                    "ingested_items": result.ingested_items,
                    "stored_items": result.stored_items,
                    "stored_signals": result.stored_signals,
                    "entity_links": result.entity_links,
                    "memory_documents": result.memory_documents,
                    "sources": result.sources,
                }
            )

        candidates = run_prism_engine_analysis(db)
        decisions = []
        deliveries = []

        for candidate in candidates:
            decision = decide_signal_route(candidate, profile)
            AgentState.record_decision(decision)
            decisions.append(decision)

            if decision["route"] != "ignored_memory_update":
                decision_deliveries = dispatcher.dispatch(decision, profile)
                AgentState.record_deliveries(decision_deliveries)
                deliveries.extend(decision_deliveries)

        details: dict[str, Any] = {
            "profile": profile.name,
            "monitor_topics": topics,
            "ingestion_runs": ingestion_results,
            "engine_runs": len(candidates),
            "decisions": _route_counts(decisions),
            "deliveries": deliveries,
            "report_frequency": profile.report_frequency.model_dump(),
        }
        AgentState.mark_success(details=details)
        return details

    except Exception:
        tb = traceback.format_exc()
        logger.error("Heartbeat failed:\n%s", tb)
        db.rollback()
        AgentState.mark_error(tb)
        return {"error": tb}
    finally:
        db.close()


def _monitor_topics(profile_topics: list[str], query: str) -> list[str]:
    topics = [topic for topic in profile_topics if topic.strip()]
    if query and query not in topics:
        topics.insert(0, query)
    return topics or ["multimodal agents"]


def _route_counts(decisions: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "alert": 0,
        "daily_digest": 0,
        "weekly_brief": 0,
        "ignored_memory_update": 0,
    }
    for decision in decisions:
        route = decision["route"]
        counts[route] = counts.get(route, 0) + 1
    return counts
