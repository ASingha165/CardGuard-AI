"""Security, PAN protection, CSV validation, and authentication boundary tests."""
import io
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import contains_raw_pan, mask_and_tokenize_card
from app.main import app


def test_raw_pan_never_stored_and_tokenized():
    raw_pan = "4532015112830366"
    assert contains_raw_pan(raw_pan) is True
    token, last4 = mask_and_tokenize_card(raw_pan, salt="test-secret")
    assert token.startswith("tok_")
    assert raw_pan not in token
    assert last4 == "0366"


def test_csv_upload_rejects_non_csv_and_empty():
    with TestClient(app) as client:
        res = client.post(
            "/api/datasets/upload",
            files={"file": ("malware.exe", b"binary", "application/octet-stream")},
        )
        assert res.status_code == 400

        res_empty = client.post(
            "/api/datasets/upload",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert res_empty.status_code == 400


def test_csv_upload_requires_amount_and_tokenizes_raw_pan():
    with TestClient(app) as client:
        bad_csv = b"merchant,country\nTestStore,US\n"
        res_bad = client.post(
            "/api/datasets/upload",
            files={"file": ("bad.csv", bad_csv, "text/csv")},
        )
        assert res_bad.status_code == 400

        good_csv = (
            b"tx_id,card_number,merchant,merchant_category,amount,country,velocity_1h,is_fraud\n"
            b"UP-1001,4532015112830366,Apex Electronics,electronics,420.50,US,2,0\n"
            b"UP-1002,5425233430109903,BitVault Exchange,crypto_exchange,3900.00,NG,6,1\n"
        )
        res_good = client.post(
            "/api/datasets/upload",
            files={"file": ("sample.csv", good_csv, "text/csv")},
        )
        assert res_good.status_code == 200
        body = res_good.json()
        assert body["row_count"] == 2
        assert body["validation_summary"]["raw_pan_detected_and_tokenized"] is True

        tx_res = client.get("/api/transactions/UP-1001")
        assert tx_res.status_code == 200
        tx_data = tx_res.json()
        assert tx_data["card_last4"] == "0366"
        assert "4532015112830366" not in str(tx_data)


def test_auth_boundary_rejects_invalid_key():
    settings = get_settings()
    prev = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = True
    try:
        with TestClient(app) as client:
            res = client.post("/api/reports", json={"report_type": "executive_summary", "format": "json"})
            assert res.status_code == 401

            res_ok = client.post(
                "/api/reports",
                json={"report_type": "executive_summary", "format": "json"},
                headers={"X-API-Key": settings.API_KEY_SECRET},
            )
            assert res_ok.status_code == 200
    finally:
        settings.REQUIRE_AUTH = prev
