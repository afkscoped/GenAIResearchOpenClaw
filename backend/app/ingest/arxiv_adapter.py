from datetime import UTC
from typing import Any

from app.ingest.base import IngestionAdapter


class ArxivAdapter(IngestionAdapter):
    source_name = "arxiv"

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        try:
            import arxiv
        except ImportError:
            return []

        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=limit,
                sort_by=arxiv.SortCriterion.SubmittedDate,
            )
            results = []
            for result in client.results(search):
                results.append(
                    {
                        "title": result.title,
                        "abstract": result.summary,
                        "source": self.source_name,
                        "url": result.entry_id,
                        "authors": [author.name for author in result.authors],
                        "organizations": [],
                        "topic": query,
                        "timestamp": result.published.astimezone(UTC),
                        "metadata": {
                            "paper_id": result.get_short_id(),
                            "pdf_url": result.pdf_url,
                            "categories": result.categories,
                        },
                        "signals": [
                            {
                                "source_type": self.source_name,
                                "mentions": 1,
                                "evidence": ["Fetched from arXiv latest results"],
                                "raw_payload": {"primary_category": result.primary_category},
                            }
                        ],
                    }
                )
            return results
        except Exception:
            return []
