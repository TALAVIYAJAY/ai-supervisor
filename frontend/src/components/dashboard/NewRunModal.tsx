'use client';

import React, { useState } from 'react';
import { X, Play, Sparkles } from 'lucide-react';
import { Supervisor } from '@/types';
import { api } from '@/lib/api';

interface NewRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  supervisors: Supervisor[];
  onCreated: (runId: string) => void;
}

const PRESET_ORDERS = [
  {
    name: 'High-Value Gaming Laptop (High Priority)',
    order_id: 'ORD-1001',
    items: [{ name: 'ASUS ROG Zephyrus G16 Laptop', price: 1899, qty: 1 }],
    customer_name: 'Jay Talaviya',
    customer_email: 'talaviyajay10@gmail.com',
    delivery_address: 'Bangalore, Karnataka, India',
    priority: 'HIGH' as const,
    sla_hours: 24,
  },
  {
    name: 'Express Ergonomic Office Chair',
    order_id: 'ORD-1002',
    items: [{ name: 'Herman Miller Embody Chair', price: 1250, qty: 1 }],
    customer_name: 'Sarah Connor',
    customer_email: 'sarah.c@example.com',
    delivery_address: 'Indiranagar, Bangalore, India',
    priority: 'MEDIUM' as const,
    sla_hours: 48,
  },
  {
    name: 'VIP Urgent Fragile Glassware',
    order_id: 'ORD-1003',
    items: [{ name: 'Handcrafted Italian Crystal Decanter Set', price: 650, qty: 1 }],
    customer_name: 'Alexander Wright (VIP)',
    customer_email: 'alex.wright@vipclub.com',
    delivery_address: 'Koramangala, Bangalore, India',
    priority: 'VIP' as const,
    sla_hours: 12,
  },
];

export default function NewRunModal({ isOpen, onClose, supervisors, onCreated }: NewRunModalProps) {
  const [selectedPreset, setSelectedPreset] = useState(0);
  const [orderId, setOrderId] = useState(PRESET_ORDERS[0].order_id);
  const [supervisorId, setSupervisorId] = useState(supervisors[0]?.id || '');
  const [initialInstructions, setInitialInstructions] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handlePresetSelect = (index: number) => {
    setSelectedPreset(index);
    setOrderId(PRESET_ORDERS[index].order_id);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      const preset = PRESET_ORDERS[selectedPreset];
      const newRun = await api.createOrderRun({
        order_id: orderId || preset.order_id,
        supervisor_id: supervisorId || supervisors[0]?.id,
        order_context: {
          ...preset,
          order_id: orderId || preset.order_id,
        },
        initial_instructions: initialInstructions || undefined,
      });

      onCreated(newRun.id);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start order run';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-150">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Play className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold text-white">Start New Order Supervisor Run</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-mono text-slate-400 uppercase mb-2 flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>Choose Order Scenario Preset</span>
            </label>
            <div className="grid grid-cols-1 gap-2">
              {PRESET_ORDERS.map((preset, idx) => (
                <button
                  type="button"
                  key={preset.name}
                  onClick={() => handlePresetSelect(idx)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    selectedPreset === idx
                      ? 'bg-indigo-600/20 border-indigo-500/60 text-white shadow-sm'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold">{preset.name}</span>
                    <span className="text-xs font-mono text-cyan-400">${preset.items[0].price}</span>
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Customer: {preset.customer_name} • SLA: {preset.sla_hours}h
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase mb-1.5">Order ID</label>
              <input
                type="text"
                value={orderId}
                onChange={(e) => setOrderId(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono text-sm focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase mb-1.5">Supervisor Template</label>
              <select
                value={supervisorId}
                onChange={(e) => setSupervisorId(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
              >
                {supervisors.map((sup) => (
                  <option key={sup.id} value={sup.id}>
                    {sup.name} ({sup.wake_up_policy})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 uppercase mb-1.5">
              Optional Initial Guidance / Instructions
            </label>
            <textarea
              rows={2}
              value={initialInstructions}
              onChange={(e) => setInitialInstructions(e.target.value)}
              placeholder="e.g. For this order, prioritize speed over cost."
              className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500 placeholder:text-slate-600"
            />
          </div>

          <div className="pt-2 flex items-center justify-end space-x-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-sm font-bold shadow-lg shadow-indigo-500/25 transition-all flex items-center space-x-2 disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{isSubmitting ? 'Starting Workflow...' : 'Launch Supervisor'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
