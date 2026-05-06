import type { LucideIcon } from 'lucide-react';

export type EngineCardProps = {
  title: string;
  subtitle: string;
  score: number;
  icon: LucideIcon;
  gradient: string;
};

export function EngineCard({ title, subtitle, score, icon: Icon }: EngineCardProps) {
  const pct = Math.round(score * 100);
  const isHot = pct >= 65;
  const isCool = pct < 35;
  return (
    <div className="surface group p-5 transition-colors duration-300 hover:border-bone-dim">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="border border-rule p-2 text-bone-dim group-hover:text-chartreuse transition-colors">
            <Icon size={16} strokeWidth={1.4} />
          </div>
          <div>
            <p className="eyebrow">{title}</p>
            <p className="font-body mt-1 text-sm italic text-bone-dim">{subtitle}</p>
          </div>
        </div>
        <div
          className={`numeral text-5xl ${isHot ? 'text-chartreuse' : isCool ? 'text-bone-mute' : 'text-bone'}`}
          style={{ lineHeight: 0.9 }}
        >
          {pct}
        </div>
      </div>
      <div className="mt-5 relative h-px bg-rule">
        <div
          className={`absolute left-0 top-0 h-px ${isHot ? 'bg-chartreuse' : 'bg-bone-dim'}`}
          style={{ width: `${pct}%`, transition: 'width 1s cubic-bezier(.2,.7,.2,1)' }}
        />
        <div
          className={`absolute -top-[3px] h-[7px] w-[2px] ${isHot ? 'bg-chartreuse' : 'bg-bone'}`}
          style={{ left: `calc(${pct}% - 1px)`, transition: 'left 1s cubic-bezier(.2,.7,.2,1)' }}
        />
      </div>
      <div className="mt-3 flex justify-between font-mono text-[9px] tracking-[0.22em] text-bone-mute">
        <span>00</span>
        <span>{isHot ? '◆ ELEVATED' : isCool ? '○ DORMANT' : '◇ STEADY'}</span>
        <span>100</span>
      </div>
    </div>
  );
}
