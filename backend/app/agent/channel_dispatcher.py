from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import requests

from app.agent.soul_profile import SoulProfile
from app.core.config import get_settings

logger = logging.getLogger("prism.agent.dispatcher")


class ChannelDispatcher:
    """Delivery adapter facade.

    The mock channel is always available. Discord is enabled only when the
    profile names the `discord` channel and DISCORD_WEBHOOK_URL is configured.
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
        if channel == "discord":
            return self._dispatch_discord(decision)
        return self._dispatch_mock(channel, decision)

    def _dispatch_mock(self, channel: str, decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "channel": channel,
            "status": "mocked",
            "delivered_at": datetime.now(UTC).isoformat(),
            "item_id": decision["signal"]["item_id"],
            "route": decision["route"],
        }

    def _dispatch_discord(self, decision: dict[str, Any]) -> dict[str, Any]:
        webhook_url = get_settings().discord_webhook_url
        if not webhook_url:
            return {
                "channel": "discord",
                "status": "skipped",
                "reason": "DISCORD_WEBHOOK_URL is not configured",
            }

        signal = decision["signal"]
        content = (
            f"PRISM {decision['route'].replace('_', ' ').title()}: {signal['title']}\n"
            f"Score: {signal['prism_score']:.2f} | Trust: {signal['trust_score']:.2f}\n"
            f"{signal['url']}"
        )
        try:
            response = requests.post(webhook_url, json={"content": content}, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Discord dispatch failed: %s", exc)
            return {"channel": "discord", "status": "error", "error": str(exc)}

        return {
            "channel": "discord",
            "status": "sent",
            "delivered_at": datetime.now(UTC).isoformat(),
            "item_id": signal["item_id"],
            "route": decision["route"],
        }
