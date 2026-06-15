import os
import sys
import time
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings
from src.ml.mock_generator import generate_mock_data

def run_training_pipeline():
    print("Starting Machine Learning Training Pipeline...")
    
    # 1. Load data
    data_path = settings.KAGGLE_DATASET_PATH
    if not data_path.exists():
        print(f"Kaggle dataset not found at {data_path}.")
        print("Generating 100,000 synthetic transactions for training...")
        df = generate_mock_data(n_samples=100000, fraud_ratio=0.002, random_state=settings.RANDOM_STATE)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(data_path, index=False)
        print("Mock dataset generated successfully.")
    else:
        print(f"Loading Kaggle dataset from {data_path}...")
        df = pd.read_csv(data_path)
    
    print(f"Dataset Shape: {df.shape}")
    print(f"Class Distribution: {df['Class'].value_counts().to_dict()}")
    fraud_pct = df['Class'].mean() * 100
    print(f"Fraud Percentage: {fraud_pct:.3f}%")
    
    # 2. Train-Test Split (Stratified)
    X = df[settings.ALL_FEATURES]
    y = df["Class"]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=settings.TEST_SIZE, 
        random_state=settings.RANDOM_STATE, 
        stratify=y
    )
    
    print(f"Training set size: {X_train.shape[0]} samples")
    print(f"Testing set size: {X_test.shape[0]} samples")
    
    # 3. Scaling Time & Amount
    # Note: V1-V28 PCA features are already scaled/centered in the Kaggle dataset.
    # Time and Amount are not. We scale them using standard scaler.
    print("Scaling features (Time and Amount)...")
    scaler = StandardScaler()
    
    # We fit the scaler on X_train's Time and Amount features, then transform both
    features_to_scale = ["Time", "Amount"]
    
    # To keep original dataframe structure, we scale into new variables
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    
    X_train_scaled[features_to_scale] = scaler.fit_transform(X_train[features_to_scale])
    X_test_scaled[features_to_scale] = scaler.transform(X_test[features_to_scale])
    
    # 4. Save processed data for evaluation
    processed_dir = settings.DATA_PROCESSED_DIR
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save test set features and label for evaluate.py
    X_test_scaled.to_csv(processed_dir / "X_test_scaled.csv", index=False)
    y_test.to_csv(processed_dir / "y_test.csv", index=False)
    print(f"Saved test splits to {processed_dir}")
    
    # 5. Train XGBoost Model
    print("Training XGBoost Classifier...")
    # Calculate scale_pos_weight to handle extreme class imbalance
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / pos_count
    print(f"Imbalance ratio (scale_pos_weight): {scale_pos_weight:.2f}")
    
    model = XGBClassifier(
        max_depth=6,
        learning_rate=0.1,
        n_estimators=100,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=settings.RANDOM_STATE,
        eval_metric="logloss",
        use_label_encoder=False
    )
    
    start_time = time.time()
    model.fit(X_train_scaled, y_train)
    elapsed = time.time() - start_time
    print(f"Model training complete in {elapsed:.2f} seconds.")
    
    # 6. Save Model and Scaler
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(model, settings.MODEL_PATH)
    joblib.dump(scaler, settings.SCALER_PATH)
    
    print(f"Model binary saved to {settings.MODEL_PATH}")
    print(f"Scaler binary saved to {settings.SCALER_PATH}")
    print("Training Pipeline Successfully Completed!")

if __name__ == "__main__":
    run_training_pipeline()
