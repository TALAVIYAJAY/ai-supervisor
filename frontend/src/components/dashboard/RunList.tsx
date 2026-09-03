'use client';

import React from 'react';
import { OrderRun } from '@/types';
import { formatLocalDateTime } from '@/lib/utils';
import { Clock, Eye, Moon, AlertTriangle, CheckCircle, Flame, PauseCircle, XCircle } from 'lucide-react';

interface RunListProps {
  runs: OrderRun[];
  selectedFilter: string;
  onFilterChange: (status: string) => void;
  selectedRunId?: string | null;
  onSelectRun?: (runId: string) => void;
}

export default function RunList({ runs, selectedFilter, onFilterChange, selectedRunId, onSelectRun }: RunListProps) {
  const filters = ['ALL', 'ACTIVE', 'SLEEPING', 'ESCALATED', 'COMPLETED', 'TERMINATED'];

  const getStatusBadge = (status: OrderRun['status']) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 animate-pulse">
            <Flame className="w-3.5 h-3.5 mr-1 text-cyan-400" />
            ACTIVE
          </span>
        );
      case 'SLEEPING':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Moon className="w-3.5 h-3.5 mr-1 text-amber-400" />
            SLEEPING
          </span>
        );
      case 'ESCALATED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-3.5 h-3.5 mr-1 text-rose-400" />
            ESCALATED
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-400" />
            COMPLETED
          </span>
        );
      case 'PAUSED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/30">
            <PauseCircle className="w-3.5 h-3.5 mr-1 text-slate-400" />
            PAUSED
          </span>
        );
      case 'TERMINATED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/30">
            <XCircle className="w-3.5 h-3.5 mr-1 text-red-400" />
            TERMINATED
          </span>
        );
      default:
        return <span className="text-xs text-slate-400">{status}</span>;
    }
  };

  const formatTime = (isoString?: string | null) => {
    return formatLocalDateTime(isoString);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div className="p-5 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">Live Order Supervisors</h2>
          <p className="text-xs text-slate-400 mt-0.5">Click any order row to view live inspector and controls below</p>
        </div>

        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800 overflow-x-auto">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => onFilterChange(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedFilter === f
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/80 text-xs uppercase font-mono text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3.5 px-5">Order ID</th>
              <th className="py-3.5 px-5">Status</th>
              <th className="py-3.5 px-5">Customer & Item</th>
              <th className="py-3.5 px-5">Next Wake-Up</th>
              <th className="py-3.5 px-5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {runs.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-500 text-sm">
                  No order supervisor runs found for this filter. Start a new order above!
                </td>
              </tr>
            ) : (
              runs.map((run) => (
                <tr
                  key={run.id}
                  onClick={() => onSelectRun && onSelectRun(run.id)}
                  className={`cursor-pointer transition-colors ${
                    selectedRunId === run.id
                      ? 'bg-indigo-950/40 hover:bg-indigo-950/60 border-l-4 border-indigo-500'
                      : 'hover:bg-slate-800/40'
                  }`}
                >
                  <td className="py-4 px-5 font-mono">
                    <span className="font-bold text-white block">{run.order_id}</span>
                    <span className="text-[11px] text-slate-400 block mt-0.5">{run.id}</span>
                  </td>

                  <td className="py-4 px-5">
                    {getStatusBadge(run.status)}
                  </td>

                  <td className="py-4 px-5">
                    <div className="font-medium text-slate-200">
                      {run.order_context?.customer_name || 'Customer'}
                    </div>
                    <div className="text-xs text-slate-400 truncate max-w-[200px]">
                      {run.order_context?.items?.[0]?.name || 'Standard Package'}
                    </div>
                  </td>

                  <td className="py-4 px-5 font-mono text-xs">
                    {run.status === 'SLEEPING' && run.next_wake_time ? (
                      <div className="flex items-center text-amber-400 space-x-1.5 font-semibold">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{formatTime(run.next_wake_time)}</span>
                      </div>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>

                  <td className="py-4 px-5 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onSelectRun) onSelectRun(run.id);
                      }}
                      className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                        selectedRunId === run.id
                          ? 'bg-indigo-600 text-white shadow-lg'
                          : 'bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600 hover:text-white border border-indigo-500/30'
                      }`}
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>{selectedRunId === run.id ? 'Inspecting' : 'Inspect'}</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
