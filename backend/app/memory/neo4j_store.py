from __future__ import annotations

from typing import Any

from app.core.config import get_settings


class Neo4jStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.driver: Any = None
        if self.settings.enable_neo4j and self.settings.neo4j_password:
            self._connect()

    def _connect(self) -> None:
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )
        except Exception:
            self.driver = None

    @property
    def available(self) -> bool:
        return self.driver is not None

    def upsert_item(self, item: Any) -> bool:
        if not self.available:
            return False
        with self.driver.session() as session:
            session.run(
                """
                MERGE (p:Paper {id: $id})
                SET p.title=$title, p.source=$source, p.topic=$topic, p.url=$url
                """,
                id=item.id,
                title=item.title,
                source=item.source,
                topic=item.topic,
                url=item.url,
            )
        return True

    def upsert_link(self, source_id: str, target_id: str, relation: str, confidence: float) -> bool:
        if not self.available:
            return False
        with self.driver.session() as session:
            session.run(
                """
                MATCH (a:Paper {id:$src}), (b:Paper {id:$tgt})
                MERGE (a)-[r:RELATES {type:$rel}]->(b)
                SET r.confidence=$conf
                """,
                src=source_id,
                tgt=target_id,
                rel=relation,
                conf=confidence,
            )
        return True

    def find_related(self, item_id: str, depth: int = 2, limit: int = 20) -> list[dict[str, Any]]:
        if not self.available:
            return []
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Paper {id:$id})-[*1..2]-(related)
                RETURN related LIMIT $limit
                """,
                id=item_id,
                limit=limit,
            )
            return [dict(record["related"]) for record in result]
