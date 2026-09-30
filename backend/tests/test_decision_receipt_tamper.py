import pytest
import copy
from datetime import datetime, timezone
from backend.app.services.receipt_service import DecisionReceiptService
from backend.app.models.schemas import ImpactFinding, PriorityLevel, ConflictState, VerificationStatus

def test_decision_receipt_cryptographic_audit_and_tamper_detection():
    """
    Verifies that:
    1. Decision receipt contains complete metadata and explicitly distinguishes
       OBSERVED, INFERRED, and SIMULATED blocks.
    2. Valid canonical receipt passes integrity verification.
    3. Mutating even 1 bit/field triggers SEAL VERIFICATION FAILURE.
    """
    now = datetime.now(timezone.utc)
    finding = ImpactFinding(
        id="finding_iso_comp1",
        event_id="evt_test_audit",
        title="Catastrophic Isolation of Gowainghat",
        finding_type="ISOLATED_COMMUNITY",
        priority=PriorityLevel.CRITICAL,
        criticality_score=94.5,
        confidence=0.88,
        conflict_state=ConflictState.NONE,
        affected_population=14500,
        affected_infrastructure_ids=["bridge_b14"],
        location_coordinates=[91.95, 24.90],
        summary="Severe flooding severed road access.",
        recommendation="Deploy emergency pontoon.",
        evidence_chain=[],
        verification_status=VerificationStatus.UNVERIFIED,
        created_at=now
    )
    
    scenes = [{
        "scene_id": "S1A_IW_GRDH_1SDV_2026",
        "sensor": "Sentinel-1 SAR",
        "acquisition_time": now.isoformat()
    }]
    
    # 1. Issue receipt
    receipt = DecisionReceiptService.create_receipt(
        finding=finding,
        event_name="Sylhet Monsoon Flood",
        satellite_scenes=scenes,
        simulation_id="sim_pontoon_01"
    )
    
    # 2. Verify explicit information categorization
    assert "satellite_scenes" in receipt.observed_evidence
    assert "sensor_modalities" in receipt.observed_evidence
    assert receipt.inferred_impacts["affected_population"] == 14500
    assert receipt.inferred_impacts["criticality_score"] == 94.5
    assert receipt.simulated_counterfactuals["counterfactual_simulation_id"] == "sim_pontoon_01"
    assert receipt.simulated_counterfactuals["badge"] == "SIMULATED / COUNTERFACTUAL"
    
    # 3. Verify legitimate receipt passes cryptographic verification
    assert DecisionReceiptService.verify_integrity(receipt) is True
    
    # 4. Tamper Test A: Mutate affected population by 1
    tampered_receipt = copy.deepcopy(receipt)
    tampered_receipt.affected_population = 14501
    assert DecisionReceiptService.verify_integrity(tampered_receipt) is False, "Seal verification should fail on tampered population!"
    
    # 5. Tamper Test B: Mutate confidence score
    tampered_receipt_b = copy.deepcopy(receipt)
    tampered_receipt_b.overall_confidence = 0.99
    assert DecisionReceiptService.verify_integrity(tampered_receipt_b) is False, "Seal verification should fail on tampered confidence!"
    
    # 6. Tamper Test C: Mutate recommendation text
    tampered_receipt_c = copy.deepcopy(receipt)
    tampered_receipt_c.primary_recommendation = "Do nothing; situation resolved."
    assert DecisionReceiptService.verify_integrity(tampered_receipt_c) is False, "Seal verification should fail on tampered recommendation!"
