from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
from backend.app.config import settings
from backend.app.services.preprocessing import (
    lee_speckle_filter, raster_to_geojson_polygons
)

class FloodDetectionResult:
    def __init__(
        self,
        binary_mask: np.ndarray,
        probability_map: np.ndarray,
        confidence_map: np.ndarray,
        flood_polygons: List[Dict[str, Any]],
        total_flooded_sqkm: float,
        mean_confidence: float,
        model_name: str,
        model_version: str
    ):
        self.binary_mask = binary_mask
        self.probability_map = probability_map
        self.confidence_map = confidence_map
        self.flood_polygons = flood_polygons
        self.total_flooded_sqkm = total_flooded_sqkm
        self.mean_confidence = mean_confidence
        self.model_name = model_name
        self.model_version = model_version

class BaseModelAdapter(ABC):
    @abstractmethod
    def predict(
        self,
        sar_vv: np.ndarray,
        sar_vh: np.ndarray,
        dem_slope: np.ndarray,
        optical_mndwi: Optional[np.ndarray],
        bounds: Tuple[float, float, float, float]
    ) -> FloodDetectionResult:
        pass

class DualPolSARTerrainAdapter(BaseModelAdapter):
    """
    Calibrated physical-statistical flood detector combining C-band SAR
    dual-polarization backscatter physics with DEM topographic slope constraints
    and optical spectral cross-verification.
    """
    
    def __init__(
        self,
        vv_threshold_db: float = settings.SAR_VV_WATER_THRESHOLD_DB,
        vh_threshold_db: float = settings.SAR_VH_WATER_THRESHOLD_DB,
        max_slope_deg: float = settings.DEM_MAX_WATER_SLOPE_DEG
    ):
        self.vv_threshold = vv_threshold_db
        self.vh_threshold = vh_threshold_db
        self.max_slope = max_slope_deg
        self.model_name = "Calibrated-DualPol-SAR+DEM"
        self.model_version = "1.2.0"

    def predict(
        self,
        sar_vv: np.ndarray,
        sar_vh: np.ndarray,
        dem_slope: Optional[np.ndarray],
        optical_mndwi: Optional[np.ndarray],
        bounds: Tuple[float, float, float, float]
    ) -> FloodDetectionResult:
        # 1. Apply speckle filtering
        vv_clean = lee_speckle_filter(sar_vv, window_size=5)
        vh_clean = lee_speckle_filter(sar_vh, window_size=5)
        
        # 2. SAR backscatter criterion for specular water reflection
        sar_water = (vv_clean < self.vv_threshold) & (vh_clean < self.vh_threshold)
        
        # 3. Topographic constraint: standing floodwaters cannot remain on steep slopes
        if dem_slope is not None:
            terrain_valid = (dem_slope <= self.max_slope)
            slope_penalty = np.clip((dem_slope - self.max_slope) / 4.0, 0.0, 1.0)
        else:
            terrain_valid = np.ones_like(sar_water, dtype=bool)
            slope_penalty = np.zeros_like(sar_vv, dtype=np.float32)
        
        # Reject radar shadows on mountain ridges
        filtered_water = sar_water & terrain_valid
        
        # 4. Compute continuous probability map
        # Distance from threshold: normalized sigmoid
        vv_dist = (self.vv_threshold - vv_clean) / 4.0
        vh_dist = (self.vh_threshold - vh_clean) / 4.0
        sar_prob = 1.0 / (1.0 + np.exp(-(vv_dist + vh_dist)))
        
        probability_map = sar_prob * (1.0 - slope_penalty)
        
        # 5. Multimodal confidence calculation
        # Baseline confidence from distance to threshold
        base_confidence = np.clip(np.abs(vv_clean - self.vv_threshold) / 8.0, 0.45, 0.95)
        if dem_slope is None:
            base_confidence -= 0.15  # Penalty for unconstrained terrain
        
        # If optical is available and unclouded, modulate confidence
        if optical_mndwi is not None:
            valid_opt = ~np.isnan(optical_mndwi)
            opt_agrees_water = (optical_mndwi > 0.0) & filtered_water
            opt_agrees_land = (optical_mndwi <= 0.0) & (~filtered_water)
            
            # Boost confidence where SAR and optical agree
            base_confidence[valid_opt & (opt_agrees_water | opt_agrees_land)] = np.minimum(
                base_confidence[valid_opt & (opt_agrees_water | opt_agrees_land)] + 0.12, 0.98
            )
            
            # Reduce confidence where unclouded optical strongly disagrees with SAR
            disagreement = valid_opt & (optical_mndwi < -0.15) & filtered_water
            base_confidence[disagreement] = np.maximum(
                base_confidence[disagreement] - 0.25, 0.35
            )
            
        confidence_map = np.clip(base_confidence, 0.1, 1.0).astype(np.float32)
        binary_mask = (probability_map >= 0.50) & terrain_valid
        
        # 6. Extract clean GeoJSON polygons
        features = raster_to_geojson_polygons(binary_mask, bounds)
        total_sqkm = sum(f["properties"].get("area_sqkm", 0.0) for f in features)
        
        mean_conf = float(np.mean(confidence_map[binary_mask])) if np.any(binary_mask) else 0.85
        
        # Inject confidence property into polygons
        for f in features:
            f["properties"]["confidence"] = round(mean_conf, 2)
            f["properties"]["detection_method"] = self.model_name
            f["properties"]["hazard_type"] = "INUNDATION"
            
        return FloodDetectionResult(
            binary_mask=binary_mask,
            probability_map=probability_map.astype(np.float32),
            confidence_map=confidence_map,
            flood_polygons=features,
            total_flooded_sqkm=round(total_sqkm, 2),
            mean_confidence=round(mean_conf, 3),
            model_name=self.model_name,
            model_version=self.model_version
        )

class SimpleUNet(nn.Module):
    """
    Lightweight 4-channel U-Net segmentation network for flood chip inference.
    Channels: [SAR_VV, SAR_VH, Optical_MNDWI, DEM_Slope]
    """
    def __init__(self, in_channels: int = 4, out_channels: int = 1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, out_channels, kernel_size=1)
        self.sigmoid = nn.Sigmoid()
        self._init_weights()
        
    def _init_weights(self):
        # Heuristic parameter initialization reflecting physical water backscatter priors.
        # CLASSIFICATION: UNTRAINED / ADAPTER (Manual spatial kernel initialization, NOT trained/pretrained weights).
        with torch.no_grad():
            nn.init.zeros_(self.conv1.weight)
            nn.init.zeros_(self.conv1.bias)
            # Channel 0: SAR VV (specular reflection below -16 dB is water -> negative weight)
            self.conv1.weight[0, 0, 1, 1] = -5.0
            self.conv1.bias[0] = 2.25
            # Channel 1: SAR VH (specular reflection below -23 dB -> negative weight)
            self.conv1.weight[1, 1, 1, 1] = -4.0
            self.conv1.bias[1] = 1.8
            # Channel 2: Optical MNDWI (normalized > 0.5 is water -> positive weight)
            self.conv1.weight[2, 2, 1, 1] = 4.0
            self.conv1.bias[2] = -2.0
            # Channel 3: DEM Slope (slope > 6 deg cannot hold floodwater -> negative penalty)
            self.conv1.weight[3, 3, 1, 1] = -6.0
            self.conv1.bias[3] = 1.2
            # Spatial context filters: 3x3 local neighborhood smoothing
            self.conv1.weight[4, 0, :, :] = -0.5
            self.conv1.bias[4] = 2.0
            self.conv1.weight[5, 1, :, :] = -0.4
            self.conv1.bias[5] = 1.6
            
            nn.init.zeros_(self.conv2.weight)
            nn.init.zeros_(self.conv2.bias)
            self.conv2.weight[0, 0, 0, 0] = 1.0
            self.conv2.weight[0, 1, 0, 0] = 0.8
            self.conv2.weight[0, 2, 0, 0] = 0.5
            self.conv2.weight[0, 3, 0, 0] = 1.2
            self.conv2.weight[0, 4, 0, 0] = 0.5
            self.conv2.weight[0, 5, 0, 0] = 0.4
            self.conv2.bias[0] = -1.5
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = torch.relu(self.conv1(x))
        return self.sigmoid(self.conv2(h))

class UNetFloodAdapter(BaseModelAdapter):
    """
    PyTorch convolutional adapter with heuristic spatial kernel initialization.
    Classification: UNTRAINED / ADAPTER (Heuristically initialized; not trained/pretrained weights).
    """
    def __init__(self):
        self.model_name = "UNet-Heuristic-Adapter"
        self.model_version = "2.1.0-untrained"
        self.model_classification = "UNTRAINED / ADAPTER"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.network = SimpleUNet(in_channels=4, out_channels=1).to(self.device)
        self.network.eval()
        
    def predict(
        self,
        sar_vv: np.ndarray,
        sar_vh: np.ndarray,
        dem_slope: np.ndarray,
        optical_mndwi: Optional[np.ndarray],
        bounds: Tuple[float, float, float, float]
    ) -> FloodDetectionResult:
        h, w = sar_vv.shape
        # Normalize inputs for CNN
        vv_norm = np.clip((sar_vv + 25.0) / 20.0, 0.0, 1.0)
        vh_norm = np.clip((sar_vh + 32.0) / 20.0, 0.0, 1.0)
        slope_norm = np.clip(dem_slope / 30.0, 0.0, 1.0)
        opt_norm = np.nan_to_num(optical_mndwi, nan=0.0) if optical_mndwi is not None else np.zeros_like(sar_vv)
        opt_norm = np.clip((opt_norm + 1.0) / 2.0, 0.0, 1.0)
        
        inp = np.stack([vv_norm, vh_norm, opt_norm, slope_norm], axis=0)[np.newaxis, ...]
        t_inp = torch.from_numpy(inp).float().to(self.device)
        
        with torch.no_grad():
            out = self.network(t_inp)
            prob = out.squeeze().cpu().numpy()
            
        mask = (prob > 0.50) & (dem_slope <= settings.DEM_MAX_WATER_SLOPE_DEG)
        confidence = np.clip(0.60 + 0.35 * np.abs(prob - 0.5) * 2.0, 0.5, 0.95)
        
        features = raster_to_geojson_polygons(mask, bounds)
        total_sqkm = sum(f["properties"].get("area_sqkm", 0.0) for f in features)
        mean_conf = float(np.mean(confidence[mask])) if np.any(mask) else 0.88
        
        for f in features:
            f["properties"]["confidence"] = round(mean_conf, 2)
            f["properties"]["detection_method"] = self.model_name
            f["properties"]["hazard_type"] = "INUNDATION"
            
        return FloodDetectionResult(
            binary_mask=mask,
            probability_map=prob.astype(np.float32),
            confidence_map=confidence.astype(np.float32),
            flood_polygons=features,
            total_flooded_sqkm=round(total_sqkm, 2),
            mean_confidence=round(mean_conf, 3),
            model_name=self.model_name,
            model_version=self.model_version
        )
