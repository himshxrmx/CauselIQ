import axios from 'axios';

const api = axios.create({
  baseURL: 'https://kzbxxn5kmovcc3lckuwamdps6u0miody.lambda-url.us-east-1.on.aws/api',
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

export interface Analysis {
  probable_cause: string;
  confidence_score: number;
  severity: string;
  impact_analysis: string;
  actionable_remediation: RemediationStep[];
  root_cause_category: string;
  timeline: TimelineEvent[];
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

export const simulateIncident = (scenario: string) =>
  api.post<{ incident_id: string; status: string }>('/simulate', { scenario });

export const fetchScenarios = () => api.get<Record<string, Scenario>>('/scenarios');

export const fetchStats = () => api.get<Stats>('/stats');

export const fetchHealth = () => api.get('/health');

export const uploadLogs = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post<{ incident_id: string; status: string }>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export default api;
