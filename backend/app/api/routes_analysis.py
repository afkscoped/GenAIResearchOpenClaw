from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import EngineRun, EntityLink, FusionReportRecord, ResearchItem, SourceSignal
from app.db.session import get_db
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


@router.get("/fusion-reports", response_model=list[FusionReportRead])
def list_fusion_reports(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)) -> list[FusionReportRead]:
    items = db.query(ResearchItem).order_by(ResearchItem.timestamp.desc()).limit(limit).all()
    return [build_fusion_report(db, item) for item in items]


@router.get("/fusion-reports/{item_id}", response_model=FusionReportRead)
def get_fusion_report(item_id: str, db: Session = Depends(get_db)) -> FusionReportRead:
    item = db.get(ResearchItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")
    return build_fusion_report(db, item)


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
