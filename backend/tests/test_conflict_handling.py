import pytest
import numpy as np
from backend.app.services.evidence_fusion import EvidenceFusionEngine
from backend.app.models.schemas import ConflictState, PriorityLevel
from backend.app.services.priority_engine import PriorityEngine
from backend.app.services.isolation_engine import IsolationAssessmentSummary

def test_sensor_conflict_sar_flooded_optical_dry():
    """
    Scenario 1: SAR indicates deep inundation (specular backscatter -21 dB),
    but unclouded optical imagery indicates dry asphalt/ground (MNDWI = -0.40).
    Expected: System must NOT choose SAR silently; it must flag CONFLICT_DETECTED
    and depress confidence to trigger verification.
    """
    h, w = 40, 40
    sar_vv = np.full((h, w), -21.0, dtype=np.float32)  # Low backscatter = specular water
    sar_vh = np.full((h, w), -27.0, dtype=np.float32)
    dem_slope = np.full((h, w), 2.0, dtype=np.float32)
    optical_mndwi = np.full((h, w), -0.40, dtype=np.float32)  # Dry ground / tarmac
    
    res = EvidenceFusionEngine.fuse_observations(
        sar_vv=sar_vv,
        sar_vh=sar_vh,
        dem_slope=dem_slope,
        optical_mndwi=optical_mndwi,
        optical_cloud_pct=0.0
    )
    
    assert res.conflict_detected is True
    assert res.conflict_count == h * w
    assert np.all(res.conflict_mask)
    # Confidence in conflict zone must be heavily suppressed
    assert float(np.mean(res.fused_confidence)) <= 0.60
    assert res.quality_status == "CONFLICT_DETECTED"

def test_sensor_conflict_sar_dry_optical_flooded():
    """
    Scenario 2: SAR indicates high land backscatter (-10.5 dB, e.g. emergent dense canopy),
    while optical MNDWI shows strong water absorption (+0.55).
    Expected: System flags CONFLICT_DETECTED with depressed confidence.
    """
    h, w = 40, 40
    sar_vv = np.full((h, w), -10.5, dtype=np.float32)  # Land / rough vegetation
    sar_vh = np.full((h, w), -16.0, dtype=np.float32)
    dem_slope = np.full((h, w), 1.0, dtype=np.float32)
    optical_mndwi = np.full((h, w), 0.55, dtype=np.float32)  # Water
    
    res = EvidenceFusionEngine.fuse_observations(
        sar_vv=sar_vv,
        sar_vh=sar_vh,
        dem_slope=dem_slope,
        optical_mndwi=optical_mndwi,
        optical_cloud_pct=5.0
    )
    
    assert res.conflict_detected is True
    assert np.all(res.conflict_mask)
    assert float(np.mean(res.fused_confidence)) <= 0.60

def test_human_ground_truth_conflict_triggers_verification():
    """
    Scenario 3: Satellite analysis indicates roadway is BLOCKED, but a field observer
    reports the roadway is OPEN (e.g. raised causeway with shallow dry crown).
    Priority engine must surface a VERIFICATION_REQUIRED finding with CONFLICT state.
    """
    event_id = "evt_conflict_audit_01"
    road_features = [{
        "type": "Feature",
        "properties": {
            "id": "road_causeway_n2",
            "name": "Highway N2 Causeway",
            "passability_state": "BLOCKED",
            "length_km": 8.5
        },
        "geometry": {"type": "LineString", "coordinates": [[91.85, 24.90], [91.95, 24.95]]}
    }]
    bridge_features = []
    facility_features = []
    isolation_summary = IsolationAssessmentSummary(
        isolated_communities_count=0,
        total_isolated_population=0,
        mean_accessibility_loss_minutes=0.0,
        communities=[]
    )
    
    # Trigger findings generation with evidence conflict detected
    findings = PriorityEngine.generate_findings(
        event_id=event_id,
        road_features=road_features,
        bridge_features=bridge_features,
        facility_features=facility_features,
        isolation_summary=isolation_summary,
        evidence_conflict_detected=True,
        mean_flood_confidence=0.88
    )
    
    conflict_findings = [f for f in findings if f.priority == PriorityLevel.VERIFY]
    assert len(conflict_findings) >= 1
    cf = conflict_findings[0]
    assert cf.conflict_state != ConflictState.NONE
    assert "reconciliation" in cf.recommendation.lower() or "reconnaissance" in cf.recommendation.lower()
    assert cf.confidence < 0.60
