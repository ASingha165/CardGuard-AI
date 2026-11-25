"""Explainable AI Investigation service.

Strictly distinguishes:
1. Observed Evidence (factual database telemetry, never fabricated)
2. Model Inference (XGBoost probability, Isolation Forest anomaly score, SHAP attributions)
"""
import uuid
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Investigation, Transaction
from app.ml.pipeline import FEATURE_COLUMNS, classify_risk_level, explain_transaction_shap


def run_transaction_investigation(db: Session, tx: Transaction, persist: bool = True) -> Investigation:
    """Build or refresh an explainable investigation dossier for a transaction."""
    settings = get_settings()

    # 1. Observed Evidence (real database counts & facts, zero fabrication)
    card_tx_count = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.dataset_id == tx.dataset_id, Transaction.card_token == tx.card_token)
        .scalar()
        or 0
    )
    device_card_count = (
        db.query(func.count(func.distinct(Transaction.card_token)))
        .filter(Transaction.dataset_id == tx.dataset_id, Transaction.device_id == tx.device_id)
        .scalar()
        or 0
    )
    ip_card_count = (
        db.query(func.count(func.distinct(Transaction.card_token)))
        .filter(Transaction.dataset_id == tx.dataset_id, Transaction.ip_subnet == tx.ip_subnet)
        .scalar()
        or 0
    )
    merchant_avg_amount = (
        db.query(func.avg(Transaction.amount))
        .filter(Transaction.dataset_id == tx.dataset_id, Transaction.merchant == tx.merchant)
        .scalar()
        or tx.amount
    )

    observed_evidence: List[Dict[str, Any]] = [
        {
            "category": "Transaction Telemetry",
            "fact": f"Amount ${tx.amount:,.2f} {tx.currency} at {tx.merchant} ({tx.merchant_category}) via {tx.channel}.",
            "metric": f"${tx.amount:,.2f}",
            "source": "observed_db_record",
        },
        {
            "category": "Velocity & Cadence",
            "fact": f"Observed 1-hour velocity: {tx.velocity_1h} transaction(s); {card_tx_count} total transaction(s) for card •••• {tx.card_last4} in active dataset.",
            "metric": f"{tx.velocity_1h} tx/1h",
            "source": "observed_db_aggregation",
        },
        {
            "category": "Infrastructure Sharing",
            "fact": f"Device {tx.device_id} is associated with {device_card_count} distinct card token(s); IP subnet {tx.ip_subnet} is associated with {ip_card_count} distinct card token(s).",
            "metric": f"{device_card_count} cards/dev",
            "source": "observed_db_aggregation",
        },
        {
            "category": "Geographic & Amount Context",
            "fact": f"Country: {tx.country} (international={bool(tx.is_international)}), distance from home baseline: {tx.distance_from_home_km:.1f} km, merchant mean ticket: ${merchant_avg_amount:,.2f}.",
            "metric": f"{tx.distance_from_home_km:.0f} km",
            "source": "observed_db_record",
        },
    ]

    # 2. Model Inference & SHAP Explainability
    row_features = {col: getattr(tx, col) for col in FEATURE_COLUMNS}
    shap_contributions = explain_transaction_shap(row_features, settings.MODEL_DIR)

    xgb_prob = float(tx.xgb_probability or 0.0)
    iso_score = float(tx.iforest_score or 0.0)
    risk_score = round(float(tx.risk_score), 1)
    risk_class = classify_risk_level(risk_score)

    top_drivers = [c for c in shap_contributions if c["direction"] == "increases_risk"][:3]
    driver_summary = (
        ", ".join(f"{d['feature']} ({d['impact_pct']}%)" for d in top_drivers)
        if top_drivers
        else "No elevated risk drivers detected"
    )

    model_inference: Dict[str, Any] = {
        "xgboost_probability": round(xgb_prob, 4),
        "isolation_forest_anomaly_score": round(iso_score, 4),
        "combined_risk_score": risk_score,
        "risk_classification": risk_class,
        "narrative": (
            f"Model inference assigns a {risk_score:.1f}/100 ({risk_class.upper()}) composite risk score "
            f"(XGBoost fraud probability {xgb_prob * 100:.1f}%, Isolation Forest anomaly {iso_score * 100:.1f}%). "
            f"Primary risk-increasing SHAP drivers: {driver_summary}."
        ),
        "provenance_notice": "Model-generated inference; verify against observed evidence before taking cardholder action.",
    }

    # 3. Recommended Analyst Actions
    recommended_actions: List[Dict[str, str]] = []
    if risk_class in ("critical", "high"):
        recommended_actions.append({
            "priority": "high",
            "action": "Place temporary authorization hold & verify cardholder via out-of-band step-up",
            "rationale": f"Composite risk {risk_score:.1f}/100 exceeds high-risk threshold.",
        })
    if device_card_count > 1 or ip_card_count > 1:
        recommended_actions.append({
            "priority": "high",
            "action": f"Inspect linked accounts on {tx.device_id} / {tx.ip_subnet} in Fraud Network Explorer",
            "rationale": f"Shared infrastructure detected across {max(device_card_count, ip_card_count)} card tokens.",
        })
    if tx.velocity_1h >= 3:
        recommended_actions.append({
            "priority": "medium",
            "action": "Review 1-hour velocity burst for card-testing pattern",
            "rationale": f"{tx.velocity_1h} transactions observed within 60 minutes.",
        })
    if not recommended_actions:
        recommended_actions.append({
            "priority": "low",
            "action": "Clear transaction or monitor passively",
            "rationale": "Risk score and observed telemetry remain within normal baseline.",
        })

    existing = (
        db.query(Investigation)
        .filter(Investigation.transaction_id == tx.id)
        .order_by(Investigation.created_at.desc())
        .first()
    )
    if existing:
        existing.risk_score = risk_score
        existing.risk_classification = risk_class
        existing.observed_evidence = observed_evidence
        existing.model_inference = model_inference
        existing.contributing_features = shap_contributions
        existing.recommended_actions = recommended_actions
        if persist:
            db.commit()
            db.refresh(existing)
        return existing

    inv = Investigation(
        case_id=f"CASE-{uuid.uuid4().hex[:8].upper()}",
        transaction_id=tx.id,
        tx_id=tx.tx_id,
        risk_score=risk_score,
        risk_classification=risk_class,
        status="escalated" if risk_class == "critical" else "open",
        observed_evidence=observed_evidence,
        model_inference=model_inference,
        contributing_features=shap_contributions,
        recommended_actions=recommended_actions,
    )
    if persist:
        db.add(inv)
        db.commit()
        db.refresh(inv)
    return inv
