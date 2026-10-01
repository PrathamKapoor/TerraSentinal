from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from backend.app.services.acquisition import SceneBundle

@dataclass
class BenchmarkSample:
    """
    Standardized, normalized representation of a benchmark evaluation unit (chip or scene).
    Decoupled from specific dataset file formats.
    """
    sample_id: str
    split: str  # 'TRAIN', 'VAL', 'TEST'
    event_id: str
    event_name: str
    country: str
    hazard_type: str
    bundle: SceneBundle
    ground_truth: np.ndarray  # (H, W) binary {0, 1}
    valid_mask: np.ndarray    # (H, W) boolean mask of valid pixels (True = valid, False = cloud/nodata)
    provenance: Dict[str, Any]
    is_real_data: bool
    source_dataset: str

class BenchmarkSource(ABC):
    """
    Abstract base source for benchmarking tracks.
    Enforces clean separation between synthetic stress testing and real Earth-observation validation.
    """
    @abstractmethod
    def get_track_name(self) -> str:
        """Returns the formal track name, e.g. 'CONTROLLED_SYNTHETIC_SENSOR_STRESS' or 'REAL_DATA_VALIDATION'."""
        pass

    @abstractmethod
    def is_real_data(self) -> bool:
        """True if the data source contains authentic satellite imagery and independent labels."""
        pass

    @abstractmethod
    def get_samples(self, split: Optional[str] = None) -> List[BenchmarkSample]:
        """Returns benchmark samples, optionally filtered by split ('TRAIN', 'VAL', 'TEST')."""
        pass
