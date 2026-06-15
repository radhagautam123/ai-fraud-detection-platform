import os
import sys
import joblib
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Set non-interactive backend for server running
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_curve,
    auc,
    precision_recall_curve,
    average_precision_score
)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings

def run_evaluation_pipeline():
    print("Starting Machine Learning Evaluation Pipeline...")
    
    # 1. Load test data
    processed_dir = settings.DATA_PROCESSED_DIR
    x_test_path = processed_dir / "X_test_scaled.csv"
    y_test_path = processed_dir / "y_test.csv"
    
    if not x_test_path.exists() or not y_test_path.exists():
        print(f"Error: Processed test data not found in {processed_dir}.")
        print("Please run train.py first to create the data splits.")
        sys.exit(1)
        
    X_test = pd.read_csv(x_test_path)
    y_test = pd.read_csv(y_test_path).squeeze()
    
    # 2. Load model
    if not settings.MODEL_PATH.exists():
        print(f"Error: Trained model binary not found at {settings.MODEL_PATH}.")
        print("Please run train.py first to train the model.")
        sys.exit(1)
        
    model = joblib.load(settings.MODEL_PATH)
    print("Loaded trained model successfully.")
    
    # 3. Perform Predictions
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= settings.MODEL_THRESHOLD).astype(int)
    
    # 4. Generate Classification Reports & Metrics
    print("\n" + "="*40)
    print("EVALUATION METRICS REPORT")
    print("="*40)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Confusion Matrix values
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"Confusion Matrix:")
    print(f"  True Negatives (Legitimate Correct): {tn}")
    print(f"  False Positives (Legitimate Flagged): {fp}")
    print(f"  False Negatives (Fraud Missed): {fn}")
    print(f"  True Positives (Fraud Flagged): {tp}")
    
    # ROC-AUC and Average Precision
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    ap = average_precision_score(y_test, y_prob)
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    print(f"Average Precision (PR-AUC) Score: {ap:.4f}")
    print("="*40 + "\n")
    
    # Ensure figures output directory exists
    figures_dir = settings.FIGURES_DIR
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # 5. Plot 1: Confusion Matrix Heatmap
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                xticklabels=["Legitimate", "Fraud"],
                yticklabels=["Legitimate", "Fraud"])
    plt.title("Confusion Matrix Heatmap")
    plt.ylabel("Actual Label")
    plt.xlabel("Predicted Label")
    plt.tight_layout()
    cm_plot_path = figures_dir / "confusion_matrix.png"
    plt.savefig(cm_plot_path, dpi=300)
    plt.close()
    print(f"Saved Confusion Matrix Heatmap to: {cm_plot_path}")
    
    # 6. Plot 2: ROC Curve
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC Curve (AUC = {roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate (FPR)")
    plt.ylabel("True Positive Rate (TPR)")
    plt.title("Receiver Operating Characteristic (ROC) Curve")
    plt.legend(loc="lower right")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    roc_plot_path = figures_dir / "roc_curve.png"
    plt.savefig(roc_plot_path, dpi=300)
    plt.close()
    print(f"Saved ROC Curve Plot to: {roc_plot_path}")
    
    # 7. Plot 3: Precision-Recall Curve
    precision, recall, _ = precision_recall_curve(y_test, y_prob)
    plt.figure(figsize=(6, 5))
    plt.plot(recall, precision, color="forestgreen", lw=2, label=f"PR Curve (AP = {ap:.4f})")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall (PR) Curve")
    plt.legend(loc="lower left")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    pr_plot_path = figures_dir / "precision_recall_curve.png"
    plt.savefig(pr_plot_path, dpi=300)
    plt.close()
    print(f"Saved Precision-Recall Curve Plot to: {pr_plot_path}")
    
    # 8. Plot 4: Feature Importance Plot
    # XGBoost uses the model's feature_importances_
    importances = model.feature_importances_
    features = X_test.columns
    df_imp = pd.DataFrame({"Feature": features, "Importance": importances})
    df_imp = df_imp.sort_values(by="Importance", ascending=False).head(15)  # top 15 features
    
    plt.figure(figsize=(8, 6))
    sns.barplot(x="Importance", y="Feature", data=df_imp, hue="Feature", legend=False, palette="viridis")
    plt.title("Top 15 Feature Importances (XGBoost)")
    plt.xlabel("Relative Importance Score")
    plt.ylabel("Feature Name")
    plt.tight_layout()
    fi_plot_path = figures_dir / "feature_importance.png"
    plt.savefig(fi_plot_path, dpi=300)
    plt.close()
    print(f"Saved Feature Importance Plot to: {fi_plot_path}")
    print("Evaluation Pipeline Successfully Completed!")

if __name__ == "__main__":
    run_evaluation_pipeline()
