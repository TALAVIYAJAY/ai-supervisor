'use client';

import React, { useState, useEffect } from 'react';
import { X, Sparkles, AlertCircle, ShoppingBag, ShieldCheck, Zap } from 'lucide-react';
import { Supervisor, OrderRun } from '@/types';
import { api } from '@/lib/api';

interface NewRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  supervisors: Supervisor[];
  onCreated: (run: OrderRun) => void;
  onStartCreation?: (orderId: string) => void;
}

const PRESET_ORDERS = [
  {
    name: 'High-Value Gaming Laptop (High Priority)',
    items: [{ name: 'ASUS ROG Zephyrus G16 Laptop', price: 1899, qty: 1 }],
    customer_name: 'Jay Talaviya',
    customer_email: 'talaviyajay10@gmail.com',
    delivery_address: 'Bangalore, Karnataka, India',
    priority: 'HIGH' as const,
    sla_hours: 24,
  },
  {
    name: 'Express Ergonomic Office Chair',
    items: [{ name: 'Herman Miller Embody Chair', price: 1250, qty: 1 }],
    customer_name: 'Sarah Connor',
    customer_email: 'sarah.c@example.com',
    delivery_address: 'Indiranagar, Bangalore, India',
    priority: 'MEDIUM' as const,
    sla_hours: 48,
  },
  {
    name: 'VIP Urgent Fragile Glassware',
    items: [{ name: 'Handcrafted Italian Crystal Decanter Set', price: 650, qty: 1 }],
    customer_name: 'Alexander Wright (VIP)',
    customer_email: 'alex.wright@vipclub.com',
    delivery_address: 'Koramangala, Bangalore, India',
    priority: 'VIP' as const,
    sla_hours: 12,
  },
];

export default function NewRunModal({ isOpen, onClose, supervisors, onCreated, onStartCreation }: NewRunModalProps) {
  const [selectedPreset, setSelectedPreset] = useState(0);
  const [orderId, setOrderId] = useState('ORD-1001');
  const [supervisorId, setSupervisorId] = useState(supervisors[0]?.id || '');
  const [initialInstructions, setInitialInstructions] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Auto-generate a unique Order ID every time the modal opens
  useEffect(() => {
    if (isOpen) {
      const uniqueNum = Math.floor(1000 + Math.random() * 9000);
      setOrderId(`ORD-${uniqueNum}`);
      setError('');
      setIsSubmitting(false);
      if (supervisors.length > 0 && !supervisorId) {
        setSupervisorId(supervisors[0].id);
      }
    }
  }, [isOpen, supervisors, supervisorId]);

  if (!isOpen) return null;

  const handlePresetSelect = (index: number) => {
    setSelectedPreset(index);
    const uniqueNum = Math.floor(1000 + Math.random() * 9000);
    setOrderId(`ORD-${uniqueNum}`);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    const preset = PRESET_ORDERS[selectedPreset];
    const finalOrderId = orderId.trim() || `ORD-${Math.floor(1000 + Math.random() * 9000)}`;
    const chosenSupervisorId = supervisorId || supervisors[0]?.id;

    // Immediately close modal and trigger visualization on main page
    onClose();
    if (onStartCreation) {
      onStartCreation(finalOrderId);
    }

    try {
      const newRun = await api.createOrderRun({
        order_id: finalOrderId,
        supervisor_id: chosenSupervisorId,
        order_context: {
          ...preset,
          order_id: finalOrderId,
        },
      });

      onCreated(newRun);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start order run';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Sparkles className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Start New Order Supervisor Run</h2>
              <p className="text-xs text-slate-400">Launches long-running workflow with autonomous AI oversight</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-mono text-slate-400 uppercase mb-2">
              Select Preset Order Context
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {PRESET_ORDERS.map((preset, idx) => (
                <button
                  type="button"
                  key={preset.name}
                  onClick={() => handlePresetSelect(idx)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    selectedPreset === idx
                      ? 'bg-indigo-600/20 border-indigo-500/60 shadow-sm text-white'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center space-x-1.5 mb-1 text-cyan-400">
                    {idx === 0 ? <ShoppingBag className="w-3.5 h-3.5" /> : idx === 1 ? <ShieldCheck className="w-3.5 h-3.5" /> : <Zap className="w-3.5 h-3.5" />}
                    <span className="text-[10px] font-mono font-bold uppercase">{preset.priority}</span>
                  </div>
                  <div className="font-semibold text-xs text-slate-200 line-clamp-1">{preset.items[0].name}</div>
                  <div className="text-[11px] text-slate-400 font-mono mt-0.5">${preset.items[0].price} • {preset.sla_hours}h SLA</div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase mb-1.5">Unique Order ID</label>
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
                {supervisors.length > 0 ? (
                  supervisors.map((sup) => (
                    <option key={sup.id} value={sup.id}>
                      {sup.name} ({sup.wake_up_policy})
                    </option>
                  ))
                ) : (
                  <option value="">Standard E-commerce Supervisor (balanced)</option>
                )}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-xs font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-bold text-xs shadow-lg shadow-indigo-500/25 flex items-center space-x-2 transition-all disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'Starting Run...' : 'Start Supervisor Run'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
