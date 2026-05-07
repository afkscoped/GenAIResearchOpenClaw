from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AgentMode = Literal["auto", "discover", "compare", "recommend", "benchmark"]


class AgentResearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    user_id: str = "default"
    mode: AgentMode = "auto"
    limit_per_source: int = Field(default=5, ge=1, le=20)
    include_demo: bool = True


class AgentRankedItem(BaseModel):
    item_id: str
    title: str
    topic: str
    source: str
    url: str
    prism_score: float
    personalised_score: float
    memory_score: float = 0.0
    graph_score: float = 0.0
    final_score: float
    verdict: str
    evidence: list[str] = Field(default_factory=list)
    reason: str = ""


class AgentRunResponse(BaseModel):
    run_id: str
    query: str
    user_id: str
    mode: str
    intent: str
    plan: dict[str, Any]
    final_answer: str
    ranked_items: list[AgentRankedItem]
    memory_hits: list[dict[str, Any]]
    graph_context: list[dict[str, Any]]
    engine_summaries: list[dict[str, Any]]
    provider_used: str
    chroma_available: bool = False
    neo4j_available: bool = False
    timings: dict[str, float] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class AgentRunRead(BaseModel):
    id: str
    query: str
    user_id: str
    mode: str
    intent: str
    llm_provider: str
    status: str
    final_answer: str
    payload: dict[str, Any]
    errors: list[str]
    timings: dict[str, float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
