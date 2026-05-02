from typing import Any

from app.ingest.base import IngestionAdapter
from app.ingest.seed_data import demo_raw_items


class MockSocialAdapter(IngestionAdapter):
    source_name = "mock_social"

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query_lower = query.lower()
        items = [item for item in demo_raw_items() if item["source"] == self.source_name]
        matched = [item for item in items if query_lower in f"{item['title']} {item['abstract']} {item['topic']}".lower()]
        return (matched or items)[:limit]


class MockJobsAdapter(IngestionAdapter):
    source_name = "mock_jobs"

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query_lower = query.lower()
        items = [item for item in demo_raw_items() if item["source"] == self.source_name]
        matched = [item for item in items if query_lower in f"{item['title']} {item['abstract']} {item['topic']}".lower()]
        return (matched or items)[:limit]
