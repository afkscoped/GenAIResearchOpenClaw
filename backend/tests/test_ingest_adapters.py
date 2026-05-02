from __future__ import annotations

import unittest
from unittest.mock import patch

from app.ingest.crossref_adapter import CrossrefAdapter
from app.ingest.engineering_blog_adapter import EngineeringBlogAdapter
from app.ingest.mock_social_adapter import MockProductLaunchAdapter
from app.ingest.normalizer import normalize_raw_item
from app.ingest.papers_with_code_adapter import PapersWithCodeAdapter
from app.ingest.semantic_scholar_adapter import SemanticScholarAdapter


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class IngestAdapterTests(unittest.TestCase):
    @patch("app.ingest.semantic_scholar_adapter.requests.get")
    def test_semantic_scholar_adapter_returns_normalizable_items(self, mock_get) -> None:
        mock_get.return_value = DummyResponse(
            {
                "data": [
                    {
                        "paperId": "s2-1",
                        "title": "Reliable Evaluation for Multimodal Agents",
                        "abstract": "Evaluation details.",
                        "url": "https://www.semanticscholar.org/paper/s2-1",
                        "authors": [{"name": "Ada Lovelace"}],
                        "publicationDate": "2025-01-12",
                        "citationCount": 17,
                        "venue": "Semantic Scholar Venue",
                        "openAccessPdf": {"url": "https://example.com/eval.pdf"},
                    }
                ]
            }
        )

        items = SemanticScholarAdapter().fetch("multimodal agents", limit=2)
        self.assertEqual(len(items), 1)
        normalized = normalize_raw_item(items[0])
        self.assertEqual(normalized.source, "semantic_scholar")
        self.assertTrue(any("Semantic Scholar" in evidence for evidence in normalized.signals[0].evidence))

    @patch("app.ingest.crossref_adapter.requests.get")
    def test_crossref_adapter_returns_normalizable_items(self, mock_get) -> None:
        mock_get.return_value = DummyResponse(
            {
                "message": {
                    "items": [
                        {
                            "title": ["Crossref Evaluation Benchmarks"],
                            "abstract": "Crossref abstract",
                            "DOI": "10.1000/demo",
                            "published-online": {"date-parts": [[2024, 7, 8]]},
                            "author": [{"given": "Grace", "family": "Hopper", "affiliation": [{"name": "Navy"}]}],
                            "container-title": ["Journal of Demo Research"],
                            "publisher": "Crossref Publisher",
                            "type": "journal-article",
                            "is-referenced-by-count": 8,
                        }
                    ]
                }
            }
        )

        items = CrossrefAdapter().fetch("evaluation", limit=1)
        self.assertEqual(len(items), 1)
        normalized = normalize_raw_item(items[0])
        self.assertEqual(normalized.source, "crossref")
        self.assertEqual(normalized.metadata["doi"], "10.1000/demo")

    @patch("app.ingest.papers_with_code_adapter.requests.get")
    def test_papers_with_code_adapter_returns_normalizable_items(self, mock_get) -> None:
        mock_get.return_value = DummyResponse(
            {
                "results": [
                    {
                        "id": "pwc-1",
                        "title": "Agents With Benchmarks",
                        "abstract": "PWC abstract",
                        "url_abs": "https://paperswithcode.com/paper/demo",
                        "url_code": "https://github.com/demo/repo",
                        "published": "2025-02-01T00:00:00Z",
                        "tasks": ["Vision-Language Navigation"],
                        "repository_count": 4,
                        "authors": [{"name": "Katherine Johnson"}],
                    }
                ]
            }
        )

        items = PapersWithCodeAdapter("https://paperswithcode.com/api/v1/papers/").fetch("agents", limit=1)
        self.assertEqual(len(items), 1)
        normalized = normalize_raw_item(items[0])
        self.assertEqual(normalized.source, "papers_with_code")
        self.assertEqual(normalized.metadata["code_url"], "https://github.com/demo/repo")

    @patch("app.ingest.engineering_blog_adapter.feedparser.parse")
    def test_engineering_blog_adapter_returns_normalizable_items(self, mock_parse) -> None:
        mock_parse.return_value = type(
            "Feed",
            (),
            {
                "entries": [
                    {
                        "title": "Engineering multimodal agent safeguards",
                        "summary": "This post covers evaluation and deployment.",
                        "link": "https://example.com/blog/agent-safeguards",
                        "author": "Engineering Team",
                        "published_parsed": (2025, 3, 4, 10, 0, 0, 0, 0, 0),
                    }
                ],
                "feed": {"title": "Example Engineering"},
            },
        )()

        items = EngineeringBlogAdapter(["https://example.com/feed"]).fetch("multimodal agents", limit=2)
        self.assertEqual(len(items), 1)
        normalized = normalize_raw_item(items[0])
        self.assertEqual(normalized.source, "engineering_blog")
        self.assertIn("Example Engineering", normalized.organizations)

    def test_mock_product_launch_adapter_returns_demo_items(self) -> None:
        items = MockProductLaunchAdapter().fetch("evaluation", limit=2)
        self.assertGreaterEqual(len(items), 1)
        normalized = normalize_raw_item(items[0])
        self.assertEqual(normalized.source, "product_launch")
        self.assertTrue(any("Product Hunt style" in evidence or "product launch" in evidence.lower() for evidence in normalized.signals[0].evidence))

    @patch("app.ingest.semantic_scholar_adapter.requests.get", side_effect=RuntimeError("boom"))
    @patch("app.ingest.crossref_adapter.requests.get", side_effect=RuntimeError("boom"))
    @patch("app.ingest.papers_with_code_adapter.requests.get", side_effect=RuntimeError("boom"))
    @patch("app.ingest.engineering_blog_adapter.feedparser.parse", side_effect=RuntimeError("boom"))
    def test_adapters_fail_safely(
        self,
        _mock_blog,
        _mock_pwc,
        _mock_crossref,
        _mock_semantic,
    ) -> None:
        self.assertEqual(SemanticScholarAdapter().fetch("agents"), [])
        self.assertEqual(CrossrefAdapter().fetch("agents"), [])
        self.assertEqual(PapersWithCodeAdapter("https://paperswithcode.com/api/v1/papers/").fetch("agents"), [])
        self.assertEqual(EngineeringBlogAdapter(["https://example.com/feed"]).fetch("agents"), [])


if __name__ == "__main__":
    unittest.main()
