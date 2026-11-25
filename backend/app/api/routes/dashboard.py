"""Executive dashboard analytics routes."""
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Dataset, Investigation, ModelRun, Transaction
from app.db.session import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard_analytics(
    range_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    dataset = (
        db.query(Dataset)
        .filter(Dataset.is_active.is_(True))
        .order_by(Dataset.created_at.desc())
        .first()
    )
    if not dataset:
        return {"dataset": None, "kpis": {}, "timeseries": [], "risk_distribution": [], "category_breakdown": [], "top_flagged": []}

    cutoff = datetime.now(timezone.utc) - timedelta(days=range_days)
    base_q = db.query(Transaction).filter(Transaction.dataset_id == dataset.id)
    window_q = base_q.filter(Transaction.timestamp >= cutoff)

    total_tx = window_q.count()
    if total_tx == 0:
        window_q = base_q
        total_tx = base_q.count()

    flagged_q = window_q.filter(Transaction.risk_score >= 75.0)
    flagged_count = flagged_q.count()
    critical_count = window_q.filter(Transaction.risk_level == "critical").count()
    exposure_usd = float(flagged_q.with_entities(func.coalesce(func.sum(Transaction.amount), 0.0)).scalar() or 0.0)
    total_volume_usd = float(window_q.with_entities(func.coalesce(func.sum(Transaction.amount), 0.0)).scalar() or 0.0)

    active_xgb = (
        db.query(ModelRun)
        .filter(ModelRun.model_name == "xgboost", ModelRun.is_active.is_(True))
        .order_by(ModelRun.created_at.desc())
        .first()
    )
    open_investigations = db.query(Investigation).filter(Investigation.status.in_(["open", "escalated"])).count()

    # Daily timeseries
    rows = window_q.order_by(Transaction.timestamp.asc()).all()
    daily_map: Dict[str, Dict] = {}
    level_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    cat_map: Dict[str, Dict] = {}

    for tx in rows:
        day_key = tx.timestamp.strftime("%Y-%m-%d") if tx.timestamp else "unknown"
        if day_key not in daily_map:
            daily_map[day_key] = {"date": day_key, "total": 0, "flagged": 0, "volume_usd": 0.0}
        daily_map[day_key]["total"] += 1
        daily_map[day_key]["volume_usd"] = round(daily_map[day_key]["volume_usd"] + tx.amount, 2)
        if tx.risk_score >= 75.0:
            daily_map[day_key]["flagged"] += 1

        level_counts[tx.risk_level] = level_counts.get(tx.risk_level, 0) + 1

        cat = tx.merchant_category
        if cat not in cat_map:
            cat_map[cat] = {"category": cat, "count": 0, "flagged": 0, "avg_risk": 0.0, "_risk_sum": 0.0}
        cat_map[cat]["count"] += 1
        cat_map[cat]["_risk_sum"] += tx.risk_score
        if tx.risk_score >= 75.0:
            cat_map[cat]["flagged"] += 1

    category_breakdown: List[Dict] = []
    for item in cat_map.values():
        item["avg_risk"] = round(item["_risk_sum"] / item["count"], 1) if item["count"] else 0.0
        del item["_risk_sum"]
        category_breakdown.append(item)
    category_breakdown.sort(key=lambda x: x["flagged"], reverse=True)

    top_flagged = (
        window_q.order_by(Transaction.risk_score.desc())
        .limit(8)
        .all()
    )

    return {
        "dataset": {
            "id": dataset.id,
            "name": dataset.name,
            "source_type": dataset.source_type,
            "row_count": dataset.row_count,
            "fraud_rate": dataset.fraud_rate,
        },
        "kpis": {
            "transactions_monitored": total_tx,
            "flagged_high_risk": flagged_count,
            "critical_alerts": critical_count,
            "exposure_at_risk_usd": round(exposure_usd, 2),
            "total_volume_usd": round(total_volume_usd, 2),
            "open_investigations": open_investigations,
            "xgb_pr_auc": active_xgb.metrics.get("pr_auc") if active_xgb else None,
            "xgb_f2": active_xgb.metrics.get("f2") if active_xgb else None,
        },
        "timeseries": list(daily_map.values())[-30:],
        "risk_distribution": [
            {"level": lvl, "count": cnt} for lvl, cnt in level_counts.items()
        ],
        "category_breakdown": category_breakdown[:8],
        "top_flagged": [
            {
                "tx_id": t.tx_id,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "card_last4": t.card_last4,
                "merchant": t.merchant,
                "merchant_category": t.merchant_category,
                "amount": t.amount,
                "country": t.country,
                "risk_score": t.risk_score,
                "risk_level": t.risk_level,
                "analyst_status": t.analyst_status,
            }
            for t in top_flagged
        ],
    }
