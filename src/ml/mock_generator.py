import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add root folder to path to import settings
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings

def generate_mock_data(n_samples: int = 50000, fraud_ratio: float = 0.002, random_state: int = 42) -> pd.DataFrame:
    """
    Generates synthetic transaction data matching the Kaggle credit card dataset schema.
    Schema: Time, V1-V28, Amount, Class.
    """
    np.random.seed(random_state)
    
    # Calculate sample counts
    n_fraud = int(n_samples * fraud_ratio)
    n_legit = n_samples - n_fraud
    
    if n_fraud < 1:
        n_fraud = 1
        n_legit = n_samples - 1
    
    # Time feature: sequence of seconds
    time_legit = np.sort(np.random.uniform(0, 172800, n_legit))  # 2 days of transactions
    time_fraud = np.sort(np.random.uniform(0, 172800, n_fraud))
    
    # Amount feature: Log-normal distribution
    # Normal transactions: average around $40-$80
    amount_legit = np.random.lognormal(mean=3.5, sigma=1.0, size=n_legit)
    # Fraud transactions: larger amount spread, often higher
    amount_fraud = np.random.lognormal(mean=5.0, sigma=1.2, size=n_fraud)
    
    # V1-V28 PCA features: Normal distribution N(0, 1) for normal
    v_legit = np.random.normal(loc=0.0, scale=1.0, size=(n_legit, 28))
    
    # Fraud has shifted distributions on key predictive components
    # (In Kaggle dataset, V3, V4, V10, V11, V12, V14, V17 are highly predictive)
    v_fraud = np.random.normal(loc=0.0, scale=1.0, size=(n_fraud, 28))
    
    # Shift some features to make them distinguishable
    v_fraud[:, 2] = np.random.normal(loc=-3.0, scale=1.5, size=n_fraud)  # V3
    v_fraud[:, 3] = np.random.normal(loc=2.5, scale=1.0, size=n_fraud)   # V4
    v_fraud[:, 9] = np.random.normal(loc=-2.8, scale=1.5, size=n_fraud)  # V10
    v_fraud[:, 10] = np.random.normal(loc=2.2, scale=1.2, size=n_fraud)  # V11
    v_fraud[:, 11] = np.random.normal(loc=-3.5, scale=1.5, size=n_fraud) # V12
    v_fraud[:, 13] = np.random.normal(loc=-4.0, scale=1.8, size=n_fraud) # V14
    v_fraud[:, 16] = np.random.normal(loc=-3.8, scale=1.6, size=n_fraud) # V17
    
    # Create DataFrames
    df_legit = pd.DataFrame(v_legit, columns=[f"V{i}" for i in range(1, 29)])
    df_legit["Time"] = time_legit
    df_legit["Amount"] = amount_legit
    df_legit["Class"] = 0
    
    df_fraud = pd.DataFrame(v_fraud, columns=[f"V{i}" for i in range(1, 29)])
    df_fraud["Time"] = time_fraud
    df_fraud["Amount"] = amount_fraud
    df_fraud["Class"] = 1
    
    # Combine and shuffle
    df = pd.concat([df_legit, df_fraud], ignore_index=True)
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    
    # Rearrange columns to match standard schema: Time, V1..V28, Amount, Class
    cols = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
    df = df[cols]
    
    return df

def save_mock_dataset(df: pd.DataFrame, dest_path: Path):
    """Saves the generated mock dataset to CSV."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest_path, index=False)
    print(f"Generated and saved {len(df)} transactions ({df['Class'].sum()} fraud, {df['Class'].mean()*100:.3f}%) to {dest_path}")

if __name__ == "__main__":
    df = generate_mock_data(n_samples=100000, fraud_ratio=0.002, random_state=42)
    save_mock_dataset(df, settings.KAGGLE_DATASET_PATH)
