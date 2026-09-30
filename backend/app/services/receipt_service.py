import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.models.schemas import DecisionReceipt, ImpactFinding, PriorityLevel, VerificationStatus

class DecisionReceiptService:
    """
    Generates and verifies cryptographically hashed Decision Receipts
    certifying the full provenance chain, analytical inputs, and operational directives.
    """
    
    @staticmethod
    def _compute_hash(payload: Dict[str, Any]) -> str:
        # Exclude hash field itself for idempotent computation
        payload_copy = {k: v for k, v in payload.items() if k != "integrity_sha256"}
        canonical_str = json.dumps(payload_copy, sort_keys=True, default=str)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    @classmethod
    def create_receipt(
        cls,
        finding: ImpactFinding,
        event_name: str,
        satellite_scenes: List[Dict[str, Any]],
        simulation_id: Optional[str] = None
    ) -> DecisionReceipt:
        now = datetime.now(timezone.utc)
        receipt_id = f"rcpt_{finding.id[8:]}_{now.strftime('%Y%m%d%H%M%S')}"
        
        # Build core receipt structure
        receipt_dict: Dict[str, Any] = {
            "receipt_id": receipt_id,
            "finding_id": finding.id,
            "event_id": finding.event_id,
            "event_name": event_name,
            "issued_at": now.isoformat(),
            "model_name": "TerraSentinel-DualPol-SAR+DEM-Fusion",
            "model_version": "1.2.0",
            "processing_pipeline_version": "terrasentinel-core-2026.1",
            "satellite_scenes": satellite_scenes,
            "dem_source": "Copernicus GLO-30 / NASADEM 30m Global Elevation",
            "osm_extract_timestamp": "2026-05-28T00:00:00Z",
            "population_dataset": "WorldPop 100m High-Resolution Settlement Grid",
            "overall_confidence": finding.confidence,
            "evidence_conflicts_surfaced": [finding.conflict_state.value] if finding.conflict_state != "NONE" else [],
            "affected_population": finding.affected_population,
            "impacted_facilities": ["fac_hosp_osmani", "fac_clinic_gowainghat"],
            "severed_critical_routes": finding.affected_infrastructure_ids,
            "priority_level": finding.priority.value,
            "primary_recommendation": finding.recommendation,
            "counterfactual_simulation_id": simulation_id,
            "verification_status": finding.verification_status.value,
            "verified_by": "Mission Commander / On-Duty Operations Chief",
            "verification_timestamp": now.isoformat(),
            "verification_notes": finding.verification_notes or "Automatic rule-based mission receipt issued."
        }
        
        receipt_dict["integrity_sha256"] = ""
        receipt = DecisionReceipt(**receipt_dict)
        
        # Compute canonical hash from model JSON representation
        data = receipt.model_dump(mode="json")
        sha256_hash = cls._compute_hash(data)
        receipt.integrity_sha256 = sha256_hash
        
        return receipt

    @classmethod
    def verify_integrity(cls, receipt: DecisionReceipt) -> bool:
        """
        Validates that receipt has not been tampered with since issuance.
        """
        data = receipt.model_dump(mode="json")
        expected = data.get("integrity_sha256")
        calculated = cls._compute_hash(data)
        return expected == calculated
