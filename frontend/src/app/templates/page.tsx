'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft, Layers, Plus, Save, Shield, Check } from 'lucide-react';
import { Supervisor } from '@/types';
import { api, apiClient } from '@/lib/api';

export default function TemplatesPage() {
  const [supervisors, setSupervisors] = useState<Supervisor[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [isCreating, setIsCreating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [baseInstruction, setBaseInstruction] = useState('');
  const [wakeUpPolicy, setWakeUpPolicy] = useState<'aggressive' | 'balanced' | 'conservative'>('balanced');
  const [modelName, setModelName] = useState('gemini-3.7-flash');

  const selectTemplate = (sup: Supervisor) => {
    setIsCreating(false);
    setSelectedId(sup.id);
    setName(sup.name);
    setDescription(sup.description || '');
    setBaseInstruction(sup.base_instruction);
    setWakeUpPolicy(sup.wake_up_policy);
    setModelName(sup.model_name || 'gemini-3.7-flash');
    setSaveSuccess(false);
  };

  useEffect(() => {
    let isMounted = true;
    const loadSupervisors = async () => {
      try {
        const data = await api.getSupervisors();
        if (isMounted && data) {
          setSupervisors(data);
          if (data.length > 0) {
            selectTemplate(data[0]);
          }
        }
      } catch (err) {
        console.error('Error fetching supervisors:', err);
      }
    };

    loadSupervisors();
    return () => {
      isMounted = false;
    };
  }, []);

  const startNewTemplate = () => {
    setIsCreating(true);
    setSelectedId('');
    setName('New Custom Supervisor');
    setDescription('Tailored operational supervisor for custom SLA requirements.');
    setBaseInstruction('You are an autonomous Order Operations Supervisor. Analyze incoming exceptions and inquiries.');
    setWakeUpPolicy('balanced');
    setModelName('gemini-3.7-flash');
    setSaveSuccess(false);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      if (isCreating) {
        const created = await api.createSupervisor({
          name,
          description,
          base_instruction: baseInstruction,
          wake_up_policy: wakeUpPolicy,
          model_name: modelName,
        });
        const allSups = await api.getSupervisors();
        setSupervisors(allSups);
        selectTemplate(created);
      } else {
        await apiClient.put(`/v1/supervisors/${selectedId}`, {
          name,
          description,
          base_instruction: baseInstruction,
          wake_up_policy: wakeUpPolicy,
          model_name: modelName,
        });
        const allSups = await api.getSupervisors();
        setSupervisors(allSups);
      }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error';
      alert(`Save failed: ${msg}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div className="flex items-center space-x-4">
          <Link
            href="/"
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center space-x-2.5">
              <Layers className="w-6 h-6 text-cyan-400" />
              <span>Supervisor Template Configuration</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Configure system prompts, Tier-1 classifier wake-up sensitivity, and LLM orchestration settings
            </p>
          </div>
        </div>

        <button
          onClick={startNewTemplate}
          className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-500/20 flex items-center space-x-2 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Template</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-4 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-400 font-bold px-1">Available Personas</h3>
          {supervisors.map((sup) => (
            <button
              key={sup.id}
              onClick={() => selectTemplate(sup)}
              className={`w-full p-4 rounded-xl border text-left transition-all ${
                selectedId === sup.id && !isCreating
                  ? 'bg-indigo-600/20 border-indigo-500/60 shadow-md text-white'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-white">{sup.name}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-950 text-cyan-400 border border-slate-800">
                  {sup.wake_up_policy}
                </span>
              </div>
              <p className="text-xs text-slate-400 line-clamp-2 mt-1 font-sans">
                {sup.description || 'No description provided.'}
              </p>
            </button>
          ))}
        </div>

        <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-base font-bold text-white">
                {isCreating ? 'Create Supervisor Template' : `Editing: ${name}`}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {isCreating ? 'Define a new autonomous supervisor setup' : `ID: ${selectedId}`}
              </p>
            </div>

            {saveSuccess && (
              <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-mono font-bold animate-in fade-in">
                <Check className="w-3.5 h-3.5" />
                <span>Saved successfully!</span>
              </span>
            )}
          </div>

          <form onSubmit={handleSave} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">Template Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">Model Engine</label>
                <select
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="gemini-3.7-flash">Google Gemini 3.7 Flash (Default / Recommended)</option>
                  <option value="gemini-2.5-flash">Google Gemini 2.5 Flash</option>
                  <option value="gemini-2.0-flash">Google Gemini 2.0 Flash</option>
                  <option value="gemini-1.5-flash">Google Gemini 1.5 Flash</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">Description</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-slate-400 mb-2 flex items-center space-x-1.5">
                <Shield className="w-3.5 h-3.5 text-cyan-400" />
                <span>Tier-1 Classifier Wake-Up Policy</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { id: 'balanced', label: 'Balanced (Standard)', desc: 'Wakes on delays, payment failures, customer questions, and terminal events.' },
                  { id: 'aggressive', label: 'Aggressive (VIP)', desc: 'Wakes on almost every event and carrier ping for zero-delay intervention.' },
                  { id: 'conservative', label: 'Conservative (Low Noise)', desc: 'Wakes strictly on critical failures or order cancellations.' },
                ].map((pol) => (
                  <button
                    type="button"
                    key={pol.id}
                    onClick={() => setWakeUpPolicy(pol.id as 'aggressive' | 'balanced' | 'conservative')}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      wakeUpPolicy === pol.id
                        ? 'bg-cyan-600/20 border-cyan-500/60 text-white shadow-sm'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                    }`}
                  >
                    <span className="text-xs font-bold block capitalize text-white mb-1">{pol.label}</span>
                    <span className="text-[11px] text-slate-400 font-sans block leading-relaxed">{pol.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5 flex items-center justify-between">
                <span>Base System Instruction (Prompt)</span>
                <span className="text-[11px] text-slate-500 lowercase">Injected into Tier-2 Agent reasoning loop</span>
              </label>
              <textarea
                rows={6}
                value={baseInstruction}
                onChange={(e) => setBaseInstruction(e.target.value)}
                className="w-full p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono text-xs leading-relaxed focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                type="submit"
                disabled={isSaving}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 flex items-center space-x-2 transition-all disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>{isSaving ? 'Saving...' : isCreating ? 'Create Template' : 'Save Changes'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
