from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.db_models import (
    DBEvent, DBFloodResult, DBInfrastructureResult, DBImpactFinding
)
from backend.app.models.schemas import (
    GeoJSONFeatureCollection, EvidenceGraphResponse, ImpactFinding
)
from backend.app.services.priority_engine import PriorityEngine

router = APIRouter(prefix="/events/{event_id}", tags=["layers"])

@router.get("/flood", response_model=Dict[str, Any])
def get_flood_layer(event_id: str, db: Session = Depends(get_db)):
    res = db.query(DBFloodResult).filter(DBFloodResult.event_id == event_id).order_by(DBFloodResult.created_at.desc()).first()
    if not res:
        return {"type": "FeatureCollection", "features": [], "summary": {}}
    return {
        "geojson": res.flood_geojson,
        "summary": res.summary_json
    }

@router.get("/changes", response_model=Dict[str, Any])
def get_change_layer(event_id: str, db: Session = Depends(get_db)):
    res = db.query(DBFloodResult).filter(DBFloodResult.event_id == event_id).order_by(DBFloodResult.created_at.desc()).first()
    if not res:
        return {"type": "FeatureCollection", "features": []}
    return res.change_geojson

@router.get("/infrastructure", response_model=Dict[str, Any])
def get_infrastructure_layers(event_id: str, db: Session = Depends(get_db)):
    res = db.query(DBInfrastructureResult).filter(DBInfrastructureResult.event_id == event_id).order_by(DBInfrastructureResult.created_at.desc()).first()
    if not res:
        return {
            "roads": {"type": "FeatureCollection", "features": []},
            "bridges": {"type": "FeatureCollection", "features": []},
            "facilities": {"type": "FeatureCollection", "features": []},
            "buildings": {"type": "FeatureCollection", "features": []},
            "summary": {}
        }
    return {
        "roads": res.roads_geojson,
        "bridges": res.bridges_geojson,
        "facilities": res.facilities_geojson,
        "buildings": res.buildings_geojson,
        "summary": res.summary_json
    }

@router.get("/isolation", response_model=List[Dict[str, Any]])
def get_isolation_layer(event_id: str, db: Session = Depends(get_db)):
    res = db.query(DBInfrastructureResult).filter(DBInfrastructureResult.event_id == event_id).order_by(DBInfrastructureResult.created_at.desc()).first()
    if not res or not res.isolated_communities_json:
        return []
    return res.isolated_communities_json

@router.get("/evidence-graph", response_model=EvidenceGraphResponse)
def get_evidence_graph(event_id: str, db: Session = Depends(get_db)):
    findings_db = db.query(DBImpactFinding).filter(DBImpactFinding.event_id == event_id).all()
    infra_res = db.query(DBInfrastructureResult).filter(DBInfrastructureResult.event_id == event_id).order_by(DBInfrastructureResult.created_at.desc()).first()
    
    roads = infra_res.roads_geojson.get("features", []) if infra_res else []
    facilities = infra_res.facilities_geojson.get("features", []) if infra_res else []
    
    findings = [
        ImpactFinding(
            id=f.id,
            event_id=f.event_id,
            title=f.title,
            finding_type=f.finding_type,
            priority=f.priority,
            criticality_score=f.criticality_score,
            confidence=f.confidence,
            conflict_state=f.conflict_state,
            affected_population=f.affected_population,
            affected_infrastructure_ids=f.affected_infrastructure_ids,
            location_coordinates=[f.location_lon, f.location_lat],
            summary=f.summary,
            recommendation=f.recommendation,
            evidence_chain=f.evidence_chain,
            verification_status=f.verification_status,
            verification_notes=f.verification_notes,
            created_at=f.created_at
        )
        for f in findings_db
    ]
    
    return PriorityEngine.build_evidence_graph(
        event_id=event_id,
        findings=findings,
        road_features=roads,
        facility_features=facilities
    )
