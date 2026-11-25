"""Report generation and export routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.security import validate_api_key
from app.db.models import Report
from app.db.session import get_db
from app.schemas.api import ReportCreateRequest
from app.services.report_service import generate_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(30).all()
    return {
        "items": [
            {
                "id": r.id,
                "report_id": r.report_id,
                "title": r.title,
                "report_type": r.report_type,
                "format": r.format,
                "summary_json": r.summary_json,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ]
    }


@router.post("")
def create_report(
    payload: ReportCreateRequest,
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    report = generate_report(
        db=db,
        report_type=payload.report_type,
        fmt=payload.format,
        dataset_id=payload.dataset_id,
    )
    return {
        "id": report.id,
        "report_id": report.report_id,
        "title": report.title,
        "report_type": report.report_type,
        "format": report.format,
        "summary_json": report.summary_json,
        "content": report.content,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.get("/{report_id}")
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "report_id": report.report_id,
        "title": report.title,
        "report_type": report.report_type,
        "format": report.format,
        "summary_json": report.summary_json,
        "content": report.content,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    media_types = {
        "json": "application/json",
        "csv": "text/csv",
        "markdown": "text/markdown",
    }
    ext = {"json": "json", "csv": "csv", "markdown": "md"}[report.format]
    return Response(
        content=report.content,
        media_type=media_types.get(report.format, "text/plain"),
        headers={"Content-Disposition": f'attachment; filename="{report.report_id}.{ext}"'},
    )
