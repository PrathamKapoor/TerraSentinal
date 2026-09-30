import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.db_models import DBEvent, DBAnalysisRun
from backend.app.models.schemas import AnalysisRunResponse, RunStatus, RunStage
from backend.app.services.pipeline import PipelineOrchestrator

router = APIRouter(prefix="", tags=["runs"])

@router.post("/events/{event_id}/runs", response_model=AnalysisRunResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_analysis_run(
    event_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    event = db.query(DBEvent).filter(DBEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc)
    
    run = DBAnalysisRun(
        id=run_id,
        event_id=event_id,
        status=RunStatus.QUEUED.value,
        stage=RunStage.INITIALIZING.value,
        progress=0.0,
        stage_message="Analysis run queued",
        started_at=now
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    # Dispatch pipeline to FastAPI background task worker
    background_tasks.add_task(PipelineOrchestrator.execute_run, event_id, run_id)
    
    return AnalysisRunResponse(
        id=run.id,
        event_id=run.event_id,
        status=run.status,
        stage=run.stage,
        progress=run.progress,
        stage_message=run.stage_message,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        execution_time_seconds=run.execution_time_seconds,
        model_name=run.model_name,
        model_version=run.model_version
    )

@router.get("/runs/{run_id}", response_model=AnalysisRunResponse)
def get_run_status(run_id: str, db: Session = Depends(get_db)):
    run = db.query(DBAnalysisRun).filter(DBAnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return AnalysisRunResponse(
        id=run.id,
        event_id=run.event_id,
        status=run.status,
        stage=run.stage,
        progress=run.progress,
        stage_message=run.stage_message,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        execution_time_seconds=run.execution_time_seconds,
        model_name=run.model_name,
        model_version=run.model_version
    )

@router.get("/events/{event_id}/runs", response_model=List[AnalysisRunResponse])
def list_event_runs(event_id: str, db: Session = Depends(get_db)):
    runs = db.query(DBAnalysisRun).filter(DBAnalysisRun.event_id == event_id).order_by(DBAnalysisRun.started_at.desc()).all()
    return [
        AnalysisRunResponse(
            id=r.id,
            event_id=r.event_id,
            status=r.status,
            stage=r.stage,
            progress=r.progress,
            stage_message=r.stage_message,
            error_message=r.error_message,
            started_at=r.started_at,
            completed_at=r.completed_at,
            execution_time_seconds=r.execution_time_seconds,
            model_name=r.model_name,
            model_version=r.model_version
        )
        for r in runs
    ]
