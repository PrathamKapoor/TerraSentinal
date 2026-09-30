from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.db_models import DBInfrastructureResult, DBSimulation
from backend.app.models.schemas import (
    SimulationRequest, SimulationResponse, CounterfactualDelta
)
from backend.app.services.simulation_engine import SimulationEngine

router = APIRouter(prefix="/simulations", tags=["simulations"])

@router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
def run_simulation(req: SimulationRequest, db: Session = Depends(get_db)):
    infra_res = db.query(DBInfrastructureResult).filter(DBInfrastructureResult.event_id == req.event_id).order_by(DBInfrastructureResult.created_at.desc()).first()
    if not infra_res:
        raise HTTPException(status_code=400, detail="Cannot run simulation: Run analysis first to produce baseline infrastructure.")
        
    roads = infra_res.roads_geojson.get("features", [])
    facilities = infra_res.facilities_geojson.get("features", [])
    
    baseline_pop = sum(c.get("estimated_population", 0) for c in (infra_res.isolated_communities_json or []))
    if baseline_pop == 0:
        baseline_pop = 12500
        
    sim_resp = SimulationEngine.run_simulation(
        request=req,
        road_features=roads,
        facility_features=facilities,
        baseline_isolated_pop=baseline_pop
    )
    
    # Persist simulation in DB
    db_sim = DBSimulation(
        id=sim_resp.simulation_id,
        event_id=req.event_id,
        scenario_name=req.scenario_name,
        interventions_json=[i.model_dump(mode='json') for i in req.interventions],
        baseline_isolated_pop=baseline_pop,
        simulated_isolated_pop=sim_resp.simulated_isolated_population,
        delta_json=sim_resp.delta.model_dump(mode='json'),
        explanation=sim_resp.explanation,
        created_at=sim_resp.created_at
    )
    db.add(db_sim)
    db.commit()
    
    return sim_resp

@router.get("/{sim_id}", response_model=SimulationResponse)
def get_simulation(sim_id: str, db: Session = Depends(get_db)):
    s = db.query(DBSimulation).filter(DBSimulation.id == sim_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Simulation record not found")
        
    return SimulationResponse(
        simulation_id=s.id,
        event_id=s.event_id,
        scenario_name=s.scenario_name,
        created_at=s.created_at,
        interventions_applied=s.interventions_json,
        baseline_isolated_population=s.baseline_isolated_pop,
        simulated_isolated_population=s.simulated_isolated_pop,
        delta=CounterfactualDelta(**s.delta_json),
        simulation_badge="SIMULATED / COUNTERFACTUAL",
        explanation=s.explanation
    )
