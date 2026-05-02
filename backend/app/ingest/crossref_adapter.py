from datetime import UTC, datetime
from typing import Any

import requests

from app.ingest.base import IngestionAdapter


class CrossrefAdapter(IngestionAdapter):
    source_name = "crossref"

    def __init__(self, mailto: str | None = None) -> None:
        self.mailto = mailto

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        headers = {"User-Agent": "PRISM Research Intelligence/0.1"}
        params: dict[str, Any] = {"query": query, "rows": min(limit, 20)}
        if self.mailto:
            params["mailto"] = self.mailto
        try:
            response = requests.get("https://api.crossref.org/works", headers=headers, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        results = []
        for work in payload.get("message", {}).get("items", []):
            title = " ".join(work.get("title", [])).strip() or "Crossref work"
            abstract = str(work.get("abstract") or "")
            doi = work.get("DOI", "")
            published_parts = (
                work.get("published-print", {}).get("date-parts")
                or work.get("published-online", {}).get("date-parts")
                or work.get("created", {}).get("date-parts")
                or []
            )
            timestamp = _parse_crossref_timestamp(published_parts)
            authors = []
            organizations = []
            for author in work.get("author", []):
                name = " ".join(part for part in [author.get("given"), author.get("family")] if part).strip()
                if name:
                    authors.append(name)
                affiliation = author.get("affiliation", [])
                if affiliation:
                    org_name = affiliation[0].get("name")
                    if org_name:
                        organizations.append(org_name)
            venue = work.get("container-title", [])
            if venue:
                organizations.append(venue[0])
            cited_by = int(work.get("is-referenced-by-count") or 0)
            results.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "source": self.source_name,
                    "url": f"https://doi.org/{doi}" if doi else work.get("URL", ""),
                    "authors": authors,
                    "organizations": organizations,
                    "topic": query,
                    "timestamp": timestamp,
                    "metadata": {
                        "doi": doi,
                        "publisher": work.get("publisher"),
                        "type": work.get("type"),
                        "journal": venue[0] if venue else "",
                    },
                    "signals": [
                        {
                            "source_type": self.source_name,
                            "mentions": max(1, cited_by),
                            "evidence": [
                                "Fetched from Crossref works search",
                                f"{cited_by} Crossref cited-by references",
                            ],
                            "raw_payload": {"doi": doi},
                        }
                    ],
                }
            )
        return results


def _parse_crossref_timestamp(date_parts: list[Any]) -> datetime:
    if date_parts and date_parts[0]:
        parts = list(date_parts[0]) + [1, 1, 1]
        try:
            return datetime(parts[0], parts[1], parts[2], tzinfo=UTC)
        except (TypeError, ValueError):
            return datetime.now(UTC)
    return datetime.now(UTC)
