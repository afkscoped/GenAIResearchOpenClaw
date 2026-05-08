import logging
import time
import re
from datetime import datetime, UTC
from typing import Any

import httpx
from app.ingest.base import IngestionAdapter
from app.core.config import get_settings

logger = logging.getLogger("prism.ingest.arxiv")

class ArxivAdapter(IngestionAdapter):
    source_name = "arxiv"

    def fetch(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        BASE_URL = "https://arxiv.org/search/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
        }
        results = []
        
        for try_number in range(3):
            try:
                params = {
                    "query": query,
                    "searchtype": "all",
                    "source": "header",
                    "size": 50
                }
                logger.debug("📡 Fetching arXiv (fast) try %d for: %s", try_number + 1, query)
                
                # 2. Always set a hard timeout on the request
                response = httpx.get(
                    BASE_URL, 
                    params=params, 
                    headers=headers,
                    timeout=httpx.Timeout(30.0, connect=10.0)
                )
                response.raise_for_status()
                html = response.text
                
                # Regex to find paper blocks
                blocks = re.findall(r'<li class="arxiv-result">.*?</li>', html, re.DOTALL)
                
                for block in blocks:
                    if len(results) >= limit:
                        break
                        
                    # Title
                    title_match = re.search(r'<p class="title is-5 mathjax">\s*(.*?)\s*</p>', block, re.DOTALL)
                    title = title_match.group(1).strip() if title_match else "Unknown Title"
                    
                    # Abstract (contained in <span class="abstract-full">...</span>)
                    abs_match = re.search(r'<span class="abstract-full.*?>(.*?)</span>', block, re.DOTALL)
                    abstract = abs_match.group(1).strip() if abs_match else ""
                    # Clean up "Less" link and search-hit spans
                    abstract = re.sub(r'<a.*?>.*?</a>', '', abstract)
                    abstract = re.sub(r'<span.*?>|</span>', '', abstract).strip()
                    
                    # URL / ID
                    id_match = re.search(r'<a href="https://arxiv.org/abs/(.*?)">', block)
                    paper_id = id_match.group(1) if id_match else ""
                    url = f"https://arxiv.org/abs/{paper_id}" if paper_id else ""
                    
                    # Authors
                    author_block = re.search(r'<p class="authors">.*?</p>', block, re.DOTALL)
                    authors = []
                    if author_block:
                        authors = re.findall(r'<a href="/search/\?searchtype=author.*?"> (.*?)</a>', author_block.group(0))
                    
                    # Date
                    date_match = re.search(r'<span class="has-text-black-bis has-text-weight-semibold">Submitted</span> (.*?);', block)
                    timestamp = datetime.now(UTC)
                    if date_match:
                        try:
                            # Format usually "7 May, 2026"
                            date_str = date_match.group(1).replace(",", "").strip()
                            timestamp = datetime.strptime(date_str, "%d %B %Y").replace(tzinfo=UTC)
                        except Exception as e:
                            logger.debug("Failed to parse date %s: %s", date_match.group(1), e)

                    results.append({
                        "title": title,
                        "abstract": abstract,
                        "source": self.source_name,
                        "url": url,
                        "authors": authors,
                        "organizations": [],
                        "topic": query,
                        "timestamp": timestamp,
                        "metadata": {
                            "paper_id": paper_id,
                        },
                        "signals": [
                            {
                                "source_type": self.source_name,
                                "mentions": 1,
                                "evidence": ["Fetched from arXiv search (fast)"],
                                "raw_payload": {},
                            }
                        ],
                    })
                
                if results:
                    logger.info("arxiv fetch (fast) returned %d results for '%s'", len(results), query)
                    return results
                
            except Exception as exc:
                logger.warning("arxiv try %d failed: %s", try_number, exc)
                if try_number < 2:
                    # 3. Increase retry sleep with exponential backoff
                    sleep_time = 3.0 * (2 ** try_number)
                    logger.info("Retrying in %.1fs...", sleep_time)
                    time.sleep(sleep_time)
        
        return []