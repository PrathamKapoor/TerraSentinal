import pytest
import numpy as np
from datetime import datetime, timezone

from backend.app.services.acquisition import SceneBundle
from backend.app.research.adapters.base import BenchmarkSample
from backend.app.research.adapters.synthetic_adapter import SyntheticStressAdapter
from backend.app.research.adapters.real_adapter import Sen1Floods11Adapter
from backend.app.research.benchmark_metrics import (
    validate_benchmark_integrity,
    BenchmarkInvalidityError
)

def test_circular_threshold_ground_truth_fails_validation():
    """
    STEP 9 ASSERTION: Detect if ground truth is mathematically derived
    from the exact threshold being evaluated. Must fail benchmark validation.
    """
    h, w = 100, 100
    # Create synthetic radar data
    sar_vv = np.random.uniform(-30.0, 0.0, (h, w)).astype(np.float32)
    # Intentionally synthesize ground truth directly from evaluated threshold (-16.0 dB)
    circular_gt = (sar_vv < -16.0).astype(np.int16)
    
    bundle = SceneBundle(
        scene_id="CIRCULAR_TEST_SCENE",
        bounds=(0.0, 0.0, 1.0, 1.0),
        pre_sar_vv=sar_vv,
        pre_sar_vh=sar_vv - 6.0,
        post_sar_vv=sar_vv,
        post_sar_vh=sar_vv - 6.0,
        optical_rgb=None,
        optical_mndwi=None,
        dem_elevation=np.zeros((h, w), dtype=np.float32),
        dem_slope=np.zeros((h, w), dtype=np.float32),
        optical_cloud_cover_pct=0.0,
        acquisition_time=datetime.now(timezone.utc),
        is_fixture=False
    )
    
    circular_sample = BenchmarkSample(
        sample_id="SAMPLE_CIRCULAR_FAKE",
        split="TEST",
        event_id="EVT_FAKE",
        event_name="Fake Event",
        country="TestCountry",
        hazard_type="TEST",
        bundle=bundle,
        ground_truth=circular_gt,
        valid_mask=np.ones((h, w), dtype=bool),
        provenance={},
        is_real_data=False,  # Not verified real data
        source_dataset="CircularGenerator"
    )
    
    pred = (sar_vv < -16.0)
    
    # Must raise BenchmarkInvalidityError
    with pytest.raises(BenchmarkInvalidityError, match="FAIL BENCHMARK VALIDATION"):
        validate_benchmark_integrity(circular_sample, pred, evaluated_track="REAL_DATA_VALIDATION")

def test_synthetic_fixture_rejected_from_real_data_track():
    """
    STEP 9 ASSERTION: The benchmark runner must refuse to evaluate synthetic fixtures
    under the REAL_DATA_VALIDATION authority.
    """
    synthetic_adapter = SyntheticStressAdapter()
    synthetic_samples = synthetic_adapter.get_samples()
    sample = synthetic_samples[0]
    pred = (sample.bundle.post_sar_vv < -16.0)
    
    with pytest.raises(BenchmarkInvalidityError, match="FAIL BENCHMARK VALIDATION.*is_real_data=False"):
        validate_benchmark_integrity(sample, pred, evaluated_track="REAL_DATA_VALIDATION")

def test_authentic_real_sample_passes_integrity_validation():
    """
    Verifies that authentic Sen1Floods11 samples with independent human labels pass integrity checks.
    """
    real_adapter = Sen1Floods11Adapter()
    real_samples = real_adapter.get_samples(split="TEST")
    assert len(real_samples) > 0
    sample = real_samples[0]
    
    pred = (sample.bundle.post_sar_vv < -16.0)
    # Should complete without raising BenchmarkInvalidityError
    validate_benchmark_integrity(sample, pred, evaluated_track="REAL_DATA_VALIDATION")
