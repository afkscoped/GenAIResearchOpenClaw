import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from app.schemas.research import NormalizedItem, SourceSignalCreate

TOPIC_KEYWORDS = {
    "multimodal agents": ["multimodal", "agent", "vision-language", "visual reasoning"],
    "healthcare ai adoption": ["hospital", "healthcare", "clinical", "medical"],
    "cross-domain graph learning": ["graph", "protein", "supply-chain", "supply chain", "message passing"],
    "evaluation and benchmarks": ["benchmark", "evaluation", "replication", "robustness"],
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed
        except ValueError:
            return datetime.now(UTC)
    return datetime.now(UTC)


def infer_topic(title: str, abstract: str, metadata: dict[str, Any]) -> str:
    explicit_topic = clean_text(metadata.get("topic"))
    if explicit_topic:
        return explicit_topic.lower()
    haystack = f"{title} {abstract} {' '.join(str(v) for v in metadata.values())}".lower()
    best_topic = "general"
    best_hits = 0
    for topic, keywords in TOPIC_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword in haystack)
        if hits > best_hits:
            best_topic = topic
            best_hits = hits
    return best_topic


def stable_id(source: str, title: str, url: str) -> str:
    basis = f"{source}:{url or title}".encode("utf-8")
    digest = hashlib.sha1(basis).hexdigest()[:12]
    safe_source = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
    return f"{safe_source}-{digest}"


def normalize_raw_item(raw: dict[str, Any]) -> NormalizedItem:
    title = clean_text(raw.get("title")) or "Untitled research item"
    abstract = clean_text(raw.get("abstract") or raw.get("summary") or raw.get("description"))
    source = clean_text(raw.get("source") or "news").lower()
    url = clean_text(raw.get("url") or raw.get("link") or f"urn:prism:{title}")
    metadata = dict(raw.get("metadata") or {})
    topic = clean_text(raw.get("topic")) or infer_topic(title, abstract, metadata)
    item_id = clean_text(raw.get("id")) or stable_id(source, title, url)

    signals = []
    for signal in raw.get("signals", []):
        signals.append(
            SourceSignalCreate(
                item_id=item_id,
                source_type=clean_text(signal.get("source_type") or source),
                stars=int(signal.get("stars") or 0),
                forks=int(signal.get("forks") or 0),
                commits=int(signal.get("commits") or 0),
                model_downloads=int(signal.get("model_downloads") or 0),
                mentions=int(signal.get("mentions") or 0),
                evidence=[clean_text(item) for item in signal.get("evidence", []) if clean_text(item)],
                raw_payload=dict(signal.get("raw_payload") or {}),
            )
        )

    return NormalizedItem(
        id=item_id,
        title=title,
        abstract=abstract,
        source=source,
        url=url,
        authors=[clean_text(author) for author in raw.get("authors", []) if clean_text(author)],
        organizations=[clean_text(org) for org in raw.get("organizations", []) if clean_text(org)],
        topic=topic.lower(),
        timestamp=parse_timestamp(raw.get("timestamp") or raw.get("published") or raw.get("updated")),
        metadata=metadata,
        signals=signals,
    )


def normalize_many(raw_items: list[dict[str, Any]]) -> list[NormalizedItem]:
    seen: set[str] = set()
    normalized: list[NormalizedItem] = []
    for raw in raw_items:
        item = normalize_raw_item(raw)
        if item.id in seen:
            continue
        seen.add(item.id)
        normalized.append(item)
    return normalized
