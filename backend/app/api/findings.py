from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.db_models import DBImpactFinding, DBEvent
from backend.app.models.schemas import (
    ImpactFinding, FindingVerificationRequest, VerificationStatus
)

router = APIRouter(prefix="", tags=["findings"])

@router.get("/events/{event_id}/findings", response_model=List[ImpactFinding])
def list_event_findings(event_id: str, db: Session = Depends(get_db)):
    findings_db = db.query(DBImpactFinding).filter(DBImpactFinding.event_id == event_id).order_by(DBImpactFinding.criticality_score.desc()).all()
    return [
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

@router.get("/findings/{finding_id}", response_model=ImpactFinding)
def get_finding_detail(finding_id: str, db: Session = Depends(get_db)):
    f = db.query(DBImpactFinding).filter(DBImpactFinding.id == finding_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    return ImpactFinding(
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

@router.post("/findings/{finding_id}/verification", response_model=ImpactFinding)
def submit_verification(
    finding_id: str,
    req: FindingVerificationRequest,
    db: Session = Depends(get_db)
):
    f = db.query(DBImpactFinding).filter(DBImpactFinding.id == finding_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    now = datetime.now(timezone.utc)
    f.verification_status = req.status.value
    f.verified_by = req.responder_id
    f.verification_notes = f"[{req.ground_truth_modality}] {req.notes}"
    f.verification_timestamp = now
    
    db.commit()
    db.refresh(f)
    
    return ImpactFinding(
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
