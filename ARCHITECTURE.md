# Architecture — CardGuard AI

## System Overview

```
┌───────────────────────────┐      REST / JSON       ┌──────────────────────────────┐
│  Next.js 15 Frontend      │ ◄────────────────────► │  FastAPI Backend             │
│  • AppShell (248px rail)  │                        │  • Auth & Security Boundary  │
│  • Recharts & React Flow  │                        │  • SQLAlchemy ORM            │
│  • 9 Analytical Views     │                        │  • ML Pipeline (XGB + IsoF)  │
└───────────────────────────┘                        └──────────────┬───────────────┘
                                                                    │
                                                     ┌──────────────▼───────────────┐
                                                     │  SQLite (dev) / PostgreSQL   │
                                                     │  • Datasets & Transactions   │
                                                     │  • ModelRuns & Investigations│
                                                     │  • Reports & AppSettings     │
                                                     └──────────────────────────────┘
```

## Backend Modules (`backend/app/`)
- `core/config.py`: Environment-driven Pydantic settings (`DATABASE_URL`, `API_KEY_SECRET`, `MAX_UPLOAD_MB`).
- `core/security.py`: HMAC-SHA256 card tokenization, raw PAN detection, CSV validation, `X-API-Key` / Bearer auth.
- `core/logging.py`: Stream logger with regex redaction for PANs and secrets.
- `ml/synthetic.py`: Deterministic synthetic credit-card transaction generator with fraud-ring clusters.
- `ml/pipeline.py`: Leakage-free split/SMOTE/threshold pipeline, Isolation Forest, XGBoost, and SHAP `TreeExplainer`.
- `services/investigation_service.py`: Combines real DB aggregations with SHAP explanations.
- `services/graph_service.py`: Builds entity-relationship graphs from observed transactions.
- `services/report_service.py`: Generates Markdown, CSV, and JSON reports.

## Frontend Modules (`frontend/src/`)
- `components/AppShell.tsx`: Persistent `248px` desktop sidebar & responsive mobile drawer across all 9 routes.
- `lib/api.ts`: Centralized fetch wrapper with `X-API-Key` injection and error handling.
- `app/*`: Dedicated App Router pages for Dashboard, Transactions, Investigations, Network, Models, Datasets, History, Reports, and Settings.
