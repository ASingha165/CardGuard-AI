"""Fraud Network Explorer relationship graph routes."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import Dataset
from app.db.session import get_db
from app.services.graph_service import build_fraud_network_graph

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("")
def get_network_graph(
    focus_tx_id: Optional[str] = Query(default=None),
    min_risk_score: float = Query(default=65.0, ge=0.0, le=100.0),
    limit: int = Query(default=25, ge=5, le=80),
    db: Session = Depends(get_db),
):
    dataset = (
        db.query(Dataset)
        .filter(Dataset.is_active.is_(True))
        .order_by(Dataset.created_at.desc())
        .first()
    )
    if not dataset:
        return {"nodes": [], "edges": [], "summary": {"transaction_count": 0, "node_count": 0, "edge_count": 0}}

    return build_fraud_network_graph(
        db=db,
        dataset_id=dataset.id,
        focus_tx_id=focus_tx_id,
        min_risk_score=min_risk_score,
        limit=limit,
    )
