from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Numeric, DateTime, Boolean, ForeignKey, Text, BigInteger
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="VIEWER")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assigned_alerts = relationship("Alert", back_populates="assigned_user")

class TrainedModel(Base):
    __tablename__ = "trained_models"

    model_version = Column(String(20), primary_key=True)
    algorithm = Column(String(50), nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow)
    auc_roc = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    model_binary_path = Column(String(255), nullable=False)

    predictions = relationship("Prediction", back_populates="model")
    metrics = relationship("ModelMetric", back_populates="model", cascade="all, delete-orphan")

class ModelMetric(Base):
    __tablename__ = "model_metrics"

    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    model_version = Column(String(20), ForeignKey("trained_models.model_version", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    model = relationship("TrainedModel", back_populates="metrics")

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(50), primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    card_holder_id = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    merchant = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)

    v1 = Column(Float)
    v2 = Column(Float)
    v3 = Column(Float)
    v4 = Column(Float)
    v5 = Column(Float)
    v6 = Column(Float)
    v7 = Column(Float)
    v8 = Column(Float)
    v9 = Column(Float)
    v10 = Column(Float)
    v11 = Column(Float)
    v12 = Column(Float)
    v13 = Column(Float)
    v14 = Column(Float)
    v15 = Column(Float)
    v16 = Column(Float)
    v17 = Column(Float)
    v18 = Column(Float)
    v19 = Column(Float)
    v20 = Column(Float)
    v21 = Column(Float)
    v22 = Column(Float)
    v23 = Column(Float)
    v24 = Column(Float)
    v25 = Column(Float)
    v26 = Column(Float)
    v27 = Column(Float)
    v28 = Column(Float)

    prediction = relationship("Prediction", uselist=False, back_populates="transaction", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(50), ForeignKey("transactions.transaction_id", ondelete="CASCADE"), nullable=False, unique=True)
    model_version = Column(String(20), ForeignKey("trained_models.model_version"), nullable=False)
    fraud_probability = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    is_fraud = Column(Boolean, nullable=False, index=True)
    prediction_timestamp = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="prediction")
    model = relationship("TrainedModel", back_populates="predictions")
    alert = relationship("Alert", uselist=False, back_populates="prediction", cascade="all, delete-orphan")

class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("predictions.prediction_id", ondelete="CASCADE"), nullable=False, unique=True)
    alert_status = Column(String(20), default="NEW", index=True)
    risk_tier = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    case_notes = Column(Text, nullable=True)
    resolution = Column(String(50), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    investigation_status = Column(String(20), default="NEW")

    prediction = relationship("Prediction", back_populates="alert")
    assigned_user = relationship("User", back_populates="assigned_alerts")
