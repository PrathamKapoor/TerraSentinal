from typing import Dict, Any, List, Tuple
import numpy as np
from backend.app.models.schemas import ChangeCategory
from backend.app.services.preprocessing import raster_to_geojson_polygons

class ChangeDetectionResult:
    def __init__(
        self,
        change_mask: np.ndarray,
        change_polygons: List[Dict[str, Any]],
        newly_flooded_sqkm: float,
        permanent_water_sqkm: float,
        receded_sqkm: float,
        expansion_factor: float
    ):
        self.change_mask = change_mask
        self.change_polygons = change_polygons
        self.newly_flooded_sqkm = newly_flooded_sqkm
        self.permanent_water_sqkm = permanent_water_sqkm
        self.receded_sqkm = receded_sqkm
        self.expansion_factor = expansion_factor

class TemporalChangeDetector:
    """
    Performs bi-temporal change detection between pre-disaster baseline water
    and post-disaster inundation extents.
    """
    
    @staticmethod
    def detect_change(
        pre_water_mask: np.ndarray,
        post_water_mask: np.ndarray,
        bounds: Tuple[float, float, float, float]
    ) -> ChangeDetectionResult:
        # Categorical codes:
        # 0: Unchanged Land
        # 1: Permanent Water (Pre=1, Post=1)
        # 2: Newly Flooded (Pre=0, Post=1) -> CRITICAL DISASTER ZONE
        # 3: Receded Water (Pre=1, Post=0)
        
        permanent_mask = (pre_water_mask & post_water_mask)
        newly_flooded_mask = ((~pre_water_mask) & post_water_mask)
        receded_mask = (pre_water_mask & (~post_water_mask))
        
        change_mask = np.zeros_like(pre_water_mask, dtype=np.uint8)
        change_mask[permanent_mask] = 1
        change_mask[newly_flooded_mask] = 2
        change_mask[receded_mask] = 3
        
        # Polygonize each category
        perm_features = raster_to_geojson_polygons(permanent_mask, bounds)
        for f in perm_features:
            f["properties"]["change_category"] = ChangeCategory.PERMANENT_WATER.value
            f["properties"]["severity"] = "BASELINE"
            
        new_features = raster_to_geojson_polygons(newly_flooded_mask, bounds)
        for f in new_features:
            f["properties"]["change_category"] = ChangeCategory.NEWLY_FLOODED.value
            f["properties"]["severity"] = "CRISIS"
            
        receded_features = raster_to_geojson_polygons(receded_mask, bounds)
        for f in receded_features:
            f["properties"]["change_category"] = ChangeCategory.RECEDED.value
            f["properties"]["severity"] = "RECOVERY"
            
        all_features = perm_features + new_features + receded_features
        
        perm_sqkm = sum(f["properties"].get("area_sqkm", 0.0) for f in perm_features)
        new_sqkm = sum(f["properties"].get("area_sqkm", 0.0) for f in new_features)
        receded_sqkm = sum(f["properties"].get("area_sqkm", 0.0) for f in receded_features)
        
        expansion_factor = (new_sqkm + perm_sqkm) / max(0.1, perm_sqkm)
        
        return ChangeDetectionResult(
            change_mask=change_mask,
            change_polygons=all_features,
            newly_flooded_sqkm=round(new_sqkm, 2),
            permanent_water_sqkm=round(perm_sqkm, 2),
            receded_sqkm=round(receded_sqkm, 2),
            expansion_factor=round(expansion_factor, 2)
        )
