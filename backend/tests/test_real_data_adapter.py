import os
import json
import pytest
import numpy as np

from backend.app.research.adapters.real_adapter import (
    Sen1Floods11Adapter,
    BRIGHTAdapter,
    RealFloodDatasetAdapter,
    RealDatasetNotPresentError
)
from backend.app.research.adapters.synthetic_adapter import SyntheticStressAdapter
from backend.app.services.foundation_models import (
    PrithviEOAdapter,
    ChangeMambaAdapter,
    TerraMindAdapter,
    FoundationModelBlockedError
)

def test_sen1floods11_adapter_loads_samples_and_splits():
    """
    Verifies that Sen1Floods11Adapter loads valid real satellite rasters
    with normalized SceneBundle structures and split integrity.
    """
    adapter = Sen1Floods11Adapter()
    samples = adapter.get_samples()
    
    assert len(samples) == 11
    
    test_samples = [s for s in samples if s.split == "TEST"]
    val_samples = [s for s in samples if s.split == "VAL"]
    train_samples = [s for s in samples if s.split == "TRAIN"]
    
    assert len(test_samples) == 3   # Bolivia Mamoré
    assert len(val_samples) == 2    # Mekong Cambodia
    assert len(train_samples) == 6  # USA, Spain, India
    
    for s in samples:
        assert s.is_real_data is True
        assert s.bundle.is_fixture is False
        assert s.bundle.post_sar_vv.shape == (512, 512)
        assert s.bundle.post_sar_vh.shape == (512, 512)
        assert s.bundle.optical_mndwi.shape == (512, 512)
        assert s.ground_truth.shape == (512, 512)
        assert s.valid_mask.shape == (512, 512)
        assert np.any(s.valid_mask)
        # Ensure label semantics: ground truth contains only 0 and 1
        unique_gt = set(np.unique(s.ground_truth[s.valid_mask]))
        assert unique_gt.issubset({0, 1})

def test_bright_adapter_blocked_when_archive_missing():
    """
    STEP 6 & STEP 11: Real adapter for BRIGHT must explicitly report BLOCKED / NOT PRESENT
    rather than faking data when files are missing.
    """
    bright = BRIGHTAdapter(local_dir="non_existent_bright_dir")
    avail, reason = bright.is_available()
    assert avail is False
    assert "REAL DATASET NOT PRESENT" in reason
    
    with pytest.raises(RealDatasetNotPresentError, match="REAL DATASET NOT PRESENT"):
        bright.get_samples()

def test_foundation_models_blocked_without_faking():
    """
    STEP 6: Foundation models (Prithvi, ChangeMamba, TerraMind) must refuse to run
    and classify as BLOCKED when real weights are not present.
    """
    prithvi = PrithviEOAdapter(weights_path="non_existent_prithvi.pt")
    avail, reason = prithvi.check_availability()
    assert avail is False
    assert "BLOCKED" in reason
    
    with pytest.raises(FoundationModelBlockedError, match="BLOCKED"):
        prithvi.predict(
            sar_vv=np.zeros((10, 10)),
            sar_vh=np.zeros((10, 10)),
            dem_slope=np.zeros((10, 10)),
            optical_mndwi=None,
            bounds=(0, 0, 1, 1)
        )
        
    mamba = ChangeMambaAdapter(weights_path="non_existent_mamba.pt")
    m_avail, m_reason = mamba.check_availability()
    assert m_avail is False
    assert "BLOCKED" in m_reason
    
    terra = TerraMindAdapter(weights_path="non_existent_terramind.pt")
    t_avail, t_reason = terra.check_availability()
    assert t_avail is False
    assert "BLOCKED" in t_reason

def test_manifest_provenance_integrity():
    """
    STEP 2: Verifies that real benchmark manifest contains required provenance fields
    including source URL, license, and SHA-256 checksums.
    """
    manifest_path = "backend/app/data/manifests/sen1floods11_manifest.json"
    assert os.path.exists(manifest_path)
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["manifest_schema_version"] == "1.0.0"
    assert data["benchmark_track"] == "REAL_DATA_VALIDATION"
    assert data["dataset_name"] == "Sen1Floods11"
    assert data["total_samples"] == 11
    
    for entry in data["samples"]:
        assert "source_urls" in entry
        assert "sha256_checksums" in entry
        assert "license" in entry
        assert entry["license"] == "Creative Commons Attribution 4.0 International (CC BY-4.0)"
        assert len(entry["sha256_checksums"]["s1"]) == 64
        assert len(entry["sha256_checksums"]["s2"]) == 64
        assert len(entry["sha256_checksums"]["label"]) == 64
