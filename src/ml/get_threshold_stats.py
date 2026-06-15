import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score

def get_stats():
    model_path = Path("models/fraud_model.pkl")
    x_test_path = Path("data/processed/X_test_scaled.csv")
    y_test_path = Path("data/processed/y_test.csv")
    
    X_test = pd.read_csv(x_test_path)
    y_test = pd.read_csv(y_test_path).squeeze()
    model = joblib.load(model_path)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Grid search
    thresholds = np.arange(0.01, 1.0, 0.01)
    
    best_f1_t = 0.5
    best_f1 = 0.0
    
    best_rec_t = 0.5
    best_rec_val = 0.0
    
    # We want to find best recall while precision >= 0.70
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # Track max F1
        if f1 > best_f1:
            best_f1 = f1
            best_f1_t = t
            
        # Track best recall with precision >= 0.70
        if precision >= 0.70:
            if recall > best_rec_val:
                best_rec_val = recall
                best_rec_t = t
                
    # Function to print stats for a threshold
    def print_metrics(name, t):
        y_pred = (y_prob >= t).astype(int)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        print(f"\nConfiguration: {name}")
        print(f"  Threshold:       {t:.2f}")
        print(f"  Precision:       {precision:.4f}")
        print(f"  Recall:          {recall:.4f}")
        print(f"  F1 Score:        {f1:.4f}")
        print(f"  False Positives: {fp}")
        print(f"  False Negatives: {fn}")
        print(f"  True Positives:  {tp}")
        print(f"  True Negatives:  {tn}")
        
    print_metrics("Best F1-Score Threshold", best_f1_t)
    print_metrics("Best Recall Threshold (Precision >= 0.70)", best_rec_t)

if __name__ == "__main__":
    get_stats()
