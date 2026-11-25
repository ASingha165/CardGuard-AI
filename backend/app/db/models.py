"""Database ORM models for CardGuard AI."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), default="synthetic")  # synthetic | uploaded
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    fraud_count: Mapped[int] = mapped_column(Integer, default=0)
    fraud_rate: Mapped[float] = mapped_column(Float, default=0.0)
    columns_json: Mapped[list] = mapped_column(JSON, default=list)
    validation_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tx_id: Mapped[str] = mapped_column(String(48), unique=True, index=True, nullable=False)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=utcnow)

    # Masked/tokenized card reference (NEVER raw PAN)
    card_token: Mapped[str] = mapped_column(String(48), index=True)
    card_last4: Mapped[str] = mapped_column(String(4))

    merchant: Mapped[str] = mapped_column(String(120), index=True)
    merchant_category: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[float] = mapped_column(Float, index=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    country: Mapped[str] = mapped_column(String(8), default="US")
    channel: Mapped[str] = mapped_column(String(24), default="card_not_present")

    device_id: Mapped[str] = mapped_column(String(64), index=True)
    ip_subnet: Mapped[str] = mapped_column(String(64), index=True)

    # Engineered / behavioral features for ML
    velocity_1h: Mapped[int] = mapped_column(Integer, default=1)
    distance_from_home_km: Mapped[float] = mapped_column(Float, default=0.0)
    amount_zscore: Mapped[float] = mapped_column(Float, default=0.0)
    is_international: Mapped[int] = mapped_column(Integer, default=0)
    hour_of_day: Mapped[int] = mapped_column(Integer, default=12)
    merchant_risk_index: Mapped[float] = mapped_column(Float, default=0.1)

    # Ground truth label (nullable for unlabeled scoring uploads)
    is_fraud: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Model predictions
    xgb_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iforest_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_level: Mapped[str] = mapped_column(String(16), default="low", index=True)  # low | medium | high | critical
    analyst_status: Mapped[str] = mapped_column(String(24), default="unreviewed", index=True)  # unreviewed | flagged | cleared | confirmed_fraud

    dataset: Mapped["Dataset"] = relationship(back_populates="transactions")
    investigations: Mapped[list["Investigation"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String(64), index=True)  # isolation_forest | xgboost
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(24), default="completed")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict)
    selected_threshold: Mapped[float] = mapped_column(Float, default=0.5)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    feature_importance: Mapped[list] = mapped_column(JSON, default=list)
    artifact_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"))
    tx_id: Mapped[str] = mapped_column(String(48), index=True)

    risk_score: Mapped[float] = mapped_column(Float)
    risk_classification: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24), default="open")  # open | escalated | resolved_fraud | resolved_legit

    observed_evidence: Mapped[list] = mapped_column(JSON, default=list)
    model_inference: Mapped[dict] = mapped_column(JSON, default=dict)
    contributing_features: Mapped[list] = mapped_column(JSON, default=list)
    recommended_actions: Mapped[list] = mapped_column(JSON, default=list)
    analyst_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    transaction: Mapped["Transaction"] = relationship(back_populates="investigations")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    report_type: Mapped[str] = mapped_column(String(32))  # executive_summary | case_dossier | model_audit
    format: Mapped[str] = mapped_column(String(16))  # json | csv | markdown
    dataset_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iforest_contamination: Mapped[float] = mapped_column(Float, default=0.035)
    xgb_threshold_override: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high_risk_cutoff: Mapped[float] = mapped_column(Float, default=75.0)
    critical_risk_cutoff: Mapped[float] = mapped_column(Float, default=90.0)
    auto_flag_critical: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
