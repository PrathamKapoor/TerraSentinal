import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from backend.app.config import settings
from backend.app.models.schemas import ConflictState

class FusionResult:
    def __init__(
        self,
        fused_probability: np.ndarray,
        fused_confidence: np.ndarray,
        conflict_mask: np.ndarray,
        conflict_detected: bool,
        conflict_count: int,
        sar_weight: float,
        optical_weight: float,
        dem_weight: float
    ):
        self.fused_probability = fused_probability
        self.fused_confidence = fused_confidence
        self.conflict_mask = conflict_mask
        self.conflict_detected = conflict_detected
        self.conflict_count = conflict_count
        self.sar_weight = sar_weight
        self.optical_weight = optical_weight
        self.dem_weight = dem_weight

class EvidenceFusionEngine:
    """
    Multimodal evidential reasoning engine fusing Synthetic Aperture Radar,
    multispectral optical water indices, and digital elevation constraints.
    Explicitly surfaces sensor conflict without collapsing discordant evidence into a false mean.
    """
    
    @staticmethod
    def fuse_observations(
        sar_vv: np.ndarray,
        sar_vh: np.ndarray,
        dem_slope: np.ndarray,
        optical_mndwi: Optional[np.ndarray],
        optical_cloud_pct: float = 0.0
    ) -> FusionResult:
        h, w = sar_vv.shape
        
        # 1. Base SAR Evidence Mass:
        # C-band SAR is all-weather, unaffected by clouds
        sar_flood_evidence = np.clip((-16.0 - sar_vv) / 6.0, 0.0, 1.0)
        sar_weight = 0.70
        
        # 2. DEM Topographic Prior:
        # High slopes strongly penalize standing floodwater
        slope_penalty = np.clip((dem_slope - settings.DEM_MAX_WATER_SLOPE_DEG) / 4.0, 0.0, 1.0)
        dem_support = 1.0 - slope_penalty
        dem_weight = 0.85
        
        # 3. Optical Evidence Mass:
        # Quality depends heavily on cloud cover
        optical_weight = 0.0
        optical_flood_evidence = np.zeros_like(sar_vv)
        conflict_mask = np.zeros((h, w), dtype=bool)
        
        if optical_mndwi is not None and optical_cloud_pct < 85.0:
            valid_opt = ~np.isnan(optical_mndwi)
            # MNDWI mapped from [-0.5, 0.5] to [0.0, 1.0]
            optical_flood_evidence = np.clip((optical_mndwi + 0.2) / 0.6, 0.0, 1.0)
            optical_weight = 0.60 * (1.0 - (optical_cloud_pct / 100.0))
            
            # Detect Conflict:
            # SAR indicates strong flood (evidence > 0.75), but Optical indicates clear dry ground (evidence < 0.25)
            # or vice-versa, on valid unclouded pixels
            sar_flooded = (sar_flood_evidence > 0.70)
            opt_dry = (optical_flood_evidence < 0.25) & valid_opt
            
            sar_dry = (sar_flood_evidence < 0.25)
            opt_flooded = (optical_flood_evidence > 0.75) & valid_opt
            
            conflict_mask = (sar_flooded & opt_dry) | (sar_dry & opt_flooded)
            
        # 4. Evidential Combination:
        # Modulated probability incorporates both SAR and Optical, constrained by DEM slope
        total_weight = sar_weight + optical_weight
        if total_weight > 0:
            raw_prob = (sar_flood_evidence * sar_weight + optical_flood_evidence * optical_weight) / total_weight
        else:
            raw_prob = sar_flood_evidence
            
        fused_prob = raw_prob * dem_support
        
        # 5. Confidence Calculation:
        # High where modalities agree; degraded in conflict zones or single-modality cloudy zones
        base_conf = 0.75 + 0.20 * np.abs(fused_prob - 0.5) * 2.0
        if optical_weight > 0.3:
            base_conf += 0.05  # Bonus for multimodal confirmation
        else:
            base_conf -= 0.08  # Penalty for missing optical verification
            
        # Heavy confidence drop in conflict zones
        base_conf[conflict_mask] = np.maximum(base_conf[conflict_mask] - 0.40, 0.35)
        fused_conf = np.clip(base_conf, 0.1, 0.98).astype(np.float32)
        
        conflict_count = int(np.sum(conflict_mask))
        conflict_detected = (conflict_count > 15)  # Meaningful cluster of conflicting pixels
        
        return FusionResult(
            fused_probability=fused_prob.astype(np.float32),
            fused_confidence=fused_conf,
            conflict_mask=conflict_mask,
            conflict_detected=conflict_detected,
            conflict_count=conflict_count,
            sar_weight=sar_weight,
            optical_weight=optical_weight,
            dem_weight=dem_weight
        )
