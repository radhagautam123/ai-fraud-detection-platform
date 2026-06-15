import os
import sys
import json
import time
import random
import argparse
import pandas as pd
from pathlib import Path
from kafka import KafkaProducer

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings
from src.ml.mock_generator import generate_mock_data

MERCHANTS = [
    ("Amazon", "shopping"),
    ("Walmart", "shopping"),
    ("Steam Games", "entertainment"),
    ("Netflix", "entertainment"),
    ("Apple Store", "shopping"),
    ("Chevron", "gas_station"),
    ("McDonalds", "food"),
    ("Uber", "transportation"),
    ("Delta Airlines", "travel"),
    ("Starbucks", "food")
]

def json_serializer(data):
    return json.dumps(data).encode("utf-8")

def get_metadata():
    merchant, category = random.choice(MERCHANTS)
    card_holder_id = f"usr_{random.randint(10000, 10500)}"
    return card_holder_id, merchant, category

def run_producer(source: str, rate: float):
    print(f"Starting transaction producer. Source: {source}, Rate: {rate} tx/sec...")
    
    # Initialize Kafka/Redpanda Producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=["localhost:9092"],
            value_serializer=json_serializer,
            max_block_ms=5000
        )
        print("Connected to Redpanda broker successfully.")
    except Exception as e:
        print(f"Failed to connect to Redpanda at localhost:9092: {e}")
        print("Please ensure docker containers are running.")
        sys.exit(1)
        
    # Load transactions
    if source == "kaggle":
        if not settings.KAGGLE_DATASET_PATH.exists():
            print(f"Error: Kaggle CSV not found at {settings.KAGGLE_DATASET_PATH}.")
            sys.exit(1)
        print(f"Streaming from Kaggle CSV: {settings.KAGGLE_DATASET_PATH}")
        df = pd.read_csv(settings.KAGGLE_DATASET_PATH)
    else:
        print("Generating mock transactions for streaming...")
        df = generate_mock_data(n_samples=5000, fraud_ratio=0.01) # higher fraud ratio for visual alerts in testing
        
    total_records = len(df)
    sent_count = 0
    
    # Iterate and send
    for idx, row in df.iterrows():
        # Get metadata
        card_holder_id, merchant, category = get_metadata()
        
        # Prepare payload
        transaction_id = f"tx_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        # Convert row values to list of floats for features, and isolate Amount/Time
        v_features = [float(row[f"V{i}"]) for i in range(1, 29)]
        
        payload = {
            "transaction_id": transaction_id,
            "timestamp": pd.Timestamp.now().isoformat(),
            "card_holder_id": card_holder_id,
            "amount": float(row["Amount"]),
            "merchant": merchant,
            "category": category,
            "Time": float(row["Time"]),
            "features": v_features
        }
        
        # Send
        try:
            producer.send("transactions", value=payload)
            sent_count += 1
            if sent_count % 50 == 0:
                print(f"Sent {sent_count}/{total_records} transactions...")
        except Exception as e:
            print(f"Error sending message: {e}")
            
        # Control rate
        if rate > 0:
            time.sleep(1.0 / rate)
            
    producer.flush()
    print("Producer run complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transaction Stream Producer")
    parser.add_argument("--source", type=str, default="mock", choices=["kaggle", "mock"],
                        help="Data source: kaggle or mock")
    parser.add_argument("--rate", type=float, default=1.0,
                        help="Streaming rate in messages per second")
    args = parser.parse_args()
    
    run_producer(source=args.source, rate=args.rate)
