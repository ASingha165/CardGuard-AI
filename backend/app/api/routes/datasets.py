"""Dataset laboratory routes: CSV upload, inspection, validation, and synthetic generation."""
import io
import uuid
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import RAW_PAN_COLUMN_NAMES, contains_raw_pan, mask_and_tokenize_card, validate_api_key
from app.db.models import Dataset, Transaction
from app.db.session import get_db
from app.ml.pipeline import FEATURE_COLUMNS, classify_risk_level, score_transactions_with_artifacts
from app.schemas.api import SyntheticDatasetRequest
from app.services.bootstrap_service import seed_and_train_dataset

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("")
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return {
        "items": [
            {
                "id": d.id,
                "name": d.name,
                "source_type": d.source_type,
                "filename": d.filename,
                "row_count": d.row_count,
                "fraud_count": d.fraud_count,
                "fraud_rate": d.fraud_rate,
                "columns": d.columns_json,
                "validation_summary": d.validation_summary,
                "is_active": d.is_active,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in datasets
        ]
    }


@router.get("/{dataset_id}/inspect")
def inspect_dataset(
    dataset_id: int,
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    sample_txs = (
        db.query(Transaction)
        .filter(Transaction.dataset_id == dataset_id)
        .order_by(Transaction.risk_score.desc())
        .limit(limit)
        .all()
    )
    return {
        "dataset": {
            "id": dataset.id,
            "name": dataset.name,
            "source_type": dataset.source_type,
            "row_count": dataset.row_count,
            "fraud_count": dataset.fraud_count,
            "fraud_rate": dataset.fraud_rate,
            "columns": dataset.columns_json,
            "validation_summary": dataset.validation_summary,
            "is_active": dataset.is_active,
        },
        "sample_rows": [
            {
                "tx_id": t.tx_id,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "card_last4": t.card_last4,
                "merchant": t.merchant,
                "merchant_category": t.merchant_category,
                "amount": t.amount,
                "country": t.country,
                "velocity_1h": t.velocity_1h,
                "risk_score": t.risk_score,
                "risk_level": t.risk_level,
                "is_fraud": t.is_fraud,
            }
            for t in sample_txs
        ],
    }


@router.post("/{dataset_id}/activate")
def activate_dataset(
    dataset_id: int,
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.query(Dataset).update({Dataset.is_active: False})
    dataset.is_active = True
    db.commit()
    return {"status": "activated", "dataset_id": dataset_id}


@router.post("/synthetic")
def generate_synthetic_dataset(
    payload: SyntheticDatasetRequest,
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    dataset = seed_and_train_dataset(db, n_rows=payload.n_rows, seed=payload.seed)
    return {
        "id": dataset.id,
        "name": dataset.name,
        "source_type": dataset.source_type,
        "row_count": dataset.row_count,
        "fraud_count": dataset.fraud_count,
        "fraud_rate": dataset.fraud_rate,
    }


@router.post("/upload")
async def upload_csv_dataset(
    file: UploadFile = File(...),
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    """
    Validate, sanitize (never store raw PANs), score, and ingest an uploaded CSV dataset.
    """
    settings = get_settings()

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .csv files are accepted.")

    raw_bytes = await file.read()
    if len(raw_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded CSV file is empty.")
    if len(raw_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_MB} MB.",
        )

    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to parse CSV file.")

    if len(df) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV contains no data rows.")
    if len(df) > settings.MAX_UPLOAD_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV exceeds maximum row limit of {settings.MAX_UPLOAD_ROWS}.",
        )

    # Normalize column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    if "amount" not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must include an 'amount' column.",
        )

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if df["amount"].isna().any() or (df["amount"] <= 0).any():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All 'amount' values must be positive numbers.",
        )

    # Check & sanitize raw card numbers (NEVER store raw PAN)
    raw_pan_detected = False
    card_col = next((c for c in ["card_token", "card_number", "pan", "cc_num", "card_last4"] if c in df.columns), None)
    if card_col and card_col in RAW_PAN_COLUMN_NAMES:
        raw_pan_detected = True

    tokens = []
    last4s = []
    for idx, val in enumerate(df[card_col] if card_col else [f"row_{i}" for i in range(len(df))]):
        s_val = str(val)
        if contains_raw_pan(s_val):
            raw_pan_detected = True
        tok, l4 = mask_and_tokenize_card(s_val)
        tokens.append(tok)
        last4s.append(l4)

    df["card_token"] = tokens
    df["card_last4"] = last4s

    # Fill optional columns with safe defaults
    defaults = {
        "merchant": "Uploaded Merchant",
        "merchant_category": "general_retail",
        "country": "US",
        "channel": "card_not_present",
        "device_id": "dev_uploaded",
        "ip_subnet": "0.0.0.0/0",
        "velocity_1h": 1,
        "distance_from_home_km": 10.0,
        "amount_zscore": 0.0,
        "is_international": 0,
        "hour_of_day": 12,
        "merchant_risk_index": 0.15,
    }
    for col, default_val in defaults.items():
        if col not in df.columns:
            df[col] = default_val
        else:
            df[col] = df[col].fillna(default_val)

    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(defaults.get(col, 0.0))

    has_labels = bool("is_fraud" in df.columns and df["is_fraud"].notna().all())
    if has_labels:
        df["is_fraud"] = pd.to_numeric(df["is_fraud"], errors="coerce").fillna(0).astype(int)
        fraud_count = int(df["is_fraud"].sum())
    else:
        fraud_count = 0

    xgb_probs, iso_scores = score_transactions_with_artifacts(df, settings.MODEL_DIR)

    db.query(Dataset).update({Dataset.is_active: False})
    dataset = Dataset(
        name=file.filename,
        source_type="uploaded",
        filename=file.filename,
        row_count=len(df),
        fraud_count=fraud_count,
        fraud_rate=round(fraud_count / len(df), 4) if len(df) else 0.0,
        columns_json=list(df.columns),
        validation_summary={
            "status": "valid",
            "raw_pan_detected_and_tokenized": bool(raw_pan_detected),
            "has_ground_truth_labels": bool(has_labels),
            "provenance": "Uploaded Dataset",
        },
        is_active=True,
    )
    db.add(dataset)
    db.flush()

    now = datetime.now(timezone.utc)
    tx_objs = []
    for idx, row in df.iterrows():
        xgb_p = float(xgb_probs[idx])
        iso_s = float(iso_scores[idx])
        risk = round((0.70 * xgb_p + 0.30 * iso_s) * 100.0, 2)
        level = classify_risk_level(risk)
        tx_id = str(row["tx_id"]) if "tx_id" in df.columns and pd.notna(row.get("tx_id")) else f"UP-{uuid.uuid4().hex[:8].upper()}"

        ts = now
        if "timestamp" in df.columns and pd.notna(row.get("timestamp")):
            try:
                ts = pd.to_datetime(row["timestamp"], utc=True).to_pydatetime()
            except Exception:
                ts = now

        tx_objs.append(
            Transaction(
                tx_id=tx_id,
                dataset_id=dataset.id,
                timestamp=ts,
                card_token=row["card_token"],
                card_last4=row["card_last4"],
                merchant=str(row["merchant"])[:120],
                merchant_category=str(row["merchant_category"])[:64],
                amount=float(row["amount"]),
                currency="USD",
                country=str(row["country"])[:8],
                channel=str(row["channel"])[:24],
                device_id=str(row["device_id"])[:64],
                ip_subnet=str(row["ip_subnet"])[:64],
                velocity_1h=int(row["velocity_1h"]),
                distance_from_home_km=float(row["distance_from_home_km"]),
                amount_zscore=float(row["amount_zscore"]),
                is_international=int(row["is_international"]),
                hour_of_day=int(row["hour_of_day"]) % 24,
                merchant_risk_index=float(row["merchant_risk_index"]),
                is_fraud=int(row["is_fraud"]) if has_labels else None,
                xgb_probability=round(xgb_p, 4),
                iforest_score=round(iso_s, 4),
                risk_score=risk,
                risk_level=level,
                analyst_status="flagged" if level == "critical" else "unreviewed",
            )
        )

    db.bulk_save_objects(tx_objs)
    db.commit()
    db.refresh(dataset)
    logger.info(f"Uploaded dataset id={dataset.id} rows={len(df)} pan_tokenized={raw_pan_detected}")

    return {
        "id": dataset.id,
        "name": dataset.name,
        "source_type": dataset.source_type,
        "row_count": dataset.row_count,
        "fraud_count": dataset.fraud_count,
        "validation_summary": dataset.validation_summary,
    }
