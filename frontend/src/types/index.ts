export interface Supervisor {
  id: string;
  name: string;
  description?: string;
  base_instruction: string;
  available_tools: string[];
  wake_up_policy: 'aggressive' | 'balanced' | 'conservative';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  name: string;
  price: number;
  qty: number;
}

export interface OrderContext {
  customer_name: string;
  customer_email: string;
  items: OrderItem[];
  delivery_address: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'VIP';
  sla_hours?: number;
  [key: string]: unknown;
}

export interface FinalSummary {
  final_summary: string;
  important_actions_taken: string[];
  key_learnings: string[];
  recommendations: string[];
}

export interface OrderRun {
  id: string;
  order_id: string;
  supervisor_id: string;
  status: 'ACTIVE' | 'SLEEPING' | 'ESCALATED' | 'COMPLETED' | 'TERMINATED' | 'PAUSED';
  order_context: OrderContext;
  compact_memory: string;
  runtime_instructions: string[];
  next_wake_time?: string | null;
  last_wake_time?: string | null;
  final_summary?: FinalSummary | null;
  created_at: string;
  updated_at: string;
}

export interface ActivityLog {
  id: string;
  run_id: string;
  log_type: 'EVENT' | 'CLASSIFICATION' | 'REASONING' | 'TOOL_EXECUTION' | 'INSTRUCTION' | 'CONTROL' | 'FINAL_SUMMARY';
  trigger_source: 'START' | 'SIGNAL' | 'TIMER' | 'OPERATOR' | 'AGENT' | 'SIMULATOR';
  title: string;
  details?: string | null;
  metadata_payload?: Record<string, unknown> | null;
  timestamp: string;
}
