import numpy as np
import pytest
from backend.app.services.flood_detector import DualPolSARTerrainAdapter, UNetFloodAdapter
from backend.app.services.preprocessing import calculate_dem_slope

def test_dual_pol_sar_detector_inundation_detection():
    adapter = DualPolSARTerrainAdapter()
    
    # Synthetic 20x20 tile
    h, w = 20, 20
    # Center 10x10 is inundated (low backscatter)
    vv = np.full((h, w), -12.0, dtype=np.float32)
    vh = np.full((h, w), -17.0, dtype=np.float32)
    
    vv[5:15, 5:15] = -21.0  # Inundated
    vh[5:15, 5:15] = -26.0  # Inundated
    
    # Flat terrain slope
    slope = np.full((h, w), 1.5, dtype=np.float32)
    bounds = (91.8, 24.8, 92.0, 25.0)
    
    res = adapter.predict(vv, vh, slope, optical_mndwi=None, bounds=bounds)
    
    assert res.total_flooded_sqkm > 0
    assert res.binary_mask[10, 10] == True
    assert res.binary_mask[0, 0] == False
    assert len(res.flood_polygons) > 0

def test_dem_slope_radar_shadow_rejection():
    adapter = DualPolSARTerrainAdapter(max_slope_deg=8.0)
    h, w = 20, 20
    
    # Mountain slope with radar shadow mimicking water
    vv = np.full((h, w), -22.0, dtype=np.float32)  # Low backscatter
    vh = np.full((h, w), -27.0, dtype=np.float32)
    
    # Steep slope 15 degrees
    slope = np.full((h, w), 15.0, dtype=np.float32)
    bounds = (91.8, 24.8, 92.0, 25.0)
    
    res = adapter.predict(vv, vh, slope, optical_mndwi=None, bounds=bounds)
    
    # Must be rejected because slope > 8.0 deg!
    assert np.all(res.binary_mask == False)
    assert res.total_flooded_sqkm == 0.0

def test_unet_flood_adapter_inference():
    adapter = UNetFloodAdapter()
    h, w = 32, 32
    vv = np.random.normal(-15.0, 3.0, (h, w)).astype(np.float32)
    vh = np.random.normal(-22.0, 3.0, (h, w)).astype(np.float32)
    slope = np.random.uniform(0.5, 5.0, (h, w)).astype(np.float32)
    mndwi = np.random.uniform(-0.5, 0.5, (h, w)).astype(np.float32)
    bounds = (91.8, 24.8, 92.0, 25.0)
    
    res = adapter.predict(vv, vh, slope, mndwi, bounds)
    assert res.probability_map.shape == (h, w)
    assert 0.0 <= res.mean_confidence <= 1.0
