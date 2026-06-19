import { useState } from 'react';
import {
  AlertCircle,
  Brain,
  Wrench,
  Clock,
  ChevronDown,
  ChevronUp,
  Terminal,
  FileText,
  Shield,
  Target,
  Copy,
  Check,
  Cpu,
  Code,
  GitBranch,
  Zap,
  Search,
  Layers,
} from 'lucide-react';
import type { Incident } from '../api';

interface InvestigationPanelProps {
  incident: Incident | null;
}

export default function InvestigationPanel({ incident }: InvestigationPanelProps) {
  const [logsOpen, setLogsOpen] = useState(false);
  const [timelineOpen, setTimelineOpen] = useState(true);
  const [agentDetailsOpen, setAgentDetailsOpen] = useState(true);
  const [hotfixOpen, setHotfixOpen] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [copiedDiff, setCopiedDiff] = useState(false);

  const copyCommand = (cmd: string, idx: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const copyDiff = (diff: string) => {
    navigator.clipboard.writeText(diff);
    setCopiedDiff(true);
    setTimeout(() => setCopiedDiff(false), 2000);
  };

  if (!incident) {
    return (
      <div className="glass-card p-12 text-center min-h-[500px] flex flex-col items-center justify-center">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-accent-cyan/10 to-accent-purple/10 flex items-center justify-center mb-4">
          <Brain className="w-10 h-10 text-accent-cyan/30" />
        </div>
        <h3 className="text-lg font-semibold text-white/50 mb-2">
          Select an Incident to Investigate
        </h3>
        <p className="text-sm text-white/25 max-w-sm">
          Choose an incident from the feed or simulate a new one to see the AI-powered root cause analysis.
        </p>
      </div>
    );
  }

  const { alert, analysis, status, raw_logs } = incident;
  const phases = analysis?.agent_phases;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ─── Incident Summary Banner ─── */}
      <div className="glass-card p-5 border-l-4 border-l-accent-cyan">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="w-4 h-4 text-accent-cyan" />
              <span className="text-xs text-white/40 uppercase tracking-wider font-medium">
                Incident #{incident.id}
              </span>
              <span className={`badge badge-${alert.severity?.toLowerCase()}`}>
                {alert.severity}
              </span>
            </div>
            <h2 className="text-xl font-bold text-white">{alert.service}</h2>
            <p className="text-sm text-white/50 mt-1">{alert.description}</p>
          </div>
          <div className="text-right text-xs text-white/30 space-y-1">
            <p className="flex items-center gap-1.5 justify-end">
              <Clock className="w-3.5 h-3.5" />
              {new Date(alert.timestamp).toLocaleString()}
            </p>
            <p className="font-mono">{alert.alert_type}</p>
            <p>{alert.region}</p>
          </div>
        </div>
      </div>

      {/* ─── Multi-Agent Pipeline Indicator ─── */}
      {(status === 'completed' || status === 'analyzing' || status === 'pending') && (
        <div className="glass-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Layers className="w-4 h-4 text-accent-purple" />
            <span className="text-xs font-semibold text-accent-purple uppercase tracking-wider">
              Multi-Agent Pipeline
            </span>
          </div>
          <div className="flex items-center justify-between gap-2">
            {/* Agent 1 */}
            <div className="flex-1 flex flex-col items-center text-center">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-1.5 transition-all ${
                status === 'completed' ? 'bg-accent-green/15 ring-1 ring-accent-green/30' :
                status === 'analyzing' ? 'bg-accent-cyan/15 ring-1 ring-accent-cyan/30 animate-pulse' :
                'bg-white/5 ring-1 ring-white/10'
              }`}>
                <Search className={`w-5 h-5 ${
                  status === 'completed' ? 'text-accent-green' :
                  status === 'analyzing' ? 'text-accent-cyan' : 'text-white/30'
                }`} />
              </div>
              <span className="text-[10px] text-white/50 font-medium">Log Triage</span>
              <span className="text-[9px] text-white/25">Agent 1</span>
            </div>

            <div className={`flex-shrink-0 w-8 h-px ${status === 'completed' ? 'bg-accent-green/40' : 'bg-white/10'}`} />

            {/* Agent 2 */}
            <div className="flex-1 flex flex-col items-center text-center">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-1.5 transition-all ${
                status === 'completed' && phases?.code_analyst ? 'bg-accent-green/15 ring-1 ring-accent-green/30' :
                'bg-white/5 ring-1 ring-white/10'
              }`}>
                <Code className={`w-5 h-5 ${
                  status === 'completed' && phases?.code_analyst ? 'text-accent-green' : 'text-white/30'
                }`} />
              </div>
              <span className="text-[10px] text-white/50 font-medium">Code Analysis</span>
              <span className="text-[9px] text-white/25">Agent 2</span>
            </div>

            <div className={`flex-shrink-0 w-8 h-px ${status === 'completed' ? 'bg-accent-green/40' : 'bg-white/10'}`} />

            {/* Agent 3 */}
            <div className="flex-1 flex flex-col items-center text-center">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-1.5 transition-all ${
                status === 'completed' ? 'bg-accent-green/15 ring-1 ring-accent-green/30' :
                'bg-white/5 ring-1 ring-white/10'
              }`}>
                <Zap className={`w-5 h-5 ${
                  status === 'completed' ? 'text-accent-green' : 'text-white/30'
                }`} />
              </div>
              <span className="text-[10px] text-white/50 font-medium">Synthesis</span>
              <span className="text-[9px] text-white/25">Agent 3</span>
            </div>
          </div>
        </div>
      )}

      {/* ─── Loading State ─── */}
      {(status === 'pending' || status === 'analyzing') && (
        <div className="glass-card p-8 text-center glow-purple">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-3 h-3 rounded-full bg-accent-purple animate-pulse-glow" />
            <div className="w-3 h-3 rounded-full bg-accent-cyan animate-pulse-glow [animation-delay:200ms]" />
            <div className="w-3 h-3 rounded-full bg-accent-pink animate-pulse-glow [animation-delay:400ms]" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-1">
            Multi-Agent Pipeline Running
          </h3>
          <p className="text-sm text-white/40">
            3 AI agents are analyzing {raw_logs?.length || 0} log events...
          </p>
          <div className="mt-4 max-w-xs mx-auto">
            <div className="shimmer h-2 rounded-full" />
          </div>
        </div>
      )}

      {/* ─── Error State ─── */}
      {status === 'failed' && (
        <div className="glass-card p-6 border-l-4 border-l-accent-red glow-red">
          <h3 className="text-base font-semibold text-accent-red flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Analysis Failed
          </h3>
          <p className="text-sm text-white/50 mt-2">{incident.error}</p>
        </div>
      )}

      {/* ─── Analysis Results ─── */}
      {analysis && status === 'completed' && (
        <>
          {/* Root Cause Card */}
          <div className="glass-card p-5 glow-cyan border-l-4 border-l-accent-cyan">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-accent-cyan" />
              <h3 className="text-sm font-semibold text-accent-cyan uppercase tracking-wider">
                AI Root Cause Analysis
              </h3>
            </div>
            <p className="text-base text-white/90 leading-relaxed">
              {analysis.probable_cause}
            </p>
            <div className="flex flex-wrap items-center gap-4 mt-4">
              <div className="flex-1 min-w-[180px]">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-white/40">Confidence</span>
                  <span className="text-accent-cyan font-bold">
                    {Math.round(analysis.confidence_score * 100)}%
                  </span>
                </div>
                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={{
                      width: `${analysis.confidence_score * 100}%`,
                      background: `linear-gradient(90deg, #00f0ff, ${
                        analysis.confidence_score > 0.8
                          ? '#10b981'
                          : analysis.confidence_score > 0.5
                          ? '#f59e0b'
                          : '#ef4444'
                      })`,
                    }}
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-accent-purple" />
                <span className="text-xs font-medium text-accent-purple uppercase tracking-wider">
                  {analysis.root_cause_category}
                </span>
              </div>
            </div>
          </div>

          {/* ─── Agent Pipeline Details ─── */}
          {phases && (
            <div className="glass-card p-5">
              <button
                onClick={() => setAgentDetailsOpen(!agentDetailsOpen)}
                className="flex items-center justify-between w-full cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-accent-cyan" />
                  <h3 className="text-sm font-semibold text-accent-cyan uppercase tracking-wider">
                    Agent Pipeline Details
                  </h3>
                </div>
                {agentDetailsOpen ? (
                  <ChevronUp className="w-4 h-4 text-white/30" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-white/30" />
                )}
              </button>

              {agentDetailsOpen && (
                <div className="mt-4 space-y-3">
                  {/* Agent 1 */}
                  <div className="rounded-xl bg-white/[0.02] border border-white/5 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Search className="w-4 h-4 text-accent-cyan" />
                      <span className="text-xs font-semibold text-accent-cyan">Phase 1 — Log Diagnostician</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        phases.log_diagnostician.status === 'WRONG'
                          ? 'bg-accent-red/15 text-accent-red'
                          : 'bg-accent-green/15 text-accent-green'
                      }`}>
                        {phases.log_diagnostician.status}
                      </span>
                      <span className="text-[10px] text-white/30 ml-auto">
                        {Math.round(phases.log_diagnostician.confidence_score * 100)}% confidence
                      </span>
                    </div>
                    <p className="text-sm text-white/60 mb-2">{phases.log_diagnostician.diagnostic_summary}</p>
                    {phases.log_diagnostician.status === 'WRONG' && phases.log_diagnostician.extracted_context && (
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <div className="rounded-lg bg-white/[0.03] p-2">
                          <span className="text-[10px] text-white/30 uppercase">Error Type</span>
                          <p className="text-xs text-accent-red font-mono mt-0.5">{phases.log_diagnostician.extracted_context.error_type}</p>
                        </div>
                        <div className="rounded-lg bg-white/[0.03] p-2">
                          <span className="text-[10px] text-white/30 uppercase">File</span>
                          <p className="text-xs text-white/60 font-mono mt-0.5 truncate">{phases.log_diagnostician.extracted_context.filepath}</p>
                        </div>
                        {phases.log_diagnostician.extracted_context.line_number > 0 && (
                          <div className="rounded-lg bg-white/[0.03] p-2">
                            <span className="text-[10px] text-white/30 uppercase">Line</span>
                            <p className="text-xs text-accent-amber font-mono mt-0.5">:{phases.log_diagnostician.extracted_context.line_number}</p>
                          </div>
                        )}
                        {phases.log_diagnostician.extracted_context.variables.length > 0 && (
                          <div className="rounded-lg bg-white/[0.03] p-2">
                            <span className="text-[10px] text-white/30 uppercase">Variables</span>
                            <div className="flex flex-wrap gap-1 mt-0.5">
                              {phases.log_diagnostician.extracted_context.variables.map((v, i) => (
                                <span key={i} className="text-[10px] font-mono bg-accent-purple/10 text-accent-purple px-1.5 py-0.5 rounded">{v}</span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    {phases.log_diagnostician.extracted_context?.error_patterns?.length > 0 && (
                      <div className="mt-2">
                        <span className="text-[10px] text-white/30 uppercase">Error Patterns Detected</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {phases.log_diagnostician.extracted_context.error_patterns.map((p, i) => (
                            <span key={i} className="text-[10px] bg-accent-red/10 text-accent-red/80 px-2 py-0.5 rounded-full">{p}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Agent 2 */}
                  {phases.code_analyst && (
                    <div className="rounded-xl bg-white/[0.02] border border-white/5 p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Code className="w-4 h-4 text-accent-amber" />
                        <span className="text-xs font-semibold text-accent-amber">Phase 2 — Code & Config Analyst</span>
                      </div>
                      <div className="space-y-2">
                        <div>
                          <span className="text-[10px] text-white/30 uppercase">Root Cause</span>
                          <p className="text-sm text-white/70 mt-0.5">{phases.code_analyst.root_cause}</p>
                        </div>
                        {phases.code_analyst.code_analysis && (
                          <div>
                            <span className="text-[10px] text-white/30 uppercase">Code Analysis</span>
                            <p className="text-xs text-white/50 mt-0.5">{phases.code_analyst.code_analysis}</p>
                          </div>
                        )}
                        {phases.code_analyst.config_analysis && (
                          <div>
                            <span className="text-[10px] text-white/30 uppercase">Config Analysis</span>
                            <p className="text-xs text-white/50 mt-0.5">{phases.code_analyst.config_analysis}</p>
                          </div>
                        )}
                        {phases.code_analyst.suggested_fix && (
                          <div>
                            <span className="text-[10px] text-white/30 uppercase">Suggested Fix</span>
                            <div className="code-block mt-1">
                              <code className="text-xs">{phases.code_analyst.suggested_fix}</code>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ─── Hotfix Diff ─── */}
          {analysis.hotfix_diff && analysis.hotfix_diff.trim() && (
            <div className="glass-card p-5">
              <button
                onClick={() => setHotfixOpen(!hotfixOpen)}
                className="flex items-center justify-between w-full cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <GitBranch className="w-5 h-5 text-accent-green" />
                  <h3 className="text-sm font-semibold text-accent-green uppercase tracking-wider">
                    Suggested Hotfix Diff
                  </h3>
                </div>
                {hotfixOpen ? (
                  <ChevronUp className="w-4 h-4 text-white/30" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-white/30" />
                )}
              </button>
              {hotfixOpen && (
                <div className="mt-3 relative group">
                  <pre className="code-block text-xs overflow-x-auto whitespace-pre-wrap">
                    {analysis.hotfix_diff.split('\n').map((line, i) => (
                      <div key={i} className={
                        line.startsWith('+') ? 'text-accent-green' :
                        line.startsWith('-') ? 'text-accent-red' :
                        line.startsWith('@@') ? 'text-accent-purple' :
                        'text-white/50'
                      }>
                        {line}
                      </div>
                    ))}
                  </pre>
                  <button
                    onClick={() => copyDiff(analysis.hotfix_diff!)}
                    className="absolute top-2 right-2 p-1.5 rounded-md bg-white/5 hover:bg-white/10 transition-colors opacity-0 group-hover:opacity-100 cursor-pointer"
                    title="Copy diff"
                  >
                    {copiedDiff ? (
                      <Check className="w-3.5 h-3.5 text-accent-green" />
                    ) : (
                      <Copy className="w-3.5 h-3.5 text-white/40" />
                    )}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Impact Analysis */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-5 h-5 text-accent-amber" />
              <h3 className="text-sm font-semibold text-accent-amber uppercase tracking-wider">
                Impact Analysis
              </h3>
            </div>
            <p className="text-sm text-white/70 leading-relaxed">
              {analysis.impact_analysis}
            </p>
          </div>

          {/* Timeline */}
          {analysis.timeline && analysis.timeline.length > 0 && (
            <div className="glass-card p-5">
              <button
                onClick={() => setTimelineOpen(!timelineOpen)}
                className="flex items-center justify-between w-full cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-accent-purple" />
                  <h3 className="text-sm font-semibold text-accent-purple uppercase tracking-wider">
                    Event Timeline
                  </h3>
                </div>
                {timelineOpen ? (
                  <ChevronUp className="w-4 h-4 text-white/30" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-white/30" />
                )}
              </button>
              {timelineOpen && (
                <div className="mt-4 space-y-0">
                  {analysis.timeline.map((evt, i) => (
                    <div key={i} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className="w-2.5 h-2.5 rounded-full bg-accent-purple/60 border-2 border-accent-purple/30 mt-1.5" />
                        {i < analysis.timeline.length - 1 && (
                          <div className="w-px flex-1 bg-accent-purple/15 my-1" />
                        )}
                      </div>
                      <div className="pb-4 min-w-0">
                        <p className="text-[10px] text-white/30 font-mono">{evt.time}</p>
                        <p className="text-sm text-white/70 mt-0.5">{evt.event}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Remediation Steps */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <Wrench className="w-5 h-5 text-accent-green" />
              <h3 className="text-sm font-semibold text-accent-green uppercase tracking-wider">
                Remediation Steps
              </h3>
            </div>
            <div className="space-y-3">
              {analysis.actionable_remediation.map((step, i) => (
                <div
                  key={i}
                  className="rounded-xl bg-white/[0.02] border border-white/5 p-4"
                >
                  <div className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 rounded-lg bg-accent-green/10 text-accent-green text-xs font-bold flex items-center justify-center mt-0.5">
                      {step.step}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/80 font-medium">
                        {step.action}
                      </p>
                      {step.command && (
                        <div className="mt-2 relative group">
                          <div className="code-block flex items-start gap-2">
                            <Terminal className="w-3.5 h-3.5 text-accent-green/50 mt-0.5 flex-shrink-0" />
                            <code className="flex-1 break-all">{step.command}</code>
                          </div>
                          <button
                            onClick={() => copyCommand(step.command, i)}
                            className="absolute top-2 right-2 p-1.5 rounded-md bg-white/5 hover:bg-white/10 transition-colors opacity-0 group-hover:opacity-100 cursor-pointer"
                            title="Copy command"
                          >
                            {copiedIdx === i ? (
                              <Check className="w-3.5 h-3.5 text-accent-green" />
                            ) : (
                              <Copy className="w-3.5 h-3.5 text-white/40" />
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* ─── Raw Logs Collapsible ─── */}
      {raw_logs && raw_logs.length > 0 && (
        <div className="glass-card p-5">
          <button
            id="toggle-raw-logs"
            onClick={() => setLogsOpen(!logsOpen)}
            className="flex items-center justify-between w-full cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-white/40" />
              <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider">
                Raw CloudWatch Logs
              </h3>
              <span className="text-[10px] text-white/20 bg-white/5 px-2 py-0.5 rounded-full">
                {raw_logs.length} events
              </span>
            </div>
            {logsOpen ? (
              <ChevronUp className="w-4 h-4 text-white/30" />
            ) : (
              <ChevronDown className="w-4 h-4 text-white/30" />
            )}
          </button>

          {logsOpen && (
            <div className="mt-3 max-h-80 overflow-y-auto">
              <div className="code-block !p-0">
                {raw_logs.map((log, i) => (
                  <div
                    key={i}
                    className={`px-4 py-1.5 border-b border-white/3 hover:bg-white/[0.02] transition-colors ${
                      log.message.includes('ERROR')
                        ? 'text-accent-red/80'
                        : log.message.includes('CRITICAL') || log.message.includes('ALERT')
                        ? 'text-accent-red'
                        : log.message.includes('WARN')
                        ? 'text-accent-amber/80'
                        : 'text-white/50'
                    }`}
                  >
                    <span className="text-white/20 mr-2 text-[10px]">
                      {log.timestamp?.split('T')[1]?.replace('Z', '') || ''}
                    </span>
                    {log.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
