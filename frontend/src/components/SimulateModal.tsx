import { X, Play, Server } from 'lucide-react';
import type { Scenario } from '../api';

interface SimulateModalProps {
  scenarios: Record<string, Scenario>;
  loading: boolean;
  onSimulate: (scenario: string) => void;
  onClose: () => void;
}

const SCENARIO_ICONS: Record<string, string> = {
  db_connection_failure: '🗄️',
  oom_kill: '💀',
  deployment_rollback: '🔄',
  cert_expiry: '🔐',
  rate_limit: '⏱️',
};

const SCENARIO_COLORS: Record<string, string> = {
  CRITICAL: 'border-accent-red/20 hover:border-accent-red/40',
  HIGH: 'border-orange-500/20 hover:border-orange-500/40',
  MEDIUM: 'border-accent-amber/20 hover:border-accent-amber/40',
  LOW: 'border-accent-green/20 hover:border-accent-green/40',
};

export default function SimulateModal({
  scenarios,
  loading,
  onSimulate,
  onClose,
}: SimulateModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative glass-card p-6 w-full max-w-lg max-h-[85vh] overflow-y-auto animate-fade-in border-white/10">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-bold text-white">Simulate Incident</h2>
            <p className="text-xs text-white/40 mt-0.5">
              Select a scenario to trigger AI analysis
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-white/5 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5 text-white/40" />
          </button>
        </div>

        <div className="space-y-3">
          {Object.entries(scenarios).map(([key, scenario]) => (
            <button
              key={key}
              id={`scenario-${key}`}
              disabled={loading}
              onClick={() => onSimulate(key)}
              className={`w-full text-left glass-card p-4 transition-all duration-200 cursor-pointer ${
                SCENARIO_COLORS[scenario.severity] || 'border-white/10'
              } ${loading ? 'opacity-50' : ''}`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl mt-0.5">
                  {SCENARIO_ICONS[key] || '⚡'}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-white">
                      {key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                    </span>
                    <span className={`badge badge-${scenario.severity.toLowerCase()}`}>
                      {scenario.severity}
                    </span>
                  </div>
                  <p className="text-xs text-white/50">{scenario.description}</p>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-white/25">
                    <span className="flex items-center gap-1">
                      <Server className="w-3 h-3" />
                      {scenario.service}
                    </span>
                    <span className="font-mono uppercase">{scenario.alert_type}</span>
                  </div>
                </div>
                <Play className="w-4 h-4 text-accent-cyan/50 mt-2 flex-shrink-0" />
              </div>
            </button>
          ))}
        </div>

        {loading && (
          <div className="mt-4 text-center text-sm text-accent-cyan animate-pulse-glow">
            Triggering simulation...
          </div>
        )}
      </div>
    </div>
  );
}
