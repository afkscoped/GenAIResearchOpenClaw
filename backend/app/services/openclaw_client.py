from __future__ import annotations

from app.agent.openclaw_client import OpenClawResult, analyze


def refine_with_openclaw(title: str, abstract: str, scores: dict[str, float]) -> OpenClawResult:
    return analyze(title=title, abstract=abstract, scores=scores)


__all__ = ["OpenClawResult", "refine_with_openclaw"]
