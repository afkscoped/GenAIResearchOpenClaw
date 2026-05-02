from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import EntityLink, ResearchItem, SourceSignal
from app.ingest.arxiv_adapter import ArxivAdapter
from app.ingest.crossref_adapter import CrossrefAdapter
from app.ingest.engineering_blog_adapter import EngineeringBlogAdapter
from app.ingest.github_adapter import GitHubAdapter
from app.ingest.huggingface_adapter import HuggingFaceAdapter
from app.ingest.mock_social_adapter import MockJobsAdapter, MockProductLaunchAdapter, MockSocialAdapter
from app.ingest.news_adapter import NewsAdapter
from app.ingest.papers_with_code_adapter import PapersWithCodeAdapter
from app.ingest.semantic_scholar_adapter import SemanticScholarAdapter
from app.ingest.normalizer import normalize_many
from app.ingest.seed_data import demo_raw_items
from app.memory.entity_linker import EntityLinker
from app.memory.vector_store import LocalVectorMemory
from app.schemas.research import NormalizedItem, PipelineRunResponse


class IngestionPipeline:
    def __init__(self) -> None:
        settings = get_settings()
        self.adapters = [
            ArxivAdapter(),
            SemanticScholarAdapter(),
            CrossrefAdapter(settings.crossref_mailto),
            GitHubAdapter(settings.github_token),
            HuggingFaceAdapter(settings.huggingface_token),
            PapersWithCodeAdapter(settings.papers_with_code_api_url),
            NewsAdapter(settings.rss_feed_list),
            EngineeringBlogAdapter(settings.engineering_blog_feed_list),
            MockSocialAdapter(),
            MockJobsAdapter(),
            MockProductLaunchAdapter(),
        ]
        self.linker = EntityLinker()
        self.memory = LocalVectorMemory()

    def run(self, db: Session, query: str = "multimodal agents", limit_per_source: int = 5, include_demo: bool = True) -> PipelineRunResponse:
        raw_items = demo_raw_items() if include_demo else []
        sources = {item["source"] for item in raw_items}
        for adapter in self.adapters:
            fetched = adapter.fetch(query=query, limit=limit_per_source)
            raw_items.extend(fetched)
            if fetched:
                sources.add(adapter.source_name)

        normalized_items = normalize_many(raw_items)
        stored_items, stored_signals = self._store_items(db, normalized_items)
        entity_links = self._store_links(db, self.linker.link_items(normalized_items))
        memory_documents = self.memory.index_items(db, normalized_items)

        return PipelineRunResponse(
            ingested_items=len(normalized_items),
            stored_items=stored_items,
            stored_signals=stored_signals,
            entity_links=entity_links,
            memory_documents=memory_documents,
            sources=sorted(sources),
        )

    def _store_items(self, db: Session, items: list[NormalizedItem]) -> tuple[int, int]:
        stored_items = 0
        stored_signals = 0
        for item in items:
            existing = db.get(ResearchItem, item.id)
            if existing is None:
                db.add(
                    ResearchItem(
                        id=item.id,
                        title=item.title,
                        abstract=item.abstract,
                        source=item.source,
                        url=item.url,
                        authors=item.authors,
                        organizations=item.organizations,
                        topic=item.topic,
                        timestamp=item.timestamp,
                        extra_metadata=item.metadata,
                    )
                )
                stored_items += 1
            for signal in item.signals:
                signal_exists = (
                    db.query(SourceSignal)
                    .filter(SourceSignal.item_id == item.id, SourceSignal.source_type == signal.source_type)
                    .first()
                )
                if signal_exists:
                    continue
                db.add(
                    SourceSignal(
                        item_id=item.id,
                        source_type=signal.source_type,
                        stars=signal.stars,
                        forks=signal.forks,
                        commits=signal.commits,
                        model_downloads=signal.model_downloads,
                        mentions=signal.mentions,
                        evidence=signal.evidence,
                        raw_payload=signal.raw_payload,
                    )
                )
                stored_signals += 1
        db.commit()
        return stored_items, stored_signals

    def _store_links(self, db: Session, candidates: list) -> int:
        stored = 0
        for candidate in candidates:
            exists = (
                db.query(EntityLink)
                .filter(
                    EntityLink.source_item_id == candidate.source_item_id,
                    EntityLink.target_item_id == candidate.target_item_id,
                    EntityLink.relation_type == candidate.relation_type,
                )
                .first()
            )
            if exists:
                continue
            db.add(
                EntityLink(
                    source_item_id=candidate.source_item_id,
                    target_item_id=candidate.target_item_id,
                    relation_type=candidate.relation_type,
                    confidence=candidate.confidence,
                    evidence=candidate.evidence,
                )
            )
            stored += 1
        db.commit()
        return stored
