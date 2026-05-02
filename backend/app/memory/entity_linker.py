import re
from collections import Counter
from itertools import combinations

from app.schemas.research import NormalizedItem


def tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {token for token in tokens if len(token) > 2}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


class EntityLinkCandidate:
    def __init__(self, source_item_id: str, target_item_id: str, relation_type: str, confidence: float, evidence: list[str]) -> None:
        self.source_item_id = source_item_id
        self.target_item_id = target_item_id
        self.relation_type = relation_type
        self.confidence = confidence
        self.evidence = evidence


class EntityLinker:
    def link_items(self, items: list[NormalizedItem]) -> list[EntityLinkCandidate]:
        links: list[EntityLinkCandidate] = []
        for left, right in combinations(items, 2):
            relation, confidence, evidence = self._compare(left, right)
            if confidence >= 0.35:
                links.append(EntityLinkCandidate(left.id, right.id, relation, confidence, evidence))
        return links

    def _compare(self, left: NormalizedItem, right: NormalizedItem) -> tuple[str, float, list[str]]:
        evidence: list[str] = []
        score_parts: list[float] = []

        if left.topic and left.topic == right.topic:
            score_parts.append(0.35)
            evidence.append(f"Shared topic: {left.topic}")

        title_similarity = jaccard(tokenize(left.title), tokenize(right.title))
        abstract_similarity = jaccard(tokenize(left.abstract), tokenize(right.abstract))
        text_similarity = max(title_similarity, abstract_similarity)
        if text_similarity >= 0.25:
            score_parts.append(min(text_similarity, 0.35))
            evidence.append(f"Text similarity: {text_similarity:.2f}")

        left_urls = self._metadata_urls(left)
        right_urls = self._metadata_urls(right)
        if left.url in right_urls or right.url in left_urls or left_urls & right_urls:
            score_parts.append(0.55)
            evidence.append("Shared or cross-referenced URL in metadata")

        shared_authors = set(left.authors) & set(right.authors)
        shared_orgs = set(left.organizations) & set(right.organizations)
        if shared_authors:
            score_parts.append(0.25)
            evidence.append(f"Shared author(s): {', '.join(sorted(shared_authors))}")
        if shared_orgs:
            score_parts.append(0.2)
            evidence.append(f"Shared organization(s): {', '.join(sorted(shared_orgs))}")

        confidence = min(sum(score_parts), 1.0)
        relation_type = self._relation_type(left, right)
        return relation_type, confidence, evidence

    def _metadata_urls(self, item: NormalizedItem) -> set[str]:
        urls = set()
        for value in item.metadata.values():
            if isinstance(value, str) and value.startswith("http"):
                urls.add(value)
            if isinstance(value, list):
                urls.update(str(entry) for entry in value if str(entry).startswith("http"))
        return urls

    def _relation_type(self, left: NormalizedItem, right: NormalizedItem) -> str:
        pair = {left.source, right.source}
        if pair == {"arxiv", "github"}:
            return "paper_repo"
        if pair == {"github", "huggingface"}:
            return "repo_model"
        if "mock_social" in pair:
            return "social_signal"
        if "mock_jobs" in pair or "news" in pair:
            return "adoption_signal"
        return "topic_similarity"


def topic_counts(items: list[NormalizedItem]) -> dict[str, int]:
    return dict(Counter(item.topic for item in items))
