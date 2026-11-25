# CardGuard AI — Vercel deployment

This repository is deployed as **two Vercel projects** from the same GitHub repository.

## 1. Backend project

- Import: `ASingha165/CardGuard-AI`
- Project name: `cardguard-ai-api`
- Root Directory: `backend`
- Framework preset: Other / Python (Vercel auto-detects FastAPI from `index.py` and `requirements.txt`)
- The Vercel entrypoint is `backend/index.py`, which exports the FastAPI ASGI app.

Set backend environment variables before production use:

- `ENVIRONMENT=production`
- `DATABASE_URL`: managed PostgreSQL connection string (do not use SQLite for production; Vercel function filesystems are ephemeral)
- `API_KEY_SECRET`: long random secret
- `REQUIRE_AUTH=true`
- `CORS_ORIGINS`: exact frontend production origin, e.g. `https://cardguard-ai.vercel.app`
- `MODEL_DIR=/tmp/cardguard-models`
- `UPLOAD_DIR=/tmp/cardguard-uploads`

Note: `/tmp` is ephemeral. Uploaded files and trained model artifacts must be stored in object storage or another persistent service before relying on them across function invocations. Check Vercel Python Function memory, duration, and bundle limits against scikit-learn, XGBoost and SHAP before production use.

## 2. Frontend project

- Import the same repository again as a second Vercel project.
- Project name: `cardguard-ai`
- Root Directory: `frontend`
- Framework preset: Next.js
- Build command: `npm run build`
- Set `CARDGUARD_API_URL` to the backend production URL, e.g. `https://cardguard-ai-api.vercel.app`.
- Set `NEXT_PUBLIC_API_URL` to an empty value so browser requests use same-origin paths and Next.js rewrites proxy `/api/*` and `/health` to the backend.

The frontend rewrites are configured in `frontend/next.config.mjs`.

## 3. Verify

- Backend: `https://<backend-domain>/health` must return JSON with `status=healthy` and `database=connected`.
- Frontend: open the production URL and verify dashboard, transactions, investigations, network, models, datasets, history, reports and settings.
- Test CSV upload, inference and report generation with synthetic data only.

Do not mark the app production-ready until the database is persistent, backend auth secrets are configured, and ML model/upload persistence has been addressed.
