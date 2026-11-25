"""Transaction search, inspection, status updates, and real-time scoring routes."""
import uuid
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import mask_and_tokenize_card, validate_api_key
from app.db.models import Dataset, Transaction
from app.db.session import get_db
from app.ml.pipeline import (
    FEATURE_COLUMNS,
    classify_risk_level,
    explain_transaction_shap,
    score_transactions_with_artifacts,
)
from app.schemas.api import ScoreTransactionRequest, TransactionStatusUpdate

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _serialize_tx(t: Transaction) -> dict:
    return {
        "id": t.id,
        "tx_id": t.tx_id,
        "dataset_id": t.dataset_id,
        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
        "card_token": t.card_token,
        "card_last4": t.card_last4,
        "merchant": t.merchant,
        "merchant_category": t.merchant_category,
        "amount": t.amount,
        "currency": t.currency,
        "country": t.country,
        "channel": t.channel,
        "device_id": t.device_id,
        "ip_subnet": t.ip_subnet,
        "velocity_1h": t.velocity_1h,
        "distance_from_home_km": t.distance_from_home_km,
        "amount_zscore": t.amount_zscore,
        "is_international": t.is_international,
        "hour_of_day": t.hour_of_day,
        "merchant_risk_index": t.merchant_risk_index,
        "is_fraud": t.is_fraud,
        "xgb_probability": t.xgb_probability,
        "iforest_score": t.iforest_score,
        "risk_score": t.risk_score,
        "risk_level": t.risk_level,
        "analyst_status": t.analyst_status,
    }


@router.get("")
def search_transactions(
    q: Optional[str] = Query(default=None, max_length=80),
    risk_level: Optional[str] = Query(default=None),
    analyst_status: Optional[str] = Query(default=None),
    min_amount: Optional[float] = Query(default=None, ge=0),
    sort_by: str = Query(default="risk_score", pattern="^(risk_score|amount|timestamp)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    dataset = (
        db.query(Dataset)
        .filter(Dataset.is_active.is_(True))
        .order_by(Dataset.created_at.desc())
        .first()
    )
    if not dataset:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    query = db.query(Transaction).filter(Transaction.dataset_id == dataset.id)

    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Transaction.tx_id.ilike(like),
                Transaction.merchant.ilike(like),
                Transaction.card_last4.ilike(like),
                Transaction.device_id.ilike(like),
                Transaction.ip_subnet.ilike(like),
            )
        )
    if risk_level and risk_level != "all":
        query = query.filter(Transaction.risk_level == risk_level)
    if analyst_status and analyst_status != "all":
        query = query.filter(Transaction.analyst_status == analyst_status)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)

    total = query.count()

    sort_col = {
        "risk_score": Transaction.risk_score,
        "amount": Transaction.amount,
        "timestamp": Transaction.timestamp,
    }[sort_by]
    query = query.order_by(sort_col.desc() if sort_dir == "desc" else sort_col.asc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_serialize_tx(t) for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/{tx_id}")
def get_transaction(tx_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.tx_id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _serialize_tx(tx)


@router.patch("/{tx_id}/status")
def update_transaction_status(
    tx_id: str,
    payload: TransactionStatusUpdate,
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    tx = db.query(Transaction).filter(Transaction.tx_id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx.analyst_status = payload.analyst_status
    db.commit()
    db.refresh(tx)
    return _serialize_tx(tx)


@router.post("/score")
def score_single_transaction(
    payload: ScoreTransactionRequest,
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    """Score a single transaction in real time with Isolation Forest, XGBoost, and SHAP."""
    settings = get_settings()
    card_token, card_last4 = mask_and_tokenize_card(payload.card_reference)

    row = {col: getattr(payload, col) for col in FEATURE_COLUMNS}
    df = pd.DataFrame([row])
    xgb_probs, iso_scores = score_transactions_with_artifacts(df, settings.MODEL_DIR)

    xgb_p = float(xgb_probs[0])
    iso_s = float(iso_scores[0])
    risk_score = round((0.70 * xgb_p + 0.30 * iso_s) * 100.0, 2)
    risk_level = classify_risk_level(risk_score)
    shap_drivers = explain_transaction_shap(row, settings.MODEL_DIR)

    tx_id = f"LIVE-{uuid.uuid4().hex[:8].upper()}"
    if payload.persist:
        dataset = (
            db.query(Dataset)
            .filter(Dataset.is_active.is_(True))
            .order_by(Dataset.created_at.desc())
            .first()
        )
        if dataset:
            tx = Transaction(
                tx_id=tx_id,
                dataset_id=dataset.id,
                timestamp=datetime.now(timezone.utc),
                card_token=card_token,
                card_last4=card_last4,
                merchant=payload.merchant,
                merchant_category=payload.merchant_category,
                amount=payload.amount,
                currency="USD",
                country=payload.country,
                channel=payload.channel,
                device_id=payload.device_id,
                ip_subnet=payload.ip_subnet,
                velocity_1h=payload.velocity_1h,
                distance_from_home_km=payload.distance_from_home_km,
                amount_zscore=payload.amount_zscore,
                is_international=payload.is_international,
                hour_of_day=payload.hour_of_day,
                merchant_risk_index=payload.merchant_risk_index,
                is_fraud=None,
                xgb_probability=round(xgb_p, 4),
                iforest_score=round(iso_s, 4),
                risk_score=risk_score,
                risk_level=risk_level,
                analyst_status="flagged" if risk_level == "critical" else "unreviewed",
            )
            db.add(tx)
            db.commit()

    return {
        "tx_id": tx_id,
        "card_token": card_token,
        "card_last4": card_last4,
        "xgb_probability": round(xgb_p, 4),
        "iforest_score": round(iso_s, 4),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "contributing_features": shap_drivers,
    }
