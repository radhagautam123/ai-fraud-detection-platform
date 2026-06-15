import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import settings

def calculate_risk_score(probability: float) -> int:
    """
    Translates raw model probability into a 0-100 scale integer risk score.
    """
    # Bound probability
    probability = max(0.0, min(1.0, float(probability)))
    return int(round(probability * 100))

def get_risk_tier(risk_score: int) -> str:
    """
    Categorizes the risk score into standard risk tiers.
    """
    if risk_score <= settings.RISK_LOW_MAX:
        return "LOW"
    elif risk_score <= settings.RISK_MEDIUM_MAX:
        return "MEDIUM"
    elif risk_score <= settings.RISK_HIGH_MAX:
        return "HIGH"
    else:
        return "CRITICAL"

def explain_transaction(transaction_data: dict, top_n: int = 3) -> list:
    """
    Provides a lightweight explanation of why a transaction might be flagged as anomalous
    by analyzing feature deviations from normal behaviour (mean=0, std=1 for PCA V-features).
    """
    deviations = []
    
    # Analyze V1-V28 PCA features
    for v_feat in settings.PCA_FEATURES:
        if v_feat in transaction_data:
            val = float(transaction_data[v_feat])
            # Since normal transactions have PCA features centered at 0 with std=1,
            # we can use the absolute value as a measure of deviation.
            abs_dev = abs(val)
            if abs_dev > 1.5:  # threshold for noteworthy deviation
                deviations.append((v_feat, val, abs_dev))
                
    # Also check Amount relative to standard amounts
    if "Amount" in transaction_data:
        amount = float(transaction_data["Amount"])
        # Standard average transaction is ~$88 in the Kaggle dataset
        # If amount is very large, flag it
        if amount > 500.0:
            deviations.append(("Amount", amount, amount / 500.0))
            
    # Sort deviations in descending order of significance
    deviations.sort(key=lambda x: x[2], reverse=True)
    
    # Format explanations
    explanations = []
    for feat, val, dev in deviations[:top_n]:
        if feat == "Amount":
            explanations.append(f"Transaction amount is exceptionally high: ${val:.2f}")
        else:
            direction = "negative" if val < 0 else "positive"
            explanations.append(f"Feature {feat} shows extreme {direction} deviation ({val:.2f}) from normal patterns")
            
    if not explanations:
        explanations.append("All features lie within typical normal ranges.")
        
    return explanations
