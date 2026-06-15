import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Project Paths
    PROJECT_NAME: str = "Fraud Detection Platform"
    
    DATA_RAW_DIR: Path = BASE_DIR / "data" / "raw"
    DATA_PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    MODELS_DIR: Path = BASE_DIR / "models"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    FIGURES_DIR: Path = BASE_DIR / "reports" / "figures"
    
    # Files
    KAGGLE_DATASET_PATH: Path = DATA_RAW_DIR / "creditcard.csv"
    MODEL_PATH: Path = MODELS_DIR / "fraud_model.pkl"
    SCALER_PATH: Path = MODELS_DIR / "scaler.pkl"
    
    # Model configuration
    RANDOM_STATE: int = 42
    TEST_SIZE: float = 0.2
    MODEL_THRESHOLD: float = 0.86  # Optimal F1 decision boundary
    
    # Risk Score thresholds
    RISK_LOW_MAX: int = 39
    RISK_MEDIUM_MAX: int = 69
    RISK_HIGH_MAX: int = 89
    
    # Features configuration
    PCA_FEATURES: list = [f"V{i}" for i in range(1, 29)]
    ALL_FEATURES: list = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/fraud_db"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
