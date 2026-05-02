import type { EntityLink, FusionReport, ItemDetail, ResearchItem, SourceSignal } from './client';

export const fallbackItems: ResearchItem[] = [
  {
    id: 'demo-sparse-routing',
    title: 'Sparse Mixture Routing for Efficient Multimodal Agents',
    abstract: 'A new routing method improves multimodal agent efficiency while reducing inference cost on visual reasoning benchmarks.',
    source: 'arxiv',
    url: 'https://arxiv.org/abs/2401.00001',
    authors: ['A. Rao', 'M. Chen'],
    organizations: ['Demo University'],
    topic: 'multimodal agents',
    timestamp: new Date().toISOString(),
    metadata: { code_url: 'https://github.com/demo-lab/sparse-router-agents', benchmark: 'MMMU, ScienceQA' },
  },
  {
    id: 'demo-replication-risk',
    title: 'Conflicting Reports on Sparse Routing Robustness in Multimodal Benchmarks',
    abstract: 'Independent evaluation suggests sparse routing gains shrink under adversarial visual prompts and distribution shift.',
    source: 'arxiv',
    url: 'https://arxiv.org/abs/2401.00002',
    authors: ['Replication Collective'],
    organizations: ['Replication Collective'],
    topic: 'multimodal agents',
    timestamp: new Date().toISOString(),
    metadata: { claim_language: 'contradicts robustness claim' },
  },
  {
    id: 'demo-cross-domain',
    title: 'Graph Neural Solvers for Protein Folding Inspire Supply-Chain Optimization',
    abstract: 'A cross-domain survey argues that graph neural message passing from biology can improve supply-chain resilience planning.',
    source: 'arxiv',
    url: 'https://arxiv.org/abs/2401.00003',
    authors: ['K. Wilson'],
    organizations: ['Systems Lab'],
    topic: 'cross-domain graph learning',
    timestamp: new Date().toISOString(),
    metadata: { source_domain: 'biology', target_domain: 'supply chain', technique: 'graph neural message passing' },
  },
];

export const fallbackReports: FusionReport[] = [
  {
    item_id: 'demo-sparse-routing',
    prism_score: 0.78,
    novelty_score: 0.82,
    trust_score: 0.75,
    controversy_score: 0.35,
    adoption_gap_score: 0.71,
    transferability_score: 0.52,
    verdict: 'High-priority PRISM opportunity: strong signal, usable trust evidence, and clear strategic value.',
    evidence: ['Signal Engine: Strong emerging signal.', 'Trust Engine: Code and benchmark signals detected.', 'Gap Engine: Industry adoption appears behind academic momentum.'],
  },
  {
    item_id: 'demo-replication-risk',
    prism_score: 0.49,
    novelty_score: 0.45,
    trust_score: 0.55,
    controversy_score: 0.82,
    adoption_gap_score: 0.42,
    transferability_score: 0.3,
    verdict: 'Contested opportunity: valuable to track, but claims require careful validation.',
    evidence: ['Debate Engine: replication and distribution shift language detected.', 'Trust Engine: dataset exists but public code is unclear.'],
  },
  {
    item_id: 'demo-cross-domain',
    prism_score: 0.66,
    novelty_score: 0.4,
    trust_score: 0.52,
    controversy_score: 0.18,
    adoption_gap_score: 0.55,
    transferability_score: 0.92,
    verdict: 'Cross-domain spark: promising transfer path detected.',
    evidence: ['Cross-Domain Engine: biology → supply chain transfer path detected.', 'Transferable technique candidate: graph neural message passing.'],
  },
];

const fallbackSignals: SourceSignal[] = [
  { id: 1, item_id: 'demo-sparse-routing', source_type: 'github', stars: 842, forks: 73, commits: 41, model_downloads: 0, mentions: 24, evidence: ['842 GitHub stars', '41 recent commits'], raw_payload: {}, created_at: new Date().toISOString() },
  { id: 2, item_id: 'demo-sparse-routing', source_type: 'huggingface', stars: 0, forks: 0, commits: 0, model_downloads: 1280, mentions: 0, evidence: ['1280 model downloads'], raw_payload: {}, created_at: new Date().toISOString() },
];

const fallbackLinks: EntityLink[] = [
  { id: 1, source_item_id: 'demo-sparse-routing', target_item_id: 'demo-replication-risk', relation_type: 'topic_similarity', confidence: 0.72, evidence: ['Shared topic: multimodal agents'], created_at: new Date().toISOString() },
  { id: 2, source_item_id: 'demo-sparse-routing', target_item_id: 'demo-cross-domain', relation_type: 'topic_similarity', confidence: 0.38, evidence: ['Technique overlap: routing/graph reasoning'], created_at: new Date().toISOString() },
];

export function fallbackDetail(item: ResearchItem): ItemDetail {
  return {
    item,
    signals: fallbackSignals.filter((signal) => signal.item_id === item.id),
    entity_links: fallbackLinks.filter((link) => link.source_item_id === item.id || link.target_item_id === item.id),
  };
}
