from datetime import UTC, datetime
from typing import Any

import requests

from app.ingest.base import IngestionAdapter


class PapersWithCodeAdapter(IngestionAdapter):
    source_name = "papers_with_code"

    def __init__(self, api_url: str) -> None:
        self.api_url = api_url.rstrip("/")

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        if not self.api_url:
            return []

        params = {"search": query, "page_size": min(limit, 20)}
        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        rows = payload.get("results", payload if isinstance(payload, list) else [])
        if not isinstance(rows, list):
            return []

        results = []
        for paper in rows[:limit]:
            published = paper.get("published") or paper.get("published_date") or paper.get("date")
            try:
                timestamp = datetime.fromisoformat(str(published).replace("Z", "+00:00")) if published else datetime.now(UTC)
            except ValueError:
                timestamp = datetime.now(UTC)

            code_count = int(paper.get("n_code_snippets") or paper.get("repository_count") or paper.get("stars") or 0)
            results.append(
                {
                    "title": paper.get("title") or paper.get("name") or "Papers With Code paper",
                    "abstract": paper.get("abstract") or paper.get("description") or "",
                    "source": self.source_name,
                    "url": paper.get("url_abs") or paper.get("url") or paper.get("paper_url") or "",
                    "authors": [author.get("name", "") for author in paper.get("authors", []) if isinstance(author, dict) and author.get("name")],
                    "organizations": [],
                    "topic": query,
                    "timestamp": timestamp,
                    "metadata": {
                        "paper_url": paper.get("paper_url"),
                        "code_url": paper.get("url_code") or paper.get("repository_url"),
                        "tasks": paper.get("tasks", []),
                    },
                    "signals": [
                        {
                            "source_type": self.source_name,
                            "mentions": max(1, code_count),
                            "evidence": [
                                "Fetched from Papers With Code API if available",
                                f"{code_count} linked code or benchmark indicators",
                            ],
                            "raw_payload": {"id": paper.get("id")},
                        }
                    ],
                }
            )
        return results
