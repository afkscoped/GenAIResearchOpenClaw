import logging
from datetime import UTC
from typing import Any

from app.ingest.base import IngestionAdapter

logger = logging.getLogger("prism.ingest.arxiv")


class ArxivAdapter(IngestionAdapter):
    source_name = "arxiv"

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        try:
            import arxiv
        except ImportError:
            logger.error("arxiv package not installed; run: pip install arxiv")
            return []

        try:
            client = arxiv.Client(
                page_size=min(limit, 100),
                delay_seconds=5.0,
                num_retries=2,
            )
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
                                "raw_payload": {
                                    "primary_category": result.primary_category
                                },
                            }
                        ],
                    }
                )
            logger.info("arxiv fetch returned %d results for '%s'", len(results), query)
            return results
        except Exception as exc:
            logger.warning("arxiv fetch failed for query '%s': %s", query, exc)
            return []