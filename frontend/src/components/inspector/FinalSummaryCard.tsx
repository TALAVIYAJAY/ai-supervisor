'use client';

import React from 'react';
import { FinalSummary } from '@/types';
import { Award, CheckCircle2, Lightbulb, TrendingUp, ShieldCheck } from 'lucide-react';

interface FinalSummaryCardProps {
  summary: FinalSummary;
}

export default function FinalSummaryCard({ summary }: FinalSummaryCardProps) {
  return (
    <div className="bg-gradient-to-br from-slate-900 via-emerald-950/20 to-slate-900 border border-emerald-500/40 rounded-2xl p-6 shadow-2xl space-y-6">
      <div className="flex items-center space-x-3 border-b border-emerald-500/20 pb-4">
        <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-lg shadow-emerald-500/20">
          <Award className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-xs font-bold">
              COMPLETED
            </span>
            <h2 className="text-lg font-bold text-white">Order Post-Mortem & Final Learnings</h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">Autonomous supervisor lifecycle review & executive summary</p>
        </div>
      </div>

      <div className="bg-slate-950/80 p-4 rounded-xl border border-emerald-500/20 text-sm text-slate-200 leading-relaxed font-sans shadow-inner">
        <span className="text-xs font-mono uppercase text-emerald-400 font-bold block mb-1.5 flex items-center space-x-1.5">
          <ShieldCheck className="w-4 h-4" />
          <span>Executive Summary</span>
        </span>
        <p className="text-slate-300">{summary.final_summary ? summary.final_summary.replace(/\*\*/g, '').replace(/\*/g, '') : ''}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2.5">
          <h4 className="text-xs font-mono uppercase text-cyan-400 font-bold flex items-center space-x-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Actions Executed</span>
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {summary.important_actions_taken?.map((action, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="text-cyan-400 font-mono text-[10px] mt-0.5">•</span>
                <span>{action ? action.replace(/\*\*/g, '').replace(/\*/g, '') : ''}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2.5">
          <h4 className="text-xs font-mono uppercase text-amber-400 font-bold flex items-center space-x-1.5">
            <Lightbulb className="w-3.5 h-3.5" />
            <span>Key Learnings</span>
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {summary.key_learnings?.map((learning, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="text-amber-400 font-mono text-[10px] mt-0.5">•</span>
                <span>{learning ? learning.replace(/\*\*/g, '').replace(/\*/g, '') : ''}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2.5">
          <h4 className="text-xs font-mono uppercase text-purple-400 font-bold flex items-center space-x-1.5">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Process Recommendations</span>
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {summary.recommendations?.map((rec, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="text-purple-400 font-mono text-[10px] mt-0.5">•</span>
                <span>{rec ? rec.replace(/\*\*/g, '').replace(/\*/g, '') : ''}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
