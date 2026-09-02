'use client';

import React, { useState } from 'react';
import { Zap, Truck, CreditCard, MessageSquare, Clock, RotateCcw, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface EventSimulatorProps {
  runId: string;
  onEventSent: () => void;
}

const PRESET_EVENTS = [
  {
    type: 'shipment_delayed',
    label: 'Shipment Delayed',
    icon: Truck,
    color: 'bg-amber-600/20 text-amber-300 border-amber-500/40 hover:bg-amber-600/30',
    description: 'Carrier delay: 48h hub congestion',
    payload: { carrier: 'FedEx', delay_hours: 48, reason: 'Severe weather and regional hub sorting backlog' },
  },
  {
    type: 'payment_failed',
    label: 'Payment Failed',
    icon: CreditCard,
    color: 'bg-rose-600/20 text-rose-300 border-rose-500/40 hover:bg-rose-600/30',
    description: 'Card authorization declined',
    payload: { failure_code: 'INSUFFICIENT_FUNDS', gateway: 'Stripe', retry_count: 1 },
  },
  {
    type: 'customer_message_received',
    label: 'Customer Message',
    icon: MessageSquare,
    color: 'bg-cyan-600/20 text-cyan-300 border-cyan-500/40 hover:bg-cyan-600/30',
    description: 'Where is my parcel? Need it urgently!',
    payload: { channel: 'sms', sender: 'Customer', message_text: 'Hi, I need this laptop before Friday. Is delivery on track?' },
  },
  {
    type: 'no_update_for_n_hours',
    label: 'No Carrier Update (24h)',
    icon: Clock,
    color: 'bg-purple-600/20 text-purple-300 border-purple-500/40 hover:bg-purple-600/30',
    description: 'SLA timeout threshold triggered',
    payload: { hours_without_update: 24, last_checkpoint: 'Transit Hub' },
  },
  {
    type: 'refund_requested',
    label: 'Refund Requested',
    icon: RotateCcw,
    color: 'bg-orange-600/20 text-orange-300 border-orange-500/40 hover:bg-orange-600/30',
    description: 'Customer initiated return request',
    payload: { reason: 'Delivery taking longer than expected', requested_amount: 1499.0 },
  },
  {
    type: 'delivered',
    label: 'Order Delivered',
    icon: CheckCircle,
    color: 'bg-emerald-600/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-600/30',
    description: 'Terminal trigger: Signed & verified',
    payload: { signed_by: 'Jay Talaviya', delivery_time: new Date().toISOString(), carrier_proof: 'SIGNATURE_VERIFIED' },
  },
];

export default function EventSimulator({ runId, onEventSent }: EventSimulatorProps) {
  const [sendingEvent, setSendingEvent] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleInject = async (event: typeof PRESET_EVENTS[0]) => {
    setSendingEvent(event.type);
    setStatusMsg(null);

    try {
      await api.injectEvent(runId, event.type, event.payload);
      setStatusMsg(`Dispatched '${event.label}' signal into workflow!`);
      onEventSent();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to send event';
      setStatusMsg(`Error: ${msg}`);
    } finally {
      setSendingEvent(null);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-amber-600/20 text-amber-400 border border-amber-500/30">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Event Generator & Simulator</h3>
            <p className="text-[11px] text-slate-400">Inject live signals to test Tier-1 classifier and agent reactions</p>
          </div>
        </div>
      </div>

      {statusMsg && (
        <div className="p-2.5 rounded-lg bg-indigo-950/60 border border-indigo-500/40 text-cyan-300 text-xs font-mono animate-in fade-in">
          {statusMsg}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {PRESET_EVENTS.map((event) => {
          const Icon = event.icon;
          const isPending = sendingEvent === event.type;

          return (
            <button
              key={event.type}
              onClick={() => handleInject(event)}
              disabled={sendingEvent !== null}
              className={`p-3 rounded-xl border text-left transition-all flex items-start space-x-3 disabled:opacity-50 ${event.color}`}
            >
              <div className="p-1.5 rounded-lg bg-slate-950/60 shrink-0 mt-0.5">
                {isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <div className="min-w-0">
                <span className="text-xs font-bold block truncate">{event.label}</span>
                <span className="text-[11px] opacity-80 block truncate mt-0.5 font-sans">
                  {event.description}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
