from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.langgraph_agent import build_prism_graph
from app.agent.soul_profile import SoulProfile, get_soul_profile, reload_soul_profile
from app.agent.state import AgentState
from app.core.config import get_settings
from app.db.models import AgentRunRecord
from app.db.session import get_db
from app.schemas.agent import AgentResearchRequest, AgentRunRead, AgentRunResponse

logger = logging.getLogger("prism.agent")

router = APIRouter(prefix="/api/agent", tags=["agent"])

_scheduler: BackgroundScheduler | None = None
_job_id = "prism-heartbeat"


def decide_signal_route(signal: dict[str, Any], profile: SoulProfile) -> dict[str, Any]:
    """Route one PRISM signal using the loaded SOUL profile."""

    thresholds = profile.thresholds
    topic = str(signal.get("topic") or "").lower()
    title = str(signal.get("title") or "").lower()
    monitored = _is_monitored(topic=topic, title=title, profile=profile)
    prism_score = float(signal.get("prism_score") or 0.0)
    trust_score = float(signal.get("trust_score") or 0.0)

    if not monitored:
        route = "ignored_memory_update"
        reason = "topic_not_monitored"
    elif trust_score < thresholds.min_trust_score:
        route = "ignored_memory_update"
        reason = "below_min_trust_score"
    elif prism_score >= thresholds.alert_prism_score:
        route = "alert"
        reason = "above_alert_threshold"
    elif prism_score >= thresholds.digest_prism_score:
        route = "daily_digest"
        reason = "above_digest_threshold"
    elif prism_score >= thresholds.weekly_brief_prism_score:
        route = "weekly_brief"
        reason = "above_weekly_brief_threshold"
    else:
        route = "ignored_memory_update"
        reason = "below_report_thresholds"

    return {
        "route": route,
        "reason": reason,
        "signal": signal,
        "thresholds": thresholds.model_dump(),
        "decided_at": datetime.now(UTC).isoformat(),
    }


def _is_monitored(topic: str, title: str, profile: SoulProfile) -> bool:
    for monitored_topic in profile.monitor_topics:
        normalized = monitored_topic.lower()
        if normalized == "all" or normalized in topic or normalized in title:
            return True
    return False


def _job_kwargs() -> dict[str, Any]:
    settings = get_settings()
    return {
        "query": settings.prism_agent_query,
        "limit_per_source": settings.prism_agent_limit_per_source,
        "include_demo": settings.prism_agent_include_demo,
    }


def _sync_next_run() -> None:
    if _scheduler is None:
        AgentState.set_next_run(None)
        return

    job = _scheduler.get_job(_job_id)
    AgentState.set_next_run(job.next_run_time if job else None)


def _scheduled_heartbeat() -> None:
    from app.agent.heartbeat import heartbeat_job

    heartbeat_job(**_job_kwargs())
    _sync_next_run()


def start_scheduler() -> None:
    global _scheduler

    settings = get_settings()
    AgentState.set_scheduler_enabled(settings.enable_scheduler)

    if not settings.enable_scheduler:
        AgentState.set_next_run(None)
        logger.info("PRISM scheduler disabled. Set ENABLE_SCHEDULER=true to enable it.")
        return

    hours = max(1, settings.prism_heartbeat_hours)
    if _scheduler and _scheduler.running:
        _sync_next_run()
        return

    _scheduler = BackgroundScheduler(timezone=UTC)
    _scheduler.add_job(
        _scheduled_heartbeat,
        trigger=IntervalTrigger(hours=hours),
        id=_job_id,
        name="PRISM heartbeat",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(UTC),
    )
    _scheduler.start()
    _sync_next_run()
    logger.info("PRISM scheduler enabled. Heartbeat interval: %d hour(s).", hours)


def stop_scheduler() -> None:
    global _scheduler

    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
    AgentState.set_scheduler_enabled(False)
    AgentState.set_next_run(None)


@router.get("/status")
def agent_status() -> dict[str, Any]:
    _sync_next_run()
    return AgentState.as_dict()


@router.get("/profile")
def agent_profile() -> dict[str, Any]:
    return get_soul_profile().model_dump()


@router.post("/profile/reload")
def reload_agent_profile() -> dict[str, Any]:
    return {
        "status": "reloaded",
        "profile": reload_soul_profile().model_dump(),
    }


@router.post("/run-once")
def run_once() -> dict[str, Any]:
    from app.agent.heartbeat import heartbeat_job

    result = heartbeat_job(**_job_kwargs())
    _sync_next_run()

    if result.get("skipped"):
        raise HTTPException(status_code=409, detail=result["reason"])

    return {
        "status": AgentState.status,
        "result": result,
        "agent": AgentState.as_dict(),
    }


@router.get("/alerts")
def agent_alerts() -> dict[str, Any]:
    return AgentState.alerts_dict()


@router.post("/research", response_model=AgentRunResponse)
def run_agent_research(payload: AgentResearchRequest, db: Session = Depends(get_db)) -> AgentRunResponse:
    result = build_prism_graph().run(
        db=db,
        query=payload.query,
        user_id=payload.user_id,
        mode=payload.mode,
        limit_per_source=payload.limit_per_source,
        include_demo=payload.include_demo,
    )
    AgentState.record_graph_run(
        {
            "run_id": result.run_id,
            "query": result.query,
            "intent": result.intent,
            "chroma_available": result.chroma_available,
            "neo4j_available": result.neo4j_available,
            "llm_provider": result.provider_used,
            "timings": result.timings,
            "errors": result.errors,
        }
    )
    return result


@router.get("/runs/{run_id}", response_model=AgentRunRead)
def read_agent_run(run_id: str, db: Session = Depends(get_db)) -> AgentRunRead:
    record = db.get(AgentRunRecord, run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return AgentRunRead.model_validate(record)
