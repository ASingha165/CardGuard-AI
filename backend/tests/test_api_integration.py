"""API integration tests across all CardGuard AI endpoints."""
from fastapi.testclient import TestClient

from app.main import app


def test_full_api_workflow():
    with TestClient(app) as client:
        # 1. Health
        h = client.get("/health")
        assert h.status_code == 200
        assert h.json()["status"] == "healthy"

        # 2. Dashboard
        d = client.get("/api/dashboard?range_days=30")
        assert d.status_code == 200
        dash = d.json()
        assert dash["kpis"]["transactions_monitored"] > 0
        assert len(dash["top_flagged"]) > 0

        # 3. Transaction Search & Pagination
        txs = client.get("/api/transactions?page=1&page_size=10&sort_by=risk_score")
        assert txs.status_code == 200
        tx_list = txs.json()["items"]
        assert len(tx_list) == 10
        target_tx_id = tx_list[0]["tx_id"]

        # 4. Real-time Transaction Scoring
        score_res = client.post(
            "/api/transactions/score",
            json={
                "amount": 5400.0,
                "merchant": "BitVault Exchange",
                "merchant_category": "crypto_exchange",
                "country": "NG",
                "velocity_1h": 6,
                "distance_from_home_km": 4200.0,
                "amount_zscore": 4.2,
                "is_international": 1,
                "hour_of_day": 2,
                "merchant_risk_index": 0.62,
                "persist": False,
            },
        )
        assert score_res.status_code == 200
        assert score_res.json()["risk_score"] > 50

        # 5. AI Investigation (Observed Evidence vs Model Inference)
        inv_res = client.post(f"/api/investigations/{target_tx_id}")
        assert inv_res.status_code == 200
        inv = inv_res.json()
        assert len(inv["observed_evidence"]) >= 3
        assert "xgboost_probability" in inv["model_inference"]
        assert len(inv["contributing_features"]) > 0
        assert len(inv["recommended_actions"]) > 0

        # 6. Fraud Network Explorer
        net_res = client.get(f"/api/network?focus_tx_id={target_tx_id}")
        assert net_res.status_code == 200
        net = net_res.json()
        assert net["summary"]["node_count"] >= 4
        assert net["summary"]["edge_count"] >= 4

        # 7. Active Models & Retrain
        mod_res = client.get("/api/models/active")
        assert mod_res.status_code == 200
        assert mod_res.json()["xgboost"] is not None
        assert mod_res.json()["isolation_forest"] is not None

        # 8. Reports & Export
        rpt_res = client.post("/api/reports", json={"report_type": "executive_summary", "format": "markdown"})
        assert rpt_res.status_code == 200
        rpt_id = rpt_res.json()["report_id"]
        dl_res = client.get(f"/api/reports/{rpt_id}/download")
        assert dl_res.status_code == 200
        assert "CardGuard AI" in dl_res.text

        # 9. Settings
        set_res = client.get("/api/settings")
        assert set_res.status_code == 200
        assert "iforest_contamination" in set_res.json()
