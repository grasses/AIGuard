
export interface User {
  id: string;
  username: string;
  email: string;
  role: 'user' | 'admin' | 'super_admin';
  balance: number;
  status: 'active' | 'inactive' | 'locked';
  created_at?: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface Asset {
  id: string;
  owner_id: string;
  type: 'llm' | 'mcp' | 'memory';
  name: string;
  enabled: boolean;
  connectivity: string;
  visibility: string;
  notes?: string;
  provider?: string;
  protocol?: string;
  base_url?: string;
  api_key?: string;
  model_names?: string[];
  max_tokens?: number;
  timeout_seconds?: number;
  max_retries?: number;
  temperature?: number;
  group_ids?: string[];
  tool_name?: string;
  description?: string;
  endpoint_url?: string;
  method?: string;
  authentication_type?: string;
  parameter_schema?: any;
  required_parameters?: string[];
  response_mapping?: any;
  index_name?: string;
  max_tokens_capacity?: number;
  persist?: boolean;
  expire_days?: number;
  created_at?: string;
  updated_at?: string;
}

export interface AssetCreateRequest {
  type: string;
  name: string;
  enabled?: boolean;
  visibility?: string;
  notes?: string;
  provider?: string;
  protocol?: string;
  base_url?: string;
  api_key?: string;
  model_names?: string[];
  max_tokens?: number;
  timeout_seconds?: number;
  max_retries?: number;
  temperature?: number;
  tool_name?: string;
  description?: string;
  endpoint_url?: string;
  method?: string;
  authentication_type?: string;
  parameter_schema?: any;
  required_parameters?: string[];
  response_mapping?: any;
  index_name?: string;
  max_tokens_capacity?: number;
  persist?: boolean;
  expire_days?: number;
}

export interface AssetUpdateRequest extends Partial<AssetCreateRequest> {}

export interface Guardrail {
  id: string;
  owner_id: string;
  name: string;
  guardrail_type: string;
  domain: string;
  position: string;
  description?: string;
  default_priority: number;
  enabled: boolean;
  endpoint_url: string;
  timeout_ms: number;
  retry_count: number;
  health_check_path?: string;
  supports_multimodal: boolean;
  streaming_enabled: boolean;
  window_tokens?: number;
  window_overlap?: number;
  hit_action: string;
  alert_methods?: string[];
  alert_recipients?: string[];
  webhook_url?: string;
  correct_template?: string;
  match_conditions?: any;
  ext_params?: any;
  created_at?: string;
  updated_at?: string;
}

export interface GuardrailCreateRequest {
  name: string;
  guardrail_type: string;
  domain: string;
  position: string;
  description?: string;
  default_priority?: number;
  enabled?: boolean;
  endpoint_url: string;
  timeout_ms?: number;
  retry_count?: number;
  health_check_path?: string;
  supports_multimodal?: boolean;
  streaming_enabled?: boolean;
  window_tokens?: number;
  window_overlap?: number;
  hit_action?: string;
  alert_methods?: string[];
  alert_recipients?: string[];
  webhook_url?: string;
  correct_template?: string;
  match_conditions?: any;
  ext_params?: any;
}

export interface GuardrailUpdateRequest extends Partial<GuardrailCreateRequest> {}

export interface TrafficConfig {
  id: string;
  owner_id: string;
  name: string;
  description?: string;
  enabled: boolean;
  execution_mode: string;
  assets_summary?: { name: string }[];
  pre_guardrail_count: number;
  post_guardrail_count: number;
  request_count_24h: number;
  block_rate_24h: number;
  created_at?: string;
  updated_at?: string;
}

export interface TrafficConfigDetail extends TrafficConfig {
  asset_ids: string[];
  guardrail_entries: {
    id: string;
    guardrail_id: string;
    guardrail_name: string;
    position: string;
    priority: number;
    enabled: boolean;
  }[];
}

export interface TrafficConfigCreateRequest {
  name: string;
  description?: string;
  enabled?: boolean;
  execution_mode?: string;
  asset_ids: string[];
  guardrail_entries: {
    guardrail_id: string;
    position: string;
    priority: number;
    enabled?: boolean;
  }[];
}

export interface RequestLog {
  id: string;
  user_id?: string;
  request_id: string;
  model: string;
  status: string;
  request_tokens: number;
  response_tokens: number;
  latency_ms: number;
  cost: number;
  points_consumed: number;
  blocked_by?: string;
  block_reason?: string;
  created_at?: string;
}

export interface RequestLogDetail extends RequestLog {
  request_messages?: any;
  response_content?: string;
  guardrail_results?: any;
  traffic_config_id?: string;
  asset_id?: string;
}

export interface DashboardStats {
  total_requests_24h: number;
  blocked_requests_24h: number;
  block_rate_24h: number;
  avg_latency_ms_24h: number;
  total_tokens_24h: number;
  points_consumed_24h: number;
  active_users_24h?: number;
  total_users?: number;
  chart_data: { time: string; count: number }[];
}

export interface AlertRule {
  id: string;
  user_id: string;
  name: string;
  enabled: boolean;
  metric: string;
  condition: string;
  threshold: number;
  window_minutes: number;
  notify_methods: string[];
  last_triggered_at?: string;
  created_at?: string;
}

export interface AlertEvent {
  id: string;
  rule_id?: string;
  level: string;
  title: string;
  message?: string;
  is_read: boolean;
  created_at?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  enabled: boolean;
  last_used_at?: string;
  created_at?: string;
}
