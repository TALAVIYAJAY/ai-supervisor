import axios from 'axios';
import { Supervisor, OrderRun, ActivityLog } from '../types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const api = {
  getSupervisors: async (): Promise<Supervisor[]> => {
    const res = await apiClient.get<Supervisor[]>('/v1/supervisors');
    return res.data;
  },

  createSupervisor: async (data: Partial<Supervisor>): Promise<Supervisor> => {
    const res = await apiClient.post<Supervisor>('/v1/supervisors', data);
    return res.data;
  },

  getSupervisorById: async (id: string): Promise<Supervisor> => {
    const res = await apiClient.get<Supervisor>(`/v1/supervisors/${id}`);
    return res.data;
  },

  getOrderRuns: async (status?: string): Promise<{ items: OrderRun[]; total: number }> => {
    const params = status && status !== 'ALL' ? { status } : {};
    const res = await apiClient.get<{ items: OrderRun[]; total: number }>('/v1/runs', { params });
    return res.data;
  },

  getOrderRun: async (runId: string): Promise<OrderRun> => {
    const res = await apiClient.get<OrderRun>(`/v1/runs/${runId}`);
    return res.data;
  },

  createOrderRun: async (data: {
    order_id: string;
    supervisor_id?: string;
    order_context: Record<string, unknown>;
    initial_instructions?: string;
  }): Promise<OrderRun> => {
    const res = await apiClient.post<OrderRun>('/v1/runs', data);
    return res.data;
  },

  getTimeline: async (runId: string): Promise<ActivityLog[]> => {
    const res = await apiClient.get<ActivityLog[]>(`/v1/runs/${runId}/timeline`);
    return res.data;
  },

  injectEvent: async (runId: string, event_type: string, payload: Record<string, unknown> = {}) => {
    const res = await apiClient.post(`/v1/runs/${runId}/events`, { event_type, payload });
    return res.data;
  },

  injectInstruction: async (runId: string, instruction: string) => {
    const res = await apiClient.post(`/v1/runs/${runId}/instructions`, { instruction });
    return res.data;
  },

  controlWorkflow: async (runId: string, action: 'pause' | 'resume' | 'terminate' | 'wake', reason?: string) => {
    const res = await apiClient.post(`/v1/runs/${runId}/controls`, { action, reason });
    return res.data;
  },

  reconcileWorkflows: async () => {
    const res = await apiClient.post<{
      status: string;
      total_checked: number;
      healthy_count: number;
      healed_count: number;
      message: string;
    }>('/v1/reconcile');
    return res.data;
  },

  checkHealth: async () => {
    try {
      const res = await axios.get('http://localhost:8000/health', { timeout: 3000 });
      return res.data;
    } catch {
      return null;
    }
  }
};
