"""Bootstrap service: seeds initial synthetic demo dataset & trains models on first startup."""
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import logger
from app.db.models import AppSettings, Dataset, ModelRun, Transaction
from app.ml.pipeline import (
    FEATURE_COLUMNS,
    classify_risk_level,
    train_isolation_forest,
    train_xgboost_classifier,
)
from app.ml.synthetic import generate_synthetic_transactions
from app.services.investigation_service import run_transaction_investigation


def seed_and_train_dataset(db: Session, n_rows: int = 1200, seed: int = 42) -> Dataset:
    """Create a synthetic dataset, train both models, score transactions, and seed initial investigations."""
    settings = get_settings()

    # Deactivate previous active datasets
    db.query(Dataset).update({Dataset.is_active: False})

    df = generate_synthetic_transactions(n_rows=n_rows, seed=seed)
    fraud_count = int(df["is_fraud"].sum())
    fraud_rate = round(float(fraud_count / len(df)), 4) if len(df) else 0.0

    dataset = Dataset(
        name=f"CardGuard-Synthetic-v4.2 ({n_rows} rows)",
        source_type="synthetic",
        filename=None,
        row_count=len(df),
        fraud_count=fraud_count,
        fraud_rate=fraud_rate,
        columns_json=list(df.columns),
        validation_summary={
            "status": "valid",
            "raw_pan_detected": False,
            "missing_values": 0,
            "provenance": "Synthetic Demo Data",
        },
        is_active=True,
    )
    db.add(dataset)
    db.flush()

    # Train Isolation Forest & XGBoost
    iso_res = train_isolation_forest(
        df,
        contamination=settings.DEFAULT_CONTAMINATION,
        random_state=seed,
        model_dir=settings.MODEL_DIR,
    )
    xgb_res = train_xgboost_classifier(
        df,
        random_state=seed,
        model_dir=settings.MODEL_DIR,
    )

    iso_scores = iso_res["scores"]
    xgb_probs = xgb_res["probabilities"]

    # Deactivate prior runs
    db.query(ModelRun).update({ModelRun.is_active: False})
    db.add(
        ModelRun(
            model_name="isolation_forest",
            dataset_id=dataset.id,
            status="completed",
            is_active=True,
            hyperparameters=iso_res["hyperparameters"],
            selected_threshold=iso_res["selected_threshold"],
            metrics=iso_res["metrics"],
            feature_importance=iso_res["feature_importance"],
            artifact_path=iso_res["artifact_path"],
        )
    )
    db.add(
        ModelRun(
            model_name="xgboost",
            dataset_id=dataset.id,
            status="completed",
            is_active=True,
            hyperparameters=xgb_res["hyperparameters"],
            selected_threshold=xgb_res["selected_threshold"],
            metrics=xgb_res["metrics"],
            feature_importance=xgb_res["feature_importance"],
            artifact_path=xgb_res["artifact_path"],
        )
    )

    tx_objects = []
    for idx, row in df.iterrows():
        xgb_p = float(xgb_probs[idx])
        iso_s = float(iso_scores[idx])
        risk = round((0.70 * xgb_p + 0.30 * iso_s) * 100.0, 2)
        level = classify_risk_level(risk)
        tx_objects.append(
            Transaction(
                tx_id=row["tx_id"],
                dataset_id=dataset.id,
                timestamp=row["timestamp"].to_pydatetime() if hasattr(row["timestamp"], "to_pydatetime") else row["timestamp"],
                card_token=row["card_token"],
                card_last4=row["card_last4"],
                merchant=row["merchant"],
                merchant_category=row["merchant_category"],
                amount=float(row["amount"]),
                currency=row["currency"],
                country=row["country"],
                channel=row["channel"],
                device_id=row["device_id"],
                ip_subnet=row["ip_subnet"],
                velocity_1h=int(row["velocity_1h"]),
                distance_from_home_km=float(row["distance_from_home_km"]),
                amount_zscore=float(row["amount_zscore"]),
                is_international=int(row["is_international"]),
                hour_of_day=int(row["hour_of_day"]),
                merchant_risk_index=float(row["merchant_risk_index"]),
                is_fraud=int(row["is_fraud"]),
                xgb_probability=round(xgb_p, 4),
                iforest_score=round(iso_s, 4),
                risk_score=risk,
                risk_level=level,
                analyst_status="flagged" if level == "critical" else "unreviewed",
            )
        )
    db.bulk_save_objects(tx_objects)
    db.commit()
    db.refresh(dataset)

    # Seed investigations for top 5 highest-risk transactions
    top_txs = (
        db.query(Transaction)
        .filter(Transaction.dataset_id == dataset.id)
        .order_by(Transaction.risk_score.desc())
        .limit(5)
        .all()
    )
    for tx in top_txs:
        run_transaction_investigation(db, tx, persist=True)

    logger.info(f"Seeded synthetic dataset id={dataset.id} rows={len(df)} fraud={fraud_count}")
    return dataset


def ensure_initial_state(db: Session) -> None:
    """Ensure AppSettings and at least one Dataset + trained models exist."""
    if not db.query(AppSettings).first():
        db.add(AppSettings(id=1))
        db.commit()

    if not db.query(Dataset).first():
        seed_and_train_dataset(db, n_rows=1200, seed=42)
