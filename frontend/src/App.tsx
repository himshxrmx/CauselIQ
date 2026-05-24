import { useState, useEffect, useCallback } from 'react';
import { fetchAlerts, fetchAlert, fetchScenarios, fetchStats, simulateIncident } from './api';
import type { Incident, Scenario, Stats } from './api';
import Header from './components/Header';
import StatsBar from './components/StatsBar';
import AlertFeed from './components/AlertFeed';
import InvestigationPanel from './components/InvestigationPanel';
import SimulateModal from './components/SimulateModal';
import UploadModal from './components/UploadModal';

function App() {
  const [incidents, setIncidents] = useState<Incident[]>(() => {
    try {
      const saved = localStorage.getItem('causeiq_incidents');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [activeIncident, setActiveIncident] = useState<Incident | null>(null);
  const [scenarios, setScenarios] = useState<Record<string, Scenario>>({});
  const [showSimModal, setShowSimModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Persist incidents to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('causeiq_incidents', JSON.stringify(incidents));
  }, [incidents]);

  // Dynamically calculate stats based on local incidents to avoid stateless backend issues
  const computedStats: Stats = {
    total_incidents: incidents.length,
    completed: incidents.filter(i => i.status === 'completed').length,
    analyzing: incidents.filter(i => i.status === 'pending' || i.status === 'analyzing').length,
    failed: incidents.filter(i => i.status === 'failed').length,
    severity_breakdown: {},
    category_breakdown: {},
    avg_confidence: (() => {
      const analyzed = incidents.filter(i => i.status === 'completed' && i.analysis && i.analysis.confidence_score);
      if (analyzed.length === 0) return 0;
      const sum = analyzed.reduce((acc, i) => acc + (i.analysis?.confidence_score || 0), 0);
      return sum / analyzed.length;
    })()
  };

  // Load scenarios once
  useEffect(() => {
    fetchScenarios().then(res => setScenarios(res.data)).catch(console.error);
  }, []);

  const handleSelectIncident = async (id: string) => {
    // Check locally first
    const local = incidents.find(i => i.id === id);
    if (local) setActiveIncident(local);
  };

  const handleSimulate = async (scenario: string) => {
    setLoading(true);
    try {
      const res = await simulateIncident(scenario);
      setShowSimModal(false);
      
      const newIncident = res.data.incident;
      setIncidents(prev => [newIncident, ...prev.filter(i => i.id !== newIncident.id)]);
      setActiveIncident(newIncident);
      setLoading(false);
    } catch (e) {
      console.error('Failed to simulate:', e);
      setLoading(false);
    }
  };

  const handleUploadSuccess = (newIncident: Incident) => {
    setShowUploadModal(false);
    setIncidents(prev => [newIncident, ...prev.filter(i => i.id !== newIncident.id)]);
    setActiveIncident(newIncident);
  };

  return (
    <div className="min-h-screen bg-dark-900 bg-grid">
      {/* Ambient glow effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-80 h-80 bg-accent-purple/5 rounded-full blur-[120px]" />
        <div className="absolute top-1/3 -right-40 w-96 h-96 bg-accent-cyan/5 rounded-full blur-[120px]" />
        <div className="absolute -bottom-40 left-1/3 w-80 h-80 bg-accent-pink/5 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10">
        <Header 
          onSimulate={() => setShowSimModal(true)} 
          onUpload={() => setShowUploadModal(true)} 
        />
        
        <StatsBar stats={computedStats} />

        <main className="max-w-[1600px] mx-auto px-4 sm:px-6 pb-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column — Alert Feed */}
            <div className="lg:col-span-4 xl:col-span-3">
              <AlertFeed
                incidents={incidents}
                activeId={activeIncident?.id || null}
                onSelect={handleSelectIncident}
              />
            </div>

            {/* Right Column — Investigation Panel */}
            <div className="lg:col-span-8 xl:col-span-9">
              <InvestigationPanel incident={activeIncident} />
            </div>
          </div>
        </main>
      </div>

      {showSimModal && (
        <SimulateModal
          scenarios={scenarios}
          loading={loading}
          onSimulate={handleSimulate}
          onClose={() => setShowSimModal(false)}
        />
      )}

      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={handleUploadSuccess}
        />
      )}
    </div>
  );
}

export default App;
