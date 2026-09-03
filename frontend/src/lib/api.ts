import axios from 'axios';
import { Supervisor, OrderRun, ActivityLog } from '../types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 60 seconds to prevent premature client timeouts
});

export const api = {
  getSupervisors: async (): Promise<Supervisor[]> => {
    try {
      const res = await apiClient.get<Supervisor[]>('/v1/supervisors');
      return res.data;
    } catch (err) {
      console.warn('Error fetching supervisors:', err);
      return [];
    }
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
    try {
      const params = status && status !== 'ALL' ? { status } : {};
      const res = await apiClient.get<{ items: OrderRun[]; total: number }>('/v1/runs', { params });
      return res.data;
    } catch (err) {
      console.warn('Error fetching order runs:', err);
      return { items: [], total: 0 };
    }
  },

  getOrderRun: async (runId: string): Promise<OrderRun | null> => {
    try {
      const res = await apiClient.get<OrderRun>(`/v1/runs/${runId}`);
      return res.data;
    } catch (err) {
      console.warn(`Error fetching order run ${runId}:`, err);
      return null;
    }
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
    try {
      const res = await apiClient.get<ActivityLog[]>(`/v1/runs/${runId}/timeline`);
      return res.data;
    } catch (err) {
      console.warn(`Error fetching timeline for ${runId}:`, err);
      return [];
    }
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
      const res = await axios.get('http://localhost:8000/health', { timeout: 4000 });
      return res.data;
    } catch {
      return null;
    }
  }
};

// Helper to extract clean error message from axios error
export function getErrorMessage(err: unknown, fallback: string = 'An error occurred'): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail === 'object') return JSON.stringify(detail);
    if (err.response?.status === 400) return 'Action not permitted in current workflow state.';
    if (err.response?.status === 404) return 'Order run not found.';
    if (err.response?.status === 500) return 'Internal server error occurred.';
  }
  if (err instanceof Error) return err.message;
  return fallback;
}
