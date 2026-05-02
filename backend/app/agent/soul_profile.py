from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.core.config import get_settings


class ProfileThresholds(BaseModel):
    alert_prism_score: float = Field(default=0.82, ge=0.0, le=1.0)
    digest_prism_score: float = Field(default=0.65, ge=0.0, le=1.0)
    weekly_brief_prism_score: float = Field(default=0.45, ge=0.0, le=1.0)
    min_trust_score: float = Field(default=0.35, ge=0.0, le=1.0)


class ProfileChannels(BaseModel):
    alerts: list[str] = Field(default_factory=lambda: ["mock"])
    daily_digest: list[str] = Field(default_factory=lambda: ["mock"])
    weekly_brief: list[str] = Field(default_factory=lambda: ["mock"])


class ReportFrequency(BaseModel):
    daily_digest_hour_utc: int = Field(default=15, ge=0, le=23)
    weekly_brief_day: str = "monday"
    weekly_brief_hour_utc: int = Field(default=15, ge=0, le=23)


class SoulProfile(BaseModel):
    name: str = "PRISM Research Agent"
    description: str = "OpenClaw-style profile for PRISM research monitoring."
    monitor_topics: list[str] = Field(default_factory=lambda: ["multimodal agents"])
    thresholds: ProfileThresholds = Field(default_factory=ProfileThresholds)
    channels: ProfileChannels = Field(default_factory=ProfileChannels)
    report_frequency: ReportFrequency = Field(default_factory=ReportFrequency)


def _profile_path() -> Path:
    raw_path = Path(get_settings().prism_soul_profile_path)
    if raw_path.is_absolute():
        return raw_path
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / raw_path


def load_soul_profile() -> SoulProfile:
    path = _profile_path()
    if not path.exists():
        return SoulProfile()

    with path.open("r", encoding="utf-8") as profile_file:
        payload = yaml.safe_load(profile_file) or {}
    return SoulProfile.model_validate(payload)


@lru_cache
def get_soul_profile() -> SoulProfile:
    return load_soul_profile()


def reload_soul_profile() -> SoulProfile:
    get_soul_profile.cache_clear()
    return get_soul_profile()
