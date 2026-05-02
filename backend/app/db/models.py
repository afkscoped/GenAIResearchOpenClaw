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
