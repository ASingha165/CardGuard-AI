# Model Methodology — CardGuard AI

## 1. Feature Engineering
Seven behavioral and transactional features are used by both models:
- `amount`: Transaction amount (USD)
- `velocity_1h`: Card transaction count in the trailing 1-hour window
- `distance_from_home_km`: Distance from cardholder home baseline
- `amount_zscore`: Cardholder-relative ticket deviation
- `is_international`: Binary cross-border indicator
- `hour_of_day`: UTC hour (0–23)
- `merchant_risk_index`: Category-level baseline risk prior

## 2. Models

### A. Isolation Forest (Unsupervised)
- `sklearn.ensemble.IsolationForest(n_estimators=150, contamination=configurable)`
- Outputs raw `decision_function` scores inverted and min-max normalized to `[0, 1]`.
- Useful for detecting novel anomalies even when ground-truth fraud labels are absent.

### B. XGBoost Classifier (Supervised)
- `xgboost.XGBClassifier` trained on stratified splits.
- **Leakage Prevention Protocol**:
  1. Stratified 60% Train / 20% Validation / 20% Test split (`train_test_split(..., stratify=y)`).
  2. `StandardScaler` fit strictly on `X_train` and applied to `X_val` and `X_test`.
  3. `SMOTE` oversampling applied **strictly to `(X_train_scaled, y_train)`** — never to validation or test sets.
  4. Classification threshold selected on `X_val` by maximizing **F2-score** (`beta=2`, weighting recall higher than precision to minimize missed fraud).
  5. Final metrics (Precision, Recall, F1, F2, PR-AUC, ROC-AUC, Confusion Matrix) evaluated once on held-out `X_test`.

## 3. Composite Risk & Explainability
- Composite Risk Score (`0–100`): `(0.70 * xgb_probability + 0.30 * iforest_score) * 100`.
- Per-transaction explanations use `shap.TreeExplainer` on the trained XGBoost model to quantify each feature's directional contribution.
