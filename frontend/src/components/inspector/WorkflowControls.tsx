'use client';

import React, { useState } from 'react';
import { PauseCircle, PlayCircle, XCircle, BellRing, SlidersHorizontal, Loader2 } from 'lucide-react';
import { OrderRun } from '@/types';
import { api, getErrorMessage } from '@/lib/api';

interface WorkflowControlsProps {
  run: OrderRun;
  onControlTriggered: () => void;
}

export default function WorkflowControls({ run, onControlTriggered }: WorkflowControlsProps) {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const handleAction = async (action: 'pause' | 'resume' | 'terminate' | 'wake', reason?: string) => {
    setLoadingAction(action);
    setFeedback(null);
    try {
      if (action === 'wake') {
        setFeedback('⚡ Force wake triggered! AI supervisor is now awake and evaluating order...');
      } else if (action === 'pause') {
        setFeedback('⏸️ Workflow paused by operator.');
      } else if (action === 'resume') {
        setFeedback('▶️ Workflow resumed.');
      } else if (action === 'terminate') {
        setFeedback('🛑 Workflow terminated by operator.');
      }

      await api.controlWorkflow(run.id, action, reason);
      onControlTriggered();
      setTimeout(() => setFeedback(null), 4000);
    } catch (err: unknown) {
      const msg = getErrorMessage(err, 'Control action failed');
      setFeedback(msg);
    } finally {
      setLoadingAction(null);
    }
  };

  const isTerminal = run.status === 'COMPLETED' || run.status === 'TERMINATED';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3.5">
      <div className="flex items-center space-x-2.5 border-b border-slate-800 pb-3">
        <div className="p-2 rounded-xl bg-slate-800 text-slate-300 border border-slate-700">
          <SlidersHorizontal className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">Workflow Lifecycle Controls</h3>
          <p className="text-[11px] text-slate-400">Direct Temporal workflow lifecycle commands</p>
        </div>
      </div>

      {feedback && (
        <div className="p-2.5 rounded-xl bg-indigo-950/70 border border-cyan-500/40 text-cyan-300 text-xs font-mono animate-in fade-in flex items-center space-x-2">
          <span>{feedback}</span>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {run.status === 'PAUSED' ? (
          <button
            onClick={() => handleAction('resume', 'Operator resumed run')}
            disabled={loadingAction !== null || isTerminal}
            className="p-2.5 rounded-xl bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 border border-emerald-500/40 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all disabled:opacity-50"
          >
            {loadingAction === 'resume' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <PlayCircle className="w-3.5 h-3.5" />}
            <span>Resume</span>
          </button>
        ) : (
          <button
            onClick={() => handleAction('pause', 'Operator paused run')}
            disabled={loadingAction !== null || isTerminal}
            className="p-2.5 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all disabled:opacity-50"
          >
            {loadingAction === 'pause' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <PauseCircle className="w-3.5 h-3.5" />}
            <span>Pause</span>
          </button>
        )}

        <button
          onClick={() => handleAction('wake', 'Manual operator wake request')}
          disabled={loadingAction !== null || isTerminal || run.status === 'ACTIVE'}
          className="p-2.5 rounded-xl bg-amber-600/20 text-amber-400 hover:bg-amber-600/30 border border-amber-500/40 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all disabled:opacity-50"
        >
          {loadingAction === 'wake' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <BellRing className="w-3.5 h-3.5" />}
          <span>Force Wake</span>
        </button>

        <button
          onClick={() => {
            if (confirm('Are you sure you want to terminate this order workflow?')) {
              handleAction('terminate', 'Terminated by operator');
            }
          }}
          disabled={loadingAction !== null || isTerminal}
          className="p-2.5 rounded-xl bg-rose-600/20 text-rose-400 hover:bg-rose-600/30 border border-rose-500/40 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all disabled:opacity-50 col-span-2 sm:col-span-2"
        >
          {loadingAction === 'terminate' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
          <span>Terminate Workflow</span>
        </button>
      </div>
    </div>
  );
}
