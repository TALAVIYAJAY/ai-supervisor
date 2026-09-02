'use client';

import React, { useState } from 'react';
import { MessageSquarePlus, Send, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface InstructionInjectorProps {
  runId: string;
  onInstructionSent: () => void;
}

export default function InstructionInjector({ runId, onInstructionSent }: InstructionInjectorProps) {
  const [instruction, setInstruction] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!instruction.trim()) return;

    setIsSubmitting(true);
    setFeedback(null);

    try {
      await api.injectInstruction(runId, instruction);
      setFeedback('Instruction injected into live run context!');
      setInstruction('');
      onInstructionSent();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to inject instruction';
      setFeedback(`Error: ${msg}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3.5">
      <div className="flex items-center space-x-2.5 border-b border-slate-800 pb-3">
        <div className="p-2 rounded-xl bg-cyan-600/20 text-cyan-400 border border-cyan-500/30">
          <MessageSquarePlus className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">Live Operator Instructions</h3>
          <p className="text-[11px] text-slate-400">Inject mid-flight guidance into the running agent memory</p>
        </div>
      </div>

      {feedback && (
        <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-500/40 text-cyan-300 text-xs font-mono">
          {feedback}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-2">
        <div className="relative">
          <textarea
            rows={2}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="e.g. For this order, prioritize speed over cost. If delayed further, authorize free priority shipping."
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting || !instruction.trim()}
            className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs flex items-center space-x-1.5 transition-all disabled:opacity-50 shadow-md shadow-cyan-500/20"
          >
            {isSubmitting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            <span>Send to Agent</span>
          </button>
        </div>
      </form>
    </div>
  );
}
