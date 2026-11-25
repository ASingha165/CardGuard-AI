"""Investigation and executive report generation service."""
import csv
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.db.models import Dataset, Investigation, ModelRun, Report, Transaction


def generate_report(
    db: Session,
    report_type: str = "executive_summary",
    fmt: str = "markdown",
    dataset_id: int | None = None,
) -> Report:
    """Generate and persist a real report from database records."""
    dataset = (
        db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset_id
        else db.query(Dataset).filter(Dataset.is_active.is_(True)).order_by(Dataset.created_at.desc()).first()
    )
    ds_id = dataset.id if dataset else None

    tx_q = db.query(Transaction)
    if ds_id is not None:
        tx_q = tx_q.filter(Transaction.dataset_id == ds_id)

    total_tx = tx_q.count()
    high_risk_txs = tx_q.filter(Transaction.risk_score >= 75.0).order_by(Transaction.risk_score.desc()).limit(50).all()
    investigations = db.query(Investigation).order_by(Investigation.created_at.desc()).limit(25).all()
    model_runs = db.query(ModelRun).filter(ModelRun.is_active.is_(True)).all()

    summary: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_name": dataset.name if dataset else "None",
        "source_type": dataset.source_type if dataset else "unknown",
        "total_transactions": total_tx,
        "high_or_critical_count": tx_q.filter(Transaction.risk_score >= 75.0).count(),
        "investigations_count": len(investigations),
        "active_models": [
            {
                "model_name": m.model_name,
                "selected_threshold": m.selected_threshold,
                "metrics": m.metrics,
            }
            for m in model_runs
        ],
    }

    if fmt == "json":
        payload = {
            "summary": summary,
            "high_risk_transactions": [
                {
                    "tx_id": t.tx_id,
                    "card_last4": t.card_last4,
                    "merchant": t.merchant,
                    "amount": t.amount,
                    "risk_score": round(t.risk_score, 2),
                    "risk_level": t.risk_level,
                    "analyst_status": t.analyst_status,
                }
                for t in high_risk_txs
            ],
            "investigations": [
                {
                    "case_id": i.case_id,
                    "tx_id": i.tx_id,
                    "risk_score": i.risk_score,
                    "risk_classification": i.risk_classification,
                    "status": i.status,
                }
                for i in investigations
            ],
        }
        content = json.dumps(payload, indent=2)
    elif fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["tx_id", "timestamp", "card_last4", "merchant", "category", "amount", "country", "risk_score", "risk_level", "analyst_status"])
        for t in high_risk_txs:
            writer.writerow([
                t.tx_id,
                t.timestamp.isoformat() if t.timestamp else "",
                t.card_last4,
                t.merchant,
                t.merchant_category,
                f"{t.amount:.2f}",
                t.country,
                f"{t.risk_score:.2f}",
                t.risk_level,
                t.analyst_status,
            ])
        content = buf.getvalue()
    else:
        lines = [
            f"# CardGuard AI — {report_type.replace('_', ' ').title()}",
            f"- **Generated:** {summary['generated_at']}",
            f"- **Dataset:** {summary['dataset_name']} (`{summary['source_type']}`)",
            f"- **Transactions Monitored:** {summary['total_transactions']:,}",
            f"- **High / Critical Risk Transactions:** {summary['high_or_critical_count']:,}",
            "",
            "## Active Model Evaluation",
        ]
        for m in summary["active_models"]:
            met = m["metrics"]
            lines.append(
                f"- **{m['model_name']}** (threshold={m['selected_threshold']}): "
                f"Precision={met.get('precision', 'N/A')}, Recall={met.get('recall', 'N/A')}, "
                f"F1={met.get('f1', 'N/A')}, F2={met.get('f2', 'N/A')}, "
                f"PR-AUC={met.get('pr_auc', 'N/A')}, ROC-AUC={met.get('roc_auc', 'N/A')}"
            )
        lines.append("")
        lines.append("## Top Flagged Transactions")
        lines.append("| TX ID | Card | Merchant | Amount | Risk Score | Level | Status |")
        lines.append("| --- | --- | --- | ---: | ---: | --- | --- |")
        for t in high_risk_txs[:15]:
            lines.append(
                f"| {t.tx_id} | •••• {t.card_last4} | {t.merchant} | ${t.amount:,.2f} | {t.risk_score:.1f} | {t.risk_level} | {t.analyst_status} |"
            )
        content = "\n".join(lines)

    report = Report(
        report_id=f"RPT-{uuid.uuid4().hex[:8].upper()}",
        title=f"{report_type.replace('_', ' ').title()} ({fmt.upper()})",
        report_type=report_type,
        format=fmt,
        dataset_id=ds_id,
        summary_json=summary,
        content=content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
