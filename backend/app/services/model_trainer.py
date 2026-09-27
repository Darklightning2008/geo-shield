import os
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from app.config import settings
from app.services.risk_engine import risk_engine
from app.schemas import ModelRetrainRequest, ModelRetrainResponse

class ModelTrainerService:
    """
    Model Retraining and Synthetic Calibration Service.
    Generates realistic environmental-landslide associations and trains LightGBM classifiers.
    Permits continuous fine-tuning and parameter adjustments.
    """

    @staticmethod
    def retrain(params: ModelRetrainRequest) -> ModelRetrainResponse:
        np.random.seed(params.random_state)
        n = params.n_samples

        # 1. Plausible environmental ranges for mountainous terrain
        rainfall_24h = np.random.uniform(0, 300, n)
        rainfall_72h = rainfall_24h + np.random.uniform(0, 200, n)
        soil_moisture = np.random.uniform(0, 100, n)
        slope = np.random.uniform(0, 60, n)
        elevation = np.random.uniform(100, 3000, n)
        historical_count = np.random.poisson(3, n)

        # 2. Physics-inspired underlying true risk function
        true_risk = (
            0.35 * (rainfall_24h / 300.0)
            + 0.15 * (rainfall_72h / 500.0)
            + 0.20 * (soil_moisture / 100.0)
            + 0.20 * (slope / 60.0)
            + 0.10 * (historical_count / 10.0)
        )

        # Realistic stochastic noise
        noise = np.random.normal(0, 0.08, n)
        true_risk_noisy = np.clip(true_risk + noise, 0, 1)

        # 22% positive class ratio (reflecting rare natural disaster occurrence)
        threshold = np.percentile(true_risk_noisy, 78)
        landslide_occurred = (true_risk_noisy > threshold).astype(int)

        data = pd.DataFrame({
            "rainfall_24h": rainfall_24h,
            "rainfall_72h": rainfall_72h,
            "soil_moisture": soil_moisture,
            "slope": slope,
            "elevation": elevation,
            "historical_landslide_count": historical_count,
            "landslide_occurred": landslide_occurred,
        })

        feature_columns = [
            "rainfall_24h", "rainfall_72h", "soil_moisture",
            "slope", "elevation", "historical_landslide_count",
        ]

        X = data[feature_columns]
        y = data["landslide_occurred"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=params.random_state, stratify=y
        )

        model = LGBMClassifier(
            n_estimators=params.n_estimators,
            max_depth=params.max_depth,
            learning_rate=params.learning_rate,
            random_state=params.random_state,
            verbosity=-1
        )
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        report = classification_report(
            y_test, y_pred,
            target_names=["No landslide", "Landslide"],
            output_dict=True
        )

        # Meteorological verification metrics (POD, FAR, CSI)
        from sklearn.metrics import confusion_matrix
        from app.services.metrics_service import metrics_service
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        verification_metric = metrics_service.build_metric(
            tp=int(tp),
            fp=int(fp),
            fn=int(fn),
            tn=int(tn),
            hazard_type="landslide",
            hazard_title="Slope Landslide & Debris Flow",
            description=f"Retrained test evaluation ({len(y_test)} hold-out test samples)",
            benchmark_standard="Hold-Out Stratified Validation Set"
        )

        # Feature importances
        importances = dict(zip(feature_columns, [round(float(imp), 4) for imp in model.feature_importances_]))

        # Save to disk
        os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
        joblib.dump({"model": model, "feature_columns": feature_columns}, settings.MODEL_PATH)

        # Reload hot model into memory
        risk_engine.model = model
        risk_engine.feature_columns = feature_columns

        return ModelRetrainResponse(
            status="success",
            message=f"Model successfully retrained on {n} synthetic samples and reloaded into active memory.",
            samples_trained=n,
            classification_report=report,
            verification_metrics=verification_metric,
            feature_importance=importances,
            saved_path=str(settings.MODEL_PATH)
        )

