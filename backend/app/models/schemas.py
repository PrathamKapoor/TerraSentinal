from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

# -------------------------------------------------------------------------
# Core Enumerations
# -------------------------------------------------------------------------

class HazardType(str, Enum):
    FLOOD = "FLOOD"
    FLASH_FLOOD = "FLASH_FLOOD"
    COASTAL_SURGE = "COASTAL_SURGE"
    CYCLONE_INUNDATION = "CYCLONE_INUNDATION"

class EventStatus(str, Enum):
    CREATED = "CREATED"
    ANALYZING = "ANALYZING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class RunStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RunStage(str, Enum):
    INITIALIZING = "INITIALIZING"
    ACQUISITION = "ACQUISITION"
    PREPROCESSING = "PREPROCESSING"
    DETECTION = "DETECTION"
    CHANGE_DETECTION = "CHANGE_DETECTION"
    EVIDENCE_FUSION = "EVIDENCE_FUSION"
    INFRASTRUCTURE_JOIN = "INFRASTRUCTURE_JOIN"
    NETWORK_ANALYSIS = "NETWORK_ANALYSIS"
    ISOLATION_ASSESSMENT = "ISOLATION_ASSESSMENT"
    PRIORITIZATION = "PRIORITIZATION"
    RECEIPT_GENERATION = "RECEIPT_GENERATION"
    DONE = "DONE"

class SensorModality(str, Enum):
    SENTINEL_1_SAR = "SENTINEL_1_SAR"
    SENTINEL_2_OPTICAL = "SENTINEL_2_OPTICAL"
    DEM = "DEM"
    GROUND_REPORT = "GROUND_REPORT"
    HISTORICAL_WATER = "HISTORICAL_WATER"

class QualityState(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"

class ChangeCategory(str, Enum):
    PERMANENT_WATER = "PERMANENT_WATER"
    NEWLY_FLOODED = "NEWLY_FLOODED"
    RECEDED = "RECEDED"
    UNCHANGED_LAND = "UNCHANGED_LAND"
    UNCERTAIN = "UNCERTAIN"

class DamageState(str, Enum):
    INTACT = "INTACT"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    DESTROYED = "DESTROYED"
    UNCERTAIN = "UNCERTAIN"

class PassabilityState(str, Enum):
    OPEN = "OPEN"
    PARTIALLY_AFFECTED = "PARTIALLY_AFFECTED"
    LIKELY_BLOCKED = "LIKELY_BLOCKED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
    REOPENING = "REOPENING"

class ConflictState(str, Enum):
    NONE = "NONE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    SAR_OPTICAL_DISAGREEMENT = "SAR_OPTICAL_DISAGREEMENT"
    GROUND_TRUTH_DISCREPANCY = "GROUND_TRUTH_DISCREPANCY"

class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERIFY = "VERIFY"

class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    UNCERTAIN = "UNCERTAIN"
    SUPERSEDED = "SUPERSEDED"

class InterventionType(str, Enum):
    RESTORE_ROAD = "RESTORE_ROAD"
    RESTORE_BRIDGE = "RESTORE_BRIDGE"
    DEPLOY_PONTOON = "DEPLOY_PONTOON"
    BLOCK_ROAD = "BLOCK_ROAD"
    DISPATCH_RESCUE_BOAT = "DISPATCH_RESCUE_BOAT"

# -------------------------------------------------------------------------
# GeoJSON Base Primitives
# -------------------------------------------------------------------------

class GeoJSONGeometry(BaseModel):
    type: str  # Point, LineString, Polygon, MultiPolygon
    coordinates: Any

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: Optional[str] = None
    geometry: GeoJSONGeometry
    properties: Dict[str, Any] = Field(default_factory=dict)

class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature] = Field(default_factory=list)

# -------------------------------------------------------------------------
# Event Entities
# -------------------------------------------------------------------------

class EventCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    hazard_type: HazardType = HazardType.FLOOD
    aoi_geojson: GeoJSONGeometry
    pre_event_date: str  # YYYY-MM-DD
    post_event_date: str # YYYY-MM-DD
    use_fixture: bool = False
    fixture_id: Optional[str] = None

class EventResponse(BaseModel):
    id: str
    name: str
    description: str
    hazard_type: HazardType
    status: EventStatus
    aoi_geojson: GeoJSONGeometry
    pre_event_date: str
    post_event_date: str
    created_at: datetime
    updated_at: datetime
    is_fixture_mode: bool = False
    fixture_id: Optional[str] = None

class AnalysisRunResponse(BaseModel):
    id: str
    event_id: str
    status: RunStatus
    stage: RunStage
    progress: float = 0.0  # 0.0 to 1.0
    stage_message: str = ""
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    model_name: str = "DualPol-SAR+DEM-Terrain"
    model_version: str = "1.2.0"

# -------------------------------------------------------------------------
# Observation & Data Quality
# -------------------------------------------------------------------------

class ObservationQuality(BaseModel):
    modality: SensorModality
    quality_state: QualityState
    cloud_cover_pct: Optional[float] = None
    incidence_angle_deg: Optional[float] = None
    spatial_resolution_meters: float
    acquisition_timestamp: datetime
    scene_id: str
    source_catalog: str
    age_hours: float
    notes: Optional[str] = ""

class EventObservationsSummary(BaseModel):
    event_id: str
    overall_confidence: float
    modalities_available: List[SensorModality]
    quality_details: List[ObservationQuality]
    map_completeness_pct: float

# -------------------------------------------------------------------------
# Level 1: Flood & Change Detection
# -------------------------------------------------------------------------

class FloodRegionSummary(BaseModel):
    total_flooded_sqkm: float
    newly_flooded_sqkm: float
    permanent_water_sqkm: float
    receded_sqkm: float
    mean_flood_confidence: float
    feature_count: int

# -------------------------------------------------------------------------
# Level 2: Infrastructure & Population Impact
# -------------------------------------------------------------------------

class InfrastructureImpactSummary(BaseModel):
    total_roads_analyzed: int
    roads_blocked_count: int
    roads_affected_count: int
    roads_blocked_km: float
    bridges_analyzed: int
    bridges_blocked_count: int
    buildings_affected_count: int
    facilities_flooded_count: int
    facilities_isolated_count: int

class PopulationImpactSummary(BaseModel):
    total_population_in_aoi: int
    directly_flooded_population: int
    isolated_population: int
    lost_hospital_access_population: int
    population_data_source: str = "WorldPop 100m / Deterministic Local Spatial Grid"

# -------------------------------------------------------------------------
# Level 3: Network & Isolation
# -------------------------------------------------------------------------

class IsolatedCommunity(BaseModel):
    component_id: str
    community_name: str
    estimated_population: int
    centroid: List[float] # [lon, lat]
    boundary_polygon: Optional[GeoJSONGeometry] = None
    severed_access_roads: List[str]
    nearest_hospital_before_km: float
    current_status: str = "COMPLETELY_ISOLATED"
    isolation_score: float  # 0.0 to 100.0

class IsolationAssessmentSummary(BaseModel):
    isolated_communities_count: int
    total_isolated_population: int
    mean_accessibility_loss_minutes: float
    communities: List[IsolatedCommunity]

# -------------------------------------------------------------------------
# Level 4: Operational Impact Findings & Prioritization
# -------------------------------------------------------------------------

class EvidenceChainItem(BaseModel):
    step: int
    layer: str  # Observation, Detection, Infrastructure, Network, Impact
    source_id: str
    description: str
    confidence: float
    modality: Optional[str] = None
    timestamp: Optional[datetime] = None

class ImpactFinding(BaseModel):
    id: str
    event_id: str
    title: str
    finding_type: str  # ISOLATED_COMMUNITY, SEVERED_ARTERIAL_ROAD, CUTOFF_CRITICAL_FACILITY, SUBMERGED_BRIDGE
    priority: PriorityLevel
    criticality_score: float  # 0 to 100
    confidence: float        # 0.0 to 1.0
    conflict_state: ConflictState = ConflictState.NONE
    affected_population: int
    affected_infrastructure_ids: List[str]
    location_coordinates: List[float] # [lon, lat]
    summary: str
    recommendation: str
    evidence_chain: List[EvidenceChainItem]
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verification_notes: Optional[str] = None
    created_at: datetime

class FindingVerificationRequest(BaseModel):
    status: VerificationStatus
    responder_id: str
    notes: str
    ground_truth_modality: str = "FIELD_OBSERVATION"

# -------------------------------------------------------------------------
# Evidence Graph
# -------------------------------------------------------------------------

class EvidenceNode(BaseModel):
    id: str
    label: str
    node_type: str  # SatelliteScene, FloodFeature, RoadSegment, Facility, PopulationPocket, Finding
    confidence: float
    data: Dict[str, Any] = Field(default_factory=dict)

class EvidenceEdge(BaseModel):
    source: str
    target: str
    relationship: str # DETECTED_BY, INTERSECTS, SEVERS_ACCESS_TO, ISOLATES, JUSTIFIES
    weight: float = 1.0
    has_conflict: bool = False

class EvidenceGraphResponse(BaseModel):
    event_id: str
    finding_id: Optional[str] = None
    nodes: List[EvidenceNode]
    edges: List[EvidenceEdge]

# -------------------------------------------------------------------------
# Counterfactual Simulation
# -------------------------------------------------------------------------

class SimulationIntervention(BaseModel):
    intervention_type: InterventionType
    target_infrastructure_id: str
    target_name: str
    new_state: PassabilityState = PassabilityState.OPEN
    cost_estimate_hours: Optional[float] = 4.0

class SimulationRequest(BaseModel):
    event_id: str
    scenario_name: str
    interventions: List[SimulationIntervention]

class CounterfactualDelta(BaseModel):
    reconnected_population: int
    restored_hospitals_count: int
    restored_facilities_count: int
    reopened_road_km: float
    reduction_in_isolated_communities: int
    average_travel_time_saved_minutes: float
    net_criticality_reduction: float

class SimulationResponse(BaseModel):
    simulation_id: str
    event_id: str
    scenario_name: str
    created_at: datetime
    interventions_applied: List[SimulationIntervention]
    baseline_isolated_population: int
    simulated_isolated_population: int
    delta: CounterfactualDelta
    simulation_badge: str = "SIMULATED / COUNTERFACTUAL"
    explanation: str

# -------------------------------------------------------------------------
# Auditable Decision Receipt
# -------------------------------------------------------------------------

class DecisionReceipt(BaseModel):
    receipt_id: str
    finding_id: str
    event_id: str
    event_name: str
    issued_at: datetime
    integrity_sha256: str
    
    # Metadata & Models
    model_name: str
    model_version: str
    processing_pipeline_version: str
    
    # Evidence & Provenance
    satellite_scenes: List[Dict[str, Any]]
    dem_source: str
    osm_extract_timestamp: datetime
    population_dataset: str
    
    # Analytical Inferences
    overall_confidence: float
    evidence_conflicts_surfaced: List[str]
    affected_population: int
    impacted_facilities: List[str]
    severed_critical_routes: List[str]
    
    # Operational Directives
    priority_level: PriorityLevel
    primary_recommendation: str
    counterfactual_simulation_id: Optional[str] = None
    
    # Human Verification Audit
    verification_status: VerificationStatus
    verified_by: Optional[str] = None
    verification_timestamp: Optional[datetime] = None
    verification_notes: Optional[str] = None

    # Explicit Information Categorization (OBSERVED / INFERRED / SIMULATED)
    observed_evidence: Dict[str, Any] = Field(default_factory=dict)
    inferred_impacts: Dict[str, Any] = Field(default_factory=dict)
    simulated_counterfactuals: Optional[Dict[str, Any]] = None

# -------------------------------------------------------------------------
# Mission Control Dashboard Summary
# -------------------------------------------------------------------------

class MissionControlSummary(BaseModel):
    event: EventResponse
    latest_run: Optional[AnalysisRunResponse]
    observations_summary: EventObservationsSummary
    flood_summary: FloodRegionSummary
    infrastructure_summary: InfrastructureImpactSummary
    population_summary: PopulationImpactSummary
    isolation_summary: IsolationAssessmentSummary
    top_findings: List[ImpactFinding]
    is_demo_mode: bool
