from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.query_filters import apply_item_search_filter
from app.db.models import PaperRating, ResearchItem
from app.db.session import get_db
from app.schemas.persona import PaperRatingCreate, PaperRatingRead, PersonaFeedbackCreate, SuggestionRead, UserPersonaRead
from app.services.persona_service import get_or_create_persona, record_feedback, suggestions, upsert_rating

router = APIRouter(prefix="/api", tags=["persona"])


@router.post("/persona/{user_id}/feedback", response_model=UserPersonaRead)
def create_feedback(user_id: str, payload: PersonaFeedbackCreate, db: Session = Depends(get_db)) -> UserPersonaRead:
    item = db.get(ResearchItem, payload.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")
    persona = record_feedback(db, user_id=user_id, item=item, action=payload.action, reward=payload.reward)
    db.commit()
    db.refresh(persona)
    return UserPersonaRead.model_validate(persona)


@router.get("/persona/{user_id}", response_model=UserPersonaRead)
def read_persona(user_id: str, db: Session = Depends(get_db)) -> UserPersonaRead:
    persona = get_or_create_persona(db, user_id)
    db.commit()
    db.refresh(persona)
    return UserPersonaRead.model_validate(persona)


@router.get("/persona/{user_id}/suggest", response_model=list[SuggestionRead])
def read_suggestions(user_id: str, limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)) -> list[SuggestionRead]:
    return suggestions(db, user_id=user_id, limit=limit)


@router.get("/persona/{user_id}/suggest/search", response_model=list[SuggestionRead])
def read_query_suggestions(
    user_id: str,
    q: str = Query(..., min_length=2),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[SuggestionRead]:
    item_ids = [
        item.id
        for item in apply_item_search_filter(db.query(ResearchItem), q).limit(200).all()
    ]
    return suggestions(db, user_id=user_id, limit=limit, item_ids=set(item_ids))


@router.post("/persona/{user_id}/reset", response_model=UserPersonaRead)
def reset_persona(user_id: str, db: Session = Depends(get_db)) -> UserPersonaRead:
    persona = get_or_create_persona(db, user_id)
    persona.liked_topics = {}
    persona.liked_sources = {}
    persona.favourite_paper_ids = []
    persona.interaction_history = []
    persona.domain_weights = {}
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return UserPersonaRead.model_validate(persona)


@router.post("/items/{item_id}/rate", response_model=PaperRatingRead)
def rate_item(item_id: str, payload: PaperRatingCreate, db: Session = Depends(get_db)) -> PaperRatingRead:
    item = db.get(ResearchItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")
    rating = upsert_rating(db, item=item, user_id=payload.user_id, payload=payload)
    db.commit()
    db.refresh(rating)
    return PaperRatingRead.model_validate(rating)


@router.get("/items/{item_id}/ratings", response_model=list[PaperRatingRead])
def list_item_ratings(item_id: str, db: Session = Depends(get_db)) -> list[PaperRatingRead]:
    item = db.get(ResearchItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Research item not found")
    ratings = db.query(PaperRating).filter(PaperRating.item_id == item_id).order_by(PaperRating.updated_at.desc()).all()
    return [PaperRatingRead.model_validate(rating) for rating in ratings]


@router.get("/persona/{user_id}/favourites", response_model=list[SuggestionRead])
def list_favourites(user_id: str, db: Session = Depends(get_db)) -> list[SuggestionRead]:
    persona = get_or_create_persona(db, user_id)
    favourite_ids = set(persona.favourite_paper_ids or [])
    return [entry for entry in suggestions(db, user_id=user_id, limit=200) if entry.item_id in favourite_ids]
