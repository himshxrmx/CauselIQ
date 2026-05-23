import { Clock, Server, ChevronRight } from 'lucide-react';
import type { Incident } from '../api';

interface AlertFeedProps {
  incidents: Incident[];
  activeId: string | null;
  onSelect: (id: string) => void;
}

function timeAgo(dateStr: string): string {
  const now = new Date();
  const then = new Date(dateStr);
  const diffMs = now.getTime() - then.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return `${Math.floor(diffHr / 24)}d ago`;
}

function severityBadge(severity: string) {
  const sev = severity?.toUpperCase() || 'MEDIUM';
  const cls = `badge badge-${sev.toLowerCase()}`;
  return <span className={cls}>{sev}</span>;
}

export default function AlertFeed({ incidents, activeId, onSelect }: AlertFeedProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-sm font-semibold text-white/70 uppercase tracking-wider">
          Incident Feed
        </h2>
        <span className="text-xs text-white/30">{incidents.length} total</span>
      </div>

      {incidents.length === 0 && (
        <div className="glass-card p-8 text-center">
          <div className="w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-3">
            <Server className="w-7 h-7 text-white/20" />
          </div>
          <p className="text-sm text-white/40 font-medium">No incidents yet</p>
          <p className="text-xs text-white/25 mt-1">
            Click "Simulate Incident" to get started
          </p>
        </div>
      )}

      <div className="space-y-2 max-h-[calc(100vh-240px)] overflow-y-auto pr-1">
        {incidents.map((inc) => {
          const isActive = inc.id === activeId;
          return (
            <button
              key={inc.id}
              id={`alert-${inc.id}`}
              onClick={() => onSelect(inc.id)}
              className={`w-full text-left glass-card p-4 cursor-pointer transition-all duration-200 animate-fade-in ${
                isActive
                  ? 'border-accent-cyan/30 glow-cyan bg-gradient-to-r from-accent-cyan/5 to-transparent'
                  : 'hover:border-white/10'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className={`status-dot ${inc.status}`} />
                    {severityBadge(inc.alert.severity)}
                    <span className="text-[10px] text-white/30 uppercase font-mono">
                      #{inc.id}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-white truncate">
                    {inc.alert.service}
                  </p>
                  <p className="text-xs text-white/40 mt-0.5 truncate">
                    {inc.alert.description}
                  </p>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-white/25">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {timeAgo(inc.created_at)}
                    </span>
                    <span className="uppercase font-mono">{inc.alert.alert_type}</span>
                  </div>
                </div>
                <ChevronRight
                  className={`w-4 h-4 mt-2 flex-shrink-0 transition-colors ${
                    isActive ? 'text-accent-cyan' : 'text-white/15'
                  }`}
                />
              </div>

              {/* Analysis preview */}
              {inc.analysis && (
                <div className="mt-3 pt-3 border-t border-white/5">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-accent-green font-medium uppercase tracking-wider">
                      {inc.analysis.root_cause_category}
                    </span>
                    <span className="text-accent-cyan">
                      {Math.round(inc.analysis.confidence_score * 100)}% confidence
                    </span>
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
