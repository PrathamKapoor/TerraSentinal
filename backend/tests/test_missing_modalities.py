import pytest
import numpy as np
from backend.app.services.evidence_fusion import EvidenceFusionEngine
from backend.app.services.flood_detector import DualPolSARTerrainAdapter

def test_missing_optical_modality_graceful_degradation():
    """
    When optical imagery is unavailable (100% cloud cover or night),
    the system must degrade gracefully to SAR-only mode with an uncertainty penalty.
    """
    h, w = 50, 50
    sar_vv = np.full((h, w), -20.0, dtype=np.float32)  # Flooded
    sar_vh = np.full((h, w), -26.0, dtype=np.float32)
    dem_slope = np.full((h, w), 2.0, dtype=np.float32)  # Flat
    
    # Optical is completely missing (None)
    fusion_res = EvidenceFusionEngine.fuse_observations(
        sar_vv=sar_vv,
        sar_vh=sar_vh,
        dem_slope=dem_slope,
        optical_mndwi=None,
        optical_cloud_pct=100.0
    )
    
    assert fusion_res.optical_weight == 0.0
    assert fusion_res.sar_weight > 0.0
    assert fusion_res.quality_status == "DEGRADED_SAR_ONLY"
    assert not fusion_res.conflict_detected
    # Confidence is penalized for missing multimodal confirmation
    assert float(np.mean(fusion_res.fused_confidence)) < 0.90
    assert np.all(fusion_res.fused_probability > 0.50)

def test_missing_sar_modality_optical_fallback():
    """
    When SAR is unavailable (orbital gap / sensor anomaly),
    the system falls back to optical-only mode if unclouded, with explicit status.
    """
    h, w = 50, 50
    mndwi = np.full((h, w), 0.45, dtype=np.float32)  # Flooded
    dem_slope = np.full((h, w), 1.5, dtype=np.float32)
    
    fusion_res = EvidenceFusionEngine.fuse_observations(
        sar_vv=None,
        sar_vh=None,
        dem_slope=dem_slope,
        optical_mndwi=mndwi,
        optical_cloud_pct=5.0
    )
    
    assert fusion_res.sar_weight == 0.0
    assert fusion_res.optical_weight > 0.0
    assert fusion_res.quality_status == "DEGRADED_OPTICAL_ONLY"
    assert not fusion_res.conflict_detected
    # Confidence is penalized by 0.18 for lacking SAR all-weather verification
    assert float(np.mean(fusion_res.fused_confidence)) < 0.85

def test_missing_dem_topographic_prior():
    """
    When DEM elevation/slope is unavailable, system marks terrain as unconstrained,
    suppressing topographic filtering and lowering confidence.
    """
    h, w = 50, 50
    sar_vv = np.full((h, w), -19.5, dtype=np.float32)
    sar_vh = np.full((h, w), -25.0, dtype=np.float32)
    
    adapter = DualPolSARTerrainAdapter()
    bounds = (91.8, 24.8, 92.2, 25.1)
    
    res = adapter.predict(
        sar_vv=sar_vv,
        sar_vh=sar_vh,
        dem_slope=None,
        optical_mndwi=None,
        bounds=bounds
    )
    
    # Should detect floodwater without error
    assert res.total_flooded_sqkm > 0
    # Mean confidence penalized due to lack of terrain validation
    assert res.mean_confidence < 0.88

def test_both_primary_modalities_missing_raises_error():
    """
    If neither SAR nor Optical data is available, system must fail explicitly,
    never fabricating synthetic observations without consent.
    """
    with pytest.raises(ValueError, match="At least one Earth observation modality"):
        EvidenceFusionEngine.fuse_observations(
            sar_vv=None,
            sar_vh=None,
            dem_slope=np.zeros((10, 10), dtype=np.float32),
            optical_mndwi=None
        )
