from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree
from backend.app.config import settings
from backend.app.models.schemas import (
    PassabilityState, DamageState, GeoJSONFeature, GeoJSONFeatureCollection
)

class InfrastructureDataset:
    def __init__(
        self,
        roads: List[Dict[str, Any]],
        bridges: List[Dict[str, Any]],
        facilities: List[Dict[str, Any]],
        buildings: List[Dict[str, Any]]
    ):
        self.roads = roads
        self.bridges = bridges
        self.facilities = facilities
        self.buildings = buildings

class InfrastructureService:
    """
    Manages transport network lines, bridges, critical facilities (hospitals, shelters),
    and building footprints. Performs spatial joins against flood masks to compute disruption.
    """
    
    @staticmethod
    def generate_synthetic_osm_network(
        bounds: Tuple[float, float, float, float]
    ) -> InfrastructureDataset:
        """
        Generates a topologically coherent road network, bridges, critical facilities,
        and buildings within the given geographical bounding box.
        """
        min_lon, min_lat, max_lon, max_lat = bounds
        d_lon = max_lon - min_lon
        d_lat = max_lat - min_lat
        
        roads: List[Dict[str, Any]] = []
        bridges: List[Dict[str, Any]] = []
        facilities: List[Dict[str, Any]] = []
        buildings: List[Dict[str, Any]] = []
        
        # 1. Critical Arterial Highway (West-East Highway N2)
        hwy_pts = [
            [min_lon + 0.05 * d_lon, min_lat + 0.48 * d_lat],
            [min_lon + 0.35 * d_lon, min_lat + 0.50 * d_lat],
            [min_lon + 0.65 * d_lon, min_lat + 0.49 * d_lat],
            [min_lon + 0.95 * d_lon, min_lat + 0.52 * d_lat]
        ]
        roads.append({
            "type": "Feature",
            "id": "road_hwy_n2_sec1",
            "geometry": {"type": "LineString", "coordinates": [hwy_pts[0], hwy_pts[1]]},
            "properties": {
                "id": "road_hwy_n2_sec1",
                "name": "Highway N2 (Western Arterial)",
                "highway": "primary",
                "lanes": 4,
                "maxspeed": 80,
                "length_km": 14.2
            }
        })
        roads.append({
            "type": "Feature",
            "id": "road_hwy_n2_sec2",
            "geometry": {"type": "LineString", "coordinates": [hwy_pts[1], hwy_pts[2]]},
            "properties": {
                "id": "road_hwy_n2_sec2",
                "name": "Highway N2 (Central River Causeway)",
                "highway": "primary",
                "lanes": 4,
                "maxspeed": 80,
                "length_km": 15.8
            }
        })
        roads.append({
            "type": "Feature",
            "id": "road_hwy_n2_sec3",
            "geometry": {"type": "LineString", "coordinates": [hwy_pts[2], hwy_pts[3]]},
            "properties": {
                "id": "road_hwy_n2_sec3",
                "name": "Highway N2 (Eastern Corridor)",
                "highway": "primary",
                "lanes": 4,
                "maxspeed": 80,
                "length_km": 13.5
            }
        })
        
        # 2. Critical Bridge over River (Bridge B-14)
        bridge_coords = [
            [min_lon + 0.48 * d_lon, min_lat + 0.49 * d_lat],
            [min_lon + 0.52 * d_lon, min_lat + 0.50 * d_lat]
        ]
        bridge_feat = {
            "type": "Feature",
            "id": "bridge_b14_surma",
            "geometry": {"type": "LineString", "coordinates": bridge_coords},
            "properties": {
                "id": "bridge_b14_surma",
                "name": "Surma River Main Bridge B-14",
                "bridge": "yes",
                "highway": "primary",
                "structure_type": "truss",
                "length_meters": 650,
                "critical_bottleneck": True
            }
        }
        bridges.append(bridge_feat)
        roads.append(bridge_feat) # Bridge is also a road network segment
        
        # 3. North-South Connector Roads
        ns_pts = [
            [min_lon + 0.35 * d_lon, min_lat + 0.15 * d_lat],
            [min_lon + 0.35 * d_lon, min_lat + 0.50 * d_lat],
            [min_lon + 0.35 * d_lon, min_lat + 0.85 * d_lat]
        ]
        roads.append({
            "type": "Feature",
            "id": "road_r101_south",
            "geometry": {"type": "LineString", "coordinates": [ns_pts[0], ns_pts[1]]},
            "properties": {"id": "road_r101_south", "name": "Regional Road R-101 (South)", "highway": "secondary", "maxspeed": 60, "length_km": 11.2}
        })
        roads.append({
            "type": "Feature",
            "id": "road_r101_north",
            "geometry": {"type": "LineString", "coordinates": [ns_pts[1], ns_pts[2]]},
            "properties": {"id": "road_r101_north", "name": "Regional Road R-101 (North Access)", "highway": "secondary", "maxspeed": 60, "length_km": 12.0}
        })
        
        # 4. Rural Feeder / Community Access Road (Road R-183 to Isolated North-East Valley)
        feeder_pts = [
            [min_lon + 0.65 * d_lon, min_lat + 0.49 * d_lat],
            [min_lon + 0.78 * d_lon, min_lat + 0.72 * d_lat],
            [min_lon + 0.88 * d_lon, min_lat + 0.88 * d_lat]
        ]
        roads.append({
            "type": "Feature",
            "id": "road_r183_sec1",
            "geometry": {"type": "LineString", "coordinates": [feeder_pts[0], feeder_pts[1]]},
            "properties": {"id": "road_r183_sec1", "name": "Sole Rural Access Road R-183", "highway": "tertiary", "maxspeed": 45, "length_km": 9.5}
        })
        roads.append({
            "type": "Feature",
            "id": "road_r183_sec2",
            "geometry": {"type": "LineString", "coordinates": [feeder_pts[1], feeder_pts[2]]},
            "properties": {"id": "road_r183_sec2", "name": "Gowainghat Valley Feeder", "highway": "unclassified", "maxspeed": 35, "length_km": 7.4}
        })
        
        # 5. Critical Facilities
        facilities.append({
            "type": "Feature",
            "id": "fac_hosp_osmani",
            "geometry": {"type": "Point", "coordinates": [min_lon + 0.25 * d_lon, min_lat + 0.45 * d_lat]},
            "properties": {
                "id": "fac_hosp_osmani",
                "name": "Osmani Medical College & Central Hospital",
                "facility_type": "HOSPITAL",
                "emergency_beds": 450,
                "trauma_center": True,
                "operational_status": "FUNCTIONING"
            }
        })
        facilities.append({
            "type": "Feature",
            "id": "fac_clinic_gowainghat",
            "geometry": {"type": "Point", "coordinates": [min_lon + 0.86 * d_lon, min_lat + 0.86 * d_lat]},
            "properties": {
                "id": "fac_clinic_gowainghat",
                "name": "Gowainghat Rural Upazila Health Complex",
                "facility_type": "CLINIC",
                "emergency_beds": 35,
                "trauma_center": False,
                "operational_status": "THREATENED"
            }
        })
        facilities.append({
            "type": "Feature",
            "id": "fac_shelter_east",
            "geometry": {"type": "Point", "coordinates": [min_lon + 0.75 * d_lon, min_lat + 0.68 * d_lat]},
            "properties": {
                "id": "fac_shelter_east",
                "name": "Govt High School Cyclone/Flood Shelter",
                "facility_type": "SHELTER",
                "capacity": 1200,
                "operational_status": "FUNCTIONING"
            }
        })
        facilities.append({
            "type": "Feature",
            "id": "fac_fire_central",
            "geometry": {"type": "Point", "coordinates": [min_lon + 0.32 * d_lon, min_lat + 0.48 * d_lat]},
            "properties": {
                "id": "fac_fire_central",
                "name": "District Central Fire & Rescue Station",
                "facility_type": "FIRE_STATION",
                "rescue_boats": 8,
                "operational_status": "FUNCTIONING"
            }
        })
        
        # 6. Sample Building Footprints
        for i in range(15):
            b_lon = min_lon + (0.2 + 0.6 * np.random.rand()) * d_lon
            b_lat = min_lat + (0.2 + 0.6 * np.random.rand()) * d_lat
            sz = 0.003
            poly = [
                [b_lon, b_lat],
                [b_lon + sz, b_lat],
                [b_lon + sz, b_lat + sz],
                [b_lon, b_lat + sz],
                [b_lon, b_lat]
            ]
            buildings.append({
                "type": "Feature",
                "id": f"bldg_{i+1}",
                "geometry": {"type": "Polygon", "coordinates": [poly]},
                "properties": {
                    "id": f"bldg_{i+1}",
                    "building": "residential" if i < 10 else "commercial",
                    "levels": 1 if i < 8 else 2
                }
            })
            
        return InfrastructureDataset(roads, bridges, facilities, buildings)

    @classmethod
    def analyze_infrastructure_impact(
        cls,
        infra: InfrastructureDataset,
        flood_polygons: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Computes spatial intersections between flood polygons and infrastructure.
        Determines passability states, building damage, and facility inundation.
        """
        # Build Shapely geometries from flood polygons
        flood_geoms = []
        for feat in flood_polygons:
            try:
                g = shape(feat["geometry"])
                if g.is_valid:
                    flood_geoms.append(g)
            except Exception:
                continue
                
        tree = STRtree(flood_geoms) if flood_geoms else None
        
        analyzed_roads: List[Dict[str, Any]] = []
        analyzed_bridges: List[Dict[str, Any]] = []
        analyzed_facilities: List[Dict[str, Any]] = []
        analyzed_buildings: List[Dict[str, Any]] = []
        
        blocked_roads_count = 0
        affected_roads_count = 0
        blocked_km = 0.0
        
        # 1. Road Network Spatial Analysis
        for road_feat in infra.roads:
            feat_copy = dict(road_feat)
            props = dict(feat_copy["properties"])
            road_line = shape(road_feat["geometry"])
            total_len = road_line.length
            
            flooded_len = 0.0
            if tree and total_len > 0:
                candidate_indices = tree.query(road_line)
                candidate_geoms = [flood_geoms[idx] for idx in candidate_indices if road_line.intersects(flood_geoms[idx])]
                if candidate_geoms:
                    merged_flood = unary_union(candidate_geoms)
                    inter = road_line.intersection(merged_flood)
                    flooded_len = inter.length
                        
            overlap_ratio = min(1.0, flooded_len / max(1e-7, total_len))
            props["flood_overlap_ratio"] = round(overlap_ratio, 3)
            
            # Determine Passability State
            is_bridge = (props.get("bridge") == "yes")
            if overlap_ratio >= settings.PASSABILITY_BLOCKED_THRESHOLD or (is_bridge and overlap_ratio > 0.25):
                props["passability_state"] = PassabilityState.BLOCKED.value
                props["speed_factor"] = 0.0
                blocked_roads_count += 1
                blocked_km += props.get("length_km", 1.0)
            elif overlap_ratio >= settings.PASSABILITY_LIKELY_BLOCKED_THRESHOLD:
                props["passability_state"] = PassabilityState.LIKELY_BLOCKED.value
                props["speed_factor"] = 0.15
                affected_roads_count += 1
            elif overlap_ratio >= settings.PASSABILITY_PARTIAL_THRESHOLD:
                props["passability_state"] = PassabilityState.PARTIALLY_AFFECTED.value
                props["speed_factor"] = 0.45
                affected_roads_count += 1
            else:
                props["passability_state"] = PassabilityState.OPEN.value
                props["speed_factor"] = 1.0
                
            props["confidence"] = 0.86
            props["last_inspected"] = "2026-05-28T12:00:00Z"
            feat_copy["properties"] = props
            analyzed_roads.append(feat_copy)
            
            if is_bridge:
                analyzed_bridges.append(feat_copy)
                
        # 2. Critical Facilities Analysis
        flooded_fac_count = 0
        for fac_feat in infra.facilities:
            f_copy = dict(fac_feat)
            props = dict(f_copy["properties"])
            pt = shape(fac_feat["geometry"])
            
            is_flooded = False
            if tree:
                candidate_indices = tree.query(pt)
                for idx in candidate_indices:
                    if pt.within(flood_geoms[idx]):
                        is_flooded = True
                        break
                        
            props["is_flooded"] = is_flooded
            if is_flooded:
                flooded_fac_count += 1
                props["operational_status"] = "FLOODED_INACCESSIBLE"
            else:
                props["operational_status"] = "FUNCTIONING"
                
            f_copy["properties"] = props
            analyzed_facilities.append(f_copy)
            
        # 3. Buildings Analysis
        for b_feat in infra.buildings:
            b_copy = dict(b_feat)
            props = dict(b_copy["properties"])
            poly = shape(b_feat["geometry"])
            
            overlap_area = 0.0
            if tree:
                for idx in tree.query(poly):
                    if poly.intersects(flood_geoms[idx]):
                        overlap_area += poly.intersection(flood_geoms[idx]).area
                        
            area_ratio = min(1.0, overlap_area / max(1e-8, poly.area))
            if area_ratio > 0.60:
                props["damage_state"] = DamageState.MAJOR.value
            elif area_ratio > 0.20:
                props["damage_state"] = DamageState.MINOR.value
            else:
                props["damage_state"] = DamageState.INTACT.value
                
            props["damage_ratio"] = round(area_ratio, 2)
            b_copy["properties"] = props
            analyzed_buildings.append(b_copy)
            
        summary = {
            "total_roads_analyzed": len(infra.roads),
            "roads_blocked_count": blocked_roads_count,
            "roads_affected_count": affected_roads_count,
            "roads_blocked_km": round(blocked_km, 2),
            "bridges_analyzed": len(infra.bridges),
            "bridges_blocked_count": sum(1 for b in analyzed_bridges if b["properties"]["passability_state"] == PassabilityState.BLOCKED.value),
            "facilities_flooded_count": flooded_fac_count,
            "buildings_affected_count": sum(1 for b in analyzed_buildings if b["properties"]["damage_state"] != DamageState.INTACT.value)
        }
        
        return analyzed_roads, analyzed_bridges, analyzed_facilities, analyzed_buildings, summary
