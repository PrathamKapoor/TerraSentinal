import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

from backend.app.services.flood_detector import FloodDetectionResult

logger = logging.getLogger(__name__)

class FoundationModelBlockedError(RuntimeError):
    """Raised when an attempt is made to execute an unavailable foundation model."""
    pass

class BaseFoundationModelAdapter(ABC):
    """
    Standard interface for remote sensing foundation models and advanced neural architectures.
    Enforces strict integrity: never fakes or mocks outputs when weights or dependencies are absent.
    """
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        pass

    @abstractmethod
    def check_availability(self) -> Tuple[bool, str]:
        """
        Verifies whether required Python dependencies, hardware drivers, and model weights
        are present in the local environment.
        Returns (is_available, status_detail).
        """
        pass

    @abstractmethod
    def predict(
        self,
        sar_vv: np.ndarray,
        sar_vh: np.ndarray,
        dem_slope: np.ndarray,
        optical_mndwi: Optional[np.ndarray],
        bounds: Tuple[float, float, float, float]
    ) -> FloodDetectionResult:
        """
        Runs neural inference. Must raise FoundationModelBlockedError if check_availability() is False.
        """
        pass

class PrithviEOAdapter(BaseFoundationModelAdapter):
    """
    NASA-IMPACT & IBM Prithvi-EO-2.0 Foundation Model Adapter.
    Requires: PyTorch, Hugging Face transformers/timm, and pretrained Prithvi ViT checkpoint.
    """
    
    def __init__(self, weights_path: Optional[str] = None):
        self._weights_path = weights_path or os.environ.get("PRITHVI_WEIGHTS_PATH")
        
    @property
    def model_name(self) -> str:
        return "NASA-IBM-Prithvi-EO-2.0"

    @property
    def model_version(self) -> str:
        return "2.0-300M"

    def check_availability(self) -> Tuple[bool, str]:
        try:
            import torch
        except ImportError:
            return False, "BLOCKED: PyTorch is not installed in the environment."
            
        if not self._weights_path or not os.path.exists(self._weights_path):
            return False, (
                "BLOCKED: Pretrained Prithvi-EO-2.0 checkpoint weights not found. "
                "Specify valid local path via PRITHVI_WEIGHTS_PATH environment variable."
            )
            
        return True, "AVAILABLE: Prithvi-EO-2.0 weights verified."

    def predict(
        self,
        sar_vv: np.ndarray,
        sar_vh: np.ndarray,
        dem_slope: np.ndarray,
        optical_mndwi: Optional[np.ndarray],
        bounds: Tuple[float, float, float, float]
    ) -> FloodDetectionResult:
        avail, reason = self.check_availability()
        if not avail:
            raise FoundationModelBlockedError(
                f"Cannot execute {self.model_name}: {reason} "
                f"TerraSentinel refuses to generate fake foundation-model inferences."
            )
        # Real inference execution would occur here when real weights are provided
        raise NotImplementedError("Real weights loading pipeline execution.")

class ChangeMambaAdapter(BaseFoundationModelAdapter):
    """
    ChangeMamba State-Space Model Adapter for Bi-temporal Disaster Change Detection.
    Requires: CUDA GPU, mamba_ssm, causal_conv1d, and pretrained change detection weights.
    """
    
    def __init__(self, weights_path: Optional[str] = None):
        self._weights_path = weights_path or os.environ.get("CHANGEMAMBA_WEIGHTS_PATH")
        
    @property
    def model_name(self) -> str:
        return "ChangeMamba-SSM"

    @property
    def model_version(self) -> str:
        return "1.0.0"

    def check_availability(self) -> Tuple[bool, str]:
        try:
            import mamba_ssm
        except ImportError:
            return False, (
                "BLOCKED: mamba_ssm CUDA C++ extension is not installed. "
                "ChangeMamba requires Linux/CUDA environment with hardware-accelerated selective scan."
            )
            
        if not self._weights_path or not os.path.exists(self._weights_path):
            return False, (
                "BLOCKED: ChangeMamba weights not found. "
                "Specify CHANGEMAMBA_WEIGHTS_PATH."
            )
            
        return True, "AVAILABLE: ChangeMamba SSM verified."

    def predict(
        self,
        sar_vv: np.ndarray,
        sar_vh: np.ndarray,
        dem_slope: np.ndarray,
        optical_mndwi: Optional[np.ndarray],
        bounds: Tuple[float, float, float, float]
    ) -> FloodDetectionResult:
        avail, reason = self.check_availability()
        if not avail:
            raise FoundationModelBlockedError(
                f"Cannot execute {self.model_name}: {reason} "
                f"TerraSentinel refuses to generate fake foundation-model inferences."
            )
        raise NotImplementedError("Real weights loading pipeline execution.")

class TerraMindAdapter(BaseFoundationModelAdapter):
    """
    TerraMind Multimodal Earth-Observation Foundation Model Adapter.
    Requires: Multimodal pretraining weights and specialized tokenizers.
    """
    
    def __init__(self, weights_path: Optional[str] = None):
        self._weights_path = weights_path or os.environ.get("TERRAMIND_WEIGHTS_PATH")
        
    @property
    def model_name(self) -> str:
        return "TerraMind-Multimodal"

    @property
    def model_version(self) -> str:
        return "1.0.0"

    def check_availability(self) -> Tuple[bool, str]:
        if not self._weights_path or not os.path.exists(self._weights_path):
            return False, (
                "BLOCKED: TerraMind foundation model weights not found in local environment. "
                "Set TERRAMIND_WEIGHTS_PATH to genuine checkpoint."
            )
        return True, "AVAILABLE: TerraMind weights verified."

    def predict(
        self,
        sar_vv: np.ndarray,
        sar_vh: np.ndarray,
        dem_slope: np.ndarray,
        optical_mndwi: Optional[np.ndarray],
        bounds: Tuple[float, float, float, float]
    ) -> FloodDetectionResult:
        avail, reason = self.check_availability()
        if not avail:
            raise FoundationModelBlockedError(
                f"Cannot execute {self.model_name}: {reason} "
                f"TerraSentinel refuses to generate fake foundation-model inferences."
            )
        raise NotImplementedError("Real weights loading pipeline execution.")
