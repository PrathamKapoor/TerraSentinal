export type HazardType = 'FLOOD' | 'FLASH_FLOOD' | 'COASTAL_SURGE' | 'CYCLONE_INUNDATION';
export type PriorityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'VERIFY';
export type PassabilityState = 'OPEN' | 'PARTIALLY_AFFECTED' | 'LIKELY_BLOCKED' | 'BLOCKED' | 'UNKNOWN' | 'REOPENING';
export type ConflictState = 'NONE' | 'CONFLICTING_EVIDENCE' | 'SAR_OPTICAL_DISAGREEMENT' | 'GROUND_TRUTH_DISCREPANCY';
export type VerificationStatus = 'UNVERIFIED' | 'CONFIRMED' | 'REJECTED' | 'UNCERTAIN' | 'SUPERSEDED';

export interface GeoJSONGeometry {
  type: string;
  coordinates: any;
}

export interface GeoJSONFeature {
  type: 'Feature';
  id?: string;
  geometry: GeoJSONGeometry;
  properties: Record<string, any>;
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

export interface EventResponse {
  id: string;
  name: string;
  description: string;
  hazard_type: HazardType;
  status: string;
  aoi_geojson: GeoJSONGeometry;
  pre_event_date: string;
  post_event_date: string;
  created_at: string;
  updated_at: string;
  is_fixture_mode: boolean;
  fixture_id?: string;
}

export interface AnalysisRunResponse {
  id: string;
  event_id: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  stage: string;
  progress: number;
  stage_message: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  execution_time_seconds?: number;
  model_name: string;
  model_version: string;
}

export interface ObservationQuality {
  modality: string;
  quality_state: string;
  cloud_cover_pct?: number;
  incidence_angle_deg?: number;
  spatial_resolution_meters: number;
  acquisition_timestamp: string;
  scene_id: string;
  source_catalog: string;
  age_hours: number;
  notes?: string;
}

export interface EventObservationsSummary {
  event_id: string;
  overall_confidence: number;
  modalities_available: string[];
  quality_details: ObservationQuality[];
  map_completeness_pct: number;
}

export interface FloodRegionSummary {
  total_flooded_sqkm: number;
  newly_flooded_sqkm: number;
  permanent_water_sqkm: number;
  receded_sqkm: number;
  mean_flood_confidence: number;
  feature_count: number;
}

export interface InfrastructureImpactSummary {
  total_roads_analyzed: number;
  roads_blocked_count: number;
  roads_affected_count: number;
  roads_blocked_km: number;
  bridges_analyzed: number;
  bridges_blocked_count: number;
  buildings_affected_count: number;
  facilities_flooded_count: number;
  facilities_isolated_count: number;
}

export interface PopulationImpactSummary {
  total_population_in_aoi: number;
  directly_flooded_population: number;
  isolated_population: number;
  lost_hospital_access_population: number;
  population_data_source: string;
}

export interface IsolatedCommunity {
  component_id: string;
  community_name: string;
  estimated_population: number;
  centroid: [number, number];
  boundary_polygon?: GeoJSONGeometry;
  severed_access_roads: string[];
  nearest_hospital_before_km: number;
  current_status: string;
  isolation_score: number;
}

export interface IsolationAssessmentSummary {
  isolated_communities_count: number;
  total_isolated_population: number;
  mean_accessibility_loss_minutes: number;
  communities: IsolatedCommunity[];
}

export interface EvidenceChainItem {
  step: number;
  layer: string;
  source_id: string;
  description: string;
  confidence: number;
  modality?: string;
  timestamp?: string;
}

export interface ImpactFinding {
  id: string;
  event_id: string;
  title: string;
  finding_type: string;
  priority: PriorityLevel;
  criticality_score: number;
  confidence: number;
  conflict_state: ConflictState;
  affected_population: number;
  affected_infrastructure_ids: string[];
  location_coordinates: [number, number];
  summary: string;
  recommendation: string;
  evidence_chain: EvidenceChainItem[];
  verification_status: VerificationStatus;
  verification_notes?: string;
  created_at: string;
}

export interface EvidenceNode {
  id: string;
  label: string;
  node_type: string;
  confidence: number;
  data: Record<string, any>;
}

export interface EvidenceEdge {
  source: string;
  target: string;
  relationship: string;
  weight: number;
  has_conflict: boolean;
}

export interface EvidenceGraphResponse {
  event_id: string;
  finding_id?: string;
  nodes: EvidenceNode[];
  edges: EvidenceEdge[];
}

export interface SimulationIntervention {
  intervention_type: string;
  target_infrastructure_id: string;
  target_name: string;
  new_state: PassabilityState;
  cost_estimate_hours?: number;
}

export interface SimulationRequest {
  event_id: string;
  scenario_name: string;
  interventions: SimulationIntervention[];
}

export interface CounterfactualDelta {
  reconnected_population: number;
  restored_hospitals_count: number;
  restored_facilities_count: number;
  reopened_road_km: number;
  reduction_in_isolated_communities: number;
  average_travel_time_saved_minutes: number;
  net_criticality_reduction: number;
}

export interface SimulationResponse {
  simulation_id: string;
  event_id: string;
  scenario_name: string;
  created_at: string;
  interventions_applied: SimulationIntervention[];
  baseline_isolated_population: number;
  simulated_isolated_population: number;
  delta: CounterfactualDelta;
  simulation_badge: string;
  explanation: string;
}

export interface DecisionReceipt {
  receipt_id: string;
  finding_id: string;
  event_id: string;
  event_name: string;
  issued_at: string;
  integrity_sha256: string;
  model_name: string;
  model_version: string;
  processing_pipeline_version: string;
  satellite_scenes: any[];
  dem_source: string;
  osm_extract_timestamp: string;
  population_dataset: string;
  overall_confidence: number;
  evidence_conflicts_surfaced: string[];
  affected_population: number;
  impacted_facilities: string[];
  severed_critical_routes: string[];
  priority_level: PriorityLevel;
  primary_recommendation: string;
  counterfactual_simulation_id?: string;
  verification_status: VerificationStatus;
  verified_by?: string;
  verification_timestamp?: string;
  verification_notes?: string;
}

export interface MissionControlSummary {
  event: EventResponse;
  latest_run?: AnalysisRunResponse;
  observations_summary: EventObservationsSummary;
  flood_summary: FloodRegionSummary;
  infrastructure_summary: InfrastructureImpactSummary;
  population_summary: PopulationImpactSummary;
  isolation_summary: IsolationAssessmentSummary;
  top_findings: ImpactFinding[];
  is_demo_mode: boolean;
}

export interface BenchmarkExperiment {
  experiment_id: string;
  name: string;
  modalities: string[];
  terrain_filtering: boolean;
  metrics: {
    iou: number;
    f1: number;
    precision: number;
    recall: number;
    false_discovery_rate: number;
    tp: number;
    fp: number;
    fn: number;
    tn: number;
  };
  runtime_ms: number;
  research_question: string;
}
