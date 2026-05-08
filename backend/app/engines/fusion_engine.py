from app.db.models import EntityLink, ResearchItem, SourceSignal
from app.engines.cross_domain_engine import CrossDomainEngine
from app.engines.debate_engine import DebateEngine
from app.engines.gap_engine import GapEngine
from app.engines.schemas import EngineResult, clamp
from app.engines.signal_engine import SignalEngine
from app.engines.trust_engine import TrustEngine
from app.schemas.research import FusionReportRead


class FusionEngine:
    def __init__(self) -> None:
        self.signal_engine = SignalEngine()
        self.trust_engine = TrustEngine()
        self.debate_engine = DebateEngine()
        self.gap_engine = GapEngine()
        self.cross_domain_engine = CrossDomainEngine()

    def analyze(
        self,
        item: ResearchItem,
        signals: list[SourceSignal],
        related_items: list[ResearchItem],
        links: list[EntityLink],
    ) -> FusionReportRead:
        signal = self.signal_engine.score(item, signals)
        trust = self.trust_engine.score(item, signals)
        debate = self.debate_engine.score(item, related_items, links)
        gap = self.gap_engine.score(item, signals, related_items)
        cross_domain = self.cross_domain_engine.score(item, related_items)

        prism_score = clamp(
            0.25 * signal.score
            + 0.25 * trust.score
            + 0.15 * (1 - debate.score)
            + 0.20 * gap.score
            + 0.15 * cross_domain.score
        )

        verdict = self._verdict(prism_score, signal, trust, debate, gap, cross_domain)
        evidence = self._evidence(signal, trust, debate, gap, cross_domain)

        return FusionReportRead(
            item_id=item.id,
            prism_score=round(prism_score, 4),
            novelty_score=signal.score,
            trust_score=trust.score,
            controversy_score=debate.score,
            adoption_gap_score=gap.score,
            transferability_score=cross_domain.score,
            verdict=verdict,
            evidence=evidence,
            cross_domain_details=cross_domain.details,
        )

    def _verdict(
        self,
        prism_score: float,
        signal: EngineResult,
        trust: EngineResult,
        debate: EngineResult,
        gap: EngineResult,
        cross_domain: EngineResult,
    ) -> str:
        if prism_score >= 0.72 and trust.score >= 0.55:
            return "High-priority PRISM opportunity: strong signal, usable trust evidence, and clear strategic value."
        if debate.score >= 0.7:
            return "Contested opportunity: valuable to track, but claims require careful validation."
        if gap.score >= 0.7:
            return "Adoption-gap opportunity: academia appears ahead of industry implementation."
        if cross_domain.score >= 0.7:
            return "Cross-domain spark: promising transfer path detected."
        if prism_score >= 0.45:
            return "Watchlist candidate: enough signal to monitor in the next research brief."
        return "Low-priority item for now: keep in memory but do not escalate."

    def _evidence(
        self,
        signal: EngineResult,
        trust: EngineResult,
        debate: EngineResult,
        gap: EngineResult,
        cross_domain: EngineResult,
    ) -> list[str]:
        grouped = [
            f"Signal Engine: {signal.verdict}",
            f"Trust Engine: {trust.verdict}",
            f"Debate Engine: {debate.verdict}",
            f"Gap Engine: {gap.verdict}",
            f"Cross-Domain Engine: {cross_domain.verdict}",
        ]
        details: list[str] = []
        for result in [signal, trust, debate, gap, cross_domain]:
            details.extend(result.evidence[:3])
        return grouped + details[:12]
