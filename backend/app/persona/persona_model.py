from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class UserPersona(BaseModel):
    user_id: str
    liked_topics: dict[str, float] = Field(default_factory=dict)
    liked_sources: dict[str, float] = Field(default_factory=dict)
    min_trust_threshold: float = 0.4
    favourite_paper_ids: list[str] = Field(default_factory=list)
    interaction_history: list[dict[str, Any]] = Field(default_factory=list)
    domain_weights: dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PersonaEngine:
    action_weights = {
        "liked": 0.3,
        "starred": 0.5,
        "dismissed": -0.2,
        "shared": 0.4,
        "viewed": 0.05,
    }

    def update(self, persona: UserPersona, item: Any, action: str) -> UserPersona:
        weight = self.action_weights.get(action, 0.0)
        topic = self._value(item, "topic", "unknown")
        source = self._value(item, "source", "unknown")
        item_id = self._value(item, "id", "")

        persona.liked_topics[topic] = self._clamp(persona.liked_topics.get(topic, 0.5) + weight)
        persona.liked_sources[source] = self._clamp(persona.liked_sources.get(source, 0.5) + weight / 2)
        persona.domain_weights[topic] = persona.liked_topics[topic]
        if action == "starred" and item_id and item_id not in persona.favourite_paper_ids:
            persona.favourite_paper_ids.append(item_id)
        persona.interaction_history.append(
            {"item_id": item_id, "topic": topic, "source": source, "action": action, "timestamp": datetime.now(UTC).isoformat()}
        )
        persona.interaction_history = persona.interaction_history[-200:]
        persona.last_updated = datetime.now(UTC)
        return persona

    def personalise_score(self, persona: UserPersona, item: Any, base_prism_score: float) -> float:
        topic = self._value(item, "topic", "unknown")
        source = self._value(item, "source", "unknown")
        topic_boost = persona.liked_topics.get(topic, 0.5) * 0.2
        source_boost = persona.liked_sources.get(source, 0.5) * 0.1
        return self._clamp(base_prism_score + topic_boost + source_boost)

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))

    def _value(self, item: Any, key: str, default: str) -> str:
        if isinstance(item, dict):
            return str(item.get(key) or default)
        return str(getattr(item, key, None) or default)
