"""
Groq LLM client for PRISM engine enhancement.

Uses the Groq API with automatic model fallback:
  Primary:  llama-3.3-70b-versatile  (best reasoning)
  Fallback: llama-3.1-8b-instant     (highest rate limits)

When ENABLE_LLM is False or the API call fails, engines continue
using their existing heuristic verdicts — no breakage.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger("prism.engines.llm")

# Model priority: best reasoning first, fastest fallback second
MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

_groq_client: Any = None


def _get_client() -> Any:
    """Lazy-initialise the Groq client once."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    settings = get_settings()
    if not settings.enable_llm or not settings.llm_api_key:
        return None

    try:
        from groq import Groq  # type: ignore[import-untyped]

        _groq_client = Groq(api_key=settings.llm_api_key)
        logger.info("Groq LLM client initialised successfully.")
        return _groq_client
    except ImportError:
        logger.warning("groq package not installed — LLM features disabled.")
        return None
    except Exception as exc:
        logger.warning("Failed to initialise Groq client: %s", exc)
        return None


def llm_available() -> bool:
    """Check whether the LLM client is ready."""
    return _get_client() is not None


def ask_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 150,
    temperature: float = 0.3,
) -> str | None:
    """Send a prompt to Groq and return the response text.

    Tries the model from .env first, then falls back to others.
    """
    client = _get_client()
    if client is None:
        return None

    settings = get_settings()
    logger.info("LLM Model from settings: %s", settings.llm_model)
    
    # Prioritise the model from .env, then the defaults
    model_priority = [settings.llm_model] + [m for m in MODELS if m != settings.llm_model]

    for model in model_priority:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content
            if text:
                logger.debug("LLM response from %s (%d chars)", model, len(text))
                return text.strip()
        except Exception as exc:
            logger.warning("Groq model %s failed: %s — trying next", model, exc)
            continue

    logger.warning("All Groq models failed; falling back to heuristic verdict.")
    return None


# ---------------------------------------------------------------------------
# Pre-built prompt helpers for each PRISM engine
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are PRISM, a research intelligence analyst. "
    "Provide concise, evidence-based assessments of scientific research signals. "
    "Be specific, cite data points when available, and keep responses under 3 sentences."
)


def enhance_verdict(
    engine_name: str,
    heuristic_verdict: str,
    heuristic_score: float,
    item_title: str,
    item_abstract: str,
    evidence_points: list[str],
    extra_context: str = "",
) -> tuple[str, list[str]]:
    """Enhance an engine's verdict and evidence using the LLM.

    Returns (enhanced_verdict, enhanced_evidence). If the LLM is
    unavailable, returns the original heuristic values unchanged.
    """
    if not llm_available():
        return heuristic_verdict, evidence_points

    # Truncate abstract to save tokens
    abstract_snippet = (item_abstract or "")[:600]
    evidence_summary = "; ".join(evidence_points[:5])

    user_prompt = (
        f"Engine: {engine_name}\n"
        f"Heuristic Score: {heuristic_score:.2f}\n"
        f"Heuristic Verdict: {heuristic_verdict}\n"
        f"Paper Title: {item_title}\n"
        f"Abstract: {abstract_snippet}\n"
        f"Evidence So Far: {evidence_summary}\n"
    )
    if extra_context:
        user_prompt += f"Additional Context: {extra_context}\n"

    user_prompt += (
        "\nProvide:\n"
        "1. VERDICT: A single-sentence enhanced verdict (more specific than the heuristic).\n"
        "2. INSIGHT: One additional insight the heuristic may have missed.\n"
        "Format your response exactly as:\n"
        "VERDICT: <your verdict>\n"
        "INSIGHT: <your insight>"
    )

    response = ask_llm(SYSTEM_PROMPT, user_prompt)
    if response is None:
        return heuristic_verdict, evidence_points

    # Parse the structured response
    enhanced_verdict = heuristic_verdict
    enhanced_evidence = list(evidence_points)

    for line in response.split("\n"):
        line = line.strip()
        if line.upper().startswith("VERDICT:"):
            enhanced_verdict = line[len("VERDICT:"):].strip()
        elif line.upper().startswith("INSIGHT:"):
            insight = line[len("INSIGHT:"):].strip()
            if insight:
                enhanced_evidence.append(f"[LLM Insight] {insight}")

    return enhanced_verdict, enhanced_evidence
