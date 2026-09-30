import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { MissionControl } from './components/MissionControl';
import { EventMap } from './components/EventMap';
import { PriorityWorkbench } from './components/PriorityWorkbench';
import { EvidenceExplorer } from './components/EvidenceExplorer';
import { ResponseSimulator } from './components/ResponseSimulator';
import { ResearchLab } from './components/ResearchLab';
import { FindingDetailModal } from './components/FindingDetailModal';
import { DecisionReceiptModal } from './components/DecisionReceiptModal';
import { api } from './services/api';
import { 
  EventResponse, MissionControlSummary, AnalysisRunResponse,
  GeoJSONFeatureCollection, EvidenceGraphResponse, ImpactFinding 
} from './types';

export function App() {
  const [currentTab, setCurrentTab] = useState<string>('control');
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [activeEventId, setActiveEventId] = useState<string>('');
  const [summary, setSummary] = useState<MissionControlSummary | null>(null);
  const [latestRun, setLatestRun] = useState<AnalysisRunResponse | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  // Layers
  const [floodLayer, setFloodLayer] = useState<GeoJSONFeatureCollection | null>(null);
  const [changeLayer, setChangeLayer] = useState<GeoJSONFeatureCollection | null>(null);
  const [roadsLayer, setRoadsLayer] = useState<GeoJSONFeatureCollection | null>(null);
  const [bridgesLayer, setBridgesLayer] = useState<GeoJSONFeatureCollection | null>(null);
  const [facilitiesLayer, setFacilitiesLayer] = useState<GeoJSONFeatureCollection | null>(null);
  const [isolationLayer, setIsolationLayer] = useState<any[]>([]);
  const [findings, setFindings] = useState<ImpactFinding[]>([]);
  const [evidenceGraph, setEvidenceGraph] = useState<EvidenceGraphResponse | null>(null);

  // Modals
  const [selectedFinding, setSelectedFinding] = useState<ImpactFinding | null>(null);
  const [receiptFindingId, setReceiptFindingId] = useState<string | null>(null);

  // Initial load
  useEffect(() => {
    initApp();
  }, []);

  const initApp = async () => {
    try {
      let list = await api.listEvents();
      if (list.length === 0) {
        // Create initial default event
        const defaultEvt = await api.createEvent({
          name: 'Cyclone Remal - Lower Surma Basin Inundation',
          description: 'Rapid onset monsoon fluvial flooding severing arterial highways and cutting off rural upazila medical access.',
          hazard_type: 'FLOOD',
          aoi_geojson: {
            type: 'Polygon',
            coordinates: [[[91.80, 24.85], [92.15, 24.85], [92.15, 25.10], [91.80, 25.10], [91.80, 24.85]]]
          },
          pre_event_date: '2026-05-15',
          post_event_date: '2026-05-28',
          use_fixture: true,
          fixture_id: 'sylhet_monsoon_2026'
        });
        list = [defaultEvt];
      }
      setEvents(list);
      const chosen = list[0].id;
      setActiveEventId(chosen);
      loadEventData(chosen);
    } catch (err) {
      console.error('App initialization failed:', err);
    }
  };

  const loadEventData = async (eventId: string) => {
    try {
      const sum = await api.getEventSummary(eventId);
      setSummary(sum);
      setLatestRun(sum.latest_run || null);
      setFindings(sum.top_findings || []);

      // Load Layers in parallel
      const [flood, changes, infra, iso, graph] = await Promise.all([
        api.getFloodLayer(eventId).catch(() => ({ geojson: { type: 'FeatureCollection' as const, features: [] }, summary: {} })),
        api.getChangeLayer(eventId).catch(() => ({ type: 'FeatureCollection' as const, features: [] })),
        api.getInfrastructureLayers(eventId).catch(() => ({
          roads: { type: 'FeatureCollection' as const, features: [] },
          bridges: { type: 'FeatureCollection' as const, features: [] },
          facilities: { type: 'FeatureCollection' as const, features: [] },
          buildings: { type: 'FeatureCollection' as const, features: [] },
          summary: {}
        })),
        api.getIsolationLayer(eventId).catch(() => []),
        api.getEvidenceGraph(eventId).catch(() => null)
      ]);

      setFloodLayer(flood.geojson);
      setChangeLayer(changes);
      setRoadsLayer(infra.roads);
      setBridgesLayer(infra.bridges);
      setFacilitiesLayer(infra.facilities);
      setIsolationLayer(iso);
      setEvidenceGraph(graph);

    } catch (err) {
      console.error(`Failed to load event data for ${eventId}:`, err);
    }
  };

  // Switch event
  const handleSelectEvent = (id: string) => {
    setActiveEventId(id);
    loadEventData(id);
  };

  // Trigger analysis pipeline
  const handleTriggerRun = async () => {
    if (!activeEventId || isRunning) return;
    setIsRunning(true);
    try {
      const run = await api.triggerRun(activeEventId);
      setLatestRun(run);

      // Poll run status
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.getRunStatus(run.id);
          setLatestRun(status);
          if (status.status === 'COMPLETED' || status.status === 'FAILED') {
            clearInterval(pollInterval);
            setIsRunning(false);
            loadEventData(activeEventId);
          }
        } catch (pollErr) {
          clearInterval(pollInterval);
          setIsRunning(false);
        }
      }, 1000);

    } catch (err) {
      console.error('Trigger run failed:', err);
      setIsRunning(false);
    }
  };

  const activeEvent = events.find((e) => e.id === activeEventId) || null;

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col font-sans">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        events={events}
        activeEvent={activeEvent}
        setActiveEventId={handleSelectEvent}
        latestRun={latestRun}
        onTriggerRun={handleTriggerRun}
        isRunning={isRunning}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'control' && (
          <MissionControl
            summary={summary}
            onSelectFinding={(f) => setSelectedFinding(f)}
            onNavigateTab={(tab) => setCurrentTab(tab)}
          />
        )}

        {currentTab === 'map' && (
          <EventMap
            floodLayer={floodLayer}
            changeLayer={changeLayer}
            roadsLayer={roadsLayer}
            bridgesLayer={bridgesLayer}
            facilitiesLayer={facilitiesLayer}
            isolationLayer={isolationLayer}
            findings={findings}
            onSelectFinding={(f) => setSelectedFinding(f)}
          />
        )}

        {currentTab === 'priorities' && (
          <PriorityWorkbench
            findings={findings}
            onSelectFinding={(f) => setSelectedFinding(f)}
            onOpenReceipt={(fId) => setReceiptFindingId(fId)}
          />
        )}

        {currentTab === 'evidence' && (
          <EvidenceExplorer graph={evidenceGraph} />
        )}

        {currentTab === 'simulator' && (
          <ResponseSimulator eventId={activeEventId} />
        )}

        {currentTab === 'research' && (
          <ResearchLab />
        )}
      </main>

      {/* Finding Detail Modal */}
      {selectedFinding && (
        <FindingDetailModal
          finding={selectedFinding}
          onClose={() => setSelectedFinding(null)}
          onOpenReceipt={(fId) => {
            setSelectedFinding(null);
            setReceiptFindingId(fId);
          }}
          onFindingUpdated={(updated) => {
            setSelectedFinding(updated);
            setFindings((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
          }}
        />
      )}

      {/* Decision Receipt Modal */}
      {receiptFindingId && (
        <DecisionReceiptModal
          findingId={receiptFindingId}
          onClose={() => setReceiptFindingId(null)}
        />
      )}
    </div>
  );
}

export default App;
