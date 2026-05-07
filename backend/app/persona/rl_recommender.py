from __future__ import annotations

import math
from typing import Any

from app.persona.persona_model import PersonaEngine, UserPersona


class ContextualBanditRecommender:
    """Small UCB1 recommender for proactive topic exploration."""

    def __init__(self, topics: list[str]) -> None:
        self.topics = topics
        self.counts = {topic: 0 for topic in topics}
        self.rewards = {topic: 0.0 for topic in topics}
        self.persona_engine = PersonaEngine()

    def select_topic(self) -> str:
        if not self.topics:
            return ""
        total = sum(self.counts.values()) + 1
        scores = {
            topic: (self.rewards[topic] / max(self.counts[topic], 1))
            + math.sqrt(2 * math.log(total) / max(self.counts[topic], 1))
            for topic in self.topics
        }
        return max(scores, key=scores.get)

    def update(self, topic: str, reward: float) -> None:
        if topic not in self.counts:
            self.topics.append(topic)
            self.counts[topic] = 0
            self.rewards[topic] = 0.0
        self.counts[topic] += 1
        self.rewards[topic] += reward

    def proactive_suggestions(self, persona: UserPersona, all_items: list[Any], limit: int = 5) -> list[Any]:
        best_topic = self.select_topic()
        matching = [item for item in all_items if self._value(item, "topic") == best_topic]
        if not matching:
            matching = list(all_items)
        return sorted(
            matching,
            key=lambda item: self.persona_engine.personalise_score(persona, item, float(getattr(item, "prism_score", 0.0) or 0.0)),
            reverse=True,
        )[:limit]

    def _value(self, item: Any, key: str) -> str:
        if isinstance(item, dict):
            return str(item.get(key) or "")
        return str(getattr(item, key, "") or "")
