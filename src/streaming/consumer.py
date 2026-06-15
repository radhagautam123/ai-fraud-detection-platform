import os
import sys
import json
import asyncio
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from kafka import KafkaConsumer
from sqlalchemy.future import select

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings
from src.common.database import async_session, init_db
from src.common.models import Transaction, Prediction, Alert, TrainedModel, ModelMetric
from src.common.utils import calculate_risk_score, get_risk_tier, explain_transaction

# Retrieve optimal threshold from centralized settings configuration
MODEL_THRESHOLD = settings.MODEL_THRESHOLD

def load_ml_assets():
    if not settings.MODEL_PATH.exists() or not settings.SCALER_PATH.exists():
        print("ML Model or Scaler binaries not found. Please run training first.")
        sys.exit(1)
    model = joblib.load(settings.MODEL_PATH)
    scaler = joblib.load(settings.SCALER_PATH)
    print("ML model and scaler loaded successfully.")
    return model, scaler

async def register_model_metadata(model, scaler):
    async with async_session() as session:
        version = "v1.0.0"
        result = await session.execute(
            select(TrainedModel).filter(TrainedModel.model_version == version)
        )
        existing_model = result.scalars().first()
        
        if not existing_model:
            print("Registering model metadata in PostgreSQL...")
            new_model = TrainedModel(
                model_version=version,
                algorithm="XGBoost",
                auc_roc=0.9758,
                f1_score=0.8556,
                model_binary_path=str(settings.MODEL_PATH)
            )
            session.add(new_model)
            
            metrics = [
                ModelMetric(model_version=version, metric_name="F1_SCORE", metric_value=0.8556),
                ModelMetric(model_version=version, metric_name="PRECISION", metric_value=0.8989),
                ModelMetric(model_version=version, metric_name="RECALL", metric_value=0.8163),
                ModelMetric(model_version=version, metric_name="ROC_AUC", metric_value=0.9758),
                ModelMetric(model_version=version, metric_name="AVERAGE_PRECISION", metric_value=0.8629)
            ]
            session.add_all(metrics)
            await session.commit()
            print("Model metadata registered successfully.")

async def process_transaction(msg_value, model, scaler):
    tx_id = msg_value["transaction_id"]
    timestamp_str = msg_value["timestamp"]
    card_holder = msg_value["card_holder_id"]
    amount = msg_value["amount"]
    merchant = msg_value["merchant"]
    category = msg_value["category"]
    raw_time = msg_value["Time"]
    v_features = msg_value["features"]
    
    scale_df = pd.DataFrame([[raw_time, amount]], columns=["Time", "Amount"])
    scaled_vals = scaler.transform(scale_df)[0]
    scaled_time = scaled_vals[0]
    scaled_amount = scaled_vals[1]
    
    feature_vector = [scaled_time] + v_features + [scaled_amount]
    X_inference = np.array([feature_vector])
    
    prob = float(model.predict_proba(X_inference)[0, 1])
    is_fraud = prob >= MODEL_THRESHOLD
    risk_score = calculate_risk_score(prob)
    risk_tier = get_risk_tier(risk_score)
    
    async with async_session() as session:
        db_tx = Transaction(
            transaction_id=tx_id,
            timestamp=pd.to_datetime(timestamp_str),
            card_holder_id=card_holder,
            amount=amount,
            merchant=merchant,
            category=category,
            **{f"v{i+1}": v_features[i] for i in range(28)}
        )
        session.add(db_tx)
        
        db_pred = Prediction(
            transaction_id=tx_id,
            model_version="v1.0.0",
            fraud_probability=prob,
            risk_score=risk_score,
            is_fraud=is_fraud
        )
        session.add(db_pred)
        
        db_alert = None
        if risk_score >= 70:
            db_alert = Alert(
                risk_tier=risk_tier,
                alert_status="UNRESOLVED"
            )
            db_pred.alert = db_alert
            
        await session.commit()
        
    print(f"Processed Tx: {tx_id} | Amount: ${amount:.2f} | Merchant: {merchant} | Fraud Prob: {prob:.4f} | Risk: {risk_score} ({risk_tier})")
    if db_alert:
        print(f"⚠️  ALERT CREATED: High-risk transaction detected! Tier: {risk_tier}")

async def start_consumer(model, scaler):
    print("Connecting to Redpanda consumer...")
    try:
        consumer = KafkaConsumer(
            "transactions",
            bootstrap_servers=["localhost:9092"],
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            auto_offset_reset="latest",
            group_id="fraud-detector-group"
        )
        print("Consumer connected to Redpanda broker. Listening for events...")
    except Exception as e:
        print(f"Failed to connect to Redpanda broker: {e}")
        sys.exit(1)
        
    while True:
        try:
            msg_pack = consumer.poll(timeout_ms=100)
            for topic_partition, messages in msg_pack.items():
                for message in messages:
                    await process_transaction(message.value, model, scaler)
            await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error processing streaming message: {e}")
            await asyncio.sleep(1)

async def main():
    model, scaler = load_ml_assets()
    await init_db()
    await register_model_metadata(model, scaler)
    await start_consumer(model, scaler)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nConsumer service stopped by user.")
        sys.exit(0)
