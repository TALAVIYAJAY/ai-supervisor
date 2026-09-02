'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { OrderRun, ActivityLog } from '@/types';
import { api } from '@/lib/api';

import TimelineFeed from '@/components/inspector/TimelineFeed';
import MemoryCard from '@/components/inspector/MemoryCard';
import EventSimulator from '@/components/inspector/EventSimulator';
import InstructionInjector from '@/components/inspector/InstructionInjector';
import WorkflowControls from '@/components/inspector/WorkflowControls';
import FinalSummaryCard from '@/components/inspector/FinalSummaryCard';

export default function RunInspectorPage() {
  const params = useParams();
  const runId = params.id as string;

  const [run, setRun] = useState<OrderRun | null>(null);
  const [timeline, setTimeline] = useState<ActivityLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!runId) return;
    let isMounted = true;

    const loadRun = async () => {
      try {
        const [runData, timelineData] = await Promise.all([
          api.getOrderRun(runId),
          api.getTimeline(runId),
        ]);
        if (isMounted) {
          setRun(runData);
          setTimeline(timelineData);
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Error fetching run data:', err);
        if (isMounted) setIsLoading(false);
      }
    };

    loadRun();
    const interval = setInterval(loadRun, 3000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [runId]);

  const handleManualRefresh = async () => {
    if (!runId) return;
    setIsRefreshing(true);
    try {
      const [runData, timelineData] = await Promise.all([
        api.getOrderRun(runId),
        api.getTimeline(runId),
      ]);
      setRun(runData);
      setTimeline(timelineData);
    } finally {
      setIsRefreshing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="py-24 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-8 h-8 animate-spin text-cyan-400" />
        <p className="text-sm font-mono">Loading order supervisor instance {runId}...</p>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="py-24 text-center text-slate-400 space-y-4">
        <p className="text-base font-bold">Order Run not found.</p>
        <Link
          href="/"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 text-white text-xs font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="flex items-center space-x-4">
          <Link
            href="/"
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>

          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-extrabold text-white font-mono tracking-tight">
                {run.order_id}
              </h1>
              <span className="text-xs font-mono text-slate-500 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                {run.id}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 flex items-center space-x-2">
              <span>Supervisor Template: <strong className="text-slate-200 font-mono">{run.supervisor_id}</strong></span>
              <span>•</span>
              <span>Started: {new Date(run.created_at).toLocaleString()}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
            title="Refresh State"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {run.final_summary && (
        <FinalSummaryCard summary={run.final_summary} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-7 space-y-6">
          <TimelineFeed logs={timeline} />
        </div>

        <div className="lg:col-span-5 space-y-6">
          <MemoryCard run={run} />
          <EventSimulator runId={run.id} onEventSent={handleManualRefresh} />
          <InstructionInjector runId={run.id} onInstructionSent={handleManualRefresh} />
          <WorkflowControls run={run} onControlTriggered={handleManualRefresh} />
        </div>
      </div>
    </div>
  );
}
