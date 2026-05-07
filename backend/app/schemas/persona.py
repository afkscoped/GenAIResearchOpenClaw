from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PersonaFeedbackCreate(BaseModel):
    item_id: str
    action: Literal["liked", "starred", "dismissed", "shared", "viewed"] = "viewed"
    reward: float | None = None


class UserPersonaRead(BaseModel):
    user_id: str
    liked_topics: dict[str, float] = Field(default_factory=dict)
    liked_sources: dict[str, float] = Field(default_factory=dict)
    min_trust_threshold: float = 0.4
    favourite_paper_ids: list[str] = Field(default_factory=list)
    interaction_history: list[dict] = Field(default_factory=list)
    domain_weights: dict[str, float] = Field(default_factory=dict)
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class PaperRatingCreate(BaseModel):
    user_id: str = "default"
    rating: int = Field(default=0, ge=0, le=5)
    tags: list[str] = Field(default_factory=list)
    notes: str = ""
    is_favourite: bool = False


class PaperRatingRead(PaperRatingCreate):
    id: int
    item_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SuggestionRead(BaseModel):
    item_id: str
    title: str
    topic: str
    source: str
    url: str
    prism_score: float
    personalised_score: float
    reason: str
