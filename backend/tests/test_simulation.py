import pytest
from backend.app.services.infrastructure import InfrastructureService
from backend.app.services.simulation_engine import SimulationEngine
from backend.app.models.schemas import (
    SimulationRequest, SimulationIntervention, InterventionType, PassabilityState
)

def test_counterfactual_simulation_reconnection():
    bounds = (91.80, 24.85, 92.15, 25.10)
    infra = InfrastructureService.generate_synthetic_osm_network(bounds)
    
    # Mark bridge as blocked
    roads = [dict(r) for r in infra.roads]
    for r in roads:
        if r["properties"].get("bridge") == "yes":
            r["properties"]["passability_state"] = PassabilityState.BLOCKED.value
            r["properties"]["speed_factor"] = 0.0
            
    req = SimulationRequest(
        event_id="evt_test",
        scenario_name="Restore Surma River Main Bridge B-14",
        interventions=[
            SimulationIntervention(
                intervention_type=InterventionType.RESTORE_BRIDGE,
                target_infrastructure_id="bridge_b14_surma",
                target_name="Surma River Main Bridge B-14",
                new_state=PassabilityState.OPEN
            )
        ]
    )
    
    res = SimulationEngine.run_simulation(
        request=req,
        road_features=roads,
        facility_features=infra.facilities,
        baseline_isolated_pop=18500
    )
    
    assert res.simulation_badge == "SIMULATED / COUNTERFACTUAL"
    assert res.delta.reconnected_population > 0
    assert res.delta.average_travel_time_saved_minutes > 0
    assert "Bridge B-14" in res.explanation
