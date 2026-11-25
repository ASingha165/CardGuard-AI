# AGENTS.md — CardGuard AI Engineering & Agent Guidelines

## Project Overview
CardGuard AI is an autonomous-grade credit-card fraud detection and explainable investigation platform.

## Architecture & Conventions
- **Backend**: `backend/app/` — FastAPI, SQLAlchemy 2.0, Pydantic v2, Scikit-learn, XGBoost, Imbalanced-learn, SHAP.
- **Frontend**: `frontend/src/` — Next.js 15 App Router, TypeScript, Tailwind CSS, Recharts, React Flow (`@xyflow/react`), Framer Motion.
- **Design System**: Precision Dark Intelligence (`#101211` surface, `#C8F169` primary accent, `Alatsi` / `Instrument Sans` / `Red Hat Mono`).

## Non-Negotiable Engineering Rules
1. **No Raw PAN Storage**: Never persist or log raw 13–19 digit card numbers. Always use `mask_and_tokenize_card()`.
2. **Zero Data Leakage**: Stratified 60/20/20 split; `StandardScaler` fit on train only; `SMOTE` applied to training data only; threshold selected on validation set; final metrics reported on held-out test set.
3. **Evidence vs. Inference Separation**: Investigation dossiers must separate `observed_evidence` (DB facts) from `model_inference` (probabilistic scores & SHAP). Never fabricate historical transactions or network edges.
4. **Verification**: Run `python -m pytest -v` in `backend/` and `npm test && npm run build` in `frontend/` after any changes.
