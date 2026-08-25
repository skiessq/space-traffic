import duckdb
import joblib
import pandas as pd
from datetime import datetime, timezone

import os
from pathlib import Path

DEFAULT_DB_PATH = os.fspath(Path(__file__).resolve().parent.parent / "space_traffic.db")
DEFAULT_MODEL_PATH = os.fspath(Path(__file__).resolve().parent.parent / "models" / "lgbm_conjunction_model.pkl")

def run_scoring_pipeline(db_path: str = DEFAULT_DB_PATH, model_path: str = DEFAULT_MODEL_PATH) -> dict:
    artifact = joblib.load(model_path)
    model = artifact["model"]
    feature_names = artifact["feature_names"]
    threshold = artifact["optimal_threshold"]

    with duckdb.connect(db_path) as con:
        df = con.execute("SELECT * FROM mart_conjunction_features WHERE dataset_split = 'test'").df()

        if df.empty:
            return {
                "events_scored": 0,
                "critical_risk_predictions": 0
            }

        probabilities = model.predict_proba(df[feature_names])[:, 1]

        scored_df = pd.DataFrame({
            "event_id": df["event_id"],
            "mission_id": df["mission_id"],
            "time_to_tca_days": df["time_to_tca_days"],
            "miss_distance": df["miss_distance"],
            "collision_risk_prob": probabilities,
            "is_critical_risk_predicted": (probabilities >= threshold).astype(int),
            "scored_at": datetime.now(timezone.utc)
        })

        con.execute("TRUNCATE TABLE cdm_risk_evaluations")
        con.execute("INSERT INTO cdm_risk_evaluations SELECT * FROM scored_df")

        critical_count = int((scored_df["is_critical_risk_predicted"] == 1).sum())

    return {
        "events_scored": len(scored_df),
        "critical_risk_predictions": critical_count
    }


if __name__ == "__main__":
    metrics = run_scoring_pipeline()
    print(metrics)