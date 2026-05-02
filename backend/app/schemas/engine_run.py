from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EngineResultSchema(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    verdict: str
    evidence: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class EngineRunRead(BaseModel):
    id: int
    item_id: str
    signal_score: float
    signal_verdict: str
    signal_evidence: list[str]
    signal_details: dict[str, Any]
    trust_score: float
    trust_verdict: str
    trust_evidence: list[str]
    trust_details: dict[str, Any]
    debate_score: float
    debate_verdict: str
    debate_evidence: list[str]
    debate_details: dict[str, Any]
    gap_score: float
    gap_verdict: str
    gap_evidence: list[str]
    gap_details: dict[str, Any]
    cross_domain_score: float
    cross_domain_verdict: str
    cross_domain_evidence: list[str]
    cross_domain_details: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FusionReportRecordRead(BaseModel):
    id: int
    item_id: str
    engine_run_id: int
    prism_score: float
    novelty_score: float
    trust_score: float
    controversy_score: float
    adoption_gap_score: float
    transferability_score: float
    verdict: str
    evidence: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EngineRunResponse(BaseModel):
    engine_run: EngineRunRead
    fusion_report: FusionReportRecordRead
