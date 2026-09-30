import pytest
from backend.app.services.infrastructure import InfrastructureService
from backend.app.services.network_engine import DynamicNetworkEngine
from backend.app.services.isolation_engine import IsolationEngine
from backend.app.models.schemas import PassabilityState

def test_dynamic_network_isolation_analysis():
    bounds = (91.80, 24.85, 92.15, 25.10)
    infra = InfrastructureService.generate_synthetic_osm_network(bounds)
    
    # Simulate a flood polygon that severs Bridge B-14 and Highway N2 Central Causeway
    synthetic_flood = [{
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[91.95, 24.95], [92.05, 24.95], [92.05, 25.02], [91.95, 25.02], [91.95, 24.95]]]
        },
        "properties": {"hazard_type": "INUNDATION"}
    }]
    
    roads, bridges, facilities, buildings, summary = InfrastructureService.analyze_infrastructure_impact(
        infra=infra,
        flood_polygons=synthetic_flood
    )
    
    assert summary["roads_blocked_count"] > 0
    assert summary["bridges_blocked_count"] > 0
    
    # Build dynamic graph
    static_G = DynamicNetworkEngine.build_network(roads, facilities)
    assert len(static_G.nodes) > 0
    assert len(static_G.edges) > 0
    
    # Route accessibility
    routing_res = DynamicNetworkEngine.analyze_dynamic_accessibility(static_G, facilities)
    assert len(routing_res.isolated_components) > 0
    
    # Isolation consequence
    iso_res = IsolationEngine.assess_isolation(routing_res, roads)
    assert iso_res.isolated_communities_count > 0
    assert iso_res.total_isolated_population > 0
    for comm in iso_res.communities:
        assert 0.0 <= comm.isolation_score <= 100.0
        assert comm.boundary_polygon is not None
