from typing import Any

from pydantic import BaseModel, Field


class EngineResult(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    verdict: str
    evidence: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
