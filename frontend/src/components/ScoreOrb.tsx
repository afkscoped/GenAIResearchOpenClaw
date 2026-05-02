type ScoreOrbProps = {
  label: string;
  score: number;
  tone?: 'cyan' | 'violet' | 'rose' | 'amber' | 'emerald';
  size?: 'sm' | 'lg';
};

const tones = {
  cyan: 'from-cyan-300 via-sky-500 to-blue-600 text-cyan-100',
  violet: 'from-violet-300 via-fuchsia-500 to-purple-700 text-violet-100',
  rose: 'from-rose-300 via-pink-500 to-red-600 text-rose-100',
  amber: 'from-amber-200 via-orange-500 to-yellow-600 text-amber-100',
  emerald: 'from-emerald-200 via-teal-500 to-cyan-600 text-emerald-100',
};

export function ScoreOrb({ label, score, tone = 'cyan', size = 'sm' }: ScoreOrbProps) {
  const pct = Math.round(score * 100);
  const dim = size === 'lg' ? 'h-44 w-44' : 'h-24 w-24';
  const inner = size === 'lg' ? 'h-36 w-36' : 'h-20 w-20';
  return (
    <div className="flex flex-col items-center gap-3">
      <div className={`${dim} rounded-full bg-gradient-to-br ${tones[tone]} p-[2px] shadow-prism`}>
        <div className="flex h-full w-full items-center justify-center rounded-full bg-slate-950/90">
          <div className={`${inner} flex flex-col items-center justify-center rounded-full border border-white/10 bg-slate-900/90`}>
            <span className={size === 'lg' ? 'text-4xl font-black' : 'text-2xl font-black'}>{pct}</span>
            <span className="text-[10px] uppercase tracking-[0.28em] text-slate-400">score</span>
          </div>
        </div>
      </div>
      <span className="text-center text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">{label}</span>
    </div>
  );
}
