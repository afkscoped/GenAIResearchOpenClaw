type ScoreOrbProps = {
  label: string;
  score: number;
  tone?: 'cyan' | 'violet' | 'rose' | 'amber' | 'emerald';
  size?: 'sm' | 'lg';
};

export function ScoreOrb({ label, score, size = 'sm' }: ScoreOrbProps) {
  const pct = Math.round(score * 100);
  const ringSize = size === 'lg' ? 220 : 110;
  const stroke = size === 'lg' ? 2 : 1;
  const radius = ringSize / 2 - 6;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;
  const ticks = size === 'lg' ? 60 : 36;

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className="dial spin-in relative grid place-items-center"
        style={{ width: ringSize, height: ringSize }}
      >
        {Array.from({ length: ticks }).map((_, i) => (
          <span
            key={i}
            className="dial-tick"
            style={{
              transform: `translateX(-50%) rotate(${(360 / ticks) * i}deg)`,
              height: i % 5 === 0 ? 10 : 4,
              opacity: i % 5 === 0 ? 0.9 : 0.35,
            }}
          />
        ))}
        <svg
          width={ringSize}
          height={ringSize}
          className="absolute inset-0 -rotate-90"
          aria-hidden
        >
          <circle
            cx={ringSize / 2}
            cy={ringSize / 2}
            r={radius}
            fill="none"
            stroke="rgba(237, 230, 211, 0.08)"
            strokeWidth={stroke}
          />
          <circle
            cx={ringSize / 2}
            cy={ringSize / 2}
            r={radius}
            fill="none"
            stroke="#D6FF3D"
            strokeWidth={stroke + 1}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="butt"
            style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(.2,.7,.2,1)' }}
          />
        </svg>
        <div className="relative z-10 flex flex-col items-center">
          <span
            className={`numeral text-bone ${size === 'lg' ? 'text-7xl' : 'text-3xl'}`}
            style={{ lineHeight: 1 }}
          >
            {pct}
          </span>
          <span className="font-mono mt-1 text-[9px] tracking-[0.32em] text-bone-mute">
            INDEX / 100
          </span>
        </div>
      </div>
      <span className="font-mono text-[10px] uppercase tracking-[0.32em] text-bone-dim">
        — {label} —
      </span>
    </div>
  );
}
