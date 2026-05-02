import math
import re
from datetime import UTC, datetime

from app.db.models import ResearchItem, SourceSignal


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(token) > 2}


def text_blob(item: ResearchItem) -> str:
    return f"{item.title} {item.abstract} {item.topic} {item.extra_metadata}".lower()


def days_old(item: ResearchItem) -> float:
    timestamp = item.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return max((datetime.now(UTC) - timestamp).total_seconds() / 86400, 0.0)


def recency_score(item: ResearchItem, half_life_days: float = 14.0) -> float:
    return math.exp(-days_old(item) / half_life_days)


def log_norm(value: float, scale: float) -> float:
    if value <= 0:
        return 0.0
    return min(math.log1p(value) / math.log1p(scale), 1.0)


def signal_totals(signals: list[SourceSignal]) -> dict[str, int]:
    return {
        "stars": sum(signal.stars for signal in signals),
        "forks": sum(signal.forks for signal in signals),
        "commits": sum(signal.commits for signal in signals),
        "downloads": sum(signal.model_downloads for signal in signals),
        "mentions": sum(signal.mentions for signal in signals),
    }


def has_any_url(metadata: dict, keys: list[str]) -> bool:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return True
    return False
