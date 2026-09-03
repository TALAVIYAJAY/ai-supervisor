'use client';

import React from 'react';
import { OrderRun } from '@/types';
import { formatLocalDateTime } from '@/lib/utils';
import { Brain, Moon, Clock, User, Package, MapPin, Sparkles } from 'lucide-react';

interface MemoryCardProps {
  run: OrderRun;
}

export default function MemoryCard({ run }: MemoryCardProps) {
  const formatTime = (isoString?: string | null) => {
    return formatLocalDateTime(isoString);
  };

  const getStatusClass = () => {
    if (run.status === 'ACTIVE') return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30 animate-pulse';
    if (run.status === 'SLEEPING') return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    if (run.status === 'ESCALATED') return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3.5">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Rolling Compact Memory</h3>
            <p className="text-[11px] text-slate-400">Context-compacted narrative maintained across sleeps</p>
          </div>
        </div>

        <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold border ${getStatusClass()}`}>
          {run.status}
        </span>
      </div>

      <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans relative shadow-inner">
        <div className="flex items-center space-x-1.5 text-purple-400 font-mono text-[10px] uppercase font-bold mb-1.5">
          <Sparkles className="w-3 h-3" />
          <span>Active Context State:</span>
        </div>
        <p className="whitespace-pre-wrap font-sans text-slate-300">
          {run.compact_memory ? run.compact_memory.replace(/\*\*/g, '').replace(/\*/g, '') : 'Awaiting initial supervisor analysis...'}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 pt-1 font-mono text-xs">
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase block mb-1 flex items-center space-x-1">
            <Moon className="w-3 h-3 text-amber-400" />
            <span>Workflow State</span>
          </span>
          <span className="text-white font-bold">
            {run.status === 'SLEEPING' ? 'Asleep (Durable Wait)' : run.status}
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase block mb-1 flex items-center space-x-1">
            <Clock className="w-3 h-3 text-cyan-400" />
            <span>Next Wake-up Timer</span>
          </span>
          <span className="text-cyan-400 font-bold">
            {formatTime(run.next_wake_time)}
          </span>
        </div>
      </div>

      <div className="pt-3 border-t border-slate-800 space-y-2 text-xs">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center space-x-1.5">
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span>Customer:</span>
          </span>
          <span className="text-slate-200 font-medium">
            {run.order_context?.customer_name} ({run.order_context?.customer_email})
          </span>
        </div>

        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center space-x-1.5">
            <Package className="w-3.5 h-3.5 text-slate-500" />
            <span>Items:</span>
          </span>
          <span className="text-slate-200 font-medium truncate max-w-[200px]">
            {run.order_context?.items?.[0]?.name} (Qty: {run.order_context?.items?.[0]?.qty})
          </span>
        </div>

        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center space-x-1.5">
            <MapPin className="w-3.5 h-3.5 text-slate-500" />
            <span>Destination:</span>
          </span>
          <span className="text-slate-200 font-medium truncate max-w-[200px]">
            {run.order_context?.delivery_address || 'India'}
          </span>
        </div>
      </div>
    </div>
  );
}
