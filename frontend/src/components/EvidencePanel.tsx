import { Sparkles } from 'lucide-react';

type EvidencePanelProps = {
  title: string;
  evidence: string[];
};

export function EvidencePanel({ title, evidence }: EvidencePanelProps) {
  return (
    <section className="surface p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-chartreuse" strokeWidth={1.4} />
          <p className="eyebrow eyebrow-accent">{title}</p>
        </div>
        <span className="font-mono text-[10px] tracking-[0.22em] text-bone-mute">
          {evidence.length.toString().padStart(2, '0')}
        </span>
      </div>
      <p className="font-body mb-4 text-[13px] italic text-bone-mute leading-relaxed">
        Each entry is a specific reasoning step — a "trace" — produced by the engines and the AI
        agent. Together they show exactly why this paper earned its score.
      </p>
      <div className="rule-ticker mb-4" />
      <ol className="space-y-4">
        {evidence.slice(0, 10).map((item, index) => (
          <li
            key={`${item}-${index}`}
            className="flex gap-4 border-b border-rule pb-4 last:border-b-0 last:pb-0"
          >
            <span className="numeral shrink-0 text-2xl text-oxblood-glow" style={{ lineHeight: 1 }}>
              {(index + 1).toString().padStart(2, '0')}
            </span>
            <p className="font-body text-[15px] leading-relaxed text-bone-warm">{item}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
