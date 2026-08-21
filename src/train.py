import duckdb
import os
import joblib
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import brier_score_loss, classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split

DB_PATH = "space_traffic.db"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "lgbm_conjunction_model.pkl")

DROP_COLUMNS = [
    "event_id",
    "mission_id",
    "dataset_split",
    "chaser_object_type",
    "risk",
    "is_current_critical_risk",
    "max_risk_estimate",
    "max_risk_scaling",
]
TARGET_COL = "is_current_critical_risk"

def load_dataset(db_path):
    with duckdb.connect(db_path) as con:
        print("Loading database")
        df = con.sql(f"select * from mart_conjunction_features").df()
    return df

def prepare_splits(df):
    train_df = df["dataset_split"] == "train"
    test_df = df["dataset_split"] == "test"

    feature_cols = [col for col in df.columns if col not in DROP_COLUMNS]

    X_train_full, y_train_full = df.loc[train_df, feature_cols], df.loc[train_df, TARGET_COL]
    X_test, y_test = df.loc[test_df, feature_cols], df.loc[test_df, TARGET_COL]

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full,
        y_train_full,
        test_size=0.15,
        stratify=y_train_full,
        random_state=42,
    )

    return X_train, y_train, X_val, y_val, X_test, y_test, feature_cols

def train_model():
    df = load_dataset(DB_PATH)

    X_train, y_train, X_val, y_val, X_test, y_test, feature_cols = prepare_splits(df)

    negative_count = (y_train == 0).sum()
    positive_count = (y_train == 1).sum()
    scale_pos_weight = negative_count / max(positive_count, 1)

    model = lgb.LGBMClassifier(
        n_estimators=1000,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        importance_type="gain",
        verbose=-1,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric=["auc", "binary_logloss"],
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)],
    )

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
    print(f"Brier Score:   {brier_score_loss(y_test, y_pred_proba):.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": model, "feature_names": feature_cols}, MODEL_PATH)
    print(f"\nModel artifact saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()