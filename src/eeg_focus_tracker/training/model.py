"""
Train the final focus-classification model.

Based on findings from notebooks/03_modeling.ipynb:
- LightGBM outperformed SVM and Random Forest under LOSO CV
- Excluding noisy sessions (4, 7, 8) improved generalization
- Feature selection did not improve performance — all 25 features are used

This script trains LightGBM with the best hyperparameters found via Optuna
on the clean dataset, then fits a final model on ALL clean sessions
(no held-out test set) for deployment.
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = PROJECT_ROOT / "data" / "processed_by_session" / "all_sessions_normalized.csv"
MODEL_DIR = PROJECT_ROOT / "models"

EXCLUDED_SESSIONS = [4, 7, 8]  # see notebooks/02_exploratory.ipynb for criteria

# Best hyperparameters found via Optuna in 03_modeling.ipynb
BEST_PARAMS = {
    "n_estimators": 164,
    "max_depth": 3,
    "learning_rate": 0.010711863369746433,
    "num_leaves": 129,
    "min_child_samples": 98,
    "subsample": 0.8890783754749252,
    "colsample_bytree": 0.9350060741234096
}


def load_clean_data():
    df = pd.read_csv(DATA_PATH)
    df_clean = df[~df['session'].isin(EXCLUDED_SESSIONS)]
    return df_clean


def train_final_model():
    df_clean = load_clean_data()
    feature_cols = [c for c in df_clean.columns if c not in ['label', 'session']]

    X = df_clean[feature_cols].values
    y = df_clean['label'].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LGBMClassifier(**BEST_PARAMS, verbose=-1, random_state=42)
    model.fit(X_scaled, y)

    return model, scaler, feature_cols


def save_artifacts(model, scaler, feature_cols):
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_DIR / "focus_model.pkl")
    joblib.dump(scaler, MODEL_DIR / "scaler.pkl")
    joblib.dump(feature_cols, MODEL_DIR / "feature_names.pkl")
    print(f"Saved model artifacts to {MODEL_DIR}")


if __name__ == "__main__":
    model, scaler, feature_cols = train_final_model()
    save_artifacts(model, scaler, feature_cols)