from datetime import UTC, datetime
from typing import Any

import requests

from app.core.config import get_settings
from app.ingest.base import IngestionAdapter


class SemanticScholarAdapter(IngestionAdapter):
    source_name = "semantic_scholar"

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        params = {
            "query": query,
            "limit": min(limit, 20),
            "fields": "title,abstract,url,authors,publicationDate,publicationVenue,openAccessPdf,citationCount,referenceCount,venue",
        }
        settings = get_settings()
        headers = {}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key

        try:
            response = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        results = []
        for paper in payload.get("data", []):
            published = paper.get("publicationDate")
            try:
                timestamp = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else datetime.now(UTC)
            except ValueError:
                timestamp = datetime.now(UTC)
            results.append(
                {
                    "title": paper.get("title") or "Semantic Scholar paper",
                    "abstract": paper.get("abstract") or "",
                    "source": self.source_name,
                    "url": paper.get("url") or (paper.get("openAccessPdf") or {}).get("url") or "",
                    "authors": [author.get("name", "") for author in paper.get("authors", []) if author.get("name")],
                    "organizations": [paper.get("venue") or (paper.get("publicationVenue") or {}).get("name", "")],
                    "topic": query,
                    "timestamp": timestamp,
                    "metadata": {
                        "paper_id": paper.get("paperId"),
                        "citation_count": int(paper.get("citationCount") or 0),
                        "reference_count": int(paper.get("referenceCount") or 0),
                        "open_access_pdf": (paper.get("openAccessPdf") or {}).get("url"),
                    },
                    "signals": [
                        {
                            "source_type": self.source_name,
                            "mentions": max(1, int(paper.get("citationCount") or 0)),
                            "evidence": [
                                "Fetched from Semantic Scholar paper search",
                                f"{int(paper.get('citationCount') or 0)} Semantic Scholar citations",
                            ],
                            "raw_payload": {"paper_id": paper.get("paperId")},
                        }
                    ],
                }
            )
        return results
