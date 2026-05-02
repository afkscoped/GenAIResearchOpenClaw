import type { LucideIcon } from 'lucide-react';

export type EngineCardProps = {
  title: string;
  subtitle: string;
  score: number;
  icon: LucideIcon;
  gradient: string;
};

export function EngineCard({ title, subtitle, score, icon: Icon, gradient }: EngineCardProps) {
  const pct = Math.round(score * 100);
  return (
    <div className="glass group relative overflow-hidden rounded-3xl p-5 transition duration-300 hover:-translate-y-1 hover:border-cyan-300/40">
      <div className={`absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gradient-to-br ${gradient} opacity-20 blur-2xl transition group-hover:opacity-40`} />
      <div className="relative flex items-start justify-between gap-4">
        <div>
          <div className="mb-4 inline-flex rounded-2xl border border-white/10 bg-white/5 p-3 text-cyan-200">
            <Icon size={20} />
          </div>
          <h3 className="text-base font-bold text-white">{title}</h3>
          <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-black text-white">{pct}</div>
          <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">index</div>
        </div>
      </div>
      <div className="relative mt-5 h-2 overflow-hidden rounded-full bg-slate-800">
        <div className={`h-full rounded-full bg-gradient-to-r ${gradient}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
