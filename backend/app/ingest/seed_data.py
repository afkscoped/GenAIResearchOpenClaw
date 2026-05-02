from datetime import UTC, datetime, timedelta


def demo_raw_items() -> list[dict]:
    now = datetime.now(UTC)
    return [
        {
            "title": "Sparse Mixture Routing for Efficient Multimodal Agents",
            "abstract": "A new routing method improves multimodal agent efficiency while reducing inference cost on visual reasoning benchmarks.",
            "source": "arxiv",
            "url": "https://arxiv.org/abs/2401.00001",
            "authors": ["A. Rao", "M. Chen"],
            "organizations": ["Demo University"],
            "topic": "multimodal agents",
            "timestamp": now - timedelta(days=2),
            "metadata": {
                "code_url": "https://github.com/demo-lab/sparse-router-agents",
                "dataset_url": "https://huggingface.co/datasets/demo/mm-routing-bench",
                "benchmark": "MMMU, ScienceQA",
                "paper_id": "2401.00001",
            },
            "signals": [
                {
                    "source_type": "arxiv",
                    "stars": 0,
                    "forks": 0,
                    "commits": 0,
                    "model_downloads": 0,
                    "mentions": 6,
                    "evidence": ["Recent arXiv upload", "Multiple researcher mentions in seeded social data"],
                    "raw_payload": {"category": "cs.AI"},
                }
            ],
        },
        {
            "title": "demo-lab/sparse-router-agents",
            "abstract": "Reference implementation for sparse routing in multimodal agents with examples and benchmark scripts.",
            "source": "github",
            "url": "https://github.com/demo-lab/sparse-router-agents",
            "authors": ["demo-lab"],
            "organizations": ["Demo University"],
            "topic": "multimodal agents",
            "timestamp": now - timedelta(days=1),
            "metadata": {
                "language": "Python",
                "license": "MIT",
                "linked_paper_title": "Sparse Mixture Routing for Efficient Multimodal Agents",
            },
            "signals": [
                {
                    "source_type": "github",
                    "stars": 842,
                    "forks": 73,
                    "commits": 41,
                    "model_downloads": 0,
                    "mentions": 0,
                    "evidence": ["842 stars", "41 recent commits", "MIT license available"],
                    "raw_payload": {"open_issues": 12},
                }
            ],
        },
        {
            "title": "demo/sparse-router-mm-agent",
            "abstract": "Multimodal sparse-router checkpoint uploaded before formal publication.",
            "source": "huggingface",
            "url": "https://huggingface.co/demo/sparse-router-mm-agent",
            "authors": ["demo"],
            "organizations": ["Demo University"],
            "topic": "multimodal agents",
            "timestamp": now - timedelta(hours=18),
            "metadata": {
                "model_type": "vision-language",
                "license": "apache-2.0",
                "linked_repo": "https://github.com/demo-lab/sparse-router-agents",
            },
            "signals": [
                {
                    "source_type": "huggingface",
                    "stars": 0,
                    "forks": 0,
                    "commits": 0,
                    "model_downloads": 1280,
                    "mentions": 0,
                    "evidence": ["1280 seeded model downloads", "Checkpoint appeared before related publication"],
                    "raw_payload": {"pipeline_tag": "image-text-to-text"},
                }
            ],
        },
        {
            "title": "Conflicting Reports on Sparse Routing Robustness in Multimodal Benchmarks",
            "abstract": "Independent evaluation suggests sparse routing gains shrink under adversarial visual prompts and distribution shift.",
            "source": "arxiv",
            "url": "https://arxiv.org/abs/2401.00002",
            "authors": ["L. Singh", "P. Gomez"],
            "organizations": ["Replication Collective"],
            "topic": "multimodal agents",
            "timestamp": now - timedelta(days=4),
            "metadata": {
                "code_url": "",
                "dataset_url": "https://huggingface.co/datasets/demo/robust-mm-eval",
                "benchmark": "RobustMM",
                "claim_language": "contradicts efficiency and robustness claim",
            },
            "signals": [
                {
                    "source_type": "arxiv",
                    "stars": 0,
                    "forks": 0,
                    "commits": 0,
                    "model_downloads": 0,
                    "mentions": 3,
                    "evidence": ["Independent replication paper", "Flags distribution-shift weakness"],
                    "raw_payload": {"category": "cs.LG"},
                }
            ],
        },
        {
            "title": "Hospitals Explore Multimodal Agents but Delay Production Deployment",
            "abstract": "Healthcare AI teams are testing multimodal reasoning systems, but compliance and evaluation gaps slow adoption.",
            "source": "news",
            "url": "https://example.com/news/hospital-multimodal-agent-adoption",
            "authors": ["PRISM Demo News"],
            "organizations": ["Example Health Systems"],
            "topic": "healthcare ai adoption",
            "timestamp": now - timedelta(days=3),
            "metadata": {
                "industry": "healthcare",
                "adoption_signal": "pilot only",
                "related_topic": "multimodal agents",
            },
            "signals": [
                {
                    "source_type": "news",
                    "stars": 0,
                    "forks": 0,
                    "commits": 0,
                    "model_downloads": 0,
                    "mentions": 9,
                    "evidence": ["Industry pilot signal", "No broad deployment yet"],
                    "raw_payload": {"publisher": "Example News"},
                }
            ],
        },
        {
            "title": "Researcher teaser: sparse routing results before conference deadline",
            "abstract": "Seeded social signal mentioning strong early results and a coming paper about sparse multimodal routing.",
            "source": "mock_social",
            "url": "https://example.com/social/sparse-routing-teaser",
            "authors": ["@demo_researcher"],
            "organizations": ["Demo University"],
            "topic": "multimodal agents",
            "timestamp": now - timedelta(hours=10),
            "metadata": {
                "platform": "mock_twitter_x",
                "engagement": 430,
                "related_repo": "https://github.com/demo-lab/sparse-router-agents",
            },
            "signals": [
                {
                    "source_type": "mock_social",
                    "stars": 0,
                    "forks": 0,
                    "commits": 0,
                    "model_downloads": 0,
                    "mentions": 24,
                    "evidence": ["Seeded researcher teaser", "High mock engagement"],
                    "raw_payload": {"likes": 390, "reposts": 40},
                }
            ],
        },
        {
            "title": "Job trend: companies request multimodal agent evaluation skills",
            "abstract": "Mock job data shows rising demand for evaluation engineers who can test multimodal AI agents.",
            "source": "mock_jobs",
            "url": "https://example.com/jobs/multimodal-agent-eval-trend",
            "authors": ["PRISM Demo Jobs"],
            "organizations": ["Example AI Employers"],
            "topic": "multimodal agents",
            "timestamp": now - timedelta(days=5),
            "metadata": {
                "job_count": 18,
                "skills": ["multimodal evaluation", "LLM agents", "benchmarking"],
                "related_topic": "multimodal agents",
            },
            "signals": [
                {
                    "source_type": "mock_jobs",
                    "stars": 0,
                    "forks": 0,
                    "commits": 0,
                    "model_downloads": 0,
                    "mentions": 18,
                    "evidence": ["18 seeded job posts mention multimodal agent evaluation"],
                    "raw_payload": {"job_count": 18},
                }
            ],
        },
        {
            "title": "Graph Neural Solvers for Protein Folding Inspire Supply-Chain Optimization",
            "abstract": "A cross-domain survey argues that graph neural message passing from biology can improve supply-chain resilience planning.",
            "source": "arxiv",
            "url": "https://arxiv.org/abs/2401.00003",
            "authors": ["K. Wilson", "S. Ito"],
            "organizations": ["Systems Lab"],
            "topic": "cross-domain graph learning",
            "timestamp": now - timedelta(days=6),
            "metadata": {
                "source_domain": "biology",
                "target_domain": "supply chain",
                "technique": "graph neural message passing",
            },
            "signals": [
                {
                    "source_type": "arxiv",
                    "stars": 0,
                    "forks": 0,
                    "commits": 0,
                    "model_downloads": 0,
                    "mentions": 4,
                    "evidence": ["Technique transfer candidate from biology to operations"],
                    "raw_payload": {"category": "cs.LG"},
                }
            ],
        },
    ]
