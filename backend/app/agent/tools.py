from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import FusionReportRecord, ResearchItem
from app.ingest.pipeline import IngestionPipeline
from app.memory.vector_store import LocalVectorMemory
from app.schemas.research import MemorySearchResult, PipelineRunResponse
from app.services.engine_runner import run_and_persist_engines


def run_prism_ingestion(
    db: Session,
    query: str,
    limit_per_source: int = 5,
    include_demo: bool = True,
) -> PipelineRunResponse:
    """Tool-like wrapper around the existing PRISM ingestion pipeline."""

    return IngestionPipeline().run(
        db=db,
        query=query,
        limit_per_source=limit_per_source,
        include_demo=include_demo,
    )


def run_prism_engine_analysis(db: Session, limit: int | None = None) -> list[dict[str, Any]]:
    """Run PRISM engines and return routing candidates for the agent layer."""

    query = db.query(ResearchItem).order_by(ResearchItem.timestamp.desc())
    if limit is not None:
        query = query.limit(limit)

    candidates: list[dict[str, Any]] = []
    for item in query.all():
        engine_run, fusion_record = run_and_persist_engines(db, item)
        db.commit()
        db.refresh(engine_run)
        db.refresh(fusion_record)
        candidates.append(_candidate_from_record(item, fusion_record))
    return candidates


def search_prism_memory(db: Session, query: str, limit: int = 10) -> list[MemorySearchResult]:
    """Tool-like wrapper around PRISM's local memory search."""

    return LocalVectorMemory().search(db=db, query=query, limit=limit)


def _candidate_from_record(item: ResearchItem, record: FusionReportRecord) -> dict[str, Any]:
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
        "fusion_report_id": record.id,
        "engine_run_id": record.engine_run_id,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
