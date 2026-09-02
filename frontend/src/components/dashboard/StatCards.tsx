'use client';

import React from 'react';
import { Activity, Moon, AlertTriangle, CheckCircle2, PackageCheck } from 'lucide-react';
import { OrderRun } from '@/types';

interface StatCardsProps {
  runs: OrderRun[];
}

export default function StatCards({ runs }: StatCardsProps) {
  const total = runs.length;
  const active = runs.filter(r => r.status === 'ACTIVE').length;
  const sleeping = runs.filter(r => r.status === 'SLEEPING').length;
  const escalated = runs.filter(r => r.status === 'ESCALATED').length;
  const completed = runs.filter(r => r.status === 'COMPLETED').length;

  const stats = [
    { title: 'Total Order Runs', count: total, icon: PackageCheck, color: 'text-indigo-400', bg: 'bg-indigo-950/40 border-indigo-800/50' },
    { title: 'Active (Reasoning)', count: active, icon: Activity, color: 'text-cyan-400', bg: 'bg-cyan-950/40 border-cyan-800/50' },
    { title: 'Sleeping (Wait Timer)', count: sleeping, icon: Moon, color: 'text-amber-400', bg: 'bg-amber-950/40 border-amber-800/50' },
    { title: 'Escalated Issues', count: escalated, icon: AlertTriangle, color: 'text-rose-400', bg: 'bg-rose-950/40 border-rose-800/50' },
    { title: 'Completed & Delivered', count: completed, icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-950/40 border-emerald-800/50' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div
            key={stat.title}
            className={`p-4 rounded-xl border ${stat.bg} backdrop-blur-sm shadow-sm transition-all hover:scale-[1.02]`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{stat.title}</span>
              <Icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div className="mt-2 flex items-baseline">
              <span className={`text-2xl font-bold font-mono ${stat.color}`}>{stat.count}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
