"""
TerraSentinel Failure Injection & Edge-Case Robustness Tests
============================================================
Validates system resilience against pathological inputs:
1. All-NaN / corrupted satellite raster arrays.
2. Complete absence of all sensory modalities.
3. Self-intersecting (bowtie) polygon geometries.
4. Empty infrastructure datasets (0 roads, 0 facilities, 0 communities).
5. Disjoint geospatial extents (flood mask completely non-overlapping with infrastructure).
"""

import numpy as np
import pytest
from shapely.geometry import Polygon, mapping
from shapely.validation import make_valid

from backend.app.services.evidence_fusion import EvidenceFusionEngine
from backend.app.services.flood_detector import DualPolSARTerrainAdapter
from backend.app.services.network_engine import DynamicNetworkEngine
from backend.app.services.infrastructure import InfrastructureService, InfrastructureDataset


def test_missing_all_modalities_raises_clear_error():
    """Verify system rejects requests when all sensory modalities are missing."""
    with pytest.raises(ValueError, match="At least one Earth observation modality"):
        EvidenceFusionEngine.fuse_observations(
            sar_vv=None,
            sar_vh=None,
            optical_mndwi=None,
            dem_slope=None,
        )


def test_corrupted_nan_sar_input_handling():
    """Verify handling when SAR imagery contains NaN values from sensor failure."""
    detector = DualPolSARTerrainAdapter()
    
    # 64x64 array full of NaNs
    nan_vv = np.full((64, 64), np.nan, dtype=np.float32)
    nan_vh = np.full((64, 64), np.nan, dtype=np.float32)
    slope = np.zeros((64, 64), dtype=np.float32)
    bounds = (91.80, 24.80, 91.95, 24.95)
    
    res = detector.predict(nan_vv, nan_vh, slope, None, bounds)
    assert res.binary_mask.shape == (64, 64)
    # Mask, probability, and confidence should not contain any NaNs
    assert not np.isnan(res.binary_mask).any()
    assert not np.isnan(res.probability_map).any()
    assert not np.isnan(res.confidence_map).any()


def test_self_intersecting_bowtie_polygon_handling():
    """Verify that self-intersecting polygon geometries (bowtie) are sanitized with make_valid."""
    # Classical bowtie polygon: (0,0) to (2,2) to (2,0) to (0,2) to (0,0)
    bowtie_coords = [(0.0, 0.0), (2.0, 2.0), (2.0, 0.0), (0.0, 2.0), (0.0, 0.0)]
    bowtie_poly = Polygon(bowtie_coords)
    assert not bowtie_poly.is_valid  # Confirm it is strictly invalid
    
    # Sanitization
    valid_poly = make_valid(bowtie_poly)
    assert valid_poly.is_valid
    
    flood_feature = {
        "type": "Feature",
        "geometry": mapping(valid_poly),
        "properties": {"severity": "HIGH"}
    }
    
    road_feature = {
        "type": "Feature",
        "id": "road_bowtie_test",
        "geometry": {"type": "LineString", "coordinates": [[1.0, 1.0], [1.5, 1.5]]},
        "properties": {"id": "road_bowtie_test", "name": "Bowtie Cross", "length_km": 1.0, "maxspeed": 50}
    }
    
    dataset = InfrastructureDataset(roads=[road_feature], bridges=[], facilities=[], buildings=[])
    analyzed_roads, _, _, _, metrics = InfrastructureService.analyze_infrastructure_impact(
        dataset, [flood_feature]
    )
    assert len(analyzed_roads) == 1
    assert analyzed_roads[0]["properties"]["passability_state"] in ["BLOCKED", "LIKELY_BLOCKED", "PARTIALLY_AFFECTED", "OPEN"]


def test_empty_infrastructure_dataset():
    """Verify network analysis and infrastructure correlation with 0 roads, 0 facilities, 0 communities."""
    empty_dataset = InfrastructureDataset(roads=[], bridges=[], facilities=[], buildings=[])
    poly_feat = {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [[[91.8, 24.8], [91.9, 24.8], [91.9, 24.9], [91.8, 24.9], [91.8, 24.8]]]},
        "properties": {}
    }
    analyzed_roads, analyzed_bridges, analyzed_facilities, analyzed_bldgs, metrics = (
        InfrastructureService.analyze_infrastructure_impact(empty_dataset, [poly_feat])
    )
    assert len(analyzed_roads) == 0
    assert len(analyzed_facilities) == 0
    assert metrics["roads_blocked_count"] == 0
    
    # Network graph build on empty features
    G = DynamicNetworkEngine.build_network(road_features=[], facility_features=[])
    assert len(G.nodes) == 0
    assert len(G.edges) == 0


def test_disjoint_spatial_extents():
    """Verify that a flood polygon located in the Pacific ocean does not falsely sever roads in Bangladesh."""
    # Flood in Pacific Ocean (0, 0)
    pacific_flood = {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [[[0.0, 0.0], [0.1, 0.0], [0.1, 0.1], [0.0, 0.1], [0.0, 0.0]]]},
        "properties": {"severity": "HIGH"}
    }
    
    # Roads in Sylhet, Bangladesh (~91.8 deg E, ~24.8 deg N)
    sylhet_road = {
        "type": "Feature",
        "id": "road_sylhet_1",
        "geometry": {"type": "LineString", "coordinates": [[91.85, 24.88], [91.87, 24.90]]},
        "properties": {"id": "road_sylhet_1", "name": "Sylhet Bypass", "length_km": 3.0, "maxspeed": 60}
    }
    sylhet_facility = {
        "type": "Feature",
        "id": "fac_sylhet_1",
        "geometry": {"type": "Point", "coordinates": [91.86, 24.89]},
        "properties": {"id": "fac_sylhet_1", "name": "Sylhet Hospital", "facility_type": "HOSPITAL"}
    }
    
    dataset = InfrastructureDataset(roads=[sylhet_road], bridges=[], facilities=[sylhet_facility], buildings=[])
    analyzed_roads, _, analyzed_facilities, _, metrics = InfrastructureService.analyze_infrastructure_impact(
        dataset, [pacific_flood]
    )
    
    assert analyzed_roads[0]["properties"]["passability_state"] == "OPEN"
    assert analyzed_roads[0]["properties"]["flood_overlap_ratio"] == 0.0
    assert analyzed_facilities[0]["properties"]["operational_status"] != "INUNDATED"
    assert metrics["roads_blocked_count"] == 0
