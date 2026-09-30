import pytest
import networkx as nx
from backend.app.services.network_engine import DynamicNetworkEngine
from backend.app.services.isolation_engine import IsolationEngine
from backend.app.models.schemas import PassabilityState

def test_single_bridge_dependency_causes_complete_isolation():
    """
    Fixture 1: Island community has only ONE bridge connecting it to the mainland hospital.
    When that bridge is BLOCKED, the island must be detected as an isolated component.
    """
    # Nodes: (0,0) Island Village, (1,0) Bridge West, (2,0) Bridge East, (3,0) Hospital
    roads = [
        # Road inside island
        {"type": "Feature", "properties": {"id": "r1", "name": "Island Lane", "length_km": 2.0, "maxspeed": 50, "passability_state": "OPEN", "speed_factor": 1.0},
         "geometry": {"type": "LineString", "coordinates": [[91.80, 24.80], [91.82, 24.80]]}},
        # Single Bridge connecting island to mainland
        {"type": "Feature", "properties": {"id": "bridge_main", "name": "Sole Access Bridge", "length_km": 1.5, "maxspeed": 40, "passability_state": "BLOCKED", "speed_factor": 0.0, "bridge": "yes"},
         "geometry": {"type": "LineString", "coordinates": [[91.82, 24.80], [91.85, 24.80]]}},
        # Mainland road to hospital
        {"type": "Feature", "properties": {"id": "r2", "name": "Mainland Arterial", "length_km": 3.0, "maxspeed": 60, "passability_state": "OPEN", "speed_factor": 1.0},
         "geometry": {"type": "LineString", "coordinates": [[91.85, 24.80], [91.90, 24.80]]}}
    ]
    facilities = [{
        "type": "Feature",
        "properties": {"id": "fac_hospital_1", "name": "District Hospital", "facility_type": "HOSPITAL", "operational_status": "FUNCTIONING"},
        "geometry": {"type": "Point", "coordinates": [91.90, 24.80]}
    }]
    
    G = DynamicNetworkEngine.build_network(roads, facilities)
    res = DynamicNetworkEngine.analyze_dynamic_accessibility(G, facilities)
    
    assert len(res.isolated_components) == 1
    # Check that island node is isolated (travel time delta is high / cutoff)
    island_node = f"{91.80},{24.80}"
    assert res.accessibility_deltas[island_node] >= 900.0  # Cut-off

def test_alternate_routes_finds_dijkstra_detour():
    """
    Fixture 2: Primary direct highway is BLOCKED, but a secondary rural detour exists.
    Expected: Island is NOT isolated, but travel time delta is strictly positive (> 15 min).
    """
    roads = [
        # Direct Highway: Blocked
        {"type": "Feature", "properties": {"id": "hwy_direct", "name": "Direct Highway", "length_km": 5.0, "maxspeed": 60, "passability_state": "BLOCKED", "speed_factor": 0.0},
         "geometry": {"type": "LineString", "coordinates": [[91.80, 24.80], [91.90, 24.80]]}},
        # Detour Segment 1 (North)
        {"type": "Feature", "properties": {"id": "detour_north", "name": "Rural Detour North", "length_km": 12.0, "maxspeed": 40, "passability_state": "OPEN", "speed_factor": 1.0},
         "geometry": {"type": "LineString", "coordinates": [[91.80, 24.80], [91.85, 24.90]]}},
        # Detour Segment 2 (East to Hospital)
        {"type": "Feature", "properties": {"id": "detour_east", "name": "Rural Detour East", "length_km": 12.0, "maxspeed": 40, "passability_state": "OPEN", "speed_factor": 1.0},
         "geometry": {"type": "LineString", "coordinates": [[91.85, 24.90], [91.90, 24.80]]}}
    ]
    facilities = [{
        "type": "Feature",
        "properties": {"id": "fac_hospital_1", "name": "District Hospital", "facility_type": "HOSPITAL", "operational_status": "FUNCTIONING"},
        "geometry": {"type": "Point", "coordinates": [91.90, 24.80]}
    }]
    
    G = DynamicNetworkEngine.build_network(roads, facilities)
    res = DynamicNetworkEngine.analyze_dynamic_accessibility(G, facilities)
    
    assert len(res.isolated_components) == 0  # Re-routed, not isolated
    origin_node = f"{91.80},{24.80}"
    # Detour is 24 km @ 40 km/h = 36 min; Pre-event was 5 km @ 60 km/h = 5 min
    # Delta should be ~ 31 minutes
    delta = res.accessibility_deltas[origin_node]
    assert 25.0 < delta < 40.0

def test_partial_passability_reduces_travel_speed():
    """
    Fixture 3: Road is PARTIALLY flooded (speed factor 0.35).
    Expected: Road remains in active graph, but transit time increases by ~185%.
    """
    roads = [
        {"type": "Feature", "properties": {"id": "r_waterlogged", "name": "Waterlogged Road", "length_km": 10.0, "maxspeed": 50, "passability_state": "PARTIAL", "speed_factor": 0.35},
         "geometry": {"type": "LineString", "coordinates": [[91.80, 24.80], [91.90, 24.80]]}}
    ]
    facilities = [{
        "type": "Feature",
        "properties": {"id": "fac_hosp", "name": "Clinic", "facility_type": "HOSPITAL", "operational_status": "FUNCTIONING"},
        "geometry": {"type": "Point", "coordinates": [91.90, 24.80]}
    }]
    
    G = DynamicNetworkEngine.build_network(roads, facilities)
    res = DynamicNetworkEngine.analyze_dynamic_accessibility(G, facilities)
    
    assert len(res.isolated_components) == 0
    delta = res.accessibility_deltas[f"{91.80},{24.80}"]
    # Static: 10 km @ 50 km/h = 12 min. Dynamic: 12 / 0.35 = 34.3 min. Delta = ~22.3 min
    assert 18.0 < delta < 26.0

def test_population_aggregation_on_isolated_communities():
    """
    Fixture 4: Verify that IsolationEngine correctly aggregates gridded population
    inside isolated network component polygons.
    """
    roads = [
        # Isolated island road
        {"type": "Feature", "properties": {"id": "r_isolated", "name": "Cutoff Ring", "length_km": 4.0, "maxspeed": 40, "passability_state": "OPEN", "speed_factor": 1.0},
         "geometry": {"type": "LineString", "coordinates": [[91.81, 24.81], [91.83, 24.83]]}},
        # Blocked connecting bridge
        {"type": "Feature", "properties": {"id": "b_cut", "name": "Submerged Bridge", "length_km": 1.0, "maxspeed": 40, "passability_state": "BLOCKED", "speed_factor": 0.0},
         "geometry": {"type": "LineString", "coordinates": [[91.83, 24.83], [91.90, 24.90]]}},
        # Mainland road with hospital
        {"type": "Feature", "properties": {"id": "r_mainland", "name": "Mainland Road", "length_km": 3.0, "maxspeed": 50, "passability_state": "OPEN", "speed_factor": 1.0},
         "geometry": {"type": "LineString", "coordinates": [[91.90, 24.90], [91.95, 24.95]]}}
    ]
    facilities = [{
        "type": "Feature",
        "properties": {"id": "fac_hosp", "name": "Main Hospital", "facility_type": "HOSPITAL", "operational_status": "FUNCTIONING"},
        "geometry": {"type": "Point", "coordinates": [91.95, 24.95]}
    }]
    
    G = DynamicNetworkEngine.build_network(roads, facilities)
    res = DynamicNetworkEngine.analyze_dynamic_accessibility(G, facilities)
    
    isolation_summary = IsolationEngine.assess_isolation(res, roads)
    assert isolation_summary.isolated_communities_count == 1
    assert isolation_summary.total_isolated_population > 0
    comm = isolation_summary.communities[0]
    assert comm.current_status == "COMPLETELY_CUT_OFF"
    assert comm.boundary_polygon is not None
