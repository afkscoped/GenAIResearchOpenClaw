from datetime import UTC, datetime
from typing import Any

import requests

from app.ingest.base import IngestionAdapter


class GitHubAdapter(IngestionAdapter):
    source_name = "github"

    def __init__(self, token: str | None = None) -> None:
        self.token = token

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        params = {
            "q": f"{query} in:name,description,readme",
            "sort": "updated",
            "order": "desc",
            "per_page": min(limit, 20),
        }
        try:
            response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        results = []
        for repo in payload.get("items", []):
            pushed_at = repo.get("pushed_at") or repo.get("updated_at")
            try:
                timestamp = datetime.fromisoformat(pushed_at.replace("Z", "+00:00")) if pushed_at else datetime.now(UTC)
            except ValueError:
                timestamp = datetime.now(UTC)
            results.append(
                {
                    "title": repo.get("full_name") or repo.get("name") or "GitHub repository",
                    "abstract": repo.get("description") or "",
                    "source": self.source_name,
                    "url": repo.get("html_url") or repo.get("url"),
                    "authors": [repo.get("owner", {}).get("login", "")],
                    "organizations": [],
                    "topic": query,
                    "timestamp": timestamp,
                    "metadata": {
                        "language": repo.get("language"),
                        "license": (repo.get("license") or {}).get("spdx_id"),
                        "open_issues": repo.get("open_issues_count", 0),
                    },
                    "signals": [
                        {
                            "source_type": self.source_name,
                            "stars": repo.get("stargazers_count", 0),
                            "forks": repo.get("forks_count", 0),
                            "commits": 0,
                            "mentions": 0,
                            "evidence": [
                                f"{repo.get('stargazers_count', 0)} GitHub stars",
                                f"{repo.get('forks_count', 0)} forks",
                            ],
                            "raw_payload": {"repo_id": repo.get("id")},
                        }
                    ],
                }
            )
        return results
