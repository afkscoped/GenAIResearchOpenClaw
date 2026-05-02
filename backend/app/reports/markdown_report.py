from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import EntityLink, ResearchItem, SourceSignal


def generate_weekly_brief(db: Session) -> str:
    items = db.query(ResearchItem).order_by(ResearchItem.timestamp.desc()).limit(25).all()
    links = db.query(EntityLink).order_by(EntityLink.confidence.desc()).limit(20).all()
    signals = db.query(SourceSignal).all()
    signals_by_item: dict[str, list[SourceSignal]] = defaultdict(list)
    for signal in signals:
        signals_by_item[signal.item_id].append(signal)

    lines = [
        "# PRISM Weekly Research Intelligence Brief",
        "",
        f"Generated: {datetime.utcnow().isoformat()}Z",
        "",
        "## Executive Summary",
        "",
        f"PRISM currently tracks {len(items)} recent research and innovation signals across papers, repositories, models, news, social mock data, and job mock data.",
        "",
        "## Tracked Signals",
        "",
    ]

    for item in items:
        total_stars = sum(signal.stars for signal in signals_by_item[item.id])
        total_mentions = sum(signal.mentions for signal in signals_by_item[item.id])
        total_downloads = sum(signal.model_downloads for signal in signals_by_item[item.id])
        lines.extend(
            [
                f"### {item.title}",
                "",
                f"- Source: `{item.source}`",
                f"- Topic: `{item.topic}`",
                f"- URL: {item.url}",
                f"- Signal summary: {total_stars} stars, {total_downloads} model downloads, {total_mentions} mentions",
                f"- Abstract: {item.abstract[:450]}",
                "",
            ]
        )

    lines.extend(["## Entity Links", ""])
    for link in links:
        evidence = "; ".join(link.evidence)
        lines.append(
            f"- `{link.relation_type}`: {link.source_item_id} ↔ {link.target_item_id} "
            f"(confidence {link.confidence:.2f}) — {evidence}"
        )

    lines.extend(
        [
            "",
            "## Next Integration Points",
            "",
            "- Intelligence engines should consume `/api/items`, `/api/items/{item_id}`, and database records.",
            "- Frontend should call `/api/run-pipeline`, `/api/items`, `/api/memory/search`, and `/api/reports/weekly.md`.",
            "- Fusion scoring should add final PRISM verdicts once Teammate 3 implements engine outputs.",
        ]
    )
    return "\n".join(lines)
