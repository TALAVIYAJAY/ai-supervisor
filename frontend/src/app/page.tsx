'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Plus, RefreshCw, CheckCircle2, X, Sparkles, Send, Clock, Brain, Loader2 } from 'lucide-react';
import { OrderRun, Supervisor, ActivityLog } from '@/types';
import { api } from '@/lib/api';
import { formatLocalDateTime } from '@/lib/utils';
import StatCards from '@/components/dashboard/StatCards';
import RunList from '@/components/dashboard/RunList';
import NewRunModal from '@/components/dashboard/NewRunModal';

import TimelineFeed from '@/components/inspector/TimelineFeed';
import EventSimulator from '@/components/inspector/EventSimulator';
import InstructionInjector from '@/components/inspector/InstructionInjector';
import WorkflowControls from '@/components/inspector/WorkflowControls';
import FinalSummaryCard from '@/components/inspector/FinalSummaryCard';

export default function DashboardPage() {
  const [runs, setRuns] = useState<OrderRun[]>([]);
  const [supervisors, setSupervisors] = useState<Supervisor[]>([]);
  const [selectedFilter, setSelectedFilter] = useState('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [syncToast, setSyncToast] = useState<string | null>(null);

  // Live Launch Progress Simulation State
  const [launchingState, setLaunchingState] = useState<{
    orderId: string;
    step: 'initializing' | 'reasoning' | 'completed';
  } | null>(null);

  // Selected Order for In-Page Inspection
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedRun, setSelectedRun] = useState<OrderRun | null>(null);
  const [timeline, setTimeline] = useState<ActivityLog[]>([]);

  // Close / Hide Inspector completely
  const handleCloseInspector = () => {
    setSelectedRunId(null);
    setSelectedRun(null);
    setTimeline([]);
  };

  // Select a run to inspect
  const handleSelectRun = async (runId: string) => {
    if (selectedRunId === runId) {
      handleCloseInspector();
      return;
    }

    setSelectedRunId(runId);
    try {
      const [runData, timelineData] = await Promise.all([
        api.getOrderRun(runId),
        api.getTimeline(runId)
      ]);
      if (runData) setSelectedRun(runData);
      setTimeline(timelineData || []);
    } catch (err) {
      console.error('Error selecting run:', err);
    }
  };

  // Unified Data Fetcher & Reconciler
  const loadDashboardData = useCallback(async (withReconcile: boolean = false) => {
    try {
      if (withReconcile) {
        setIsRefreshing(true);
        try {
          await api.reconcileWorkflows();
        } catch {
          // Graceful fallback
        }
      }

      const [runsData, supsData] = await Promise.all([
        api.getOrderRuns(selectedFilter),
        api.getSupervisors()
      ]);

      setRuns(runsData.items || []);
      setSupervisors(supsData || []);

      if (selectedRunId) {
        const [updatedRun, updatedTimeline] = await Promise.all([
          api.getOrderRun(selectedRunId),
          api.getTimeline(selectedRunId)
        ]);
        if (updatedRun) {
          setSelectedRun(updatedRun);
          setTimeline(updatedTimeline || []);
        }
      }

      if (withReconcile) {
        setSyncToast('Workflows synchronized & updated!');
        setTimeout(() => setSyncToast(null), 3000);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      if (withReconcile) {
        setIsRefreshing(false);
      }
    }
  }, [selectedFilter, selectedRunId]);

  // Initial Mount & 4s Auto-Polling
  useEffect(() => {
    let isMounted = true;

    const poll = async () => {
      try {
        const [runsData, supsData] = await Promise.all([
          api.getOrderRuns(selectedFilter),
          api.getSupervisors()
        ]);
        if (isMounted) {
          setRuns(runsData.items || []);
          setSupervisors(supsData || []);

          if (selectedRunId) {
            const [runData, timeData] = await Promise.all([
              api.getOrderRun(selectedRunId),
              api.getTimeline(selectedRunId)
            ]);
            if (isMounted && runData) {
              setSelectedRun(runData);
              setTimeline(timeData || []);
            }
          }
        }
      } catch (err) {
        console.warn('Background poll notice:', err);
      }
    };

    poll();
    const interval = setInterval(poll, 4000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedFilter, selectedRunId]);

  // Handler when user starts order creation in modal
  const handleStartCreation = (orderId: string) => {
    setLaunchingState({ orderId, step: 'initializing' });
    setTimeout(() => {
      setLaunchingState((prev) => (prev ? { ...prev, step: 'reasoning' } : null));
    }, 1200);
  };

  const handleOrderCreated = async (newRun: OrderRun) => {
    // 1. Instantly inject row into table - 0ms delay!
    setRuns((prev) => [newRun, ...prev.filter((r) => r.id !== newRun.id)]);

    // 2. Select it immediately for inspector
    setSelectedRunId(newRun.id);
    setSelectedRun(newRun);

    // 3. Complete progress bar to 100%
    setLaunchingState((prev) => (prev ? { ...prev, step: 'completed' } : null));

    // 4. Fetch timeline in background
    api.getTimeline(newRun.id).then((tl) => {
      if (tl) setTimeline(tl);
    });

    // 5. Dismiss banner smoothly after 450ms
    setTimeout(() => {
      setLaunchingState(null);
    }, 450);
  };

  const handleManualRefresh = () => {
    loadDashboardData(true);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Header & Action Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
            <span>Order Supervisor Operations</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            All-in-one autonomous order workflow manager with event-driven AI reasoning
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-cyan-500/50 text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-semibold flex items-center space-x-2 transition-all shadow-sm disabled:opacity-50"
            title="Refresh and synchronize all workflows with Temporal"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-cyan-400' : 'text-slate-400'}`} />
            <span>{isRefreshing ? 'Syncing...' : 'Refresh'}</span>
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white text-sm font-bold shadow-lg shadow-indigo-500/25 flex items-center space-x-2 transition-all hover:scale-[1.02]"
          >
            <Plus className="w-4 h-4" />
            <span>Launch New Order</span>
          </button>
        </div>
      </div>

      {syncToast && (
        <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-xs font-mono animate-in fade-in flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-cyan-400" />
          <span>{syncToast}</span>
        </div>
      )}

      {/* Real-Time Order Creation & Bootstrapping Visualization Card */}
      {launchingState && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-indigo-950/90 via-slate-900 to-cyan-950/80 border border-indigo-500/50 shadow-2xl animate-in fade-in slide-in-from-top-4 duration-300 space-y-3.5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3.5">
              <div className="p-2.5 rounded-xl bg-indigo-600/30 text-cyan-400 border border-indigo-500/40 shadow-inner">
                <Loader2 className="w-5 h-5 animate-spin text-cyan-300" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <span>Launching Autonomous Order Supervisor</span>
                  <span className="font-mono text-cyan-300 px-2 py-0.5 rounded bg-slate-950 border border-indigo-500/40 text-xs font-bold">
                    {launchingState.orderId}
                  </span>
                </h3>
                <p className="text-xs text-slate-300 mt-0.5">
                  {launchingState.step === 'initializing' && 'Registering workflow with state machine and durable timers...'}
                  {launchingState.step === 'reasoning' && 'AI agent performing initial order assessment and setting SLA monitoring policy...'}
                  {launchingState.step === 'completed' && 'Workflow successfully initialized! Supervisor is now online and active.'}
                </p>
              </div>
            </div>
            <span className={`text-xs font-mono font-bold px-3 py-1 rounded-full border ${
              launchingState.step === 'completed'
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : 'bg-indigo-500/20 text-cyan-300 border-cyan-500/40 animate-pulse'
            }`}>
              {launchingState.step === 'initializing' && '1/3 INITIALIZING'}
              {launchingState.step === 'reasoning' && '2/3 AI ASSESSMENT'}
              {launchingState.step === 'completed' && '3/3 READY'}
            </span>
          </div>

          {/* Animated Multi-Stage Progress Bar */}
          <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800 shadow-inner">
            <div
              className="bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 h-2 transition-all duration-500 ease-out"
              style={{
                width:
                  launchingState.step === 'initializing'
                    ? '35%'
                    : launchingState.step === 'reasoning'
                    ? '75%'
                    : '100%',
              }}
            />
          </div>
        </div>
      )}

      {/* Metric Stat Cards */}
      <StatCards runs={runs} />

      {/* Interactive Orders List Table */}
      <RunList
        runs={runs}
        selectedFilter={selectedFilter}
        onFilterChange={setSelectedFilter}
        selectedRunId={selectedRunId}
        onSelectRun={handleSelectRun}
      />

      {/* Super Simple 1-Page Inspector (Zero Tabs, Pure Simplicity!) */}
      {selectedRun && selectedRunId && (
        <div className="space-y-5 pt-2 border-t border-slate-800 animate-in fade-in slide-in-from-top-4 duration-200">
          
          {/* 1. Header & Rolling Memory Banner */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3.5">
              <div className="flex items-center space-x-3.5">
                <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
                  <Sparkles className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
                    <h2 className="text-lg font-bold text-white font-mono">{selectedRun.order_id}</h2>
                    <span className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {selectedRun.id}
                    </span>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                      selectedRun.status === 'ACTIVE' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' :
                      selectedRun.status === 'SLEEPING' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                      selectedRun.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' :
                      selectedRun.status === 'ESCALATED' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' :
                      'bg-slate-700 text-slate-300'
                    }`}>
                      {selectedRun.status}
                    </span>
                    {selectedRun.status === 'SLEEPING' && selectedRun.next_wake_time && (
                      <span className="text-xs font-mono text-amber-400 flex items-center space-x-1 font-semibold">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Next Wake: {formatLocalDateTime(selectedRun.next_wake_time)}</span>
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Customer: <span className="text-slate-200 font-medium">{selectedRun.order_context?.customer_name || 'Customer'}</span> • 
                    Item: <span className="text-slate-200 font-medium">{selectedRun.order_context?.items?.[0]?.name || 'Standard Package'}</span>
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={handleCloseInspector}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer border border-slate-700 shadow-sm"
              >
                <X className="w-4 h-4 text-slate-400" />
                <span>Close Inspector</span>
              </button>
            </div>

            {/* AI Rolling Memory Card */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs shadow-inner">
              <span className="text-[11px] font-mono text-purple-400 font-bold uppercase flex items-center space-x-1.5 mb-1.5">
                <Brain className="w-3.5 h-3.5 text-purple-400" />
                <span>AI Rolling Compact Memory</span>
              </span>
              <p className="text-slate-300 font-sans leading-relaxed text-xs">
                {selectedRun.compact_memory ? selectedRun.compact_memory.replace(/\*\*/g, '').replace(/\*/g, '') : 'Awaiting initial supervisor analysis...'}
              </p>
            </div>
          </div>

          {/* 2. Post-Mortem Report (Visible when Completed) */}
          {selectedRun.final_summary && (
            <FinalSummaryCard summary={selectedRun.final_summary} />
          )}

          {/* 3. Action Panel: Send Events & Human Guidance (Guarded by State) */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Send className="w-4 h-4 text-cyan-400" />
                  <span>Workflow Actions & Event Signals</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {selectedRun.status === 'COMPLETED' || selectedRun.status === 'TERMINATED'
                    ? 'This order has reached its terminal state. No further events can be injected.'
                    : selectedRun.status === 'PAUSED'
                    ? 'Workflow is PAUSED. Resume workflow to inject events.'
                    : 'Click any signal below to trigger Tier-1 classification and autonomous AI reactions.'}
                </p>
              </div>

              {/* Pause / Resume / Terminate Controls */}
              <WorkflowControls run={selectedRun} onControlTriggered={handleManualRefresh} />
            </div>

            {/* If NOT Completed: Show Event Simulator Buttons & Operator Guidance */}
            {selectedRun.status !== 'COMPLETED' && selectedRun.status !== 'TERMINATED' ? (
              <div className="space-y-4">
                <EventSimulator runId={selectedRun.id} status={selectedRun.status} onEventSent={handleManualRefresh} />
                <div className="pt-3 border-t border-slate-800/80">
                  <InstructionInjector runId={selectedRun.id} onInstructionSent={handleManualRefresh} />
                </div>
              </div>
            ) : (
              <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center space-x-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Workflow Completed • All fulfillment SLA requirements fulfilled • Lifecycle ended.</span>
              </div>
            )}
          </div>

          {/* 4. Live Activity Timeline (Right Underneath!) */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
            <TimelineFeed logs={timeline} />
          </div>

        </div>
      )}

      {/* New Order Preset Launcher Modal */}
      <NewRunModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        supervisors={supervisors}
        onStartCreation={handleStartCreation}
        onCreated={handleOrderCreated}
      />
    </div>
  );
}
