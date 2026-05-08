"""
OpenClaw AI Agent Service — PRISM Research Intelligence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A standalone FastAPI microservice that provides LLM-powered research
analysis. PRISM sends heuristic scores; OpenClaw returns reasoning,
a refined score, and an action decision (alert / digest / ignore).

Run:  uvicorn openclaw_service:app --port 9000 --reload
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Load .env from backend/ directory ────────────────────────────────
_env_path = Path(__file__).parent / "backend" / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
    print(f"INFO:     [OK] Loaded environment from {_env_path}")
else:
    load_dotenv()  # try current directory or system env

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
logger = logging.getLogger("openclaw")

# ── Pydantic Models ──────────────────────────────────────────────────

class ScoresPayload(BaseModel):
    trust: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    gap: float = Field(ge=0, le=1)
    cross_domain: float = Field(ge=0, le=1)
    controversy: float = Field(ge=0, le=1)


class AnalyzeRequest(BaseModel):
    title: str
    abstract: str
    scores: ScoresPayload


class AnalyzeResponse(BaseModel):
    prism_score: float
    verdict: str
    reasoning: str
    action: str  # "alert" | "digest" | "ignore"


# ── LLM Client ───────────────────────────────────────────────────────

_groq_client: Any = None

MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
]


def _get_groq_client() -> Any:
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        logger.warning("LLM_API_KEY not set — OpenClaw will use heuristic fallback.")
        return None

    try:
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
        logger.info("[OK] Groq LLM client initialised for OpenClaw.")
        return _groq_client
    except ImportError:
        logger.warning("groq package not installed. pip install groq")
        return None
    except Exception as e:
        logger.warning("Failed to init Groq: %s", e)
        return None


def _ask_llm(system: str, user: str, max_tokens: int = 250) -> str | None:
    client = _get_groq_client()
    if client is None:
        return None

    model = os.getenv("LLM_MODEL", MODELS[0])
    model_priority = [model] + [m for m in MODELS if m != model]

    for m in model_priority:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            text = resp.choices[0].message.content
            if text:
                logger.info("INFO: LLM response from %s (%d chars)", m, len(text))
                return text.strip()
        except Exception as e:
            logger.warning("[!] Model %s failed: %s — trying next", m, e)
            continue

    return None


# ── Heuristic Fallback ────────────────────────────────────────────────

def _heuristic_analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """Pure math fallback when LLM is unavailable."""
    s = req.scores
    prism_score = round(
        0.25 * s.novelty
        + 0.25 * s.trust
        + 0.15 * (1 - s.controversy)
        + 0.20 * s.gap
        + 0.15 * s.cross_domain,
        4,
    )

    if prism_score >= 0.72 and s.trust >= 0.55:
        verdict = "High-priority opportunity with strong signal and trust."
        action = "alert"
    elif prism_score >= 0.55:
        verdict = "Watchlist candidate worth monitoring."
        action = "digest"
    else:
        verdict = "Low-priority item for now."
        action = "ignore"

    return AnalyzeResponse(
        prism_score=prism_score,
        verdict=verdict,
        reasoning="fallback: heuristic scoring (LLM unavailable)",
        action=action,
    )


# ── Core Analysis Logic ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are OpenClaw, an agentic research intelligence analyst.
You receive heuristic engine scores and a paper's metadata.
Your job is to provide a refined assessment.

Respond in EXACTLY this format (no extra text):
SCORE: <float between 0.0 and 1.0>
VERDICT: <one sentence verdict>
REASONING: <2-3 sentences explaining your assessment>
ACTION: <one of: alert, digest, ignore>

Rules for ACTION:
- alert: score >= 0.7 AND trust >= 0.5 — genuinely important finding
- digest: score >= 0.45 — worth including in a daily summary  
- ignore: everything else — store in memory but don't escalate"""


def _llm_analyze(req: AnalyzeRequest) -> AnalyzeResponse | None:
    """Use LLM for rich analysis. Returns None on failure."""
    s = req.scores
    user_prompt = (
        f"Paper Title: {req.title}\n"
        f"Abstract: {req.abstract[:500]}\n\n"
        f"Engine Scores:\n"
        f"  Novelty (Signal):  {s.novelty:.2f}\n"
        f"  Trust:             {s.trust:.2f}\n"
        f"  Controversy:       {s.controversy:.2f}\n"
        f"  Adoption Gap:      {s.gap:.2f}\n"
        f"  Cross-Domain:      {s.cross_domain:.2f}\n\n"
        f"Analyze this research item."
    )

    response = _ask_llm(SYSTEM_PROMPT, user_prompt)
    if response is None:
        return None

    # Parse structured response
    prism_score = 0.5
    verdict = "Analysis complete."
    reasoning = ""
    action = "digest"

    for line in response.split("\n"):
        line = line.strip()
        upper = line.upper()
        if upper.startswith("SCORE:"):
            try:
                prism_score = max(0.0, min(1.0, float(line.split(":", 1)[1].strip())))
            except ValueError:
                pass
        elif upper.startswith("VERDICT:"):
            verdict = line.split(":", 1)[1].strip()
        elif upper.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
        elif upper.startswith("ACTION:"):
            raw_action = line.split(":", 1)[1].strip().lower()
            if raw_action in {"alert", "digest", "ignore"}:
                action = raw_action

    return AnalyzeResponse(
        prism_score=round(prism_score, 4),
        verdict=verdict,
        reasoning=reasoning or "LLM analysis completed.",
        action=action,
    )


# ── FastAPI App ───────────────────────────────────────────────────────

app = FastAPI(
    title="OpenClaw Agent Service",
    description="Agentic research intelligence microservice for PRISM",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "openclaw-agent",
        "llm_available": _get_groq_client() is not None,
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    logger.info("<< OpenClaw received: '%s'", req.title[:80])
    logger.info("   Scores: trust=%.2f novelty=%.2f gap=%.2f xdom=%.2f controversy=%.2f",
                req.scores.trust, req.scores.novelty, req.scores.gap,
                req.scores.cross_domain, req.scores.controversy)

    # Rate-limit self to stay within Groq free tier
    time.sleep(2.0)

    result = _llm_analyze(req)
    if result is None:
        logger.warning("⚡ LLM failed — falling back to heuristic.")
        result = _heuristic_analyze(req)

    logger.info(">> OpenClaw response: score=%.2f action=%s verdict='%s'",
                result.prism_score, result.action, result.verdict[:60])
    return result
