from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import EngineRun, EntityLink, FusionReportRecord, ResearchItem, SourceSignal
from app.db.session import get_db
from app.api.query_filters import apply_item_search_filter
from app.engines.fusion_engine import FusionEngine
from app.schemas.engine_run import EngineRunRead, EngineRunResponse, FusionReportRecordRead
from app.schemas.research import FusionReportRead
from app.services.engine_runner import run_and_persist_engines

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def related_context(db: Session, item: ResearchItem) -> tuple[list[ResearchItem], list[EntityLink]]:
    links = (
        db.query(EntityLink)
        .filter((EntityLink.source_item_id == item.id) | (EntityLink.target_item_id == item.id))
        .order_by(EntityLink.confidence.desc())
        .limit(25)
        .all()
    )
    linked_ids = set()
    for link in links:
        if link.source_item_id != item.id:
            linked_ids.add(link.source_item_id)
        if link.target_item_id != item.id:
            linked_ids.add(link.target_item_id)

    related_items = []
    if linked_ids:
        related_items.extend(db.query(ResearchItem).filter(ResearchItem.id.in_(linked_ids)).all())

    same_topic = (
        db.query(ResearchItem)
        .filter(ResearchItem.topic == item.topic, ResearchItem.id != item.id)
        .order_by(ResearchItem.timestamp.desc())
        .limit(10)
        .all()
    )
    seen = {related.id for related in related_items}
    for related in same_topic:
        if related.id not in seen:
            related_items.append(related)
            seen.add(related.id)
    return related_items, links


def build_fusion_report(db: Session, item: ResearchItem) -> FusionReportRead:
    signals = db.query(SourceSignal).filter(SourceSignal.item_id == item.id).all()
    related_items, links = related_context(db, item)
    return FusionEngine().analyze(item=item, signals=signals, related_items=related_items, links=links)


def record_to_fusion_report(db: Session, record: FusionReportRecord) -> FusionReportRead:
    engine_run = db.get(EngineRun, record.engine_run_id)
    return FusionReportRead(
        item_id=record.item_id,
        prism_score=record.prism_score,
        novelty_score=record.novelty_score,
        trust_score=record.trust_score,
        controversy_score=record.controversy_score,
        adoption_gap_score=record.adoption_gap_score,
        transferability_score=record.transferability_score,
        verdict=record.verdict,
        evidence=record.evidence,
        cross_domain_details=engine_run.cross_domain_details if engine_run else {},
    )


@router.get("/fusion-reports", response_model=list[FusionReportRead])
def list_fusion_reports(
    q: str | None = Query(default=None, min_length=2),
    limit: int = Query(default=15, ge=1, le=100),
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[FusionReportRead]:
    """Return fusion reports for the latest items.
    
    Uses CACHING: If a report already exists in FusionReportRecord, use it.
    Otherwise, run the engines once and persist.
    """
    item_query = db.query(ResearchItem).order_by(ResearchItem.timestamp.desc())
    items = apply_item_search_filter(item_query, q).limit(limit).all()
    results = []
    
    for item in items:
        cached = None
        if not refresh:
            cached = db.query(FusionReportRecord).filter(FusionReportRecord.item_id == item.id).order_by(FusionReportRecord.created_at.desc()).first()
        
        if cached:
            results.append(record_to_fusion_report(db, cached))
        else:
            _, fusion_record = run_and_persist_engines(db, item)
            db.commit()
            db.refresh(fusion_record)
            results.append(record_to_fusion_report(db, fusion_record))
            
    return results


@router.get("/fusion-reports/{item_id}", response_model=FusionReportRead)
def get_fusion_report(
    item_id: str,
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> FusionReportRead:
    item = db.get(ResearchItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")
    
    cached = None
    if not refresh:
        cached = db.query(FusionReportRecord).filter(FusionReportRecord.item_id == item_id).order_by(FusionReportRecord.created_at.desc()).first()
        if cached:
            return record_to_fusion_report(db, cached)
    
    _, fusion_record = run_and_persist_engines(db, item)
    db.commit()
    db.refresh(fusion_record)
    return record_to_fusion_report(db, fusion_record)


# ---------------------------------------------------------------------------
# Persistent engine-run endpoints
# ---------------------------------------------------------------------------


@router.post("/run-engines", response_model=EngineRunResponse, status_code=201)
def run_engines(
    item_id: str = Query(..., description="ID of the ResearchItem to analyse"),
    db: Session = Depends(get_db),
) -> EngineRunResponse:
    """Run all five analysis engines for *item_id*, persist the results, and
    return the persisted EngineRun + FusionReportRecord.

    The existing dynamic /fusion-reports endpoint is **not** affected.
    """
    item = db.get(ResearchItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")

    engine_run, fusion_record = run_and_persist_engines(db, item)
    db.commit()
    db.refresh(engine_run)
    db.refresh(fusion_record)

    return EngineRunResponse(
        engine_run=EngineRunRead.model_validate(engine_run),
        fusion_report=FusionReportRecordRead.model_validate(fusion_record),
    )


@router.get("/engine-runs/{item_id}", response_model=list[EngineRunRead])
def list_engine_runs(
    item_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[EngineRunRead]:
    """Return all persisted EngineRun records for *item_id*, newest first."""
    item = db.get(ResearchItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")

    runs = (
        db.query(EngineRun)
        .filter(EngineRun.item_id == item_id)
        .order_by(EngineRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [EngineRunRead.model_validate(r) for r in runs]


@router.get("/fusion-history/{item_id}", response_model=list[FusionReportRecordRead])
def list_fusion_history(
    item_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[FusionReportRecordRead]:
    """Return all persisted FusionReportRecord rows for *item_id*, newest first."""
    item = db.get(ResearchItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")

    records = (
        db.query(FusionReportRecord)
        .filter(FusionReportRecord.item_id == item_id)
        .order_by(FusionReportRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return [FusionReportRecordRead.model_validate(r) for r in records]
