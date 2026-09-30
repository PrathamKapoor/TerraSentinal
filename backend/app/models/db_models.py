from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class DBEvent(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    hazard_type = Column(String, default="FLOOD")
    status = Column(String, default="CREATED", index=True)
    aoi_geojson = Column(JSON, nullable=False)
    pre_event_date = Column(String, nullable=False)
    post_event_date = Column(String, nullable=False)
    is_fixture_mode = Column(Boolean, default=False)
    fixture_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("DBAnalysisRun", back_populates="event", cascade="all, delete-orphan")
    findings = relationship("DBImpactFinding", back_populates="event", cascade="all, delete-orphan")

class DBAnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False, index=True)
    status = Column(String, default="QUEUED", index=True)
    stage = Column(String, default="INITIALIZING")
    progress = Column(Float, default=0.0)
    stage_message = Column(Text, default="")
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)
    model_name = Column(String, default="DualPol-SAR+DEM-Terrain")
    model_version = Column(String, default="1.2.0")

    event = relationship("DBEvent", back_populates="runs")

class DBObservation(Base):
    __tablename__ = "observations"

    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False, index=True)
    modality = Column(String, nullable=False)
    quality_state = Column(String, default="HIGH")
    cloud_cover_pct = Column(Float, nullable=True)
    incidence_angle_deg = Column(Float, nullable=True)
    spatial_resolution_meters = Column(Float, default=10.0)
    acquisition_timestamp = Column(DateTime, nullable=False)
    scene_id = Column(String, nullable=False)
    source_catalog = Column(String, default="STAC")
    age_hours = Column(Float, default=0.0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class DBFloodResult(Base):
    __tablename__ = "flood_results"

    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False, index=True)
    run_id = Column(String, nullable=False, index=True)
    flood_geojson = Column(JSON, nullable=False)
    change_geojson = Column(JSON, nullable=False)
    summary_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DBInfrastructureResult(Base):
    __tablename__ = "infrastructure_results"

    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False, index=True)
    run_id = Column(String, nullable=False, index=True)
    roads_geojson = Column(JSON, nullable=False)
    bridges_geojson = Column(JSON, nullable=False)
    facilities_geojson = Column(JSON, nullable=False)
    buildings_geojson = Column(JSON, nullable=False)
    isolated_communities_json = Column(JSON, nullable=False)
    summary_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DBImpactFinding(Base):
    __tablename__ = "impact_findings"

    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False, index=True)
    run_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    finding_type = Column(String, nullable=False)
    priority = Column(String, default="HIGH", index=True)
    criticality_score = Column(Float, default=50.0)
    confidence = Column(Float, default=0.8)
    conflict_state = Column(String, default="NONE")
    affected_population = Column(Integer, default=0)
    affected_infrastructure_ids = Column(JSON, default=list)
    location_lon = Column(Float, nullable=False)
    location_lat = Column(Float, nullable=False)
    summary = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    evidence_chain = Column(JSON, default=list)
    verification_status = Column(String, default="UNVERIFIED", index=True)
    verification_notes = Column(Text, nullable=True)
    verified_by = Column(String, nullable=True)
    verification_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("DBEvent", back_populates="findings")

class DBSimulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False, index=True)
    scenario_name = Column(String, nullable=False)
    interventions_json = Column(JSON, nullable=False)
    baseline_isolated_pop = Column(Integer, default=0)
    simulated_isolated_pop = Column(Integer, default=0)
    delta_json = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DBDecisionReceipt(Base):
    __tablename__ = "decision_receipts"

    id = Column(String, primary_key=True, index=True)
    finding_id = Column(String, ForeignKey("impact_findings.id"), nullable=False, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False, index=True)
    receipt_json = Column(JSON, nullable=False)
    integrity_sha256 = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
