import pytest
import numpy as np
from shapely.geometry import Polygon, LineString, shape, box
from shapely.validation import make_valid
from backend.app.services.preprocessing import raster_to_geojson_polygons
from backend.app.services.infrastructure import InfrastructureService, InfrastructureDataset

def test_equirectangular_area_calculation_accuracy():
    """
    Verifies that degree-to-kilometer scaling respects geographic latitude:
    At 25° N (Sylhet):
    1 deg lat = 111.32 km
    1 deg lon = 111.32 * cos(25°) = 111.32 * 0.9063 = 100.89 km
    A 0.1 x 0.1 degree square should measure ~ 111.32 * 100.89 * 0.01 = ~112.3 sq km.
    """
    bounds = (91.9, 24.9, 92.0, 25.0)  # 0.1 x 0.1 deg at ~25° N
    mask = np.ones((50, 50), dtype=bool)  # Entire area is flooded
    
    polys = raster_to_geojson_polygons(mask, bounds, min_area_pixels=10)
    assert len(polys) == 1
    area_sqkm = polys[0]["properties"]["area_sqkm"]
    
    expected_area = 0.1 * 111.32 * 0.1 * 111.32 * np.cos(np.radians(24.95))
    assert abs(area_sqkm - expected_area) / expected_area < 0.03  # Within 3% tolerance

def test_polygon_geometry_validity_guarantee():
    """
    Verifies that complex concave binary masks vectorized with raster_to_geojson_polygons
    always yield strictly valid geometries (geom.is_valid is True).
    """
    np.random.seed(42)
    # Generate noisy fractal mask with holes and narrow necks
    mask = np.zeros((80, 80), dtype=bool)
    mask[20:60, 20:60] = True
    mask[30:50, 30:50] = False  # Hole
    mask[15:25, 40:70] = True   # Concave arm
    
    bounds = (91.8, 24.8, 92.2, 25.2)
    polys = raster_to_geojson_polygons(mask, bounds, simplify_tolerance=0.0004)
    
    assert len(polys) > 0
    for p in polys:
        geom = shape(p["geometry"])
        assert geom.is_valid is True
        assert not geom.is_empty

def test_road_flood_intersection_non_double_counting():
    """
    Verifies that two overlapping or contiguous flood polygons intersecting the same
    road segment do NOT double-count the flooded length.
    """
    # 10 km east-west road
    road_geom = {"type": "LineString", "coordinates": [[91.80, 24.85], [91.90, 24.85]]}
    road_feat = {
        "type": "Feature",
        "properties": {"id": "r_test", "name": "Test Road", "length_km": 10.0, "maxspeed": 60},
        "geometry": road_geom
    }
    
    # Two overlapping flood polygons covering the middle section (91.83 to 91.87) = 40% of road
    poly1 = box(91.83, 24.84, 91.86, 24.86)
    poly2 = box(91.85, 24.84, 91.87, 24.86)  # Overlaps poly1 between 91.85 and 91.86
    
    flood_polys = [
        {"geometry": {"type": "Polygon", "coordinates": [list(poly1.exterior.coords)]}},
        {"geometry": {"type": "Polygon", "coordinates": [list(poly2.exterior.coords)]}}
    ]
    
    infra = InfrastructureDataset(roads=[road_feat], bridges=[], facilities=[], buildings=[])
    analyzed_roads, _, _, _, _ = InfrastructureService.analyze_infrastructure_impact(infra, flood_polys)
    
    overlap = analyzed_roads[0]["properties"]["flood_overlap_ratio"]
    # Total combined span is 91.83 to 91.87 out of 91.80 to 91.90 = 0.04 / 0.10 = 0.40 (40%)
    # If double-counted, it would be 0.03 + 0.02 = 0.50 (50%)
    assert abs(overlap - 0.40) < 0.02
