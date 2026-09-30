import pytest
import copy
from backend.app.services.simulation_engine import SimulationEngine
from backend.app.models.schemas import SimulationRequest, SimulationIntervention, PassabilityState

def test_counterfactual_simulation_preserves_observed_state_immutability():
    """
    Verifies that running a counterfactual intervention simulation NEVER mutates
    the original observed road features or infrastructure dictionaries.
    """
    observed_roads = [
        {
            "type": "Feature",
            "properties": {
                "id": "bridge_b14",
                "name": "Bridge B-14",
                "passability_state": "BLOCKED",
                "speed_factor": 0.0,
                "length_km": 1.2
            },
            "geometry": {"type": "LineString", "coordinates": [[91.80, 24.80], [91.82, 24.80]]}
        },
        {
            "type": "Feature",
            "properties": {
                "id": "road_arterial",
                "name": "Main Road",
                "passability_state": "OPEN",
                "speed_factor": 1.0,
                "length_km": 5.0
            },
            "geometry": {"type": "LineString", "coordinates": [[91.82, 24.80], [91.90, 24.80]]}
        }
    ]
    observed_facilities = [{
        "type": "Feature",
        "properties": {"id": "fac_hospital", "name": "District Hospital", "facility_type": "HOSPITAL", "operational_status": "FUNCTIONING"},
        "geometry": {"type": "Point", "coordinates": [91.90, 24.80]}
    }]
    
    # Snapshot original before simulation
    roads_snapshot = copy.deepcopy(observed_roads)
    facilities_snapshot = copy.deepcopy(observed_facilities)
    
    req = SimulationRequest(
        event_id="evt_sim_test",
        scenario_name="Emergency Pontoon on Bridge B-14",
        interventions=[
            SimulationIntervention(
                target_infrastructure_id="bridge_b14",
                target_name="Bridge B-14",
                intervention_type="DEPLOY_PONTOON",
                new_state=PassabilityState.OPEN
            )
        ]
    )
    
    sim_res = SimulationEngine.run_simulation(
        request=req,
        road_features=observed_roads,
        facility_features=observed_facilities,
        baseline_isolated_pop=8500
    )
    
    # 1. Verify observed state is 100% UNMUTATED
    assert observed_roads == roads_snapshot, "Observed road features were mutated during simulation!"
    assert observed_facilities == facilities_snapshot, "Observed facilities were mutated!"
    assert observed_roads[0]["properties"]["passability_state"] == "BLOCKED"
    assert observed_roads[0]["properties"]["speed_factor"] == 0.0
    
    # 2. Verify simulation output clearly carries the SIMULATED badge
    assert sim_res.simulation_badge == "SIMULATED / COUNTERFACTUAL"
    
    # 3. Verify delta impacts were recomputed dynamically
    assert sim_res.delta.reconnected_population > 0
    assert sim_res.delta.reopened_road_km == 1.2
    assert sim_res.delta.average_travel_time_saved_minutes > 0.0
    assert sim_res.simulated_isolated_population < sim_res.baseline_isolated_population
