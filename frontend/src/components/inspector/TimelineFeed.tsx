'use client';

import React from 'react';
import { ActivityLog } from '@/types';
import { formatLocalTime } from '@/lib/utils';
import { Zap, Cpu, Brain, Wrench, MessageSquare, Sliders, CheckCircle2, Clock, Truck, CreditCard } from 'lucide-react';

interface TimelineFeedProps {
  logs: ActivityLog[];
}

interface ToolActionItem {
  action: string;
  status: string;
  details: string;
}

export default function TimelineFeed({ logs }: TimelineFeedProps) {
  const getLogIcon = (log: ActivityLog) => {
    switch (log.log_type) {
      case 'EVENT':
        if (log.title.includes('payment')) return <CreditCard className="w-4 h-4 text-rose-400" />;
        if (log.title.includes('shipment') || log.title.includes('delivered')) return <Truck className="w-4 h-4 text-cyan-400" />;
        if (log.title.includes('customer')) return <MessageSquare className="w-4 h-4 text-emerald-400" />;
        return <Zap className="w-4 h-4 text-amber-400" />;
      case 'CLASSIFICATION':
        return <Cpu className="w-4 h-4 text-purple-400" />;
      case 'REASONING':
        return <Brain className="w-4 h-4 text-indigo-400" />;
      case 'TOOL_EXECUTION':
        return <Wrench className="w-4 h-4 text-cyan-400" />;
      case 'INSTRUCTION':
        return <MessageSquare className="w-4 h-4 text-amber-400" />;
      case 'CONTROL':
        return <Sliders className="w-4 h-4 text-slate-400" />;
      case 'FINAL_SUMMARY':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getLogBadge = (log: ActivityLog) => {
    switch (log.log_type) {
      case 'EVENT':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">SIGNAL / EVENT</span>;
      case 'CLASSIFICATION':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">TIER-1 CLASSIFIER</span>;
      case 'REASONING':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">TIER-2 AGENT</span>;
      case 'INSTRUCTION':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">LIVE INSTRUCTION</span>;
      case 'CONTROL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-500/10 text-slate-400 border border-slate-500/20">CONTROL</span>;
      case 'FINAL_SUMMARY':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">POST-MORTEM</span>;
      default:
        return null;
    }
  };

  const formatTimestamp = (iso: string) => {
    return formatLocalTime(iso);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
        <div>
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <span>Live Activity Timeline</span>
            <span className="text-xs font-mono font-normal text-slate-500">({logs.length} entries)</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Real-time stream of incoming signals, classifier decisions, thoughts, and tool executions</p>
        </div>
      </div>

      {logs.length === 0 ? (
        <div className="py-16 text-center text-slate-500">
          <Clock className="w-8 h-8 mx-auto mb-2 opacity-40" />
          <p className="text-sm">No activity recorded yet. Waiting for initial workflow execution...</p>
        </div>
      ) : (
        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
          {logs.map((log) => {
            const toolActions = (log.metadata_payload?.tool_actions as ToolActionItem[] | undefined) || [];

            return (
              <div key={log.id} className="relative group">
                <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-slate-950 border border-slate-700 flex items-center justify-center shadow-md group-hover:scale-110 transition-transform">
                  {getLogIcon(log)}
                </div>

                <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 transition-all hover:border-slate-700 shadow-sm">
                  <div className="flex items-start justify-between gap-3 mb-1.5">
                    <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                      {getLogBadge(log)}
                      <span className="text-sm font-bold text-white">{log.title ? log.title.replace(/\*\*/g, '').replace(/\*/g, '') : ''}</span>
                    </div>
                    <span className="text-xs font-mono text-slate-500 whitespace-nowrap">
                      {formatTimestamp(log.timestamp)}
                    </span>
                  </div>

                  {log.details && (
                    <p className="text-xs text-slate-300 leading-relaxed font-sans mt-2 whitespace-pre-wrap bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/50">
                      {log.details ? log.details.replace(/\*\*/g, '').replace(/\*/g, '') : ''}
                    </p>
                  )}

                  {toolActions.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2">
                      <span className="text-[11px] font-mono uppercase text-cyan-400 font-semibold block">
                        Tools Executed ({toolActions.length}):
                      </span>
                      {toolActions.map((action, aIdx) => (
                        <div
                          key={aIdx}
                          className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-800/40 text-xs text-slate-200"
                        >
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[10px] font-bold">
                              {action.action}
                            </span>
                            <span className="text-[11px] text-emerald-400 font-mono">[{action.status}]</span>
                          </div>
                          <p className="text-slate-300 text-xs mt-0.5">{action.details ? action.details.replace(/\*\*/g, '').replace(/\*/g, '') : ''}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
