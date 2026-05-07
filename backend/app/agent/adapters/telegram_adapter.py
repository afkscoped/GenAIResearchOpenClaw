from __future__ import annotations

from typing import Any

import requests


class TelegramAdapter:
    def __init__(self, bot_token: str | None = None, chat_id: str | None = None) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    def available(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_alert(self, item: dict[str, Any]) -> dict[str, Any]:
        if not self.available():
            return {"channel": "telegram", "status": "skipped", "reason": "credentials missing"}
        text = f"PRISM Alert: {item.get('title')}\nScore: {item.get('prism_score', 0):.2f}\n{item.get('url', '')}"
        response = requests.post(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            json={"chat_id": self.chat_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
        return {"channel": "telegram", "status": "sent"}

    async def handle_message(self, update: Any, context: Any) -> None:
        return None
