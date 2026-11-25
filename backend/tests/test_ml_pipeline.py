"""ML pipeline, evaluation metrics, and data leakage prevention tests."""
import numpy as np

from app.ml.pipeline import (
    prepare_leakage_free_splits,
    select_validation_threshold,
    train_isolation_forest,
    train_xgboost_classifier,
)
from app.ml.synthetic import generate_synthetic_transactions


def test_no_data_leakage_in_splits_and_smote():
    df = generate_synthetic_transactions(n_rows=500, seed=7)
    splits = prepare_leakage_free_splits(df, random_state=7, apply_smote=True)

    # 60% train, 20% val, 20% test
    assert len(splits.y_train) == 300
    assert len(splits.y_val) == 100
    assert len(splits.y_test) == 100

    # SMOTE must ONLY expand training set; val & test remain untouched and imbalanced
    assert len(splits.y_train_resampled) > len(splits.y_train)
    assert int(splits.y_train_resampled.sum()) == int((splits.y_train_resampled == 0).sum())
    assert int(splits.y_val.sum()) < len(splits.y_val) * 0.15
    assert int(splits.y_test.sum()) < len(splits.y_test) * 0.15

    # Scaler mean should match raw training distribution, not test distribution
    assert splits.scaler.n_samples_seen_ == len(splits.y_train)


def test_validation_threshold_selection_returns_valid_range():
    y_val = np.array([0, 0, 0, 0, 1, 1, 0, 0, 1, 0])
    probs = np.array([0.05, 0.12, 0.22, 0.35, 0.78, 0.88, 0.10, 0.45, 0.62, 0.18])
    thr = select_validation_threshold(y_val, probs)
    assert 0.15 <= thr <= 0.85


def test_isolation_forest_and_xgboost_metrics():
    df = generate_synthetic_transactions(n_rows=600, seed=42)
    iso = train_isolation_forest(df, contamination=0.045, random_state=42)
    assert "precision" in iso["metrics"]
    assert "recall" in iso["metrics"]
    assert "f1" in iso["metrics"]
    assert "f2" in iso["metrics"]
    assert "pr_auc" in iso["metrics"]
    assert "roc_auc" in iso["metrics"]
    assert "confusion_matrix" in iso["metrics"]

    xgb = train_xgboost_classifier(df, random_state=42)
    m = xgb["metrics"]
    assert m["smote_applied_to_train_only"] is True
    assert m["roc_auc"] > 0.80
    assert m["pr_auc"] > 0.50
    assert set(m["confusion_matrix"].keys()) == {"tn", "fp", "fn", "tp"}
