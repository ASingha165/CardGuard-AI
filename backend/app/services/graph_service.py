"""Relationship graph builder from real database transactions.

Constructs entity-relationship graphs (Transactions, Cards, Merchants, Devices, IP Subnets)
strictly from observed database records. Never fabricates relationships.
"""
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.db.models import Transaction


def build_fraud_network_graph(
    db: Session,
    dataset_id: int,
    focus_tx_id: Optional[str] = None,
    min_risk_score: float = 65.0,
    limit: int = 35,
) -> Dict[str, Any]:
    """Build nodes and edges for React Flow from observed transactions."""
    query = db.query(Transaction).filter(Transaction.dataset_id == dataset_id)

    if focus_tx_id:
        anchor = query.filter(Transaction.tx_id == focus_tx_id).first()
        if anchor:
            txs = (
                query.filter(
                    (Transaction.card_token == anchor.card_token)
                    | (Transaction.device_id == anchor.device_id)
                    | (Transaction.ip_subnet == anchor.ip_subnet)
                )
                .order_by(Transaction.risk_score.desc())
                .limit(limit)
                .all()
            )
        else:
            txs = []
    else:
        txs = (
            query.filter(Transaction.risk_score >= min_risk_score)
            .order_by(Transaction.risk_score.desc())
            .limit(limit)
            .all()
        )
        if not txs:
            txs = query.order_by(Transaction.risk_score.desc()).limit(min(limit, 15)).all()

    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    seen_edges: Set[str] = set()

    def add_node(node_id: str, node_type: str, label: str, meta: Dict[str, Any]) -> None:
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "label": label,
                "meta": meta,
            }

    def add_edge(source: str, target: str, relation: str) -> None:
        key = f"{source}->{target}:{relation}"
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append({
                "id": f"e_{len(edges) + 1}",
                "source": source,
                "target": target,
                "relation": relation,
            })

    for tx in txs:
        tx_node = f"tx:{tx.tx_id}"
        card_node = f"card:{tx.card_token}"
        merchant_node = f"merchant:{tx.merchant}"
        device_node = f"device:{tx.device_id}"
        ip_node = f"ip:{tx.ip_subnet}"

        add_node(tx_node, "transaction", tx.tx_id, {
            "amount": tx.amount,
            "risk_score": round(tx.risk_score, 1),
            "risk_level": tx.risk_level,
            "is_fraud": tx.is_fraud,
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
        })
        add_node(card_node, "card", f"•••• {tx.card_last4}", {
            "card_token": tx.card_token,
            "last4": tx.card_last4,
        })
        add_node(merchant_node, "merchant", tx.merchant, {
            "category": tx.merchant_category,
            "risk_index": tx.merchant_risk_index,
        })
        add_node(device_node, "device", tx.device_id, {"device_id": tx.device_id})
        add_node(ip_node, "ip_subnet", tx.ip_subnet, {"ip_subnet": tx.ip_subnet, "country": tx.country})

        add_edge(card_node, tx_node, "INITIATED")
        add_edge(tx_node, merchant_node, "AT_MERCHANT")
        add_edge(tx_node, device_node, "FROM_DEVICE")
        add_edge(tx_node, ip_node, "VIA_IP")

    # Compute degree counts to highlight shared hubs
    degree: Dict[str, int] = {}
    for e in edges:
        degree[e["source"]] = degree.get(e["source"], 0) + 1
        degree[e["target"]] = degree.get(e["target"], 0) + 1

    for nid, node in nodes.items():
        node["meta"]["degree"] = degree.get(nid, 0)

    shared_devices = [n for n in nodes.values() if n["type"] == "device" and n["meta"]["degree"] > 1]
    shared_ips = [n for n in nodes.values() if n["type"] == "ip_subnet" and n["meta"]["degree"] > 1]

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "summary": {
            "transaction_count": len(txs),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "shared_devices": len(shared_devices),
            "shared_ip_subnets": len(shared_ips),
        },
    }
