'use client';

import React from 'react';
import Link from 'next/link';
import { OrderRun } from '@/types';
import { Clock, Eye, Moon, AlertTriangle, CheckCircle, Flame, PauseCircle, XCircle } from 'lucide-react';

interface RunListProps {
  runs: OrderRun[];
  selectedFilter: string;
  onFilterChange: (status: string) => void;
}

export default function RunList({ runs, selectedFilter, onFilterChange }: RunListProps) {
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
    if (!isoString) return 'None';
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div className="p-5 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white">Live Order Supervisors</h2>
          <p className="text-xs text-slate-400 mt-0.5">Temporal long-running workflow state machine runs</p>
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
              <th className="py-3.5 px-5">Next Wake-up</th>
              <th className="py-3.5 px-5">Rolling Memory Summary</th>
              <th className="py-3.5 px-5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {runs.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-500">
                  No order supervisor runs found for this filter. Start a new order above!
                </td>
              </tr>
            ) : (
              runs.map((run) => (
                <tr key={run.id} className="hover:bg-slate-800/40 transition-colors group">
                  <td className="py-4 px-5 font-mono font-bold text-white">
                    <Link href={`/runs/${run.id}`} className="hover:text-cyan-400 transition-colors flex items-center space-x-2">
                      <span>{run.order_id}</span>
                    </Link>
                    <span className="block text-[11px] text-slate-500 font-mono font-normal mt-0.5">{run.id}</span>
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
                      <div className="flex items-center text-amber-400 space-x-1.5">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{formatTime(run.next_wake_time)}</span>
                      </div>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>

                  <td className="py-4 px-5 max-w-xs">
                    <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed bg-slate-950/40 p-2 rounded-lg border border-slate-800/50">
                      {run.compact_memory || 'No memory recorded.'}
                    </p>
                  </td>

                  <td className="py-4 px-5 text-right">
                    <Link
                      href={`/runs/${run.id}`}
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600 hover:text-white border border-indigo-500/30 text-xs font-semibold transition-all"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </Link>
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
