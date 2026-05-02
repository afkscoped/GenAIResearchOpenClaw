from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import EntityLink, ResearchItem, SourceSignal
from app.db.session import get_db
from app.schemas.research import EntityLinkRead, ResearchItemRead, SourceSignalRead

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=list[ResearchItemRead])
def list_items(
    topic: str | None = None,
    source: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ResearchItem]:
    query = db.query(ResearchItem).order_by(ResearchItem.timestamp.desc())
    if topic:
        query = query.filter(ResearchItem.topic.ilike(f"%{topic}%"))
    if source:
        query = query.filter(ResearchItem.source == source)
    return query.limit(limit).all()


@router.get("/{item_id}")
def get_item_detail(item_id: str, db: Session = Depends(get_db)) -> dict:
    item = db.get(ResearchItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")

    signals = db.query(SourceSignal).filter(SourceSignal.item_id == item_id).all()
    links = (
        db.query(EntityLink)
        .filter((EntityLink.source_item_id == item_id) | (EntityLink.target_item_id == item_id))
        .order_by(EntityLink.confidence.desc())
        .all()
    )
    return {
        "item": ResearchItemRead.model_validate(item),
        "signals": [SourceSignalRead.model_validate(signal) for signal in signals],
        "entity_links": [EntityLinkRead.model_validate(link) for link in links],
    }


@router.get("/{item_id}/signals", response_model=list[SourceSignalRead])
def get_item_signals(item_id: str, db: Session = Depends(get_db)) -> list[SourceSignal]:
    item = db.get(ResearchItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")
    return db.query(SourceSignal).filter(SourceSignal.item_id == item_id).all()
