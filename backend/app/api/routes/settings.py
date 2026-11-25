"""Application settings routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import validate_api_key
from app.db.models import AppSettings
from app.db.session import get_db
from app.schemas.api import SettingsUpdateRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_app_settings(db: Session = Depends(get_db)):
    cfg = get_settings()
    row = db.query(AppSettings).first()
    if not row:
        row = AppSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)

    return {
        "iforest_contamination": row.iforest_contamination,
        "xgb_threshold_override": row.xgb_threshold_override,
        "high_risk_cutoff": row.high_risk_cutoff,
        "critical_risk_cutoff": row.critical_risk_cutoff,
        "auto_flag_critical": row.auto_flag_critical,
        "require_auth": cfg.REQUIRE_AUTH,
        "max_upload_mb": cfg.MAX_UPLOAD_MB,
        "environment": cfg.ENVIRONMENT,
    }


@router.patch("")
def update_app_settings(
    payload: SettingsUpdateRequest,
    _analyst: str = Depends(validate_api_key),
    db: Session = Depends(get_db),
):
    row = db.query(AppSettings).first()
    if not row:
        row = AppSettings(id=1)
        db.add(row)

    if payload.iforest_contamination is not None:
        row.iforest_contamination = payload.iforest_contamination
    if payload.xgb_threshold_override is not None:
        row.xgb_threshold_override = payload.xgb_threshold_override
    if payload.high_risk_cutoff is not None:
        row.high_risk_cutoff = payload.high_risk_cutoff
    if payload.critical_risk_cutoff is not None:
        row.critical_risk_cutoff = payload.critical_risk_cutoff
    if payload.auto_flag_critical is not None:
        row.auto_flag_critical = payload.auto_flag_critical

    db.commit()
    db.refresh(row)
    return {
        "status": "updated",
        "iforest_contamination": row.iforest_contamination,
        "xgb_threshold_override": row.xgb_threshold_override,
        "high_risk_cutoff": row.high_risk_cutoff,
        "critical_risk_cutoff": row.critical_risk_cutoff,
        "auto_flag_critical": row.auto_flag_critical,
    }
