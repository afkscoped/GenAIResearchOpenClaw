from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SourceName = Literal["arxiv", "github", "huggingface", "news", "mock_social", "mock_jobs"]


class ResearchItemBase(BaseModel):
    title: str
    abstract: str = ""
    source: SourceName
    url: str
    authors: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    topic: str = "general"
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchItemCreate(ResearchItemBase):
    id: str | None = None


class ResearchItemRead(ResearchItemBase):
    id: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="extra_metadata")

    model_config = ConfigDict(from_attributes=True)


class SourceSignalCreate(BaseModel):
    item_id: str
    source_type: str
    stars: int = 0
    forks: int = 0
    commits: int = 0
    model_downloads: int = 0
    mentions: int = 0
    evidence: list[str] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class SourceSignalRead(SourceSignalCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NormalizedItem(BaseModel):
    id: str
    title: str
    abstract: str = ""
    source: SourceName
    url: str
    authors: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    topic: str = "general"
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    signals: list[SourceSignalCreate] = Field(default_factory=list)


class EntityLinkRead(BaseModel):
    id: int
    source_item_id: str
    target_item_id: str
    relation_type: str
    confidence: float
    evidence: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PipelineRunResponse(BaseModel):
    ingested_items: int
    stored_items: int
    stored_signals: int
    entity_links: int
    memory_documents: int
    sources: list[str]


class MemorySearchResult(BaseModel):
    item_id: str
    title: str
    topic: str
    url: str
    score: float
    matched_terms: list[str]


class FusionReportRead(BaseModel):
    item_id: str
    prism_score: float
    novelty_score: float
    trust_score: float
    controversy_score: float
    adoption_gap_score: float
    transferability_score: float
    verdict: str
    evidence: list[str]


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
