import numpy as np
from typing import Dict, Any, Callable, Tuple, Optional

from backend.app.services.acquisition import SceneBundle
from backend.app.services.evidence_fusion import EvidenceFusionEngine
from backend.app.services.flood_detector import DualPolSARTerrainAdapter, UNetFloodAdapter

BASELINE_SPECS = [
    {
        "baseline_id": "BASE-A",
        "name": "SAR-Only Dual-Pol Thresholding",
        "classification": "HEURISTIC",
        "modalities": ["Sentinel-1 SAR VV", "Sentinel-1 SAR VH"],
        "description": "Standard radar backscatter thresholding (VV < -16.0 dB and VH < -23.0 dB)."
    },
    {
        "baseline_id": "BASE-B",
        "name": "Optical-Only MNDWI Thresholding",
        "classification": "HEURISTIC",
        "modalities": ["Sentinel-2 MSI MNDWI"],
        "description": "Green/SWIR spectral water index thresholding (MNDWI > 0.0) on valid pixels."
    },
    {
        "baseline_id": "BASE-C",
        "name": "Multimodal SAR + Optical Consensus",
        "classification": "HEURISTIC",
        "modalities": ["Sentinel-1 SAR", "Sentinel-2 MNDWI"],
        "description": "Union consensus combining SAR water detection with optical water detection."
    },
    {
        "baseline_id": "BASE-D",
        "name": "TerraSentinel Evidence-Fusion Engine",
        "classification": "HEURISTIC",
        "modalities": ["Sentinel-1 SAR", "Sentinel-2 MSI", "DEM Slope Prior"],
        "description": "Dempster-Shafer evidential belief combination with discordance conflict tracking."
    },
    {
        "baseline_id": "BASE-E",
        "name": "Convolutional U-Net Spatial Adapter",
        "classification": "UNTRAINED / ADAPTER",
        "modalities": ["4-Channel Tensor (SAR VV/VH, Optical, DEM)"],
        "description": "PyTorch convolutional encoder-decoder with heuristic spatial kernel initialization (untrained weights)."
    }
]

class RealBenchmarkBaselines:
    """
    Standardized baseline predictors for Real Earth Observation evaluation.
    Every baseline is explicitly bound to its algorithmic classification.
    """
    
    def __init__(self):
        self.fusion_engine = EvidenceFusionEngine()
        self.unet_adapter = UNetFloodAdapter()

    def predict_baseline_a_sar_only(self, bundle: SceneBundle) -> np.ndarray:
        """Baseline A: SAR Dual-Pol Thresholding (HEURISTIC)"""
        return (bundle.post_sar_vv < -16.0) & (bundle.post_sar_vh < -23.0)

    def predict_baseline_b_optical_only(self, bundle: SceneBundle) -> np.ndarray:
        """Baseline B: Optical MNDWI Thresholding (HEURISTIC)"""
        if bundle.optical_mndwi is None:
            return np.zeros_like(bundle.post_sar_vv, dtype=bool)
        valid = ~np.isnan(bundle.optical_mndwi)
        pred = np.zeros_like(bundle.post_sar_vv, dtype=bool)
        pred[valid] = (bundle.optical_mndwi[valid] > 0.0)
        return pred

    def predict_baseline_c_multimodal_consensus(self, bundle: SceneBundle) -> np.ndarray:
        """Baseline C: Multimodal Consensus (HEURISTIC)"""
        sar_pred = (bundle.post_sar_vv < -16.0)
        opt_pred = self.predict_baseline_b_optical_only(bundle)
        return sar_pred | opt_pred

    def predict_baseline_d_evidence_fusion(self, bundle: SceneBundle) -> np.ndarray:
        """Baseline D: TerraSentinel Evidence-Fusion Engine (HEURISTIC)"""
        res = self.fusion_engine.fuse_observations(
            sar_vv=bundle.post_sar_vv,
            sar_vh=bundle.post_sar_vh,
            dem_slope=bundle.dem_slope,
            optical_mndwi=bundle.optical_mndwi,
            optical_cloud_pct=bundle.optical_cloud_cover_pct
        )
        return (res.fused_probability > 0.45)

    def predict_baseline_e_unet_adapter(self, bundle: SceneBundle) -> np.ndarray:
        """Baseline E: Convolutional U-Net Adapter (UNTRAINED / ADAPTER)"""
        res = self.unet_adapter.predict(
            sar_vv=bundle.post_sar_vv,
            sar_vh=bundle.post_sar_vh,
            dem_slope=bundle.dem_slope,
            optical_mndwi=bundle.optical_mndwi,
            bounds=bundle.bounds
        )
        return res.binary_mask

    def run_all_baselines_on_bundle(
        self,
        bundle: SceneBundle
    ) -> Dict[str, np.ndarray]:
        """Runs all 5 baselines on a SceneBundle."""
        return {
            "BASE-A": self.predict_baseline_a_sar_only(bundle),
            "BASE-B": self.predict_baseline_b_optical_only(bundle),
            "BASE-C": self.predict_baseline_c_multimodal_consensus(bundle),
            "BASE-D": self.predict_baseline_d_evidence_fusion(bundle),
            "BASE-E": self.predict_baseline_e_unet_adapter(bundle)
        }
