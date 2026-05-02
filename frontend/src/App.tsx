import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Atom,
  Bell,
  BrainCircuit,
  Command,
  Download,
  FlaskConical,
  GitBranch,
  Globe2,
  Layers3,
  Loader2,
  Network,
  Orbit,
  Radar as RadarIcon,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Swords,
  Telescope,
  TrendingUp,
  X,
  Zap,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  api,
  type AgentAlertsResponse,
  type EngineRun,
  type FusionReport,
  type ItemDetail,
  type MemorySearchResult,
  type ResearchItem,
} from './api/client';
import {
  fallbackAgentAlerts,
  fallbackDetail,
  fallbackEngineRuns,
  fallbackItems,
  fallbackMemoryResults,
  fallbackReports,
} from './api/fallback';
import { EngineCard } from './components/EngineCard';
import { EvidencePanel } from './components/EvidencePanel';
import { ScoreOrb } from './components/ScoreOrb';
import { SignalConstellation } from './components/SignalConstellation';

type ViewKey = 'command' | 'topics' | 'battle' | 'atlas' | 'radar' | 'history' | 'alerts';

const sourceColors = ['#22d3ee', '#a78bfa', '#fb7185', '#f59e0b', '#34d399', '#60a5fa'];

const views: Array<{ key: ViewKey; label: string; icon: typeof Activity }> = [
  { key: 'command', label: 'Command', icon: Activity },
  { key: 'topics', label: 'Topics', icon: Telescope },
  { key: 'battle', label: 'Battle', icon: Swords },
  { key: 'atlas', label: 'Gap Atlas', icon: Layers3 },
  { key: 'radar', label: 'X-Domain', icon: RadarIcon },
  { key: 'history', label: 'History', icon: TrendingUp },
  { key: 'alerts', label: 'Alerts', icon: Bell },
];

function byReport(items: ResearchItem[], reports: FusionReport[]) {
  return items
    .map((item) => ({ item, report: reports.find((report) => report.item_id === item.id) }))
    .sort((left, right) => (right.report?.prism_score ?? 0) - (left.report?.prism_score ?? 0));
}

function scoreLabel(score: number) {
  if (score >= 0.75) return 'critical';
  if (score >= 0.55) return 'rising';
  if (score >= 0.35) return 'watch';
  return 'quiet';
}

function sourceChart(items: ResearchItem[]) {
  const counts = items.reduce<Record<string, number>>((acc, item) => {
    acc[item.source] = (acc[item.source] ?? 0) + 1;
    return acc;
  }, {});
  return Object.entries(counts).map(([name, value]) => ({ name: name.replace('_', ' '), value }));
}

function engineTimeline(reports: FusionReport[]) {
  return reports.slice(0, 8).map((report, index) => ({
    name: `S${index + 1}`,
    novelty: Math.round(report.novelty_score * 100),
    trust: Math.round(report.trust_score * 100),
    gap: Math.round(report.adoption_gap_score * 100),
  }));
}

function topicData(items: ResearchItem[], reports: FusionReport[]) {
  const grouped = items.reduce<Record<string, { topic: string; count: number; score: number; trust: number; gap: number }>>((acc, item) => {
    const report = reports.find((entry) => entry.item_id === item.id);
    const current = acc[item.topic] ?? { topic: item.topic, count: 0, score: 0, trust: 0, gap: 0 };
    current.count += 1;
    current.score += report?.prism_score ?? 0;
    current.trust += report?.trust_score ?? 0;
    current.gap += report?.adoption_gap_score ?? 0;
    acc[item.topic] = current;
    return acc;
  }, {});

  return Object.values(grouped)
    .map((entry) => ({
      ...entry,
      score: Math.round((entry.score / entry.count) * 100),
      trust: Math.round((entry.trust / entry.count) * 100),
      gap: Math.round((entry.gap / entry.count) * 100),
    }))
    .sort((left, right) => right.score - left.score);
}

function reportFor(item: ResearchItem, reports: FusionReport[]) {
  return reports.find((report) => report.item_id === item.id) ?? fallbackReports[0];
}

function App() {
  const [items, setItems] = useState<ResearchItem[]>(fallbackItems);
  const [reports, setReports] = useState<FusionReport[]>(fallbackReports);
  const [selectedId, setSelectedId] = useState(fallbackItems[0].id);
  const [detail, setDetail] = useState<ItemDetail>(fallbackDetail(fallbackItems[0]));
  const [history, setHistory] = useState<EngineRun[]>(fallbackEngineRuns);
  const [alerts, setAlerts] = useState<AgentAlertsResponse>(fallbackAgentAlerts);
  const [memoryResults, setMemoryResults] = useState<MemorySearchResult[]>(fallbackMemoryResults);
  const [loading, setLoading] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notice, setNotice] = useState('Demo fallback loaded. Run the backend pipeline to switch to live PRISM memory.');
  const [query, setQuery] = useState('multimodal agents');
  const [activeView, setActiveView] = useState<ViewKey>('command');

  const ranked = useMemo(() => byReport(items, reports), [items, reports]);
  const selected = ranked.find((entry) => entry.item.id === selectedId) ?? ranked[0];
  const selectedReport = selected?.report ?? reports[0];
  const topReport = ranked[0]?.report ?? reports[0];
  const sourceData = useMemo(() => sourceChart(items), [items]);
  const timelineData = useMemo(() => engineTimeline(reports), [reports]);
  const topics = useMemo(() => topicData(items, reports), [items, reports]);

  async function loadLiveData() {
    setLoading(true);
    try {
      const [nextItems, nextReports, nextAlerts] = await Promise.all([
        api.listItems(),
        api.listFusionReports(),
        api.listAgentAlerts().catch(() => fallbackAgentAlerts),
      ]);
      if (nextItems.length > 0) {
        setItems(nextItems);
        setReports(nextReports.length > 0 ? nextReports : fallbackReports);
        setSelectedId(nextItems[0].id);
        setAlerts(nextAlerts);
        setNotice('Live backend data loaded from PRISM memory.');
      } else {
        setNotice('Backend is reachable but has no data yet. Run the pipeline.');
      }
    } catch (error) {
      setItems(fallbackItems);
      setReports(fallbackReports);
      setSelectedId(fallbackItems[0].id);
      setAlerts(fallbackAgentAlerts);
      setNotice('Backend unavailable. Showing offline demo constellation.');
    } finally {
      setLoading(false);
    }
  }

  async function runPipeline() {
    setLoading(true);
    try {
      const result = await api.runPipeline(query);
      setNotice(`Pipeline complete: ${result.ingested_items} ingested, ${result.stored_items} new items, ${result.entity_links} links.`);
      await loadLiveData();
    } catch (error) {
      setNotice('Could not run backend pipeline. Keep using fallback mode or start FastAPI.');
      setLoading(false);
    }
  }

  async function searchMemory(nextQuery = query) {
    setQuery(nextQuery);
    try {
      const results = await api.searchMemory(nextQuery);
      setMemoryResults(results.length > 0 ? results : fallbackMemoryResults);
    } catch (error) {
      setMemoryResults(fallbackMemoryResults);
    }
  }

  useEffect(() => {
    loadLiveData();
  }, []);

  useEffect(() => {
    const item = items.find((entry) => entry.id === selectedId);
    if (!item) return;
    api
      .getItem(item.id)
      .then(setDetail)
      .catch(() => setDetail(fallbackDetail(item)));
    api
      .listEngineRuns(item.id)
      .then((runs) => setHistory(runs.length > 0 ? runs : fallbackEngineRuns))
      .catch(() => setHistory(fallbackEngineRuns));
  }, [selectedId, items]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setPaletteOpen((open) => !open);
      }
      if (event.key === 'Escape') setPaletteOpen(false);
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const shellProps = {
    items,
    reports,
    ranked,
    selected,
    selectedReport,
    topReport,
    sourceData,
    timelineData,
    detail,
    topics,
    history,
    alerts,
    setSelectedId,
    setActiveView,
  };

  return (
    <main className="min-h-screen overflow-hidden px-4 py-6 md:px-8 lg:px-10">
      <div className="pointer-events-none fixed inset-0 prism-grid opacity-30" />
      <div className="relative mx-auto max-w-7xl">
        <NavBar
          activeView={activeView}
          loading={loading}
          query={query}
          setActiveView={setActiveView}
          setPaletteOpen={setPaletteOpen}
          setQuery={setQuery}
          runPipeline={runPipeline}
        />

        {activeView === 'command' && <CommandCenter notice={notice} {...shellProps} />}
        {activeView === 'topics' && <TopicExplorer topics={topics} ranked={ranked} setSelectedId={setSelectedId} setActiveView={setActiveView} />}
        {activeView === 'battle' && <ContradictionBattle ranked={ranked} />}
        {activeView === 'atlas' && <AdoptionGapAtlas ranked={ranked} topics={topics} />}
        {activeView === 'radar' && <CrossDomainRadar ranked={ranked} />}
        {activeView === 'history' && <EngineHistoryChart history={history} selectedTitle={selected?.item.title ?? 'Selected item'} />}
        {activeView === 'alerts' && <AlertCenter alerts={alerts} />}

        <Footer />
      </div>
      {paletteOpen && (
        <MemoryPalette
          query={query}
          results={memoryResults}
          setQuery={setQuery}
          close={() => setPaletteOpen(false)}
          searchMemory={searchMemory}
          setSelectedId={setSelectedId}
          setActiveView={setActiveView}
        />
      )}
    </main>
  );
}

function NavBar({
  activeView,
  loading,
  query,
  setActiveView,
  setPaletteOpen,
  setQuery,
  runPipeline,
}: {
  activeView: ViewKey;
  loading: boolean;
  query: string;
  setActiveView: (view: ViewKey) => void;
  setPaletteOpen: (open: boolean) => void;
  setQuery: (query: string) => void;
  runPipeline: () => void;
}) {
  return (
    <nav className="mb-8 rounded-[2rem] border border-white/10 bg-slate-950/60 p-4 shadow-prism backdrop-blur-xl">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-4">
          <div className="relative grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-cyan-300 via-violet-400 to-fuchsia-500 text-slate-950 shadow-prism">
            <Orbit size={28} />
            <div className="absolute -right-1 -top-1 h-4 w-4 rounded-full bg-emerald-300 shadow-[0_0_24px_#34d399]" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.42em] text-cyan-300">PRISM</p>
            <h1 className="text-2xl font-black tracking-tight text-white md:text-3xl">Research Intelligence Command Center</h1>
          </div>
        </div>
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <button onClick={() => setPaletteOpen(true)} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-bold text-white transition hover:bg-white/10">
            <Command size={16} />
            Memory
          </button>
          <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3">
            <Search size={16} className="text-slate-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500 md:w-52"
              placeholder="research query"
            />
          </div>
          <button onClick={runPipeline} className="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-black text-slate-950 transition hover:bg-cyan-200">
            {loading ? <Loader2 className="animate-spin" size={16} /> : <RefreshCw size={16} />}
            Run PRISM
          </button>
          <a href={api.weeklyReportUrl()} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/10">
            <Download size={16} />
            Brief
          </a>
        </div>
      </div>
      <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
        {views.map((view) => {
          const Icon = view.icon;
          return (
            <button
              key={view.key}
              onClick={() => setActiveView(view.key)}
              className={`inline-flex shrink-0 items-center gap-2 rounded-2xl px-4 py-2 text-xs font-black uppercase tracking-[0.16em] transition ${
                activeView === view.key ? 'bg-cyan-300 text-slate-950' : 'border border-white/10 bg-white/[0.04] text-slate-300 hover:bg-white/10'
              }`}
            >
              <Icon size={14} />
              {view.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function CommandCenter({
  notice,
  items,
  ranked,
  selected,
  selectedReport,
  topReport,
  sourceData,
  timelineData,
  detail,
  setSelectedId,
}: any) {
  return (
    <>
      <section className="mb-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="glass relative overflow-hidden rounded-[2.2rem] p-7 md:p-9">
          <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-cyan-400/20 blur-3xl" />
          <div className="absolute -bottom-24 left-1/2 h-72 w-72 rounded-full bg-fuchsia-500/20 blur-3xl" />
          <div className="relative z-10 grid gap-8 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.28em] text-cyan-200">
                <Activity size={14} /> always-on agent loop
              </div>
              <h2 className="max-w-3xl text-4xl font-black leading-tight text-white md:text-6xl">
                Detect what will matter before it becomes obvious.
              </h2>
              <p className="mt-5 max-w-2xl text-base leading-8 text-slate-300">
                PRISM fuses early source signals, replication risk, debate clusters, adoption gaps, and cross-domain sparks into one explainable intelligence stream.
              </p>
              <div className="mt-6 rounded-3xl border border-white/10 bg-slate-950/50 p-4 text-sm text-slate-300">
                <span className="font-bold text-cyan-200">Status:</span> {notice}
              </div>
            </div>
            <ScoreOrb label="PRISM priority" score={topReport?.prism_score ?? 0} tone="violet" size="lg" />
          </div>
        </div>
        <SignalConstellation items={items} />
      </section>

      <section className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <EngineCard title="Signal" subtitle="pre-publication traction" score={selectedReport?.novelty_score ?? 0} icon={Zap} gradient="from-cyan-300 to-blue-600" />
        <EngineCard title="Trust" subtitle="replication readiness" score={selectedReport?.trust_score ?? 0} icon={ShieldCheck} gradient="from-emerald-300 to-teal-600" />
        <EngineCard title="Debate" subtitle="claim conflict pressure" score={selectedReport?.controversy_score ?? 0} icon={FlaskConical} gradient="from-rose-300 to-pink-600" />
        <EngineCard title="Gap Map" subtitle="industry lag index" score={selectedReport?.adoption_gap_score ?? 0} icon={Layers3} gradient="from-amber-200 to-orange-600" />
        <EngineCard title="X-Domain" subtitle="transfer opportunity" score={selectedReport?.transferability_score ?? 0} icon={RadarIcon} gradient="from-violet-300 to-fuchsia-600" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-6">
          <RankedQueue ranked={ranked} selectedId={selected?.item.id} setSelectedId={setSelectedId} />
          <SourceMix sourceData={sourceData} />
        </div>
        <div className="space-y-6">
          {selected && selectedReport && <DetailPanel selected={selected} selectedReport={selectedReport} />}
          <div className="grid gap-6 lg:grid-cols-2">
            <EvidencePanel title="explainability trace" evidence={selectedReport?.evidence ?? []} />
            <EntityLinks detail={detail} />
          </div>
          <EngineTrend timelineData={timelineData} />
        </div>
      </section>
    </>
  );
}

function RankedQueue({ ranked, selectedId, setSelectedId }: any) {
  return (
    <div className="glass rounded-[2rem] p-5">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-cyan-300">ranked opportunities</p>
          <h2 className="mt-2 text-2xl font-black text-white">PRISM queue</h2>
        </div>
        <Telescope className="text-cyan-200" />
      </div>
      <div className="space-y-3">
        {ranked.map(({ item, report }: { item: ResearchItem; report?: FusionReport }) => (
          <button
            key={item.id}
            onClick={() => setSelectedId(item.id)}
            className={`w-full rounded-3xl border p-4 text-left transition hover:-translate-y-0.5 ${selectedId === item.id ? 'border-cyan-300/60 bg-cyan-300/10' : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.06]'}`}
          >
            <div className="mb-3 flex items-start justify-between gap-3">
              <h3 className="line-clamp-2 text-sm font-bold text-white">{item.title}</h3>
              <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-black text-cyan-100">{Math.round((report?.prism_score ?? 0) * 100)}</span>
            </div>
            <div className="flex flex-wrap gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
              <span className="rounded-full bg-slate-900 px-2 py-1">{item.source.replace('_', ' ')}</span>
              <span className="rounded-full bg-slate-900 px-2 py-1">{scoreLabel(report?.prism_score ?? 0)}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function SourceMix({ sourceData }: { sourceData: Array<{ name: string; value: number }> }) {
  return (
    <div className="glass rounded-[2rem] p-5">
      <p className="text-xs font-bold uppercase tracking-[0.28em] text-cyan-300">source mix</p>
      <div className="mt-5 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sourceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.16)" />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
            <YAxis stroke="#94a3b8" fontSize={11} />
            <Tooltip contentStyle={{ background: '#020617', border: '1px solid rgba(148,163,184,.25)', borderRadius: 16 }} />
            <Bar dataKey="value" radius={[12, 12, 4, 4]}>
              {sourceData.map((entry, index) => <Cell key={entry.name} fill={sourceColors[index % sourceColors.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function DetailPanel({ selected, selectedReport }: any) {
  return (
    <section className="glass overflow-hidden rounded-[2rem] p-6">
      <div className="mb-5 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="mb-3 flex flex-wrap gap-2">
            <span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.2em] text-cyan-200">{selected.item.source.replace('_', ' ')}</span>
            <span className="rounded-full bg-violet-300/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.2em] text-violet-200">{selected.item.topic}</span>
          </div>
          <h2 className="text-3xl font-black leading-tight text-white">{selected.item.title}</h2>
          <p className="mt-4 text-sm leading-7 text-slate-300">{selected.item.abstract}</p>
        </div>
        <a href={selected.item.url} target="_blank" rel="noreferrer" className="inline-flex shrink-0 items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-bold text-white hover:bg-white/10">
          Source <ArrowUpRight size={16} />
        </a>
      </div>
      <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-5">
        <div className="mb-2 flex items-center gap-3 text-cyan-200">
          <BrainCircuit size={20} />
          <span className="text-xs font-bold uppercase tracking-[0.28em]">fusion verdict</span>
        </div>
        <p className="text-lg font-bold text-white">{selectedReport.verdict}</p>
      </div>
    </section>
  );
}

function EntityLinks({ detail }: { detail: ItemDetail }) {
  return (
    <section className="glass rounded-3xl p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="rounded-2xl bg-violet-400/10 p-2 text-violet-300">
          <Network size={18} />
        </div>
        <h3 className="text-sm font-bold uppercase tracking-[0.24em] text-slate-300">linked intelligence</h3>
      </div>
      <div className="space-y-3">
        {detail.entity_links.length === 0 && <p className="text-sm text-slate-400">No entity links in fallback detail for this item yet.</p>}
        {detail.entity_links.map((link) => (
          <div key={link.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-bold text-white">{link.relation_type.replace('_', ' ')}</span>
              <span className="text-xs font-black text-cyan-200">{Math.round(link.confidence * 100)}%</span>
            </div>
            <p className="mt-2 text-xs text-slate-400">{link.evidence.join(' / ')}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function EngineTrend({ timelineData }: { timelineData: Array<Record<string, number | string>> }) {
  return (
    <section className="glass rounded-[2rem] p-5">
      <div className="mb-5 flex items-center gap-3">
        <Globe2 className="text-cyan-200" />
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-cyan-300">opportunity atlas</p>
          <h3 className="text-xl font-black text-white">engine trend contours</h3>
        </div>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={timelineData}>
            <defs>
              <linearGradient id="novelty" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#22d3ee" stopOpacity={0.55}/><stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/></linearGradient>
              <linearGradient id="trust" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#34d399" stopOpacity={0.45}/><stop offset="95%" stopColor="#34d399" stopOpacity={0}/></linearGradient>
              <linearGradient id="gap" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#f59e0b" stopOpacity={0.45}/><stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/></linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
            <YAxis stroke="#94a3b8" fontSize={11} />
            <Tooltip contentStyle={{ background: '#020617', border: '1px solid rgba(148,163,184,.25)', borderRadius: 16 }} />
            <Area type="monotone" dataKey="novelty" stroke="#22d3ee" fill="url(#novelty)" strokeWidth={3} />
            <Area type="monotone" dataKey="trust" stroke="#34d399" fill="url(#trust)" strokeWidth={3} />
            <Area type="monotone" dataKey="gap" stroke="#f59e0b" fill="url(#gap)" strokeWidth={3} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function TopicExplorer({ topics, ranked, setSelectedId, setActiveView }: any) {
  return (
    <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
      <Panel eyebrow="topic explorer" title="Research terrain by monitored theme" icon={Telescope}>
        <div className="space-y-3">
          {topics.map((topic: any) => (
            <div key={topic.topic} className="rounded-3xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-black text-white">{topic.topic}</h3>
                  <p className="text-sm text-slate-400">{topic.count} signals captured</p>
                </div>
                <span className="text-2xl font-black text-cyan-200">{topic.score}</span>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-xs font-bold text-slate-300">
                <Metric label="trust" value={topic.trust} />
                <Metric label="gap" value={topic.gap} />
                <Metric label="priority" value={topic.score} />
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel eyebrow="evidence-first queue" title="Top signals inside the topic map" icon={Sparkles}>
        <div className="grid gap-3 md:grid-cols-2">
          {ranked.map(({ item, report }: any) => (
            <button
              key={item.id}
              onClick={() => {
                setSelectedId(item.id);
                setActiveView('command');
              }}
              className="rounded-3xl border border-white/10 bg-slate-950/50 p-4 text-left transition hover:border-cyan-300/50 hover:bg-cyan-300/10"
            >
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">{item.topic}</p>
              <h3 className="mt-2 line-clamp-2 text-base font-black text-white">{item.title}</h3>
              <p className="mt-3 text-sm text-slate-400">{report?.evidence?.[0] ?? 'Fallback evidence available.'}</p>
            </button>
          ))}
        </div>
      </Panel>
    </section>
  );
}

function ContradictionBattle({ ranked }: any) {
  const contenders = ranked
    .filter(({ report }: any) => (report?.controversy_score ?? 0) > 0.2)
    .slice(0, 6);

  return (
    <Panel eyebrow="contradiction battle" title="Where claims are most contested" icon={Swords}>
      <div className="grid gap-4 lg:grid-cols-2">
        {contenders.map(({ item, report }: any, index: number) => (
          <div key={item.id} className="rounded-3xl border border-rose-300/20 bg-rose-300/[0.05] p-5">
            <div className="mb-4 flex items-center justify-between">
              <span className="rounded-full bg-rose-300/10 px-3 py-1 text-xs font-black uppercase tracking-[0.18em] text-rose-200">claim {index + 1}</span>
              <span className="text-2xl font-black text-rose-200">{Math.round((report?.controversy_score ?? 0) * 100)}</span>
            </div>
            <h3 className="text-xl font-black text-white">{item.title}</h3>
            <p className="mt-3 text-sm leading-6 text-slate-300">{item.abstract}</p>
            <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/60 p-4">
              <p className="text-xs font-bold uppercase tracking-[0.22em] text-cyan-300">debate evidence</p>
              <p className="mt-2 text-sm text-slate-300">{report?.evidence?.find((entry: string) => entry.toLowerCase().includes('debate')) ?? report?.evidence?.[0] ?? 'No contradiction evidence returned yet.'}</p>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function AdoptionGapAtlas({ ranked, topics }: any) {
  const scatter = ranked.map(({ item, report }: any) => ({
    name: item.title.slice(0, 28),
    x: Math.round((report?.trust_score ?? 0) * 100),
    y: Math.round((report?.adoption_gap_score ?? 0) * 100),
    z: Math.round((report?.prism_score ?? 0) * 100),
    topic: item.topic,
  }));

  return (
    <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <Panel eyebrow="adoption gap atlas" title="High-trust research that industry has not absorbed" icon={Layers3}>
        <div className="h-[28rem]">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.16)" />
              <XAxis dataKey="x" name="trust" stroke="#94a3b8" fontSize={11} />
              <YAxis dataKey="y" name="gap" stroke="#94a3b8" fontSize={11} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ background: '#020617', border: '1px solid rgba(148,163,184,.25)', borderRadius: 16 }} />
              <Scatter data={scatter} fill="#22d3ee" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </Panel>
      <Panel eyebrow="gap clusters" title="Topic pressure summary" icon={AlertTriangle}>
        <div className="space-y-3">
          {topics.map((topic: any) => (
            <div key={topic.topic} className="rounded-3xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex justify-between gap-3">
                <span className="font-black text-white">{topic.topic}</span>
                <span className="font-black text-amber-200">{topic.gap}</span>
              </div>
              <div className="mt-3 h-2 rounded-full bg-slate-800">
                <div className="h-2 rounded-full bg-gradient-to-r from-amber-300 to-fuchsia-400" style={{ width: `${topic.gap}%` }} />
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </section>
  );
}

function CrossDomainRadar({ ranked }: any) {
  const radarData = ranked.slice(0, 6).map(({ item, report }: any) => ({
    topic: item.topic.slice(0, 16),
    transfer: Math.round((report?.transferability_score ?? 0) * 100),
    novelty: Math.round((report?.novelty_score ?? 0) * 100),
  }));

  return (
    <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <Panel eyebrow="cross-domain radar" title="Transfer paths with strategic upside" icon={RadarIcon}>
        <div className="h-[30rem]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(148,163,184,0.22)" />
              <PolarAngleAxis dataKey="topic" stroke="#cbd5e1" fontSize={11} />
              <Radar name="transfer" dataKey="transfer" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.28} />
              <Radar name="novelty" dataKey="novelty" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.18} />
              <Tooltip contentStyle={{ background: '#020617', border: '1px solid rgba(148,163,184,.25)', borderRadius: 16 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </Panel>
      <Panel eyebrow="transfer evidence" title="Cross-domain candidates" icon={GitBranch}>
        <div className="space-y-3">
          {ranked
            .filter(({ report }: any) => (report?.transferability_score ?? 0) > 0.35)
            .map(({ item, report }: any) => (
              <div key={item.id} className="rounded-3xl border border-violet-300/20 bg-violet-300/[0.05] p-4">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-black text-white">{item.title}</h3>
                  <span className="text-xl font-black text-violet-200">{Math.round((report?.transferability_score ?? 0) * 100)}</span>
                </div>
                <p className="mt-2 text-sm text-slate-300">{report?.evidence?.find((entry: string) => entry.toLowerCase().includes('cross')) ?? report?.verdict}</p>
              </div>
            ))}
        </div>
      </Panel>
    </section>
  );
}

function EngineHistoryChart({ history, selectedTitle }: { history: EngineRun[]; selectedTitle: string }) {
  const data = history
    .slice()
    .reverse()
    .map((run, index) => ({
      name: `R${index + 1}`,
      signal: Math.round(run.signal_score * 100),
      trust: Math.round(run.trust_score * 100),
      debate: Math.round(run.debate_score * 100),
      gap: Math.round(run.gap_score * 100),
      cross: Math.round(run.cross_domain_score * 100),
    }));

  return (
    <Panel eyebrow="engine history" title={selectedTitle} icon={TrendingUp}>
      <div className="h-[30rem]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
            <YAxis stroke="#94a3b8" fontSize={11} />
            <Tooltip contentStyle={{ background: '#020617', border: '1px solid rgba(148,163,184,.25)', borderRadius: 16 }} />
            <Area type="monotone" dataKey="signal" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.12} strokeWidth={3} />
            <Area type="monotone" dataKey="trust" stroke="#34d399" fill="#34d399" fillOpacity={0.1} strokeWidth={3} />
            <Area type="monotone" dataKey="debate" stroke="#fb7185" fill="#fb7185" fillOpacity={0.1} strokeWidth={3} />
            <Area type="monotone" dataKey="gap" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.1} strokeWidth={3} />
            <Area type="monotone" dataKey="cross" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.1} strokeWidth={3} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-4 text-sm text-slate-400">Falls back to demo history when `/api/analysis/engine-runs/{'{item_id}'}` is unavailable.</p>
    </Panel>
  );
}

function AlertCenter({ alerts }: { alerts: AgentAlertsResponse }) {
  const rows = alerts.decisions.length > 0 ? alerts.decisions : alerts.alerts;
  return (
    <Panel eyebrow="alert center" title="OpenClaw-style routing decisions" icon={Bell}>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <Metric label="alerts" value={alerts.alerts.length} />
        <Metric label="decisions" value={alerts.decisions.length} />
        <Metric label="deliveries" value={alerts.deliveries.length} />
      </div>
      <div className="space-y-3">
        {rows.map((decision, index) => (
          <div key={`${decision.signal.item_id}-${index}`} className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <span className={`rounded-full px-3 py-1 text-xs font-black uppercase tracking-[0.18em] ${decision.route === 'alert' ? 'bg-rose-300/15 text-rose-200' : 'bg-cyan-300/10 text-cyan-200'}`}>
                {decision.route.replace('_', ' ')}
              </span>
              <span className="text-xs font-bold text-slate-400">{decision.reason.replace(/_/g, ' ')}</span>
            </div>
            <h3 className="text-xl font-black text-white">{decision.signal.title}</h3>
            <p className="mt-2 text-sm text-slate-300">{decision.signal.verdict}</p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
              <span className="rounded-full bg-slate-900 px-2 py-1">{decision.signal.topic}</span>
              <span className="rounded-full bg-slate-900 px-2 py-1">{Math.round(decision.signal.prism_score * 100)} priority</span>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function MemoryPalette({
  query,
  results,
  setQuery,
  close,
  searchMemory,
  setSelectedId,
  setActiveView,
}: {
  query: string;
  results: MemorySearchResult[];
  setQuery: (query: string) => void;
  close: () => void;
  searchMemory: (query: string) => void;
  setSelectedId: (id: string) => void;
  setActiveView: (view: ViewKey) => void;
}) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-start bg-slate-950/80 px-4 py-20 backdrop-blur-xl md:place-items-center md:py-0">
      <div className="w-full max-w-3xl overflow-hidden rounded-[2rem] border border-cyan-300/20 bg-slate-950 shadow-prism">
        <div className="flex items-center gap-3 border-b border-white/10 px-5 py-4">
          <Search className="text-cyan-300" size={20} />
          <input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') searchMemory(query);
            }}
            className="flex-1 bg-transparent text-lg font-bold text-white outline-none placeholder:text-slate-500"
            placeholder="Search PRISM memory..."
          />
          <button onClick={close} className="rounded-xl border border-white/10 p-2 text-slate-300 hover:bg-white/10">
            <X size={18} />
          </button>
        </div>
        <div className="max-h-[28rem] overflow-y-auto p-4">
          {results.map((result) => (
            <button
              key={result.item_id}
              onClick={() => {
                setSelectedId(result.item_id);
                setActiveView('command');
                close();
              }}
              className="mb-3 w-full rounded-3xl border border-white/10 bg-white/[0.03] p-4 text-left hover:border-cyan-300/50 hover:bg-cyan-300/10"
            >
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-black text-white">{result.title}</h3>
                <span className="font-black text-cyan-200">{Math.round(result.score * 100)}</span>
              </div>
              <p className="mt-2 text-sm text-slate-400">{result.topic} / {result.matched_terms.join(', ')}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Panel({ eyebrow, title, icon: Icon, children }: { eyebrow: string; title: string; icon: typeof Activity; children: React.ReactNode }) {
  return (
    <section className="glass rounded-[2rem] p-6">
      <div className="mb-6 flex items-center gap-3">
        <div className="rounded-2xl bg-cyan-300/10 p-2 text-cyan-200">
          <Icon size={20} />
        </div>
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.28em] text-cyan-300">{eyebrow}</p>
          <h2 className="mt-1 text-2xl font-black text-white">{title}</h2>
        </div>
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-3">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-black text-white">{value}</p>
    </div>
  );
}

function Footer() {
  return (
    <footer className="mt-10 grid gap-4 rounded-[2rem] border border-white/10 bg-slate-950/50 p-5 text-sm text-slate-400 md:grid-cols-3">
      <div className="flex items-center gap-3"><Sparkles className="text-cyan-300" /> Early detection tells you what is about to matter.</div>
      <div className="flex items-center gap-3"><Atom className="text-violet-300" /> Fusion reasoning turns fragmented signals into decisions.</div>
      <div className="flex items-center gap-3"><GitBranch className="text-emerald-300" /> Modular engines make PRISM easy to extend.</div>
    </footer>
  );
}

export default App;
