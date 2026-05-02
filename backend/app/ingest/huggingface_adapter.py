from datetime import UTC, datetime
from typing import Any

import requests

from app.ingest.base import IngestionAdapter


class HuggingFaceAdapter(IngestionAdapter):
    source_name = "huggingface"

    def __init__(self, token: str | None = None) -> None:
        self.token = token

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        params = {"search": query, "limit": min(limit, 20), "sort": "lastModified", "direction": -1}
        try:
            response = requests.get("https://huggingface.co/api/models", headers=headers, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        results = []
        for model in payload:
            updated_at = model.get("lastModified") or model.get("createdAt")
            try:
                timestamp = datetime.fromisoformat(updated_at.replace("Z", "+00:00")) if updated_at else datetime.now(UTC)
            except ValueError:
                timestamp = datetime.now(UTC)
            model_id = model.get("modelId") or model.get("id") or "unknown-model"
            results.append(
                {
                    "title": model_id,
                    "abstract": f"Hugging Face model matching query '{query}'.",
                    "source": self.source_name,
                    "url": f"https://huggingface.co/{model_id}",
                    "authors": [model_id.split("/")[0]] if "/" in model_id else [],
                    "organizations": [],
                    "topic": query,
                    "timestamp": timestamp,
                    "metadata": {
                        "pipeline_tag": model.get("pipeline_tag"),
                        "library_name": model.get("library_name"),
                        "tags": model.get("tags", []),
                    },
                    "signals": [
                        {
                            "source_type": self.source_name,
                            "model_downloads": int(model.get("downloads") or 0),
                            "mentions": int(model.get("likes") or 0),
                            "evidence": [
                                f"{int(model.get('downloads') or 0)} model downloads",
                                f"{int(model.get('likes') or 0)} Hugging Face likes",
                            ],
                            "raw_payload": {"model_id": model_id},
                        }
                    ],
                }
            )
        return results
