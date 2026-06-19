import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
});

export interface Alert {
  service: string;
  timestamp: string;
  alert_type: string;
  description: string;
  log_group?: string;
  region: string;
  severity: string;
}

export interface RemediationStep {
  step: number;
  action: string;
  command: string;
}

export interface TimelineEvent {
  time: string;
  event: string;
}

export interface ExtractedContext {
  error_type: string;
  filepath: string;
  line_number: number;
  variables: string[];
  error_patterns: string[];
}

export interface LogDiagnostician {
  status: 'CORRECT' | 'WRONG';
  confidence_score: number;
  diagnostic_summary: string;
  extracted_context: ExtractedContext;
}

export interface CodeAnalyst {
  root_cause: string;
  code_analysis: string;
  config_analysis: string;
  suggested_fix: string;
}

export interface AgentPhases {
  log_diagnostician: LogDiagnostician;
  code_analyst: CodeAnalyst | null;
}

export interface Analysis {
  probable_cause: string;
  confidence_score: number;
  severity: string;
  impact_analysis: string;
  actionable_remediation: RemediationStep[];
  root_cause_category: string;
  timeline: TimelineEvent[];
  agent_phases?: AgentPhases;
  hotfix_diff?: string;
}

export interface Incident {
  id: string;
  alert: Alert;
  raw_logs?: { timestamp: string; message: string; logStreamName: string }[];
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  analysis: Analysis | null;
  error: string | null;
}

export interface Scenario {
  service: string;
  alert_type: string;
  severity: string;
  description: string;
}

export interface Stats {
  total_incidents: number;
  completed: number;
  analyzing: number;
  failed: number;
  severity_breakdown: Record<string, number>;
  category_breakdown: Record<string, number>;
  avg_confidence: number;
}

export const fetchAlerts = () => api.get<Incident[]>('/alerts');

export const fetchAlert = (id: string) => api.get<Incident>(`/alerts/${id}`);

export const simulateIncident = (scenarioId: string) => 
  api.post<{ incident: Incident; scenario: string; message: string }>('/simulate', { scenario: scenarioId });

export const fetchScenarios = () => api.get<Record<string, Scenario>>('/scenarios');

export const fetchStats = () => api.get<Stats>('/stats');

export const fetchHealth = () => api.get('/health');

export const uploadLogs = (file: File, codeFile?: File) => {
  const formData = new FormData();
  formData.append('file', file);
  if (codeFile) {
    formData.append('code_file', codeFile);
  }
  return api.post<{ incident: Incident; message: string }>('/upload', formData);
};

export default api;
