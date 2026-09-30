import networkx as nx
from typing import Dict, Any, List, Tuple, Optional
from shapely.geometry import shape, Point, LineString
from backend.app.models.schemas import PassabilityState

class RoutingGraphResult:
    def __init__(
        self,
        full_graph: nx.Graph,
        active_graph: nx.Graph,
        isolated_components: List[List[Any]],
        hospitals_reachable: Dict[str, bool],
        accessibility_deltas: Dict[str, float]
    ):
        self.full_graph = full_graph
        self.active_graph = active_graph
        self.isolated_components = isolated_components
        self.hospitals_reachable = hospitals_reachable
        self.accessibility_deltas = accessibility_deltas

class DynamicNetworkEngine:
    """
    Constructs dynamic flood-aware transport graphs, updating edge impedances
    based on satellite-detected inundation, and computing shortest paths and connectivity.
    """
    
    @staticmethod
    def _coord_key(coord: List[float]) -> Tuple[float, float]:
        return (round(coord[0], 5), round(coord[1], 5))

    @classmethod
    def build_network(
        cls,
        road_features: List[Dict[str, Any]],
        facility_features: List[Dict[str, Any]]
    ) -> nx.Graph:
        """
        Builds static graph topology from road linestrings.
        """
        G = nx.Graph()
        
        for feat in road_features:
            props = feat["properties"]
            coords = feat["geometry"]["coordinates"]
            if len(coords) < 2:
                continue
                
            u = cls._coord_key(coords[0])
            v = cls._coord_key(coords[-1])
            
            length_km = props.get("length_km", 1.0)
            base_speed = props.get("maxspeed", 50)
            road_id = props.get("id", "road")
            passability = props.get("passability_state", PassabilityState.OPEN.value)
            speed_factor = props.get("speed_factor", 1.0)
            
            # Static travel time in minutes
            static_time_min = (length_km / max(10, base_speed)) * 60.0
            
            G.add_edge(
                u, v,
                id=road_id,
                name=props.get("name", "Road"),
                length_km=length_km,
                base_speed=base_speed,
                passability_state=passability,
                speed_factor=speed_factor,
                static_time_min=static_time_min,
                is_bridge=(props.get("bridge") == "yes")
            )
            
        return G

    @classmethod
    def analyze_dynamic_accessibility(
        cls,
        static_graph: nx.Graph,
        facility_features: List[Dict[str, Any]]
    ) -> RoutingGraphResult:
        """
        Derives active passable graph by removing or heavily weighting BLOCKED edges,
        and computes shortest path travel-time degradation to critical facilities.
        """
        active_G = static_graph.copy()
        
        # Remove or penalize severed edges
        for u, v, data in list(active_G.edges(data=True)):
            passability = data.get("passability_state", PassabilityState.OPEN.value)
            speed_factor = data.get("speed_factor", 1.0)
            
            if passability == PassabilityState.BLOCKED.value or speed_factor <= 0.0:
                active_G.remove_edge(u, v)
            else:
                # Degraded speed increases travel time
                data["dynamic_time_min"] = data["static_time_min"] / max(0.05, speed_factor)

        # Identify hospital nodes
        hospital_nodes = []
        for fac in facility_features:
            props = fac["properties"]
            if props.get("facility_type") == "HOSPITAL" and props.get("operational_status") != "FLOODED_INACCESSIBLE":
                pt = fac["geometry"]["coordinates"]
                fac_node = cls._coord_key(pt)
                
                # Find nearest node in graph
                best_node = None
                best_dist = float("inf")
                for n in static_graph.nodes():
                    d = (n[0] - fac_node[0])**2 + (n[1] - fac_node[1])**2
                    if d < best_dist:
                        best_dist = d
                        best_node = n
                if best_node:
                    hospital_nodes.append((props.get("id"), props.get("name"), best_node))
                    
        # Connected components in active graph
        components = list(nx.connected_components(active_G))
        
        # Determine which components contain functioning hospitals
        hosp_nodes_set = {hn[2] for hn in hospital_nodes}
        
        isolated_components = []
        for comp in components:
            if not comp.intersection(hosp_nodes_set):
                # This component has ZERO paths to any functioning hospital!
                isolated_components.append(list(comp))
                
        # Accessibility deltas for all nodes
        accessibility_deltas: Dict[str, float] = {}
        for n in static_graph.nodes():
            node_str = f"{n[0]},{n[1]}"
            # Pre-event shortest time to hospital
            pre_times = []
            for hid, hname, hnode in hospital_nodes:
                try:
                    t = nx.shortest_path_length(static_graph, source=n, target=hnode, weight="static_time_min")
                    pre_times.append(t)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass
            t_pre = min(pre_times) if pre_times else 999.0
            
            # Post-event shortest time in active graph
            post_times = []
            for hid, hname, hnode in hospital_nodes:
                try:
                    if n in active_G and hnode in active_G:
                        t = nx.shortest_path_length(active_G, source=n, target=hnode, weight="dynamic_time_min")
                        post_times.append(t)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pass
            t_post = min(post_times) if post_times else 999.0  # Cut off
            
            delta = t_post - t_pre
            accessibility_deltas[node_str] = round(delta, 1)

        hospitals_reachable = {}
        for hid, hname, hnode in hospital_nodes:
            hospitals_reachable[hid] = (hnode in active_G and active_G.degree(hnode) > 0)
            
        return RoutingGraphResult(
            full_graph=static_graph,
            active_graph=active_G,
            isolated_components=isolated_components,
            hospitals_reachable=hospitals_reachable,
            accessibility_deltas=accessibility_deltas
        )
