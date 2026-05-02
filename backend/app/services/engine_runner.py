"""
engine_runner.py
----------------
Orchestrates every analysis engine for a single ResearchItem, persists the
results as an EngineRun + FusionReportRecord, and returns both ORM objects.

The existing `build_fusion_report()` helper in routes_analysis.py continues
to work untouched (dynamic / non-persisted path).  This service is only
called by the three new /run-engines, /engine-runs, and /fusion-history
endpoints.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import (
    EngineRun,
    EntityLink,
    FusionReportRecord,
    ResearchItem,
    SourceSignal,
)
from app.engines.cross_domain_engine import CrossDomainEngine
from app.engines.debate_engine import DebateEngine
from app.engines.fusion_engine import FusionEngine
from app.engines.gap_engine import GapEngine
from app.engines.signal_engine import SignalEngine
from app.engines.trust_engine import TrustEngine


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _related_context(
    db: Session, item: ResearchItem
) -> tuple[list[ResearchItem], list[EntityLink]]:
    """Re-implement the same context query used by routes_analysis to avoid
    importing from a routes module (keeps the service layer clean)."""
    links = (
        db.query(EntityLink)
        .filter(
            (EntityLink.source_item_id == item.id)
            | (EntityLink.target_item_id == item.id)
        )
        .order_by(EntityLink.confidence.desc())
        .limit(25)
        .all()
    )
    linked_ids: set[str] = set()
    for link in links:
        if link.source_item_id != item.id:
            linked_ids.add(link.source_item_id)
        if link.target_item_id != item.id:
            linked_ids.add(link.target_item_id)

    related_items: list[ResearchItem] = []
    if linked_ids:
        related_items.extend(
            db.query(ResearchItem).filter(ResearchItem.id.in_(linked_ids)).all()
        )

    same_topic = (
        db.query(ResearchItem)
        .filter(ResearchItem.topic == item.topic, ResearchItem.id != item.id)
        .order_by(ResearchItem.timestamp.desc())
        .limit(10)
        .all()
    )
    seen = {r.id for r in related_items}
    for r in same_topic:
        if r.id not in seen:
            related_items.append(r)
            seen.add(r.id)

    return related_items, links


# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------

def run_and_persist_engines(
    db: Session, item: ResearchItem
) -> tuple[EngineRun, FusionReportRecord]:
    """Run all five analysis engines for *item*, persist results to the
    database, and return ``(engine_run, fusion_report_record)``.

    Raises
    ------
    sqlalchemy.exc.SQLAlchemyError
        Propagated to the caller; the session is **not** committed here so
        the route handler controls the transaction boundary.
    """
    signals: list[SourceSignal] = (
        db.query(SourceSignal).filter(SourceSignal.item_id == item.id).all()
    )
    related_items, links = _related_context(db, item)

    # --- run individual engines --------------------------------------------
    signal_result = SignalEngine().score(item, signals)
    trust_result = TrustEngine().score(item, signals)
    debate_result = DebateEngine().score(item, related_items, links)
    gap_result = GapEngine().score(item, signals, related_items)
    cross_domain_result = CrossDomainEngine().score(item, related_items)

    # --- persist EngineRun -------------------------------------------------
    engine_run = EngineRun(
        item_id=item.id,
        signal_score=signal_result.score,
        signal_verdict=signal_result.verdict,
        signal_evidence=signal_result.evidence,
        signal_details=signal_result.details,
        trust_score=trust_result.score,
        trust_verdict=trust_result.verdict,
        trust_evidence=trust_result.evidence,
        trust_details=trust_result.details,
        debate_score=debate_result.score,
        debate_verdict=debate_result.verdict,
        debate_evidence=debate_result.evidence,
        debate_details=debate_result.details,
        gap_score=gap_result.score,
        gap_verdict=gap_result.verdict,
        gap_evidence=gap_result.evidence,
        gap_details=gap_result.details,
        cross_domain_score=cross_domain_result.score,
        cross_domain_verdict=cross_domain_result.verdict,
        cross_domain_evidence=cross_domain_result.evidence,
        cross_domain_details=cross_domain_result.details,
    )
    db.add(engine_run)
    db.flush()  # populate engine_run.id before creating FusionReportRecord

    # --- build fusion scores (same formula as FusionEngine.analyze) --------
    fusion_report_read = FusionEngine().analyze(
        item=item,
        signals=signals,
        related_items=related_items,
        links=links,
    )

    # --- persist FusionReportRecord ----------------------------------------
    fusion_record = FusionReportRecord(
        item_id=item.id,
        engine_run_id=engine_run.id,
        prism_score=fusion_report_read.prism_score,
        novelty_score=fusion_report_read.novelty_score,
        trust_score=fusion_report_read.trust_score,
        controversy_score=fusion_report_read.controversy_score,
        adoption_gap_score=fusion_report_read.adoption_gap_score,
        transferability_score=fusion_report_read.transferability_score,
        verdict=fusion_report_read.verdict,
        evidence=fusion_report_read.evidence,
    )
    db.add(fusion_record)
    # caller commits

    return engine_run, fusion_record
