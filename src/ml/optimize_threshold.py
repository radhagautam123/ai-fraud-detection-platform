import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import precision_recall_curve, f1_score, precision_score, recall_score

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings

def optimize_threshold():
    processed_dir = settings.DATA_PROCESSED_DIR
    x_test_path = processed_dir / "X_test_scaled.csv"
    y_test_path = processed_dir / "y_test.csv"
    
    if not x_test_path.exists() or not y_test_path.exists():
        print("Error: Processed test data not found.")
        sys.exit(1)
        
    X_test = pd.read_csv(x_test_path)
    y_test = pd.read_csv(y_test_path).squeeze()
    
    if not settings.MODEL_PATH.exists():
        print("Error: Model not found.")
        sys.exit(1)
        
    model = joblib.load(settings.MODEL_PATH)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # 1. Find optimal threshold by iterating over fine grid
    thresholds = np.arange(0.01, 1.0, 0.01)
    best_threshold = 0.5
    best_f1 = 0.0
    best_precision = 0.0
    best_recall = 0.0
    
    print("Threshold Optimization Scan:")
    print(f"{'Threshold':<12} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 50)
    
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # Show key points in stdout
        if int(round(t * 100)) % 10 == 0 or t in [0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5, 0.7, 0.9]:
            print(f"{t:<12.2f} | {precision:<10.4f} | {recall:<10.4f} | {f1:<10.4f}")
            
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = t
            best_precision = precision
            best_recall = recall
            
    print("-" * 50)
    print("OPTIMIZATION RESULT:")
    print(f"  Recommended Optimal Threshold: {best_threshold:.2f}")
    print(f"  Max F1-Score:                  {best_f1:.4f}")
    print(f"  Corresponding Precision:       {best_precision:.4f}")
    print(f"  Corresponding Recall:          {best_recall:.4f}")
    
    # Check default 0.5 threshold for comparison
    y_pred_50 = (y_prob >= 0.5).astype(int)
    f1_50 = f1_score(y_test, y_pred_50, zero_division=0)
    print(f"  Default (0.50) F1-Score:       {f1_50:.4f}")

if __name__ == "__main__":
    optimize_threshold()
