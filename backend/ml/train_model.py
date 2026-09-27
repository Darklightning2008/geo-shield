"""
Trains a LightGBM classifier on REAL historical landslide data:
- Positive cases: 267 real GPS landslide coordinates from the 2018 Western Ghats (Kodagu/Wayanad)
  catastrophic monsoon disaster, with actual ERA5 reanalysis rainfall & soil moisture data.
- Negative controls: Same mountain locations during dry seasons, lowland flat terrain during heavy rain,
  and moderate rain days without slope failure.

Run this script with:
    python ml/train_model.py

Outputs:
    ml/risk_model.pkl
"""

import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "real_landslide_dataset.csv"

def train():
    if not DATA_PATH.exists():
        print("Real dataset not found. Generating real historical dataset first...")
        from build_real_dataset import build_dataset
        build_dataset()

    print(f"Loading real historical landslide dataset from: {DATA_PATH} ...")
    data = pd.read_csv(DATA_PATH)
    print(f"Dataset shape: {data.shape[0]} samples with {data.shape[1]} columns.")
    print(f"Class distribution:\n{data['landslide_occurred'].value_counts()}")

    feature_columns = [
        "rainfall_24h",
        "rainfall_72h",
        "soil_moisture",
        "slope",
        "elevation",
        "historical_landslide_count"
    ]

    X = data[feature_columns]
    y = data["landslide_occurred"]

    # 80/20 Stratified Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print("\nTraining LightGBM Classifier on real historical records...")
    model = LGBMClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        num_leaves=15,
        random_state=42,
        verbosity=-1
    )

    # 5-Fold Cross Validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc")
    print(f"5-Fold Cross-Validation ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    model.fit(X_train, y_train)

    # Test set evaluation
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n=== CLASSIFICATION REPORT (TEST SET) ===")
    print(classification_report(y_test, y_pred, target_names=["No Landslide (0)", "Landslide (1)"]))

    auc = roc_auc_score(y_test, y_prob)
    print(f"Test ROC-AUC Score: {auc:.4f}")

    print("\n=== CONFUSION MATRIX ===")
    print(confusion_matrix(y_test, y_pred))

    print("\n=== FEATURE IMPORTANCE ===")
    for col, imp in sorted(zip(feature_columns, model.feature_importances_), key=lambda x: x[1], reverse=True):
        print(f"  * {col:28s}: {imp:4d}")

    # Save trained model artifact
    model_output_path = BASE_DIR / "risk_model.pkl"
    joblib.dump({"model": model, "feature_columns": feature_columns, "dataset": "real_western_ghats_2018"}, model_output_path)
    print(f"\n[SUCCESS] Saved real-data trained model artifact to: {model_output_path}")

    return model, feature_columns

if __name__ == "__main__":
    train()