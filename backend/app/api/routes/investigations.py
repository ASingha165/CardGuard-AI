"""AI Investigation Workspace & Investigation History routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import validate_api_key
from app.db.models import Investigation, Transaction
from app.db.session import get_db
from app.schemas.api import InvestigationUpdate
from app.services.investigation_service import run_transaction_investigation

router = APIRouter(prefix="/api/investigations", tags=["investigations"])


def _serialize_investigation(inv: Investigation) -> dict:
    tx = inv.transaction
    return {
        "id": inv.id,
        "case_id": inv.case_id,
        "tx_id": inv.tx_id,
        "risk_score": inv.risk_score,
        "risk_classification": inv.risk_classification,
        "status": inv.status,
        "observed_evidence": inv.observed_evidence,
        "model_inference": inv.model_inference,
        "contributing_features": inv.contributing_features,
        "recommended_actions": inv.recommended_actions,
        "analyst_notes": inv.analyst_notes,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        "transaction": {
            "tx_id": tx.tx_id,
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
            "card_last4": tx.card_last4,
            "card_token": tx.card_token,
            "merchant": tx.merchant,
            "merchant_category": tx.merchant_category,
            "amount": tx.amount,
            "currency": tx.currency,
            "country": tx.country,
            "channel": tx.channel,
            "device_id": tx.device_id,
            "ip_subnet": tx.ip_subnet,
            "velocity_1h": tx.velocity_1h,
            "analyst_status": tx.analyst_status,
        } if tx else None,
    }


@router.get("")
def list_investigations(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Investigation).order_by(Investigation.created_at.desc())
    if status and status != "all":
        query = query.filter(Investigation.status == status)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_serialize_investigation(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{tx_id}")
def create_or_refresh_investigation(
    tx_id: str,
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    tx = db.query(Transaction).filter(Transaction.tx_id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    inv = run_transaction_investigation(db, tx, persist=True)
    return _serialize_investigation(inv)


@router.get("/{case_id}")
def get_investigation(case_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation case not found")
    return _serialize_investigation(inv)


@router.patch("/{case_id}")
def update_investigation(
    case_id: str,
    payload: InvestigationUpdate,
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation case not found")
    inv.status = payload.status
    if payload.analyst_notes is not None:
        inv.analyst_notes = payload.analyst_notes

    if inv.transaction:
        if payload.status == "resolved_fraud":
            inv.transaction.analyst_status = "confirmed_fraud"
        elif payload.status == "resolved_legit":
            inv.transaction.analyst_status = "cleared"
        elif payload.status == "escalated":
            inv.transaction.analyst_status = "flagged"

    db.commit()
    db.refresh(inv)
    return _serialize_investigation(inv)
