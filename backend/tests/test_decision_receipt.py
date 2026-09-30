from datetime import datetime, timezone
import pytest
from backend.app.models.schemas import ImpactFinding, PriorityLevel, VerificationStatus, ConflictState
from backend.app.services.receipt_service import DecisionReceiptService

def test_decision_receipt_creation_and_integrity_verification():
    now = datetime.now(timezone.utc)
    finding = ImpactFinding(
        id="finding_iso_comp_1",
        event_id="evt_remal",
        title="Catastrophic Isolation of Gowainghat Valley",
        finding_type="ISOLATED_COMMUNITY",
        priority=PriorityLevel.CRITICAL,
        criticality_score=94.5,
        confidence=0.89,
        conflict_state=ConflictState.NONE,
        affected_population=14200,
        affected_infrastructure_ids=["bridge_b14_surma"],
        location_coordinates=[91.95, 24.98],
        summary="Access severed by deep inundation.",
        recommendation="Deploy pontoon bridge immediately.",
        evidence_chain=[],
        verification_status=VerificationStatus.UNVERIFIED,
        created_at=now
    )
    
    sat_scenes = [
        {"scene_id": "S1A_IW_GRDH_1SDV", "modality": "SENTINEL_1_SAR", "timestamp": now.isoformat()}
    ]
    
    receipt = DecisionReceiptService.create_receipt(
        finding=finding,
        event_name="Cyclone Remal",
        satellite_scenes=sat_scenes
    )
    
    assert receipt.receipt_id.startswith("rcpt_")
    assert len(receipt.integrity_sha256) == 64
    assert DecisionReceiptService.verify_integrity(receipt) == True
    
    # Tampering test: modify a field in receipt
    tampered_dict = receipt.model_dump()
    tampered_dict["affected_population"] = 999999
    
    from backend.app.models.schemas import DecisionReceipt
    tampered_receipt = DecisionReceipt(**tampered_dict)
    # Verification MUST fail when content was modified after issuance!
    assert DecisionReceiptService.verify_integrity(tampered_receipt) == False
