"""
openclaw_client.py
------------------
HTTP client that calls the external OpenClaw Agent Service.

If the service is unreachable or returns an error, the client falls back
to heuristic scoring so the PRISM pipeline never breaks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger("prism.agent.openclaw_client")

@dataclass
class OpenClawResult:
    """Structured result from the OpenClaw Agent Service."""
    prism_score: float
    verdict: str
    reasoning: str
    action: str  # "alert" | "digest" | "ignore"
    source: str  # "openclaw" or "fallback"


def analyze(
    title: str,
    abstract: str,
    scores: dict[str, float],
) -> OpenClawResult:
    """Send item data + engine scores to OpenClaw and return the result.

    Falls back to heuristic scoring if OpenClaw is unreachable.
    """
    settings = get_settings()
    if not settings.enable_openclaw:
        return _fallback(scores)

    payload = {
        "title": title,
        "abstract": abstract[:600],  # limit payload size
        "scores": {
            "trust": scores.get("trust", 0.0),
            "novelty": scores.get("novelty", 0.0),
            "gap": scores.get("gap", 0.0),
            "cross_domain": scores.get("cross_domain", 0.0),
            "controversy": scores.get("controversy", 0.0),
        },
    }

    logger.info("📡 Calling OpenClaw for: '%s'", title[:60])
    logger.debug("   Payload: %s", payload)

    try:
        with httpx.Client(timeout=settings.openclaw_timeout_seconds) as client:
            resp = client.post(f"{settings.openclaw_url}/analyze", json=payload)
            resp.raise_for_status()
            data = resp.json()

        logger.info("📨 OpenClaw responded: score=%.2f action=%s",
                     data["prism_score"], data["action"])

        return OpenClawResult(
            prism_score=data["prism_score"],
            verdict=data["verdict"],
            reasoning=data["reasoning"],
            action=data["action"],
            source="openclaw",
        )

    except httpx.ConnectError:
        logger.warning("🔌 OpenClaw service not reachable at %s — using fallback.", settings.openclaw_url)
        return _fallback(scores)
    except httpx.TimeoutException:
        logger.warning("⏰ OpenClaw timed out after %.1fs — using fallback.", settings.openclaw_timeout_seconds)
        return _fallback(scores)
    except Exception as exc:
        logger.error("❌ OpenClaw error: %s — using fallback.", exc)
        return _fallback(scores)


def _fallback(scores: dict[str, float]) -> OpenClawResult:
    """Heuristic fallback when OpenClaw is unavailable."""
    s = scores
    prism_score = round(
        0.25 * s.get("novelty", 0)
        + 0.25 * s.get("trust", 0)
        + 0.15 * (1 - s.get("controversy", 0))
        + 0.20 * s.get("gap", 0)
        + 0.15 * s.get("cross_domain", 0),
        4,
    )

    if prism_score >= 0.72 and s.get("trust", 0) >= 0.55:
        verdict = "High-priority opportunity with strong signal and trust."
        action = "alert"
    elif prism_score >= 0.45:
        verdict = "Watchlist candidate worth monitoring."
        action = "digest"
    else:
        verdict = "Low-priority item for now."
        action = "ignore"

    return OpenClawResult(
        prism_score=prism_score,
        verdict=verdict,
        reasoning="fallback: heuristic scoring (OpenClaw service unavailable)",
        action=action,
        source="fallback",
    )
