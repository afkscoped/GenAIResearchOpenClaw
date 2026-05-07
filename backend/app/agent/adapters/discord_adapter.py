from __future__ import annotations

from typing import Any

import requests


class DiscordAdapter:
    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url

    def available(self) -> bool:
        return bool(self.webhook_url)

    def send_alert(self, item: dict[str, Any]) -> dict[str, Any]:
        if not self.webhook_url:
            return {"channel": "discord", "status": "skipped", "reason": "webhook missing"}
        content = f"PRISM Alert: {item.get('title')}\nScore: {item.get('prism_score', 0):.2f}\n{item.get('url', '')}"
        response = requests.post(self.webhook_url, json={"content": content}, timeout=10)
        response.raise_for_status()
        return {"channel": "discord", "status": "sent"}

    async def on_message(self, message: Any) -> None:
        return None
