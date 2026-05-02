from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import EntityLink
from app.db.session import get_db
from app.memory.vector_store import LocalVectorMemory
from app.schemas.research import EntityLinkRead, MemorySearchResult

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/search", response_model=list[MemorySearchResult])
def search_memory(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[MemorySearchResult]:
    return LocalVectorMemory().search(db=db, query=q, limit=limit)


@router.get("/links", response_model=list[EntityLinkRead])
def list_entity_links(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)) -> list[EntityLink]:
    return db.query(EntityLink).order_by(EntityLink.confidence.desc()).limit(limit).all()
