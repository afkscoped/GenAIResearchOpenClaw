import math
import re
from collections import Counter

from sqlalchemy.orm import Session

from app.db.models import MemoryDocument, ResearchItem
from app.schemas.research import MemorySearchResult, NormalizedItem


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [token for token in tokens if len(token) > 2]


def sparse_embedding(text: str) -> tuple[list[float], list[str]]:
    counts = Counter(tokenize(text))
    if not counts:
        return [], []
    most_common = counts.most_common(64)
    max_count = max(count for _, count in most_common)
    signature = [token for token, _ in most_common]
    embedding = [count / max_count for _, count in most_common]
    return embedding, signature


def cosine_from_signatures(query_terms: set[str], document_terms: list[str]) -> tuple[float, list[str]]:
    doc_terms = set(document_terms)
    matched = sorted(query_terms & doc_terms)
    if not query_terms or not doc_terms:
        return 0.0, []
    score = len(matched) / math.sqrt(len(query_terms) * len(doc_terms))
    return float(score), matched


class LocalVectorMemory:
    def index_items(self, db: Session, items: list[NormalizedItem]) -> int:
        created = 0
        for item in items:
            exists = db.query(MemoryDocument).filter(MemoryDocument.item_id == item.id).first()
            if exists:
                continue
            text = f"{item.title}\n{item.abstract}\n{item.topic}\n{item.metadata}"
            embedding, signature = sparse_embedding(text)
            db.add(MemoryDocument(item_id=item.id, text=text, embedding=embedding, token_signature=signature))
            created += 1
        db.commit()
        return created

    def search(self, db: Session, query: str, limit: int = 10) -> list[MemorySearchResult]:
        query_terms = set(tokenize(query))
        documents = db.query(MemoryDocument).join(ResearchItem).all()
        scored: list[MemorySearchResult] = []
        for document in documents:
            score, matched = cosine_from_signatures(query_terms, document.token_signature)
            if score <= 0:
                continue
            item = document.item
            scored.append(
                MemorySearchResult(
                    item_id=item.id,
                    title=item.title,
                    topic=item.topic,
                    url=item.url,
                    score=round(score, 4),
                    matched_terms=matched,
                )
            )
        return sorted(scored, key=lambda result: result.score, reverse=True)[:limit]
