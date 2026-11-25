# CardGuard AI

**Precision Credit-Card Fraud Detection, ML Evaluation & Explainable AI Investigation Platform**

CardGuard AI is a full-stack financial intelligence platform built with **Next.js (TypeScript)**, **FastAPI (Python 3.12)**, **XGBoost**, **Isolation Forest**, **SHAP**, and **React Flow**.

## Key Capabilities

1. **Executive Dashboard (`/`)** — Real-time KPIs, detection velocity over time, merchant category risk exposure, and priority flagged transactions.
2. **Transaction Intelligence (`/transactions`)** — Searchable, filterable, paginated transaction ledger with live single-transaction scoring and analyst disposition updates.
3. **AI Investigation Workspace (`/investigations`)** — Explainable transaction dossiers that strictly separate **Observed Evidence** (factual DB telemetry) from **Model Inference** (XGBoost probability, Isolation Forest anomaly score, SHAP feature attributions, and recommended analyst actions).
4. **Fraud Network Explorer (`/network`)** — Interactive React Flow graph linking card tokens, transactions, merchants, devices, and IP subnets from observed database records.
5. **Model Intelligence (`/models`)** — Isolation Forest & XGBoost training, Precision/Recall/F1/F2/PR-AUC/ROC-AUC evaluation, confusion matrix, and PR curve visualization.
6. **Dataset Laboratory (`/datasets`)** — CSV upload with schema validation, size limits, automatic raw PAN tokenization, and synthetic demo data generation.
7. **Investigation History (`/history`)** — Auditable case log with status filtering and analyst notes.
8. **Reports & Exports (`/reports`)** — Audit-ready report generation and download in Markdown, CSV, and JSON.
9. **Settings (`/settings`)** — Contamination, risk cutoffs, and API key configuration.

## Quick Start (Local Development)

### 1. Backend (FastAPI + ML)
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000`.

## Running Tests
```bash
# Backend & ML tests
cd backend && python -m pytest -v

# Frontend component tests & production build
cd frontend && npm test && npm run build
```

## Security & Data Provenance
- Raw card numbers (PANs) are **never stored** in the database or logs; any raw PAN column in uploaded CSVs is automatically HMAC-SHA256 tokenized (`tok_...`) with only `card_last4` retained.
- Demonstration datasets are explicitly labeled **Synthetic Demo Data**.
