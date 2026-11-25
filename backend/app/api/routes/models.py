"""Model training and evaluation routes (Isolation Forest & XGBoost)."""
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import validate_api_key
from app.db.models import Dataset, ModelRun, Transaction
from app.db.session import get_db
from app.ml.pipeline import (
    FEATURE_COLUMNS,
    classify_risk_level,
    train_isolation_forest,
    train_xgboost_classifier,
)
from app.schemas.api import TrainModelRequest

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_model_runs(db: Session = Depends(get_db)):
    runs = db.query(ModelRun).order_by(ModelRun.created_at.desc()).limit(20).all()
    return {
        "items": [
            {
                "id": r.id,
                "model_name": r.model_name,
                "dataset_id": r.dataset_id,
                "status": r.status,
                "is_active": r.is_active,
                "hyperparameters": r.hyperparameters,
                "selected_threshold": r.selected_threshold,
                "metrics": r.metrics,
                "feature_importance": r.feature_importance,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    }


@router.get("/active")
def get_active_models(db: Session = Depends(get_db)):
    iso = (
        db.query(ModelRun)
        .filter(ModelRun.model_name == "isolation_forest", ModelRun.is_active.is_(True))
        .order_by(ModelRun.created_at.desc())
        .first()
    )
    xgb = (
        db.query(ModelRun)
        .filter(ModelRun.model_name == "xgboost", ModelRun.is_active.is_(True))
        .order_by(ModelRun.created_at.desc())
        .first()
    )

    def serialize(r: ModelRun | None):
        if not r:
            return None
        return {
            "id": r.id,
            "model_name": r.model_name,
            "dataset_id": r.dataset_id,
            "selected_threshold": r.selected_threshold,
            "hyperparameters": r.hyperparameters,
            "metrics": r.metrics,
            "feature_importance": r.feature_importance,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }

    return {"isolation_forest": serialize(iso), "xgboost": serialize(xgb)}


@router.post("/train")
def train_models(
    payload: TrainModelRequest,
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    dataset = (
        db.query(Dataset).filter(Dataset.id == payload.dataset_id).first()
        if payload.dataset_id
        else db.query(Dataset).filter(Dataset.is_active.is_(True)).order_by(Dataset.created_at.desc()).first()
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="No active dataset found for training.")

    txs = db.query(Transaction).filter(Transaction.dataset_id == dataset.id).all()
    if len(txs) < 50:
        raise HTTPException(status_code=400, detail="At least 50 transactions are required for model training.")

    df = pd.DataFrame([
        {
            "id": t.id,
            **{col: getattr(t, col) for col in FEATURE_COLUMNS},
            "is_fraud": t.is_fraud,
        }
        for t in txs
    ])

    results = {}
    iso_scores = None
    xgb_probs = None

    if payload.model_name in ("isolation_forest", "both"):
        iso_res = train_isolation_forest(
            df,
            contamination=payload.contamination,
            random_state=settings.RANDOM_STATE,
            model_dir=settings.MODEL_DIR,
        )
        db.query(ModelRun).filter(ModelRun.model_name == "isolation_forest").update({ModelRun.is_active: False})
        run = ModelRun(
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
        db.add(run)
        iso_scores = iso_res["scores"]
        results["isolation_forest"] = {
            "selected_threshold": iso_res["selected_threshold"],
            "metrics": iso_res["metrics"],
            "feature_importance": iso_res["feature_importance"],
        }

    if payload.model_name in ("xgboost", "both"):
        labeled_count = int(df["is_fraud"].notna().sum())
        if labeled_count < 30 or df["is_fraud"].dropna().nunique() < 2:
            raise HTTPException(
                status_code=400,
                detail="XGBoost requires labeled data with both fraud (1) and legitimate (0) classes.",
            )
        xgb_res = train_xgboost_classifier(
            df,
            random_state=settings.RANDOM_STATE,
            max_depth=payload.max_depth,
            learning_rate=payload.learning_rate,
            n_estimators=payload.n_estimators,
            threshold_override=payload.threshold_override,
            model_dir=settings.MODEL_DIR,
        )
        db.query(ModelRun).filter(ModelRun.model_name == "xgboost").update({ModelRun.is_active: False})
        run = ModelRun(
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
        db.add(run)
        xgb_probs = xgb_res["probabilities"]
        results["xgboost"] = {
            "selected_threshold": xgb_res["selected_threshold"],
            "metrics": xgb_res["metrics"],
            "feature_importance": xgb_res["feature_importance"],
        }

    # Update transaction scores in DB
    for idx, tx in enumerate(txs):
        x_p = float(xgb_probs[idx]) if xgb_probs is not None else float(tx.xgb_probability or 0.0)
        i_s = float(iso_scores[idx]) if iso_scores is not None else float(tx.iforest_score or 0.0)
        risk = round((0.70 * x_p + 0.30 * i_s) * 100.0, 2)
        tx.xgb_probability = round(x_p, 4)
        tx.iforest_score = round(i_s, 4)
        tx.risk_score = risk
        tx.risk_level = classify_risk_level(risk)

    db.commit()
    return {"status": "trained", "dataset_id": dataset.id, "results": results}
