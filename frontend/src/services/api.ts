import {
  EventResponse, MissionControlSummary, AnalysisRunResponse,
  GeoJSONFeatureCollection, EvidenceGraphResponse, ImpactFinding,
  SimulationRequest, SimulationResponse, DecisionReceipt, BenchmarkExperiment
} from '../types';

const BASE_URL = '/api/v1';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API Error ${res.status}: ${errorBody}`);
  }
  return res.json();
}

export const api = {
  // Events
  listEvents: () => fetchJSON<EventResponse[]>('/events'),
  getEvent: (id: string) => fetchJSON<EventResponse>(`/events/${id}`),
  getEventSummary: (id: string) => fetchJSON<MissionControlSummary>(`/events/${id}/summary`),
  createEvent: (data: any) => fetchJSON<EventResponse>('/events', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Runs
  triggerRun: (eventId: string) => fetchJSON<AnalysisRunResponse>(`/events/${eventId}/runs`, {
    method: 'POST',
  }),
  getRunStatus: (runId: string) => fetchJSON<AnalysisRunResponse>(`/runs/${runId}`),
  listRuns: (eventId: string) => fetchJSON<AnalysisRunResponse[]>(`/events/${eventId}/runs`),

  // Layers
  getFloodLayer: (eventId: string) => fetchJSON<{ geojson: GeoJSONFeatureCollection; summary: any }>(`/events/${eventId}/flood`),
  getChangeLayer: (eventId: string) => fetchJSON<GeoJSONFeatureCollection>(`/events/${eventId}/changes`),
  getInfrastructureLayers: (eventId: string) => fetchJSON<{
    roads: GeoJSONFeatureCollection;
    bridges: GeoJSONFeatureCollection;
    facilities: GeoJSONFeatureCollection;
    buildings: GeoJSONFeatureCollection;
    summary: any;
  }>(`/events/${eventId}/infrastructure`),
  getIsolationLayer: (eventId: string) => fetchJSON<any[]>(`/events/${eventId}/isolation`),
  getEvidenceGraph: (eventId: string) => fetchJSON<EvidenceGraphResponse>(`/events/${eventId}/evidence-graph`),

  // Findings
  listFindings: (eventId: string) => fetchJSON<ImpactFinding[]>(`/events/${eventId}/findings`),
  getFinding: (id: string) => fetchJSON<ImpactFinding>(`/findings/${id}`),
  verifyFinding: (id: string, data: { status: string; responder_id: string; notes: string; ground_truth_modality?: string }) =>
    fetchJSON<ImpactFinding>(`/findings/${id}/verification`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Simulations
  runSimulation: (data: SimulationRequest) => fetchJSON<SimulationResponse>('/simulations', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getSimulation: (simId: string) => fetchJSON<SimulationResponse>(`/simulations/${simId}`),

  // Decision Receipts
  getReceipt: (receiptId: string) => fetchJSON<DecisionReceipt>(`/receipts/${receiptId}`),
  verifyReceipt: (receiptId: string) => fetchJSON<{ receipt_id: string; is_valid: boolean; recorded_sha256: string; status: string; verified_at: string }>(`/receipts/${receiptId}/verify`, {
    method: 'POST',
  }),

  // Research Lab
  getBenchmarks: () => fetchJSON<BenchmarkExperiment[]>('/research/benchmarks'),
  runAllBenchmarks: () => fetchJSON<BenchmarkExperiment[]>('/research/run-all', {
    method: 'POST',
  }),
};
