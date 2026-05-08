"""
state.py
--------
In-memory singleton that tracks the agent's runtime state.

Deliberately kept in its own module (not inside scheduler.py or router.py)
so every layer can import it without creating circular dependencies.

Thread-safety: APScheduler runs jobs in background threads. A small in-process
lock prevents overlapping heartbeat runs in this single-process dev setup.
"""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any


class AgentState:
    """Mutable singleton - only class-level attributes and class methods."""

    status: str = "idle"          # idle | running | ok | error
    last_run_at: datetime | None = None
    last_run_details: dict[str, Any] = {}
    last_error: str | None = None
    next_run_at: datetime | None = None
    run_count: int = 0
    scheduler_enabled: bool = False
    alerts: list[dict[str, Any]] = []
    deliveries: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    latest_graph: dict[str, Any] = {}
    _run_lock = Lock()

    # -----------------------------------------------------------------------
    # Mutation helpers
    # -----------------------------------------------------------------------

    @classmethod
    def begin_run(cls) -> bool:
        if not cls._run_lock.acquire(blocking=False):
            return False
        cls.status = "running"
        cls.last_error = None
        return True

    @classmethod
    def mark_success(cls, details: dict[str, Any]) -> None:
        try:
            cls.status = "ok"
            cls.last_run_at = datetime.now(UTC)
            cls.last_run_details = details
            cls.last_error = None
            cls.run_count += 1
        finally:
            cls._release_run_lock()

    @classmethod
    def mark_error(cls, traceback_str: str) -> None:
        try:
            cls.status = "error"
            cls.last_run_at = datetime.now(UTC)
            cls.last_error = traceback_str
            cls.run_count += 1
        finally:
            cls._release_run_lock()

    @classmethod
    def set_next_run(cls, next_run_at: datetime | None) -> None:
        cls.next_run_at = next_run_at

    @classmethod
    def set_scheduler_enabled(cls, enabled: bool) -> None:
        cls.scheduler_enabled = enabled

    @classmethod
    def record_decision(cls, decision: dict[str, Any]) -> None:
        cls.decisions.insert(0, decision)
        cls.decisions = cls.decisions[:200]
        if decision.get("route") == "alert":
            cls.alerts.insert(0, decision)
            cls.alerts = cls.alerts[:100]

    @classmethod
    def record_deliveries(cls, deliveries: list[dict[str, Any]]) -> None:
        cls.deliveries = deliveries + cls.deliveries
        cls.deliveries = cls.deliveries[:200]

    @classmethod
    def record_graph_run(cls, details: dict[str, Any]) -> None:
        cls.latest_graph = details

    @classmethod
    def _release_run_lock(cls) -> None:
        try:
            cls._run_lock.release()
        except RuntimeError:
            pass

    @classmethod
    def as_dict(cls) -> dict[str, Any]:
        return {
            "scheduler_enabled": cls.scheduler_enabled,
            "status": cls.status,
            "run_count": cls.run_count,
            "last_run_at": cls.last_run_at.isoformat() if cls.last_run_at else None,
            "next_run_at": cls.next_run_at.isoformat() if cls.next_run_at else None,
            "last_run_details": cls.last_run_details,
            "last_error": cls.last_error,
            "errors": [cls.last_error] if cls.last_error else cls.last_run_details.get("engine_errors", []),
            "alerts_count": len(cls.alerts),
            "deliveries_count": len(cls.deliveries),
            "latest_graph": cls.latest_graph,
        }

    @classmethod
    def alerts_dict(cls) -> dict[str, Any]:
        return {
            "alerts": cls.alerts,
            "deliveries": cls.deliveries,
            "decisions": cls.decisions,
        }
