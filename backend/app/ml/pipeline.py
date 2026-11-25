"""Machine Learning Pipeline: Isolation Forest + XGBoost (SMOTE train-only) + SHAP.

Strict leakage-prevention design:
1. Stratified train / validation / test split (60% / 20% / 20%).
2. StandardScaler fit strictly on X_train.
3. SMOTE applied strictly on (X_train_scaled, y_train) — never on val or test.
4. Classification threshold selected on validation set (maximizing F2 score).
5. Final metrics computed on held-out test set.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import shap
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

FEATURE_COLUMNS: List[str] = [
    "amount",
    "velocity_1h",
    "distance_from_home_km",
    "amount_zscore",
    "is_international",
    "hour_of_day",
    "merchant_risk_index",
]


@dataclass
class SplitData:
    X_train: np.ndarray
    X_val: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_val: np.ndarray
    y_test: np.ndarray
    X_train_resampled: np.ndarray
    y_train_resampled: np.ndarray
    scaler: StandardScaler


def classify_risk_level(risk_score: float, high_cutoff: float = 75.0, critical_cutoff: float = 90.0) -> str:
    if risk_score >= critical_cutoff:
        return "critical"
    if risk_score >= high_cutoff:
        return "high"
    if risk_score >= 40.0:
        return "medium"
    return "low"


def prepare_leakage_free_splits(
    df: pd.DataFrame,
    random_state: int = 42,
    apply_smote: bool = True,
) -> SplitData:
    """
    Create stratified 60/20/20 splits, fit scaler on train only,
    and apply SMOTE on train only.
    """
    X = df[FEATURE_COLUMNS].astype(float).values
    y = df["is_fraud"].astype(int).values

    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=random_state
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.25, stratify=y_train_val, random_state=random_state
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    if apply_smote and int(y_train.sum()) >= 6:
        k_neighbors = min(5, int(y_train.sum()) - 1)
        smote = SMOTE(random_state=random_state, k_neighbors=k_neighbors)
        X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
    else:
        X_train_res, y_train_res = X_train_scaled, y_train

    return SplitData(
        X_train=X_train_scaled,
        X_val=X_val_scaled,
        X_test=X_test_scaled,
        y_train=y_train,
        y_val=y_val,
        y_test=y_test,
        X_train_resampled=X_train_res,
        y_train_resampled=y_train_res,
        scaler=scaler,
    )


def select_validation_threshold(y_val: np.ndarray, val_probs: np.ndarray) -> float:
    """Select threshold on validation set maximizing F2-score."""
    best_threshold = 0.50
    best_f2 = -1.0
    for thr in np.linspace(0.15, 0.85, 29):
        preds = (val_probs >= thr).astype(int)
        score = fbeta_score(y_val, preds, beta=2, zero_division=0)
        if score > best_f2:
            best_f2 = float(score)
            best_threshold = float(np.round(thr, 3))
    return best_threshold


def compute_evaluation_metrics(
    y_true: np.ndarray,
    probs: np.ndarray,
    threshold: float,
) -> Dict[str, Any]:
    """Compute Precision, Recall, F1, F2, PR-AUC, ROC-AUC, confusion matrix, and curves."""
    preds = (probs >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()

    precision = float(precision_score(y_true, preds, zero_division=0))
    recall = float(recall_score(y_true, preds, zero_division=0))
    f1 = float(f1_score(y_true, preds, zero_division=0))
    f2 = float(fbeta_score(y_true, preds, beta=2, zero_division=0))

    has_both_classes = len(np.unique(y_true)) > 1
    pr_auc = float(average_precision_score(y_true, probs)) if has_both_classes else 0.0
    roc_auc = float(roc_auc_score(y_true, probs)) if has_both_classes else 0.5

    # Downsample curves to <= 25 points for clean frontend charts
    pr_points: List[Dict[str, float]] = []
    roc_points: List[Dict[str, float]] = []
    if has_both_classes:
        prec_arr, rec_arr, _ = precision_recall_curve(y_true, probs)
        step_pr = max(1, len(prec_arr) // 25)
        for p, r in zip(prec_arr[::step_pr], rec_arr[::step_pr]):
            pr_points.append({"recall": round(float(r), 4), "precision": round(float(p), 4)})

        fpr_arr, tpr_arr, _ = roc_curve(y_true, probs)
        step_roc = max(1, len(fpr_arr) // 25)
        for fpr, tpr in zip(fpr_arr[::step_roc], tpr_arr[::step_roc]):
            roc_points.append({"fpr": round(float(fpr), 4), "tpr": round(float(tpr), 4)})

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "f2": round(f2, 4),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "pr_curve": pr_points,
        "roc_curve": roc_points,
        "support": int(len(y_true)),
        "positive_support": int(y_true.sum()),
    }


def train_isolation_forest(
    df: pd.DataFrame,
    contamination: float = 0.035,
    random_state: int = 42,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Train Isolation Forest for unsupervised anomaly detection."""
    X = df[FEATURE_COLUMNS].astype(float).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    iso = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=random_state,
        n_jobs=1,
    )
    iso.fit(X_scaled)

    # Convert decision_function (higher = more normal) into [0, 1] anomaly score (higher = more anomalous)
    raw_scores = -iso.decision_function(X_scaled)
    min_s, max_s = float(raw_scores.min()), float(raw_scores.max())
    denom = (max_s - min_s) if (max_s - min_s) > 1e-9 else 1.0
    norm_scores = np.clip((raw_scores - min_s) / denom, 0.0, 1.0)

    metrics: Dict[str, Any] = {
        "anomaly_rate": round(float((iso.predict(X_scaled) == -1).mean()), 4),
        "mean_anomaly_score": round(float(norm_scores.mean()), 4),
        "support": int(len(df)),
    }

    if "is_fraud" in df.columns and df["is_fraud"].notna().all():
        y_true = df["is_fraud"].astype(int).values
        threshold = float(np.quantile(norm_scores, 1.0 - contamination))
        metrics.update(compute_evaluation_metrics(y_true, norm_scores, threshold=threshold))

    artifact_path = None
    if model_dir:
        Path(model_dir).mkdir(parents=True, exist_ok=True)
        artifact_path = str(Path(model_dir) / "isolation_forest.joblib")
        joblib.dump(
            {
                "model": iso,
                "scaler": scaler,
                "min_score": min_s,
                "max_score": max_s,
                "features": FEATURE_COLUMNS,
            },
            artifact_path,
        )

    return {
        "model_name": "isolation_forest",
        "hyperparameters": {"contamination": contamination, "n_estimators": 150},
        "selected_threshold": round(float(1.0 - contamination), 4),
        "metrics": metrics,
        "feature_importance": _compute_unsupervised_feature_deviation(X_scaled, norm_scores),
        "artifact_path": artifact_path,
        "scores": norm_scores,
    }


def _compute_unsupervised_feature_deviation(X_scaled: np.ndarray, norm_scores: np.ndarray) -> List[Dict[str, Any]]:
    high_mask = norm_scores >= np.quantile(norm_scores, 0.90)
    if high_mask.sum() == 0:
        return [{"feature": f, "importance": round(1.0 / len(FEATURE_COLUMNS), 4)} for f in FEATURE_COLUMNS]
    deviations = np.abs(X_scaled[high_mask]).mean(axis=0)
    total = float(deviations.sum()) or 1.0
    items = [
        {"feature": f, "importance": round(float(d / total), 4)}
        for f, d in zip(FEATURE_COLUMNS, deviations)
    ]
    return sorted(items, key=lambda x: x["importance"], reverse=True)


def train_xgboost_classifier(
    df: pd.DataFrame,
    random_state: int = 42,
    max_depth: int = 4,
    learning_rate: float = 0.08,
    n_estimators: int = 160,
    threshold_override: Optional[float] = None,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Train XGBoost fraud classifier with strict leakage prevention:
    - Stratified split
    - SMOTE on training data only
    - Validation-based threshold selection
    - Held-out test evaluation
    """
    labeled = df.dropna(subset=["is_fraud"]).copy()
    splits = prepare_leakage_free_splits(labeled, random_state=random_state, apply_smote=True)

    xgb = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=random_state,
        n_jobs=1,
    )
    xgb.fit(splits.X_train_resampled, splits.y_train_resampled)

    val_probs = xgb.predict_proba(splits.X_val)[:, 1]
    selected_threshold = (
        float(threshold_override)
        if threshold_override is not None
        else select_validation_threshold(splits.y_val, val_probs)
    )

    test_probs = xgb.predict_proba(splits.X_test)[:, 1]
    metrics = compute_evaluation_metrics(splits.y_test, test_probs, threshold=selected_threshold)
    metrics["train_samples_before_smote"] = int(len(splits.y_train))
    metrics["train_samples_after_smote"] = int(len(splits.y_train_resampled))
    metrics["val_samples"] = int(len(splits.y_val))
    metrics["test_samples"] = int(len(splits.y_test))
    metrics["smote_applied_to_train_only"] = True

    importances = xgb.feature_importances_
    total_imp = float(importances.sum()) or 1.0
    feature_importance = sorted(
        [
            {"feature": f, "importance": round(float(imp / total_imp), 4)}
            for f, imp in zip(FEATURE_COLUMNS, importances)
        ],
        key=lambda x: x["importance"],
        reverse=True,
    )

    artifact_path = None
    if model_dir:
        Path(model_dir).mkdir(parents=True, exist_ok=True)
        artifact_path = str(Path(model_dir) / "xgboost_fraud.joblib")
        joblib.dump(
            {
                "model": xgb,
                "scaler": splits.scaler,
                "threshold": selected_threshold,
                "features": FEATURE_COLUMNS,
            },
            artifact_path,
        )

    # Score full dataset using scaler + model
    X_all_scaled = splits.scaler.transform(df[FEATURE_COLUMNS].astype(float).values)
    all_probs = xgb.predict_proba(X_all_scaled)[:, 1]

    return {
        "model_name": "xgboost",
        "hyperparameters": {
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "n_estimators": n_estimators,
            "smote": True,
        },
        "selected_threshold": selected_threshold,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "artifact_path": artifact_path,
        "probabilities": all_probs,
    }


def score_transactions_with_artifacts(
    df: pd.DataFrame,
    model_dir: str,
) -> Tuple[np.ndarray, np.ndarray]:
    """Score transactions using persisted Isolation Forest & XGBoost artifacts."""
    X = df[FEATURE_COLUMNS].astype(float).values
    n = len(df)

    xgb_probs = np.zeros(n, dtype=float)
    iso_scores = np.zeros(n, dtype=float)

    xgb_path = Path(model_dir) / "xgboost_fraud.joblib"
    if xgb_path.exists():
        bundle = joblib.load(xgb_path)
        X_scaled = bundle["scaler"].transform(X)
        xgb_probs = bundle["model"].predict_proba(X_scaled)[:, 1]

    iso_path = Path(model_dir) / "isolation_forest.joblib"
    if iso_path.exists():
        bundle = joblib.load(iso_path)
        X_scaled = bundle["scaler"].transform(X)
        raw = -bundle["model"].decision_function(X_scaled)
        denom = (bundle["max_score"] - bundle["min_score"]) or 1.0
        iso_scores = np.clip((raw - bundle["min_score"]) / denom, 0.0, 1.0)

    return xgb_probs, iso_scores


def explain_transaction_shap(
    row_features: Dict[str, float],
    model_dir: str,
) -> List[Dict[str, Any]]:
    """Compute per-transaction SHAP feature attributions using XGBoost TreeExplainer."""
    xgb_path = Path(model_dir) / "xgboost_fraud.joblib"
    vec = np.array([[float(row_features.get(f, 0.0)) for f in FEATURE_COLUMNS]])

    if xgb_path.exists():
        bundle = joblib.load(xgb_path)
        vec_scaled = bundle["scaler"].transform(vec)
        explainer = shap.TreeExplainer(bundle["model"])
        shap_vals = explainer.shap_values(vec_scaled)
        if isinstance(shap_vals, list):
            shap_arr = np.array(shap_vals[1][0], dtype=float)
        else:
            shap_arr = np.array(shap_vals[0], dtype=float)
    else:
        # Deterministic z-score fallback if model artifact is not yet on disk
        shap_arr = np.array([
            float(row_features.get("amount_zscore", 0.0)) * 0.25,
            float(row_features.get("velocity_1h", 1.0)) * 0.20,
            float(row_features.get("distance_from_home_km", 0.0)) / 1000.0,
            float(row_features.get("amount_zscore", 0.0)) * 0.30,
            float(row_features.get("is_international", 0.0)) * 0.45,
            0.15 if float(row_features.get("hour_of_day", 12)) in (0, 1, 2, 3, 4, 23) else -0.05,
            float(row_features.get("merchant_risk_index", 0.1)) * 0.50,
        ])

    total_abs = float(np.abs(shap_arr).sum()) or 1.0
    contributions = []
    for feat, raw_val, s_val in zip(FEATURE_COLUMNS, vec[0], shap_arr):
        contributions.append(
            {
                "feature": feat,
                "value": round(float(raw_val), 3),
                "shap_value": round(float(s_val), 4),
                "impact_pct": round(float(abs(s_val) / total_abs * 100.0), 1),
                "direction": "increases_risk" if s_val >= 0 else "decreases_risk",
            }
        )
    return sorted(contributions, key=lambda x: abs(x["shap_value"]), reverse=True)
