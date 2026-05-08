from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agent.soul_profile import SoulProfile


class ChannelDispatcher:
    """Submission-safe delivery facade.

    Delivery is intentionally local-only: routed decisions are recorded in
    memory so every research-agent tab works without Discord, Telegram, Reddit,
    or any other webhook.
    """

    def dispatch(self, decision: dict[str, Any], profile: SoulProfile) -> list[dict[str, Any]]:
        channels = self._channels_for(decision["route"], profile)
        return [self._dispatch_one(channel, decision) for channel in channels]

    def _channels_for(self, route: str, profile: SoulProfile) -> list[str]:
        if route == "alert":
            return profile.channels.alerts
        if route == "daily_digest":
            return profile.channels.daily_digest
        if route == "weekly_brief":
            return profile.channels.weekly_brief
        return ["mock"]

    def _dispatch_one(self, channel: str, decision: dict[str, Any]) -> dict[str, Any]:
        return self._dispatch_mock(channel, decision)

    def _dispatch_mock(self, channel: str, decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "channel": channel,
            "status": "mocked",
            "delivered_at": datetime.now(UTC).isoformat(),
            "item_id": decision["signal"]["item_id"],
            "route": decision["route"],
        }
