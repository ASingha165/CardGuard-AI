"""Pydantic request and response schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TrainModelRequest(BaseModel):
    dataset_id: Optional[int] = None
    model_name: str = Field(default="both", pattern="^(isolation_forest|xgboost|both)$")
    contamination: float = Field(default=0.035, ge=0.005, le=0.25)
    max_depth: int = Field(default=4, ge=2, le=10)
    learning_rate: float = Field(default=0.08, ge=0.01, le=0.5)
    n_estimators: int = Field(default=160, ge=20, le=500)
    threshold_override: Optional[float] = Field(default=None, ge=0.05, le=0.95)


class ScoreTransactionRequest(BaseModel):
    amount: float = Field(..., gt=0, le=1_000_000)
    merchant: str = Field(..., min_length=1, max_length=120)
    merchant_category: str = Field(default="electronics", max_length=64)
    country: str = Field(default="US", min_length=2, max_length=8)
    channel: str = Field(default="card_not_present", max_length=24)
    card_reference: str = Field(default="tok_demo_card", min_length=4, max_length=64)
    device_id: str = Field(default="dev_manual_01", max_length=64)
    ip_subnet: str = Field(default="192.168.1.0/24", max_length=64)
    velocity_1h: int = Field(default=1, ge=0, le=500)
    distance_from_home_km: float = Field(default=12.0, ge=0, le=25000)
    amount_zscore: float = Field(default=0.0, ge=-10, le=25)
    is_international: int = Field(default=0, ge=0, le=1)
    hour_of_day: int = Field(default=14, ge=0, le=23)
    merchant_risk_index: float = Field(default=0.2, ge=0.0, le=1.0)
    persist: bool = False


class TransactionStatusUpdate(BaseModel):
    analyst_status: str = Field(..., pattern="^(unreviewed|flagged|cleared|confirmed_fraud)$")


class InvestigationUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|escalated|resolved_fraud|resolved_legit)$")
    analyst_notes: Optional[str] = Field(default=None, max_length=4000)


class ReportCreateRequest(BaseModel):
    report_type: str = Field(default="executive_summary", pattern="^(executive_summary|case_dossier|model_audit)$")
    format: str = Field(default="markdown", pattern="^(markdown|json|csv)$")
    dataset_id: Optional[int] = None


class SettingsUpdateRequest(BaseModel):
    iforest_contamination: Optional[float] = Field(default=None, ge=0.005, le=0.25)
    xgb_threshold_override: Optional[float] = Field(default=None, ge=0.05, le=0.95)
    high_risk_cutoff: Optional[float] = Field(default=None, ge=40.0, le=95.0)
    critical_risk_cutoff: Optional[float] = Field(default=None, ge=60.0, le=99.0)
    auto_flag_critical: Optional[bool] = None


class SyntheticDatasetRequest(BaseModel):
    n_rows: int = Field(default=1200, ge=200, le=10000)
    seed: int = Field(default=42, ge=1, le=999999)
