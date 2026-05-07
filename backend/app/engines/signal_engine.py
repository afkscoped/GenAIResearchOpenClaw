from app.db.models import ResearchItem, SourceSignal
from app.engines.llm_client import enhance_verdict
from app.engines.schemas import EngineResult, clamp
from app.engines.utils import log_norm, recency_score, signal_totals


class SignalEngine:
    def score(self, item: ResearchItem, signals: list[SourceSignal]) -> EngineResult:
        totals = signal_totals(signals)
        star_score = log_norm(totals["stars"], 1000)
        fork_score = log_norm(totals["forks"], 200)
        commit_score = log_norm(totals["commits"], 80)
        download_score = log_norm(totals["downloads"], 5000)
        mention_score = log_norm(totals["mentions"], 80)
        recent = recency_score(item)
        source_boost = 0.1 if item.source in {"arxiv", "huggingface", "mock_social"} else 0.0

        score = clamp(
            0.25 * star_score
            + 0.1 * fork_score
            + 0.15 * commit_score
            + 0.2 * download_score
            + 0.15 * mention_score
            + 0.15 * recent
            + source_boost
        )

        evidence = [
            f"Recency score is {recent:.2f} based on the item timestamp.",
            f"Observed {totals['stars']} stars, {totals['forks']} forks, {totals['commits']} commits, {totals['downloads']} downloads, and {totals['mentions']} mentions.",
        ]
        for signal in signals[:3]:
            evidence.extend(signal.evidence[:2])

        if score >= 0.7:
            verdict = "Strong emerging signal with multi-source traction."
        elif score >= 0.4:
            verdict = "Moderate emerging signal worth monitoring."
        else:
            verdict = "Weak early signal; keep as background context."

        verdict, evidence = enhance_verdict(
            engine_name="SignalEngine",
            heuristic_verdict=verdict,
            heuristic_score=score,
            item_title=item.title,
            item_abstract=item.abstract or "",
            evidence_points=evidence,
            extra_context=f"source={item.source}, totals={totals}",
        )

        return EngineResult(score=round(score, 4), verdict=verdict, evidence=evidence, details=totals)

