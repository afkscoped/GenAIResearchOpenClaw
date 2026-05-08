import { useState } from 'react';
import { Loader2, MessageCircle, Send, ArrowUpRight } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

import {
  type ChatCitation,
  type ChatMessage,
  type ResearchItem,
  type FusionReport
} from '../api/client';

type RankedEntry = { item: ResearchItem; report?: FusionReport };

export function PaperChat({
  ranked,
  chatMessages,
  setChatMessages,
  chatLoading,
  setChatLoading,
  setSelectedId,
  setActiveView,
}: {
  ranked: RankedEntry[];
  chatMessages: ChatMessage[];
  setChatMessages: (msgs: ChatMessage[]) => void;
  chatLoading: boolean;
  setChatLoading: (v: boolean) => void;
  setSelectedId: (id: string) => void;
  setActiveView: (v: any) => void;
}) {
  const [input, setInput] = useState('');
  const [focusedPaper, setFocusedPaper] = useState('');

  async function sendMessage() {
    const question = input.trim();
    if (!question || chatLoading) return;
    const newMessages: ChatMessage[] = [...chatMessages, { role: 'user', content: question }];
    setChatMessages(newMessages);
    setInput('');
    setChatLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, item_id: focusedPaper || null, context_limit: 8 }),
      });
      const data = await resp.json();
      setChatMessages([...newMessages, {
        role: 'assistant',
        content: data.answer ?? 'No response received.',
        citations: data.citations ?? [],
      }]);
    } catch {
      setChatMessages([...newMessages, { role: 'assistant', content: 'Failed to reach the chat API. Make sure the backend is running.' }]);
    } finally {
      setChatLoading(false);
    }
  }

  return (
    <section>
      <div className="mb-6">
        <div className="flex items-center gap-4">
          <span className="font-mono text-[10px] tracking-[0.32em] text-chartreuse">§ X</span>
          <span className="font-mono text-[9px] tracking-[0.28em] text-bone-mute uppercase">Ask Papers</span>
          <div className="flex-1" style={{ borderBottom: '1px dashed rgba(237,230,211,0.12)' }} />
        </div>
        <h2 className="font-display mt-3 text-3xl tracking-tightest text-bone md:text-4xl" style={{ fontFamily: 'var(--font-display, serif)' }}>
          Talk to your research
        </h2>
      </div>

      <div className="mb-6 border-l-2 border-l-chartreuse bg-ink-deep/60 px-5 py-4" style={{ borderColor: 'var(--chartreuse, #D6FF3D)' }}>
        <p className="font-mono text-[9px] tracking-[0.28em] text-chartreuse uppercase mb-2">— How It Works —</p>
        <div className="font-body text-[15px] leading-relaxed italic text-bone-warm space-y-2" style={{ color: 'var(--bone-warm, #c5baa6)' }}>
          Ask questions about any paper in PRISM's memory. The AI retrieves relevant papers via
          semantic search and answers grounded in their abstracts, metadata, and PRISM scores.
          Optionally focus on a specific paper for deeper analysis.
        </div>
      </div>

      {/* Paper focus selector */}
      <div className="mb-6 border border-rule bg-ink-deep p-4" style={{ borderColor: 'rgba(237,230,211,0.08)' }}>
        <label className="font-mono text-[9px] tracking-[0.28em] text-bone-mute uppercase block mb-2">
          Focus on a specific paper (optional)
        </label>
        <select
          value={focusedPaper}
          onChange={(e) => setFocusedPaper(e.target.value)}
          className="w-full bg-transparent border border-rule p-3 text-bone font-body text-sm outline-none"
          style={{ borderColor: 'rgba(237,230,211,0.08)', color: 'var(--bone, #EDE6D3)' }}
        >
          <option value="">All papers (general search)</option>
          {ranked.slice(0, 20).map(({ item }) => (
            <option key={item.id} value={item.id}>
              {item.title.slice(0, 90)} ({item.topic})
            </option>
          ))}
        </select>
      </div>

      {/* Chat messages */}
      <div className="border border-rule bg-ink-deep mb-4" style={{ borderColor: 'rgba(237,230,211,0.08)', minHeight: '300px', maxHeight: '500px', overflowY: 'auto' }}>
        {chatMessages.length === 0 && (
          <div className="p-8 text-center">
            <MessageCircle size={32} className="mx-auto mb-4" style={{ color: 'rgba(237,230,211,0.2)' }} />
            <p className="font-body italic text-sm" style={{ color: 'var(--bone-mute, #6b6560)' }}>
              Ask a question about your research papers...
            </p>
            <div className="mt-4 grid gap-2 max-w-md mx-auto">
              {['What are the key findings on attention mechanisms?',
                'Compare the trust scores of the top papers',
                'Which paper has the highest adoption gap and why?',
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => { setInput(q); }}
                  className="text-left p-3 border border-rule text-sm font-body transition-colors hover:bg-ink-soft"
                  style={{ borderColor: 'rgba(237,230,211,0.08)', color: 'var(--bone-warm, #c5baa6)' }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {chatMessages.map((msg, i) => (
          <div key={i} className={`p-5 border-b border-rule ${msg.role === 'user' ? '' : 'bg-ink-soft'}`} style={{ borderColor: 'rgba(237,230,211,0.08)' }}>
            <div className="flex items-center gap-2 mb-2">
              <span className="font-mono text-[9px] tracking-[0.28em] uppercase" style={{ color: msg.role === 'user' ? 'var(--chartreuse, #D6FF3D)' : 'var(--bone-mute, #6b6560)' }}>
                {msg.role === 'user' ? '— You —' : '— PRISM —'}
              </span>
            </div>
            <div className="font-body text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--bone-warm, #c5baa6)' }}>
              {msg.content}
            </div>
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-3 pt-3 border-t border-rule" style={{ borderColor: 'rgba(237,230,211,0.06)' }}>
                <p className="font-mono text-[9px] tracking-[0.28em] text-bone-mute uppercase mb-2">Sources</p>
                <div className="flex flex-wrap gap-2">
                  {msg.citations.map((c) => (
                    <button
                      key={c.item_id}
                      onClick={() => { setSelectedId(c.item_id); setActiveView('command'); }}
                      className="inline-flex items-center gap-1 px-2 py-1 border border-rule text-xs font-body transition-colors hover:bg-ink-soft"
                      style={{ borderColor: 'rgba(237,230,211,0.08)', color: 'var(--bone, #EDE6D3)' }}
                    >
                      {c.title.slice(0, 50)}...
                      <ArrowUpRight size={10} />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
        {chatLoading && (
          <div className="p-5 flex items-center gap-3">
            <Loader2 className="animate-spin" size={16} style={{ color: 'var(--chartreuse, #D6FF3D)' }} />
            <span className="font-body italic text-sm" style={{ color: 'var(--bone-mute, #6b6560)' }}>PRISM is thinking...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex items-center gap-3 border border-rule bg-ink-deep px-4 py-3" style={{ borderColor: 'rgba(237,230,211,0.08)' }}>
        <MessageCircle size={14} style={{ color: 'var(--chartreuse, #D6FF3D)' }} />
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') sendMessage(); }}
          className="flex-1 bg-transparent font-body text-sm outline-none"
          style={{ color: 'var(--bone, #EDE6D3)' }}
          placeholder="Ask about your papers..."
          disabled={chatLoading}
        />
        <button onClick={sendMessage} disabled={chatLoading || !input.trim()} className="p-2 transition-colors" style={{ color: input.trim() ? 'var(--chartreuse, #D6FF3D)' : 'var(--bone-mute, #6b6560)' }}>
          <Send size={16} />
        </button>
      </div>
    </section>
  );
}
