export type ResearchItem = {
  id: string;
  title: string;
  abstract: string;
  source: 'arxiv' | 'github' | 'huggingface' | 'news' | 'mock_social' | 'mock_jobs' | 'semantic_scholar' | 'crossref' | 'papers_with_code' | 'product_launch' | 'engineering_blog';
  url: string;
  authors: string[];
  organizations: string[];
  topic: string;
  timestamp: string;
  metadata: Record<string, unknown>;
  created_at?: string;
};

export type SourceSignal = {
  id: number;
  item_id: string;
  source_type: string;
  stars: number;
  forks: number;
  commits: number;
  model_downloads: number;
  mentions: number;
  evidence: string[];
  raw_payload: Record<string, unknown>;
  created_at: string;
};

export type EntityLink = {
  id: number;
  source_item_id: string;
  target_item_id: string;
  relation_type: string;
  confidence: number;
  evidence: string[];
  created_at: string;
};

export type FusionReport = {
  item_id: string;
  prism_score: number;
  novelty_score: number;
  trust_score: number;
  controversy_score: number;
  adoption_gap_score: number;
  transferability_score: number;
  verdict: string;
  evidence: string[];
};

export type EngineRun = {
  id: number;
  item_id: string;
  signal_score: number;
  signal_verdict: string;
  trust_score: number;
  trust_verdict: string;
  debate_score: number;
  debate_verdict: string;
  gap_score: number;
  gap_verdict: string;
  cross_domain_score: number;
  cross_domain_verdict: string;
  created_at: string;
};

export type ItemDetail = {
  item: ResearchItem;
  signals: SourceSignal[];
  entity_links: EntityLink[];
};

export type PipelineRunResponse = {
  ingested_items: number;
  stored_items: number;
  stored_signals: number;
  entity_links: number;
  memory_documents: number;
  sources: string[];
  item_ids: string[];
};

export type MemorySearchResult = {
  item_id: string;
  title: string;
  topic: string;
  url: string;
  score: number;
  matched_terms: string[];
};

export type AgentAlertDecision = {
  route: 'alert' | 'daily_digest' | 'weekly_brief' | 'ignored_memory_update';
  reason: string;
  decided_at: string;
  signal: FusionReport & {
    title: string;
    topic: string;
    source: string;
    url: string;
  };
};

export type AgentAlertsResponse = {
  alerts: AgentAlertDecision[];
  decisions: AgentAlertDecision[];
  deliveries: Array<Record<string, unknown>>;
};

export type OpenClawStatus = {
  enable_openclaw: boolean;
  openclaw_url: string;
  has_discord_webhook: boolean;
  has_llm_key: boolean;
  credentials_configured: Record<string, boolean>;
};

export type UserPersona = {
  user_id: string;
  liked_topics: Record<string, number>;
  liked_sources: Record<string, number>;
  min_trust_threshold: number;
  favourite_paper_ids: string[];
  interaction_history: Array<Record<string, unknown>>;
  domain_weights: Record<string, number>;
  last_updated: string;
};

export type Suggestion = {
  item_id: string;
  title: string;
  topic: string;
  source: string;
  url: string;
  prism_score: number;
  personalised_score: number;
  reason: string;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  runPipeline: (query = 'multimodal agents', includeDemo = false) =>
    request<PipelineRunResponse>(`/api/run-pipeline?query=${encodeURIComponent(query)}&include_demo=${includeDemo ? 'true' : 'false'}`, { method: 'POST' }),
  listItems: (query?: string) => request<ResearchItem[]>(`/api/items?limit=100${query ? `&q=${encodeURIComponent(query)}` : ''}`),
  getItem: (id: string) => request<ItemDetail>(`/api/items/${id}`),
  listFusionReports: (query?: string, refresh = false) =>
    request<FusionReport[]>(`/api/analysis/fusion-reports?limit=100&refresh=${refresh ? 'true' : 'false'}${query ? `&q=${encodeURIComponent(query)}` : ''}`),
  getFusionReport: (id: string) => request<FusionReport>(`/api/analysis/fusion-reports/${id}`),
  listEngineRuns: (id: string) => request<EngineRun[]>(`/api/analysis/engine-runs/${id}?limit=20`),
  searchMemory: (query: string) => request<MemorySearchResult[]>(`/api/memory/search?q=${encodeURIComponent(query)}&limit=8`),
  listLinks: () => request<EntityLink[]>('/api/memory/links?limit=100'),
  listAgentAlerts: () => request<AgentAlertsResponse>('/api/agent/alerts'),
  openClawStatus: () => request<OpenClawStatus>('/api/openclaw/status'),
  getPersona: (userId = 'default') => request<UserPersona>(`/api/persona/${encodeURIComponent(userId)}`),
  getSuggestions: (userId = 'default', query?: string) =>
    query
      ? request<Suggestion[]>(`/api/persona/${encodeURIComponent(userId)}/suggest/search?q=${encodeURIComponent(query)}&limit=10`)
      : request<Suggestion[]>(`/api/persona/${encodeURIComponent(userId)}/suggest?limit=10`),
  sendFeedback: (userId: string, itemId: string, action: 'liked' | 'starred' | 'dismissed' | 'shared' | 'viewed') =>
    request<UserPersona>(`/api/persona/${encodeURIComponent(userId)}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId, action }),
    }),
  weeklyReportUrl: () => `${API_BASE}/api/reports/weekly.md`,
};
