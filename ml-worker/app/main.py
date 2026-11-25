"""Container-hosted CardGuard ML worker. Keep heavy ML dependencies out of Vercel."""
import os
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.ml.pipeline import (
    FEATURE_COLUMNS,
    explain_transaction_shap,
    score_transactions_with_artifacts,
    train_isolation_forest,
    train_xgboost_classifier,
)

MODEL_DIR = os.getenv("MODEL_DIR", "/var/lib/cardguard/models")
WORKER_TOKEN = os.getenv("ML_WORKER_TOKEN", "")
Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)
app = FastAPI(title="CardGuard ML Worker", version="1.0.0")


class ScoreRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(min_length=1, max_length=50000)


class ExplainRequest(BaseModel):
    features: dict[str, float]


class TrainRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(min_length=50, max_length=50000)
    model_name: str = "both"
    contamination: float = 0.035
    random_state: int = 42
    max_depth: int = 4
    learning_rate: float = 0.08
    n_estimators: int = 160
    threshold_override: float | None = None


def authorize(x_worker_token: str | None):
    if not WORKER_TOKEN or x_worker_token != WORKER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid ML worker credentials")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "cardguard-ml-worker"}


@app.post("/internal/score")
def score(payload: ScoreRequest, x_worker_token: str | None = Header(default=None)):
    authorize(x_worker_token)
    frame = pd.DataFrame(payload.rows)
    xgb, iso = score_transactions_with_artifacts(frame, MODEL_DIR)
    return {"xgb_probabilities": xgb.tolist(), "isolation_scores": iso.tolist()}


@app.post("/internal/explain")
def explain(payload: ExplainRequest, x_worker_token: str | None = Header(default=None)):
    authorize(x_worker_token)
    return {"contributing_features": explain_transaction_shap(payload.features, MODEL_DIR)}


@app.post("/internal/train")
def train(payload: TrainRequest, x_worker_token: str | None = Header(default=None)):
    authorize(x_worker_token)
    frame = pd.DataFrame(payload.rows)
    result = {}
    iso_scores = None
    xgb_probs = None
    if payload.model_name in ("isolation_forest", "both"):
        iso = train_isolation_forest(frame, contamination=payload.contamination,
                                     random_state=payload.random_state, model_dir=MODEL_DIR)
        iso_scores = iso["scores"].tolist()
        result["isolation_forest"] = {k: iso[k] for k in ("hyperparameters", "selected_threshold", "metrics", "feature_importance", "artifact_path")}
    if payload.model_name in ("xgboost", "both"):
        xgb = train_xgboost_classifier(frame, random_state=payload.random_state,
                                       max_depth=payload.max_depth, learning_rate=payload.learning_rate,
                                       n_estimators=payload.n_estimators,
                                       threshold_override=payload.threshold_override, model_dir=MODEL_DIR)
        xgb_probs = xgb["probabilities"].tolist()
        result["xgboost"] = {k: xgb[k] for k in ("hyperparameters", "selected_threshold", "metrics", "feature_importance", "artifact_path")}
    result["xgb_probabilities"] = xgb_probs
    result["isolation_scores"] = iso_scores
    return result
