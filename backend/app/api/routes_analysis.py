from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import EntityLink, ResearchItem, SourceSignal
from app.db.session import get_db
from app.engines.fusion_engine import FusionEngine
from app.schemas.research import FusionReportRead

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
