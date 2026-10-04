// frontend/lib/api.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Auth Helpers ──────────────────────────────────────────────
function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') {
    return {};
  }
  const token = localStorage.getItem('access_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// ── Shared Types ──────────────────────────────────────────────
export interface DataQualityFinding {
  rule_id: string;
  rule_name: string;
  severity: 'ERROR' | 'WARNING' | 'INFO';
  description: string;
  count: number;
  impact_summary?: string;
  details?: Record<string, any>;
  provenance_records?: ProvenanceTrace[];
}

export interface ProvenanceTrace {
  finding_id: string;
  rule_id: string;
  rule_name: string;
  severity: 'ERROR' | 'WARNING' | 'INFO';
  source_table: string;
  source_field: string;
  record_identifier: string;
  subject_id: string | number;
  timestamp: string;
  query_rule: string;
  transformation: string;
  status: string;
}

export interface DataQualityReport {
  summary: {
    total_findings: number;
    errors: number;
    warnings: number;
    info: number;
    total_row_findings: number;
    total_dataset_findings: number;
  };
  row_findings: DataQualityFinding[];
  dataset_findings: DataQualityFinding[];
  provenance: ProvenanceTrace[];
}

export interface AIExplanation {
  summary: string;
  key_findings: string[];
  limitations: string[];
  uncertainty: string[];
  available?: boolean;
}

export interface ChatResponse {
  query: string;
  sql_query: string;
  explanation: string;
  ai_explanation?: AIExplanation;
  inclusion_criteria?: string[];
  exclusion_criteria?: string[];
  limitations?: string[];
  results: Record<string, any>[];
  data_quality_report: DataQualityReport;
  provenance: ProvenanceTrace[];
  source_tables?: string[];
  execution_time_ms: number;
  total_rows: number;
  error?: string;
}

export interface QualityRule {
  rule_id: string;
  name: string;
  description: string;
  category: string;
  severity: 'ERROR' | 'WARNING' | 'INFO';
  version: string;
}

export interface TableOverview {
  table_name: string;
  purpose?: string;
  row_count: number;
  column_count: number;
  columns: { name: string; type: string }[];
  data_summary?: {
    summary_type?: string;
    chart_label?: string;
    items: Array<{ label: string; value: number }>;
  };
}

export interface InsightsResponse {
  timestamp: string;
  database_overview: {
    total_tables: number;
    total_rows: number;
    total_columns: number;
    largest_table: string;
  };
  table_inventory: TableOverview[];
  missingness_report: Array<{
    table_name: string;
    column_name: string;
    total_rows: number;
    missing_rows: number;
    missing_pct: number;
    severity: string;
  }>;
  duplicate_analysis: Record<string, { total_rows: number; duplicate_rows: number; duplicate_pct: number }>;
  unit_variation: {
    labevents_unit_variation: {
      items_with_multiple_units: number;
      details: Array<{ item_id: number; label: string; unit_counts: Record<string, number> }>;
    };
    chartevents_unit_variation: {
      items_with_multiple_units: number;
      details: Array<{ item_id: number; label: string; unit_counts: Record<string, number> }>;
    };
  };
  measurement_coverage: {
    total_patients: number;
    patients_with_lab_data: number;
    patients_with_chart_data: number;
    lab_coverage_pct: number;
    chart_coverage_pct: number;
  };
  coding_patterns: {
    icd_version_distribution: Record<string, number>;
    total_diagnoses: number;
    admissions_with_mixed_icd_versions: number;
  };
  quality_summary: {
    total_flags: number;
    missingness_flags?: number;
    duplicate_flags?: number;
    unit_variation_flags?: number;
    coding_flags?: number;
    rules_applied?: number;
    total_database_findings?: number;
    severity_breakdown?: Record<string, number>;
  };
}

// ── Auth Types ────────────────────────────────────────────────
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    name: string;
    email: string;
  };
}

export interface HistoryItem {
  id: number;
  query: string;
  sql_query: string;
  total_rows: number;
  execution_time_ms: number;
  quality_flags_count: number;
  created_at: string;
}

export interface HistoryResponse {
  history: HistoryItem[];
}

// ── Public Endpoints ──────────────────────────────────────────

export async function checkBackendHealth(): Promise<{ status: string; service?: string; error?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err: any) {
    return { status: 'error', error: err.message || 'Failed to connect to backend server' };
  }
}

export async function sendQuery(query: string): Promise<ChatResponse> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  };
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || `Server error ${res.status}`);
  }
  return await res.json();
}

export async function fetchDatasetInsights(): Promise<InsightsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/insights`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch dataset insights: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchQualityRules(): Promise<{ total_rules: number; rules: QualityRule[] }> {
  const res = await fetch(`${API_BASE_URL}/api/rules`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch quality rules: ${res.statusText}`);
  }
  return await res.json();
}

export async function fetchSchema(): Promise<{
  total_tables: number;
  schema: Record<string, { row_count: number; columns: Array<{ name: string; type: string }> }>;
}> {
  const res = await fetch(`${API_BASE_URL}/api/schema`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`Failed to fetch DB schema: ${res.statusText}`);
  }
  return await res.json();
}

// ── Auth Endpoints ────────────────────────────────────────────

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Login failed');
  }
  return res.json();
}

export async function signup(name: string, email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Signup failed');
  }
  return res.json();
}

export async function getCurrentUser(): Promise<{ id: number; name: string; email: string }> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  };
  const res = await fetch(`${API_BASE_URL}/api/auth/me`, { headers });
  if (!res.ok) {
    throw new Error('Failed to fetch user profile');
  }
  return res.json();
}

export async function saveHistory(
  query: string,
  sql_query: string,
  total_rows: number,
  execution_time_ms: number,
  quality_flags_count: number
): Promise<{ status: string }> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  };
  const res = await fetch(`${API_BASE_URL}/api/auth/history`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ query, sql_query, total_rows, execution_time_ms, quality_flags_count }),
  });
  if (!res.ok) {
    throw new Error('Failed to save history');
  }
  return res.json();
}

export async function getHistory(): Promise<HistoryResponse> {
  const headers: HeadersInit = {
    ...getAuthHeaders(),
  };
  const res = await fetch(`${API_BASE_URL}/api/auth/history`, { headers });
  if (!res.ok) {
    throw new Error('Failed to fetch history');
  }
  return res.json();
}