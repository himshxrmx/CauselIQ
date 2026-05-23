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
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [activeIncident, setActiveIncident] = useState<Incident | null>(null);
  const [scenarios, setScenarios] = useState<Record<string, Scenario>>({});
  const [stats, setStats] = useState<Stats | null>(null);
  const [showSimModal, setShowSimModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Fetch incidents list
  const loadIncidents = useCallback(async () => {
    try {
      const res = await fetchAlerts();
      setIncidents(res.data);
    } catch (e) {
      console.error('Failed to fetch alerts:', e);
    }
  }, []);

  // Fetch stats
  const loadStats = useCallback(async () => {
    try {
      const res = await fetchStats();
      setStats(res.data);
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
  }, []);

  // Load scenarios once
  useEffect(() => {
    fetchScenarios().then(res => setScenarios(res.data)).catch(console.error);
  }, []);

  // Poll incidents every 3s
  useEffect(() => {
    loadIncidents();
    loadStats();
    const interval = setInterval(() => {
      loadIncidents();
      loadStats();
    }, 3000);
    return () => clearInterval(interval);
  }, [loadIncidents, loadStats]);

  // When active incident is analyzing, poll for completion
  useEffect(() => {
    if (!activeIncident || activeIncident.status === 'completed' || activeIncident.status === 'failed') return;
    
    const interval = setInterval(async () => {
      try {
        const res = await fetchAlert(activeIncident.id);
        setActiveIncident(res.data);
        if (res.data.status === 'completed' || res.data.status === 'failed') {
          loadIncidents();
          loadStats();
        }
      } catch (e) {
        console.error('Failed to poll incident:', e);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeIncident, loadIncidents, loadStats]);

  const handleSelectIncident = async (id: string) => {
    try {
      const res = await fetchAlert(id);
      setActiveIncident(res.data);
    } catch (e) {
      console.error('Failed to fetch incident:', e);
    }
  };

  const handleSimulate = async (scenario: string) => {
    setLoading(true);
    try {
      const res = await simulateIncident(scenario);
      setShowSimModal(false);
      // Immediately fetch the new incident
      setTimeout(async () => {
        await loadIncidents();
        await loadStats();
        const detail = await fetchAlert(res.data.incident_id);
        setActiveIncident(detail.data);
        setLoading(false);
      }, 500);
    } catch (e) {
      console.error('Failed to simulate:', e);
      setLoading(false);
    }
  };

  const handleUploadSuccess = (incidentId: string) => {
    setShowUploadModal(false);
    setTimeout(async () => {
      await loadIncidents();
      await loadStats();
      const detail = await fetchAlert(incidentId);
      setActiveIncident(detail.data);
    }, 500);
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
        
        {stats && <StatsBar stats={stats} />}

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
