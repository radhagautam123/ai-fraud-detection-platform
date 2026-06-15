from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Numeric, DateTime, Boolean, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class TrainedModel(Base):
    __tablename__ = "trained_models"
    
    model_version = Column(String(20), primary_key=True)
    algorithm = Column(String(50), nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow)
    auc_roc = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    model_binary_path = Column(String(255), nullable=False)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="model")
    metrics = relationship("ModelMetric", back_populates="model", cascade="all, delete-orphan")

class ModelMetric(Base):
    __tablename__ = "model_metrics"
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    model_version = Column(String(20), ForeignKey("trained_models.model_version", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(50), nullable=False)  # 'F1_SCORE', 'PRECISION', 'RECALL', 'ROC_AUC', etc.
    metric_value = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    model = relationship("TrainedModel", back_populates="metrics")

class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String(50), primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    card_holder_id = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    merchant = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    
    # V1-V28 PCA features
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
    
    # Relationships
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
    
    # Relationships
    transaction = relationship("Transaction", back_populates="prediction")
    model = relationship("TrainedModel", back_populates="predictions")
    alert = relationship("Alert", uselist=False, back_populates="prediction", cascade="all, delete-orphan")

class Alert(Base):
    __tablename__ = "alerts"
    
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("predictions.prediction_id", ondelete="CASCADE"), nullable=False, unique=True)
    alert_status = Column(String(20), default="UNRESOLVED", index=True) # UNRESOLVED, INVESTIGATING, RESOLVED
    risk_tier = Column(String(10), nullable=False) # HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prediction = relationship("Prediction", back_populates="alert")
