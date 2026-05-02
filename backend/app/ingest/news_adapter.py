from datetime import UTC, datetime
from typing import Any

import feedparser

from app.ingest.base import IngestionAdapter


class NewsAdapter(IngestionAdapter):
    source_name = "news"

    def __init__(self, feeds: list[str]) -> None:
        self.feeds = feeds

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query_terms = [term for term in query.lower().split() if len(term) > 2]
        results = []
        for feed_url in self.feeds:
            if len(results) >= limit:
                break
            try:
                feed = feedparser.parse(feed_url)
            except Exception:
                continue
            for entry in feed.entries:
                if len(results) >= limit:
                    break
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                haystack = f"{title} {summary}".lower()
                if query_terms and not any(term in haystack for term in query_terms):
                    continue
                parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
                timestamp = datetime(*parsed_time[:6], tzinfo=UTC) if parsed_time else datetime.now(UTC)
                results.append(
                    {
                        "title": title,
                        "abstract": summary,
                        "source": self.source_name,
                        "url": entry.get("link", ""),
                        "authors": [entry.get("author", "")] if entry.get("author") else [],
                        "organizations": [feed.feed.get("title", "")] if feed.feed.get("title") else [],
                        "topic": query,
                        "timestamp": timestamp,
                        "metadata": {"feed_url": feed_url, "publisher": feed.feed.get("title", "")},
                        "signals": [
                            {
                                "source_type": self.source_name,
                                "mentions": 1,
                                "evidence": ["Matched query in RSS/news feed"],
                                "raw_payload": {"feed_url": feed_url},
                            }
                        ],
                    }
                )
        return results
