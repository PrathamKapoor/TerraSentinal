import numpy as np
import pytest
from backend.app.services.evidence_fusion import EvidenceFusionEngine
from backend.app.models.schemas import ConflictState

def test_evidence_fusion_agreement():
    h, w = 30, 30
    # Both SAR and Optical observe flood
    sar_vv = np.full((h, w), -21.0, dtype=np.float32)
    sar_vh = np.full((h, w), -27.0, dtype=np.float32)
    dem_slope = np.full((h, w), 2.0, dtype=np.float32)
    optical_mndwi = np.full((h, w), 0.45, dtype=np.float32)
    
    res = EvidenceFusionEngine.fuse_observations(
        sar_vv=sar_vv,
        sar_vh=sar_vh,
        dem_slope=dem_slope,
        optical_mndwi=optical_mndwi,
        optical_cloud_pct=10.0
    )
    
    assert res.fused_probability.mean() > 0.70
    assert res.fused_confidence.mean() > 0.85
    assert not res.conflict_detected
    assert res.conflict_count == 0

def test_evidence_fusion_conflict_detection():
    h, w = 30, 30
    # SAR indicates deep flood, but unclouded optical indicates clear dry ground
    sar_vv = np.full((h, w), -22.0, dtype=np.float32) # Strong flood backscatter
    sar_vh = np.full((h, w), -28.0, dtype=np.float32)
    dem_slope = np.full((h, w), 1.5, dtype=np.float32)
    optical_mndwi = np.full((h, w), -0.35, dtype=np.float32) # Clear dry land
    
    res = EvidenceFusionEngine.fuse_observations(
        sar_vv=sar_vv,
        sar_vh=sar_vh,
        dem_slope=dem_slope,
        optical_mndwi=optical_mndwi,
        optical_cloud_pct=0.0 # Clear sky
    )
    
    # Must trigger conflict flag
    assert res.conflict_detected
    assert res.conflict_count > 15
    # In conflict zone, confidence must drop
    assert res.fused_confidence.mean() < 0.60
