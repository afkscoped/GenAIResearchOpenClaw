import { GitBranch, Newspaper, RadioTower, ScrollText, Server, Users } from 'lucide-react';
import type { ResearchItem } from '../api/client';

const icons = {
  arxiv: ScrollText,
  github: GitBranch,
  huggingface: Server,
  news: Newspaper,
  mock_social: RadioTower,
  mock_jobs: Users,
};

export function SignalConstellation({ items }: { items: ResearchItem[] }) {
  const sources = Array.from(new Set(items.map((item) => item.source)));
  return (
    <section className="glass relative min-h-[300px] overflow-hidden rounded-[2rem] p-6">
      <div className="absolute inset-0 prism-grid opacity-40" />
      <div className="relative z-10 mb-6">
        <p className="text-xs font-bold uppercase tracking-[0.3em] text-cyan-300">source constellation</p>
        <h2 className="mt-2 text-2xl font-black text-white">Live signal map</h2>
      </div>
      <div className="relative z-10 grid grid-cols-2 gap-4 md:grid-cols-3">
        {sources.map((source, index) => {
          const Icon = icons[source];
          const count = items.filter((item) => item.source === source).length;
          return (
            <div key={source} className="rounded-3xl border border-white/10 bg-slate-950/60 p-4" style={{ transform: `translateY(${index % 2 === 0 ? 0 : 18}px)` }}>
              <div className="mb-4 inline-flex rounded-2xl bg-cyan-400/10 p-3 text-cyan-200">
                <Icon size={20} />
              </div>
              <div className="text-2xl font-black text-white">{count}</div>
              <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">{source.replace('_', ' ')}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
