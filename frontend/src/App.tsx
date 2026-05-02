import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowUpRight,
  Atom,
  BrainCircuit,
  Download,
  FlaskConical,
  GitBranch,
  Globe2,
  Layers3,
  Loader2,
  Network,
  Orbit,
  Radar,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Telescope,
  Zap,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api, type FusionReport, type ItemDetail, type ResearchItem } from './api/client';
import { fallbackDetail, fallbackItems, fallbackReports } from './api/fallback';
import { EngineCard } from './components/EngineCard';
import { EvidencePanel } from './components/EvidencePanel';
import { ScoreOrb } from './components/ScoreOrb';
import { SignalConstellation } from './components/SignalConstellation';

const sourceColors = ['#22d3ee', '#a78bfa', '#fb7185', '#f59e0b', '#34d399', '#60a5fa'];

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

function App() {
  const [items, setItems] = useState<ResearchItem[]>(fallbackItems);
  const [reports, setReports] = useState<FusionReport[]>(fallbackReports);
  const [selectedId, setSelectedId] = useState(fallbackItems[0].id);
  const [detail, setDetail] = useState<ItemDetail>(fallbackDetail(fallbackItems[0]));
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState('Demo fallback loaded. Run the backend pipeline to switch to live PRISM memory.');
  const [query, setQuery] = useState('multimodal agents');

  const ranked = useMemo(() => byReport(items, reports), [items, reports]);
  const selected = ranked.find((entry) => entry.item.id === selectedId) ?? ranked[0];
  const selectedReport = selected?.report ?? reports[0];
  const topReport = ranked[0]?.report ?? reports[0];
  const sourceData = useMemo(() => sourceChart(items), [items]);
  const timelineData = useMemo(() => engineTimeline(reports), [reports]);

  async function loadLiveData() {
    setLoading(true);
    try {
      const [nextItems, nextReports] = await Promise.all([api.listItems(), api.listFusionReports()]);
      if (nextItems.length > 0) {
        setItems(nextItems);
        setReports(nextReports.length > 0 ? nextReports : fallbackReports);
        setSelectedId(nextItems[0].id);
        setNotice('Live backend data loaded from PRISM memory.');
      } else {
        setNotice('Backend is reachable but has no data yet. Run the pipeline.');
      }
    } catch (error) {
      setItems(fallbackItems);
      setReports(fallbackReports);
      setSelectedId(fallbackItems[0].id);
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
  }, [selectedId, items]);

  return (
    <main className="min-h-screen overflow-hidden px-4 py-6 md:px-8 lg:px-10">
      <div className="pointer-events-none fixed inset-0 prism-grid opacity-30" />
      <div className="relative mx-auto max-w-7xl">
        <nav className="mb-8 flex flex-col gap-4 rounded-[2rem] border border-white/10 bg-slate-950/60 p-4 shadow-prism backdrop-blur-xl md:flex-row md:items-center md:justify-between">
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
        </nav>

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
          <EngineCard title="X-Domain" subtitle="transfer opportunity" score={selectedReport?.transferability_score ?? 0} icon={Radar} gradient="from-violet-300 to-fuchsia-600" />
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="space-y-6">
            <div className="glass rounded-[2rem] p-5">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.28em] text-cyan-300">ranked opportunities</p>
                  <h2 className="mt-2 text-2xl font-black text-white">PRISM queue</h2>
                </div>
                <Telescope className="text-cyan-200" />
              </div>
              <div className="space-y-3">
                {ranked.map(({ item, report }) => (
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
          </div>

          <div className="space-y-6">
            {selected && selectedReport && (
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
            )}

            <div className="grid gap-6 lg:grid-cols-2">
              <EvidencePanel title="explainability trace" evidence={selectedReport?.evidence ?? []} />
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
                      <p className="mt-2 text-xs text-slate-400">{link.evidence.join(' · ')}</p>
                    </div>
                  ))}
                </div>
              </section>
            </div>

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
          </div>
        </section>

        <footer className="mt-10 grid gap-4 rounded-[2rem] border border-white/10 bg-slate-950/50 p-5 text-sm text-slate-400 md:grid-cols-3">
          <div className="flex items-center gap-3"><Sparkles className="text-cyan-300" /> Early detection tells you what is about to matter.</div>
          <div className="flex items-center gap-3"><Atom className="text-violet-300" /> Fusion reasoning turns fragmented signals into decisions.</div>
          <div className="flex items-center gap-3"><GitBranch className="text-emerald-300" /> Modular engines make PRISM easy to extend.</div>
        </footer>
      </div>
    </main>
  );
}

export default App;
