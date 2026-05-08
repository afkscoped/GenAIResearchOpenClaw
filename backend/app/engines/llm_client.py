"""Groq-first LLM client for PRISM engine enhancement.

The engine path is deliberately resilient:
- Groq is used first when ENABLE_LLM=true and GROQ_API_KEY/LLM_API_KEY is set.
- Ollama is used next through the local llama3 model.
- Heuristic engine verdicts are returned unchanged if both providers fail.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger("prism.engines.llm")

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
    api_key = settings.groq_api_key or settings.llm_api_key
    if not settings.enable_llm or not api_key:
        return None

    try:
        from groq import Groq  # type: ignore[import-untyped]

        _groq_client = Groq(api_key=api_key)
        logger.info("Groq LLM client initialised successfully.")
        return _groq_client
    except ImportError:
        logger.warning("groq package not installed; Groq LLM features disabled.")
        return None
    except Exception as exc:
        logger.warning("Failed to initialise Groq client: %s", exc)
        return None


def _ollama_available() -> bool:
    settings = get_settings()
    if not settings.enable_llm:
        return False
    try:
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def llm_available() -> bool:
    """Check whether any LLM provider is ready."""
    return _get_client() is not None or _ollama_available()


def ask_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 150,
    temperature: float = 0.3,
) -> str | None:
    """Send a prompt to Groq, then Ollama, and return the response text."""
    text, _provider = ask_llm_with_provider(
        system_prompt,
        user_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return text


def ask_llm_with_provider(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 150,
    temperature: float = 0.3,
) -> tuple[str | None, str]:
    """Send a prompt and return response text plus provider name."""
    settings = get_settings()
    client = _get_client()
    if client is not None:
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
                    logger.debug("LLM response from Groq %s (%d chars)", model, len(text))
                    return text.strip(), "groq"
            except Exception as exc:
                logger.warning("Groq model %s failed: %s; trying next", model, exc)

    ollama_text = _ask_ollama(system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature)
    if ollama_text:
        return ollama_text, "ollama"

    logger.warning("All LLM providers failed; falling back to heuristic verdict.")
    return None, "heuristic"


def _ask_ollama(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int,
    temperature: float,
) -> str | None:
    settings = get_settings()
    if not settings.enable_llm:
        return None
    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        text = response.json().get("message", {}).get("content")
        if text:
            logger.info("LLM response from Ollama %s (%d chars)", settings.ollama_model, len(text))
            return text.strip()
    except Exception as exc:
        logger.warning("Ollama fallback failed: %s", exc)
    return None


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
    """Enhance an engine verdict and evidence using the configured LLM stack."""
    if not llm_available():
        return heuristic_verdict, evidence_points

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
        "1. VERDICT: A single-sentence enhanced verdict.\n"
        "2. INSIGHT: One additional insight the heuristic may have missed.\n"
        "Format your response exactly as:\n"
        "VERDICT: <your verdict>\n"
        "INSIGHT: <your insight>"
    )

    response = ask_llm(SYSTEM_PROMPT, user_prompt)
    if response is None:
        return heuristic_verdict, evidence_points

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
