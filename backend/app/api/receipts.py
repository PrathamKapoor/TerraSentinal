from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.db_models import DBDecisionReceipt
from backend.app.models.schemas import DecisionReceipt
from backend.app.services.receipt_service import DecisionReceiptService

router = APIRouter(prefix="", tags=["receipts"])

@router.get("/receipts/{receipt_id}", response_model=DecisionReceipt)
def get_receipt(receipt_id: str, db: Session = Depends(get_db)):
    r = db.query(DBDecisionReceipt).filter(DBDecisionReceipt.id == receipt_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Decision Receipt not found")
    return DecisionReceipt(**r.receipt_json)

@router.get("/events/{event_id}/receipts", response_model=List[DecisionReceipt])
def list_event_receipts(event_id: str, db: Session = Depends(get_db)):
    receipts_db = db.query(DBDecisionReceipt).filter(DBDecisionReceipt.event_id == event_id).order_by(DBDecisionReceipt.created_at.desc()).all()
    return [DecisionReceipt(**r.receipt_json) for r in receipts_db]

@router.post("/receipts/{receipt_id}/verify", response_model=Dict[str, Any])
def verify_receipt(receipt_id: str, db: Session = Depends(get_db)):
    r = db.query(DBDecisionReceipt).filter(DBDecisionReceipt.id == receipt_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Decision Receipt not found")
        
    receipt = DecisionReceipt(**r.receipt_json)
    is_valid = DecisionReceiptService.verify_integrity(receipt)
    
    return {
        "receipt_id": receipt.receipt_id,
        "is_valid": is_valid,
        "recorded_sha256": receipt.integrity_sha256,
        "status": "CRYPTOGRAPHICALLY_VERIFIED" if is_valid else "TAMPER_DETECTED",
        "verified_at": receipt.issued_at
    }
