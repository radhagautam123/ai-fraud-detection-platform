import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ----------------------------------
# Page Configuration
# ----------------------------------

st.set_page_config(
    page_title="AI Fraud Detection Dashboard",
    page_icon="🚨",
    layout="wide"
)

# Auto refresh every 5 seconds
st_autorefresh(
    interval=5000,
    key="dashboard_refresh"
)

# ----------------------------------
# Dashboard Title
# ----------------------------------

st.title("🚨 AI-Powered Real-Time Credit Card Fraud Detection")

# ----------------------------------
# KPI Metrics
# ----------------------------------

try:
    metrics = requests.get(
        "http://127.0.0.1:8000/metrics"
    ).json()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Transactions",
        metrics["total_transactions"]
    )

    col2.metric(
        "Predictions",
        metrics["total_predictions"]
    )

    col3.metric(
        "Alerts",
        metrics["total_alerts"]
    )

    col4.metric(
        "Fraud Predictions",
        metrics["fraud_predictions"]
    )

    col5.metric(
        "Avg Risk Score",
        metrics["avg_risk_score"]
    )

except Exception as e:
    st.error(f"Metrics API Error: {e}")

# ----------------------------------
# Recent Alerts
# ----------------------------------

st.divider()

st.subheader("🚨 Recent Alerts")

try:

    alerts = requests.get(
        "http://127.0.0.1:8000/alerts"
    ).json()

    if alerts:
        st.dataframe(
            pd.DataFrame(alerts),
            use_container_width=True
        )
    else:
        st.info("No alerts found.")

except Exception as e:
    st.error(f"Alerts API Error: {e}")

# ----------------------------------
# Risk Distribution Chart
# ----------------------------------

st.divider()

st.subheader("📊 Risk Distribution")

try:

    risk_data = requests.get(
        "http://127.0.0.1:8000/risk-distribution"
    ).json()

    if risk_data:

        df_risk = pd.DataFrame(
            list(risk_data.items()),
            columns=["Risk Tier", "Count"]
        )

        fig = px.bar(
            df_risk,
            x="Risk Tier",
            y="Count",
            title="Fraud Alert Distribution"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        st.info("No risk data available.")

except Exception as e:
    st.error(f"Risk Distribution API Error: {e}")

# ----------------------------------
# Recent Transactions
# ----------------------------------

st.divider()

st.subheader("💳 Recent Transactions")

try:

    txs = requests.get(
        "http://127.0.0.1:8000/transactions"
    ).json()

    if txs:
        st.dataframe(
            pd.DataFrame(txs),
            use_container_width=True
        )
    else:
        st.info("No transactions found.")

except Exception as e:
    st.error(f"Transactions API Error: {e}")

# ----------------------------------
# Model Information
# ----------------------------------

st.divider()

st.subheader("🧠 Model Information")

try:

    model = requests.get(
        "http://127.0.0.1:8000/model-info"
    ).json()

    if model:

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Version",
            model.get("version", "N/A")
        )

        col2.metric(
            "Algorithm",
            model.get("algorithm", "N/A")
        )

        col3.metric(
            "ROC-AUC",
            round(float(model.get("auc_roc", 0)), 4)
        )

        col4.metric(
            "F1 Score",
            round(float(model.get("f1_score", 0)), 4)
        )

    else:
        st.warning("Model information unavailable.")

except Exception as e:
    st.error(f"Model API Error: {e}")