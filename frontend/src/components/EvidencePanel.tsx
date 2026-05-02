import { CheckCircle2, Sparkles } from 'lucide-react';

type EvidencePanelProps = {
  title: string;
  evidence: string[];
};

export function EvidencePanel({ title, evidence }: EvidencePanelProps) {
  return (
    <section className="glass rounded-3xl p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="rounded-2xl bg-cyan-400/10 p-2 text-cyan-300">
          <Sparkles size={18} />
        </div>
        <h3 className="text-sm font-bold uppercase tracking-[0.24em] text-slate-300">{title}</h3>
      </div>
      <div className="space-y-3">
        {evidence.slice(0, 10).map((item, index) => (
          <div key={`${item}-${index}`} className="flex gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-sm text-slate-300">
            <CheckCircle2 className="mt-0.5 shrink-0 text-emerald-300" size={16} />
            <span>{item}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
