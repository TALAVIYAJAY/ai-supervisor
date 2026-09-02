'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, RefreshCw, CheckCircle2 } from 'lucide-react';
import { OrderRun, Supervisor } from '@/types';
import { api } from '@/lib/api';
import StatCards from '@/components/dashboard/StatCards';
import RunList from '@/components/dashboard/RunList';
import NewRunModal from '@/components/dashboard/NewRunModal';

export default function DashboardPage() {
  const router = useRouter();
  const [runs, setRuns] = useState<OrderRun[]>([]);
  const [supervisors, setSupervisors] = useState<Supervisor[]>([]);
  const [selectedFilter, setSelectedFilter] = useState('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [syncToast, setSyncToast] = useState<string | null>(null);

  // 1. On Mount / F5 & Background Poll: Safe React 19 pattern
  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        const [runsData, supsData] = await Promise.all([
          api.getOrderRuns(selectedFilter),
          api.getSupervisors()
        ]);
        if (isMounted) {
          setRuns(runsData.items || []);
          setSupervisors(supsData || []);
        }
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 4000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedFilter]);

  // 2. UI In-Place Refresh Button Handler with Full Reconcile
  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    try {
      try {
        await api.reconcileWorkflows();
      } catch {
        // Graceful fallback
      }

      const [runsData, supsData] = await Promise.all([
        api.getOrderRuns(selectedFilter),
        api.getSupervisors()
      ]);

      setRuns(runsData.items || []);
      setSupervisors(supsData || []);
      setSyncToast('Workflows synchronized & updated!');
      setTimeout(() => setSyncToast(null), 3000);
    } catch (err) {
      console.error('Error refreshing dashboard data:', err);
    } finally {
      setIsRefreshing(false);
    }
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
            Autonomous long-running Temporal workflows with 2-tier Gemini AI reasoning and event-driven wake/sleep
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Unified In-Place Refresh & Sync Button */}
          <button
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-cyan-500/50 text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-semibold flex items-center space-x-2 transition-all shadow-sm disabled:opacity-50"
            title="Refresh and synchronize all workflows with Temporal"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-cyan-400' : 'text-slate-400'}`} />
            <span>{isRefreshing ? 'Syncing...' : 'Refresh'}</span>
          </button>

          {/* Launch New Order Modal Button */}
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white text-sm font-bold shadow-lg shadow-indigo-500/25 flex items-center space-x-2 transition-all hover:scale-[1.02]"
          >
            <Plus className="w-4 h-4" />
            <span>Launch New Order</span>
          </button>
        </div>
      </div>

      {/* Sync Toast Feedback Banner */}
      {syncToast && (
        <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-xs font-mono animate-in fade-in flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-cyan-400" />
          <span>{syncToast}</span>
        </div>
      )}

      {/* Metric Stat Cards */}
      <StatCards runs={runs} />

      {/* Interactive Orders List Table */}
      <RunList
        runs={runs}
        selectedFilter={selectedFilter}
        onFilterChange={setSelectedFilter}
      />

      {/* New Order Preset Launcher Modal */}
      <NewRunModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        supervisors={supervisors}
        onCreated={(runId) => {
          handleManualRefresh();
          router.push(`/runs/${runId}`);
        }}
      />
    </div>
  );
}
