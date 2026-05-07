from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import FusionReportRecord, PaperRating, ResearchItem, UserPersonaRecord
from app.schemas.persona import SuggestionRead

ACTION_WEIGHTS = {
    "liked": 0.3,
    "starred": 0.5,
    "dismissed": -0.2,
    "shared": 0.4,
    "viewed": 0.05,
}


def get_or_create_persona(db: Session, user_id: str) -> UserPersonaRecord:
    persona = db.get(UserPersonaRecord, user_id)
    if persona is not None:
        return persona
    persona = UserPersonaRecord(user_id=user_id, last_updated=datetime.now(UTC).replace(tzinfo=None))
    db.add(persona)
    db.flush()
    return persona


def record_feedback(db: Session, user_id: str, item: ResearchItem, action: str, reward: float | None = None) -> UserPersonaRecord:
    persona = get_or_create_persona(db, user_id)
    weight = ACTION_WEIGHTS.get(action, 0.0) if reward is None else reward
    liked_topics = dict(persona.liked_topics or {})
    liked_sources = dict(persona.liked_sources or {})
    domain_weights = dict(persona.domain_weights or {})
    liked_topics[item.topic] = _clamp(float(liked_topics.get(item.topic, 0.5)) + weight)
    liked_sources[item.source] = _clamp(float(liked_sources.get(item.source, 0.5)) + weight / 2)
    domain_weights[item.topic] = liked_topics[item.topic]
    history = list(persona.interaction_history or [])
    history.append({
        "item_id": item.id,
        "topic": item.topic,
        "source": item.source,
        "action": action,
        "reward": weight,
        "timestamp": datetime.now(UTC).isoformat(),
    })
    persona.liked_topics = liked_topics
    persona.liked_sources = liked_sources
    persona.domain_weights = domain_weights
    persona.interaction_history = history[-200:]
    if action == "starred" and item.id not in (persona.favourite_paper_ids or []):
        persona.favourite_paper_ids = [*list(persona.favourite_paper_ids or []), item.id]
    persona.last_updated = datetime.now(UTC).replace(tzinfo=None)
    db.add(persona)
    return persona


def upsert_rating(db: Session, item: ResearchItem, user_id: str, payload: Any) -> PaperRating:
    rating = db.query(PaperRating).filter(PaperRating.item_id == item.id, PaperRating.user_id == user_id).first()
    if rating is None:
        rating = PaperRating(item_id=item.id, user_id=user_id)
    rating.rating = payload.rating
    rating.tags = payload.tags
    rating.notes = payload.notes
    rating.is_favourite = payload.is_favourite
    rating.updated_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(rating)
    persona = get_or_create_persona(db, user_id)
    favourites = list(persona.favourite_paper_ids or [])
    if payload.is_favourite and item.id not in favourites:
        favourites.append(item.id)
    if not payload.is_favourite and item.id in favourites:
        favourites.remove(item.id)
    persona.favourite_paper_ids = favourites
    persona.last_updated = datetime.now(UTC).replace(tzinfo=None)
    db.add(persona)
    return rating


def suggestions(db: Session, user_id: str, limit: int = 10, item_ids: set[str] | None = None) -> list[SuggestionRead]:
    persona = get_or_create_persona(db, user_id)
    query = db.query(ResearchItem).order_by(ResearchItem.timestamp.desc())
    if item_ids is not None:
        if not item_ids:
            return []
        query = query.filter(ResearchItem.id.in_(item_ids))
    items = query.limit(200).all()
    output: list[SuggestionRead] = []
    for item in items:
        report = db.query(FusionReportRecord).filter(FusionReportRecord.item_id == item.id).order_by(FusionReportRecord.created_at.desc()).first()
        base_score = report.prism_score if report else 0.0
        topic_boost = float((persona.liked_topics or {}).get(item.topic, 0.5)) * 0.2
        source_boost = float((persona.liked_sources or {}).get(item.source, 0.5)) * 0.1
        personalised = _clamp(base_score + topic_boost + source_boost)
        output.append(SuggestionRead(
            item_id=item.id,
            title=item.title,
            topic=item.topic,
            source=item.source,
            url=item.url,
            prism_score=round(base_score, 4),
            personalised_score=round(personalised, 4),
            reason=f"topic={item.topic}, source={item.source}",
        ))
    return sorted(output, key=lambda entry: entry.personalised_score, reverse=True)[:limit]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
