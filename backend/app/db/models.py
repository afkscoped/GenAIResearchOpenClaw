from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ResearchItem(Base):
    __tablename__ = "research_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    abstract: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(50), index=True)
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    authors: Mapped[list[str]] = mapped_column(JSON, default=list)
    organizations: Mapped[list[str]] = mapped_column(JSON, default=list)
    topic: Mapped[str] = mapped_column(String(200), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    extra_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    signals: Mapped[list["SourceSignal"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    memories: Mapped[list["MemoryDocument"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    engine_runs: Mapped[list["EngineRun"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    fusion_reports: Mapped[list["FusionReportRecord"]] = relationship(back_populates="item", cascade="all, delete-orphan")


class SourceSignal(Base):
    __tablename__ = "source_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("research_items.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(50), index=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    commits: Mapped[int] = mapped_column(Integer, default=0)
    model_downloads: Mapped[int] = mapped_column(Integer, default=0)
    mentions: Mapped[int] = mapped_column(Integer, default=0)
    evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    item: Mapped[ResearchItem] = relationship(back_populates="signals")


class EntityLink(Base):
    __tablename__ = "entity_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_item_id: Mapped[str] = mapped_column(String, index=True)
    target_item_id: Mapped[str] = mapped_column(String, index=True)
    relation_type: Mapped[str] = mapped_column(String(100), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MemoryDocument(Base):
    __tablename__ = "memory_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("research_items.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(JSON, default=list)
    token_signature: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    item: Mapped[ResearchItem] = relationship(back_populates="memories")


class EngineRun(Base):
    __tablename__ = "engine_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("research_items.id"), index=True)
    signal_score: Mapped[float] = mapped_column(Float, default=0.0)
    signal_verdict: Mapped[str] = mapped_column(String(500), default="")
    signal_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    signal_details: Mapped[dict] = mapped_column(JSON, default=dict)
    
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    trust_verdict: Mapped[str] = mapped_column(String(500), default="")
    trust_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    trust_details: Mapped[dict] = mapped_column(JSON, default=dict)
    
    debate_score: Mapped[float] = mapped_column(Float, default=0.0)
    debate_verdict: Mapped[str] = mapped_column(String(500), default="")
    debate_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    debate_details: Mapped[dict] = mapped_column(JSON, default=dict)
    
    gap_score: Mapped[float] = mapped_column(Float, default=0.0)
    gap_verdict: Mapped[str] = mapped_column(String(500), default="")
    gap_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    gap_details: Mapped[dict] = mapped_column(JSON, default=dict)
    
    cross_domain_score: Mapped[float] = mapped_column(Float, default=0.0)
    cross_domain_verdict: Mapped[str] = mapped_column(String(500), default="")
    cross_domain_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    cross_domain_details: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    item: Mapped[ResearchItem] = relationship(back_populates="engine_runs")


class FusionReportRecord(Base):
    __tablename__ = "fusion_report_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("research_items.id"), index=True)
    engine_run_id: Mapped[int] = mapped_column(ForeignKey("engine_runs.id"), index=True)
    prism_score: Mapped[float] = mapped_column(Float)
    novelty_score: Mapped[float] = mapped_column(Float)
    trust_score: Mapped[float] = mapped_column(Float)
    controversy_score: Mapped[float] = mapped_column(Float)
    adoption_gap_score: Mapped[float] = mapped_column(Float)
    transferability_score: Mapped[float] = mapped_column(Float)
    verdict: Mapped[str] = mapped_column(String(500))
    evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    item: Mapped[ResearchItem] = relationship(back_populates="fusion_reports")


class UserPersonaRecord(Base):
    __tablename__ = "user_personas"

    user_id: Mapped[str] = mapped_column(String(200), primary_key=True, index=True)
    liked_topics: Mapped[dict] = mapped_column(JSON, default=dict)
    liked_sources: Mapped[dict] = mapped_column(JSON, default=dict)
    min_trust_threshold: Mapped[float] = mapped_column(Float, default=0.4)
    favourite_paper_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    interaction_history: Mapped[list[dict]] = mapped_column(JSON, default=list)
    domain_weights: Mapped[dict] = mapped_column(JSON, default=dict)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class PaperRating(Base):
    __tablename__ = "paper_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("research_items.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(200), index=True)
    rating: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    is_favourite: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class AgentRunRecord(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    query: Mapped[str] = mapped_column(String(500), index=True)
    user_id: Mapped[str] = mapped_column(String(200), index=True, default="default")
    mode: Mapped[str] = mapped_column(String(50), index=True, default="auto")
    intent: Mapped[str] = mapped_column(String(50), index=True, default="discover")
    llm_provider: Mapped[str] = mapped_column(String(50), default="heuristic")
    status: Mapped[str] = mapped_column(String(50), default="ok")
    final_answer: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list)
    timings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
