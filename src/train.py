import duckdb
import os
import joblib
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import average_precision_score, classification_report, confusion_matrix, f1_score, fbeta_score, precision_recall_curve
from sklearn.model_selection import GroupShuffleSplit


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
        df = con.sql(f"select * from mart_conjunction_features").df()
    return df

def prepare_splits(df):
    train_df = (df["dataset_split"] == "train") & (df["time_to_tca_days"] > 2.0)
    test_df = df["dataset_split"] == "test"

    feature_cols = [col for col in df.columns 
                    if col not in DROP_COLUMNS
                    and not col.startswith("chaser_corr_") 
                    and not col.startswith("target_corr_")]

    X_train_full = df.loc[train_df, feature_cols].reset_index(drop=True)
    y_train_full = df.loc[train_df, TARGET_COL].reset_index(drop=True)
    groups = df.loc[train_df, "event_id"].reset_index(drop=True)

    X_test = df.loc[test_df, feature_cols].reset_index(drop=True)
    y_test = df.loc[test_df, TARGET_COL].reset_index(drop=True)

    gss = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
    train_idx, val_idx = next(gss.split(X_train_full, y_train_full, groups=groups))

    X_train, y_train = X_train_full.iloc[train_idx], y_train_full.iloc[train_idx]
    X_val, y_val = X_train_full.iloc[val_idx], y_train_full.iloc[val_idx]

    return X_train, y_train, X_val, y_val, X_test, y_test, feature_cols

def find_best_threshold(y_true, val_probs, target_recall=0.85):
    precisions, recalls, thresholds = precision_recall_curve(y_true, val_probs)
    
    valid_indices = np.where(recalls[:-1] >= target_recall)[0]
    if len(valid_indices) == 0:
        return thresholds[0], 0.0
    
    best_idx = valid_indices[np.argmax(precisions[valid_indices])]
    return thresholds[best_idx], precisions[best_idx]

def train_model():
    df = load_dataset("space_traffic.db")

    X_train, y_train, X_val, y_val, X_test, y_test, feature_cols = prepare_splits(df)

    negative_count = (y_train == 0).sum()
    positive_count = (y_train == 1).sum()
    scale_pos_weight = np.sqrt(negative_count / max(positive_count, 1))

    model = lgb.LGBMClassifier(
        n_estimators=1500,
        learning_rate=0.02,
        num_leaves=63,
        max_depth=8,
        feature_fraction=0.8,
        bagging_fraction=0.8,
        bagging_freq=1,
        min_data_in_leaf=50,
        verbose=-1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        reg_alpha=0.5,
        reg_lambda=2.0
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="average_precision",
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
    )

    val_probs = model.predict_proba(X_val)[:, 1]
    test_probs = model.predict_proba(X_test)[:, 1]
    best_threshold, best_val_f1 = find_best_threshold(y_val, val_probs)
    y_pred = (test_probs >= best_threshold).astype(int)

    print(f"Average Precision Score: {average_precision_score(y_test, test_probs):.4f}")
    print(f"Best Threshold: {best_threshold:.4f}")
    print(f"Best F-beta Score: {best_val_f1:.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": model, "feature_names": feature_cols, "optimal_threshold": best_threshold}, MODEL_PATH)
    print(f"\nModel artifact saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()