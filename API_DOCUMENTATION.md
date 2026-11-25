# API Documentation — CardGuard AI

Base URL: `http://localhost:8000` (local)

## Authentication
When `REQUIRE_AUTH=true`, mutating endpoints require `X-API-Key: <API_KEY_SECRET>` or `Authorization: Bearer <API_KEY_SECRET>`.

## Endpoints

### Health
- `GET /health` — Service & database connectivity status.

### Dashboard
- `GET /api/dashboard?range_days=30` — KPIs, daily detection timeseries, category breakdown, and top flagged transactions.

### Datasets
- `GET /api/datasets` — List all datasets.
- `GET /api/datasets/{dataset_id}/inspect?limit=25` — Inspect dataset metadata and top-risk sample rows.
- `POST /api/datasets/upload` — Multipart CSV upload (`file`). Enforces `.csv`, `MAX_UPLOAD_MB`, `amount > 0`, and auto-tokenizes raw PANs.
- `POST /api/datasets/synthetic` — Generate a synthetic dataset (`n_rows`, `seed`) and retrain models.
- `POST /api/datasets/{dataset_id}/activate` — Switch active dataset.

### Models
- `GET /api/models` — List recent model runs.
- `GET /api/models/active` — Active Isolation Forest & XGBoost runs with metrics and curves.
- `POST /api/models/train` — Train `isolation_forest`, `xgboost`, or `both` on active dataset.

### Transactions
- `GET /api/transactions?q=&risk_level=&analyst_status=&sort_by=risk_score&sort_dir=desc&page=1&page_size=20` — Paginated search.
- `GET /api/transactions/{tx_id}` — Single transaction details.
- `PATCH /api/transactions/{tx_id}/status` — Update `analyst_status` (`unreviewed`, `flagged`, `cleared`, `confirmed_fraud`).
- `POST /api/transactions/score` — Real-time scoring + SHAP drivers for a single transaction.

### Investigations
- `GET /api/investigations?status=&page=1&page_size=20` — List investigation cases.
- `POST /api/investigations/{tx_id}` — Create or refresh explainable AI investigation dossier.
- `GET /api/investigations/{case_id}` — Get case dossier.
- `PATCH /api/investigations/{case_id}` — Update case disposition and analyst notes.

### Fraud Network
- `GET /api/network?focus_tx_id=&min_risk_score=65&limit=25` — Entity-relationship graph (cards, transactions, merchants, devices, IP subnets).

### Reports
- `GET /api/reports` — List generated reports.
- `POST /api/reports` — Generate report (`report_type`: `executive_summary` | `case_dossier` | `model_audit`, `format`: `markdown` | `json` | `csv`).
- `GET /api/reports/{report_id}` — Preview report.
- `GET /api/reports/{report_id}/download` — Download report file.

### Settings
- `GET /api/settings` — Read risk cutoffs and environment settings.
- `PATCH /api/settings` — Update `iforest_contamination`, `xgb_threshold_override`, `high_risk_cutoff`, `critical_risk_cutoff`, `auto_flag_critical`.
