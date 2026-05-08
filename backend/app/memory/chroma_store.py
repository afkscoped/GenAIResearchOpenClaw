from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.memory.vector_store import LocalVectorMemory
from app.schemas.research import MemorySearchResult, NormalizedItem


class ChromaVectorMemory:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.local_fallback = LocalVectorMemory()
        self._collection: Any = None
        self._model: Any = None
        self._available = False
        self._initialise()

    def _initialise(self) -> None:
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
            client = chromadb.PersistentClient(path=self.settings.chroma_persist_path)
            self._collection = client.get_or_create_collection("prism_research")
            self._model = SentenceTransformer(self.settings.embedding_model)
            self._available = True
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def index_items(self, db: Session, items: list[NormalizedItem]) -> int:
        if not self._available or self._collection is None or self._model is None:
            return self.local_fallback.index_items(db, items)
        docs: list[str] = []
        ids: list[str] = []
        metas: list[dict[str, str]] = []
        for item in items:
            docs.append(f"{item.title}\n{item.abstract}\n{item.topic}")
            ids.append(item.id)
            metas.append({"source": item.source, "url": item.url, "topic": item.topic})
        if not docs:
            return 0
        embeddings = self._model.encode(docs).tolist()
        self._collection.upsert(documents=docs, ids=ids, metadatas=metas, embeddings=embeddings)
        return len(docs)

    def search(self, db: Session, query: str, limit: int = 10) -> list[MemorySearchResult]:
        if not self._available or self._collection is None or self._model is None:
            return self.local_fallback.search(db, query, limit)
        embedding = self._model.encode(query).tolist()
        results = self._collection.query(query_embeddings=[embedding], n_results=limit)
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        local_by_id = {result.item_id: result for result in self.local_fallback.search(db, query, limit=200)}
        output: list[MemorySearchResult] = []
        for index, item_id in enumerate(ids):
            local = local_by_id.get(item_id)
            if local is None:
                continue
            distance = distances[index] if index < len(distances) else 1.0
            local.score = round(max(0.0, 1.0 - float(distance)), 4)
            output.append(local)
        return output[:limit]
