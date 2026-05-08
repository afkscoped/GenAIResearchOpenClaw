import logging
import asyncio
from app.ingest.arxiv_adapter import ArxivAdapter

logging.basicConfig(level=logging.DEBUG)

adapter = ArxivAdapter()
results = adapter.fetch("diffusion models", limit=2)
for r in results:
    print(f"Title: {r['title']}")
    print(f"URL: {r['url']}")
    print("-" * 20)
