import { BookOpen, Code, Cpu, GitBranch, Globe, Newspaper, RadioTower, Rocket, ScrollText, Search, Server, Users } from 'lucide-react';
import type { ResearchItem } from '../api/client';

const icons: Record<string, typeof Globe> = {
  arxiv: ScrollText,
  github: GitBranch,
  huggingface: Server,
  news: Newspaper,
  mock_social: RadioTower,
  mock_jobs: Users,
  semantic_scholar: BookOpen,
  crossref: Globe,
  papers_with_code: Code,
  engineering_blog: Cpu,
  mock_product_launch: Rocket,
};

export function SignalConstellation({ items }: { items: ResearchItem[] }) {
  const sources = Array.from(new Set(items.map((item) => item.source)));
  const total = items.length;
  return (
    <section className="surface relative overflow-hidden p-6">
      <div className="flex items-baseline justify-between">
        <div>
          <p className="eyebrow eyebrow-accent">III · Source Constellation</p>
          <h2 className="font-display mt-2 text-3xl tracking-tightest text-bone">
            Live signal map
          </h2>
        </div>
        <span className="numeral text-5xl text-bone-dim">{total}</span>
      </div>
      <p className="font-body mt-3 text-[13px] italic text-bone-mute leading-relaxed max-w-2xl">
        Each tile represents a monitored data source. Wider coverage across sources means better
        intelligence — the more channels PRISM listens to, the harder it is for an emerging signal
        to slip past unnoticed.
      </p>
      <div className="rule-ticker my-5" />
      <div className="grid grid-cols-2 gap-px bg-rule md:grid-cols-3">
        {sources.map((source, index) => {
          const Icon = icons[source] ?? Search;
          const count = items.filter((item) => item.source === source).length;
          const pct = Math.round((count / total) * 100);
          return (
            <div
              key={source}
              className="bg-ink-deep p-4 reveal"
              style={{ animationDelay: `${0.1 + index * 0.08}s` }}
            >
              <div className="flex items-center justify-between">
                <Icon size={16} strokeWidth={1.4} className="text-bone-dim" />
                <span className="font-mono text-[9px] tracking-[0.22em] text-bone-mute">
                  {pct}%
                </span>
              </div>
              <div className="numeral mt-3 text-4xl text-bone" style={{ lineHeight: 1 }}>
                {count.toString().padStart(2, '0')}
              </div>
              <div className="font-mono mt-2 text-[10px] uppercase tracking-[0.2em] text-bone-dim">
                {source.replace('_', ' ')}
              </div>
              <div className="mt-3 h-px bg-rule">
                <div className="h-px bg-chartreuse" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
