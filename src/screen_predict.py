import duckdb
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from sgp4.api import Satrec, WGS72

artifact = joblib.load("./models/lgbm_conjunction_model.pkl")
model = artifact["model"]
features = artifact["feature_names"]
threshold = artifact["optimal_threshold"]

def load_candidate_pairs(db_path):
    with duckdb.connect(db_path) as con:
        df = con.sql(f"select * from mart_conjunction_candidates").df()
    return df

def init_satrec(inc_deg, ecc, raan_deg, argp_deg, ma_deg, mm_rev_day, bstar):
    sat = Satrec()
    sat.sgp4init(
        WGS72, 'i', 0, 0.0, bstar, 0.0, 0.0,
        ecc,
        np.radians(argp_deg),
        np.radians(inc_deg),
        np.radians(ma_deg),
        mm_rev_day * 2.0 * np.pi / 1440.0,
        np.radians(raan_deg)
    )
    return sat

def propagate_pair(row, start_time, duration_days=3.0, step_minutes=10.0):
    sat_t = init_satrec(row["target_inc"], row["target_ecc"], row["target_raan"], 
                       row["target_argp"], row["target_ma"], row["target_mm"], row["target_bstar"])
    sat_c = init_satrec(row["chaser_inc"], row["chaser_ecc"], row["chaser_raan"], 
                       row["chaser_argp"], row["chaser_ma"], row["chaser_mm"], row["chaser_bstar"])

    total_steps = int((duration_days * 1440.0) / step_minutes)
    min_dist_m = float("inf")
    tca_rel_speed = 0.0
    tca_time_days = 0.0

    for step in range(total_steps):
        t = start_time + timedelta(minutes=step * step_minutes)
        jd = 2440587.5 + (t.replace(tzinfo=timezone.utc).timestamp() / 86400.0)
        err_t, r_t, v_t = sat_t.sgp4(jd, 0.0)
        err_c, r_c, v_c = sat_c.sgp4(jd, 0.0)

        if err_t == 0 and err_c == 0:
            dist_m = np.linalg.norm(np.array(r_t) - np.array(r_c)) * 1000.0
            if dist_m < min_dist_m:
                min_dist_m = dist_m
                tca_rel_speed = np.linalg.norm(np.array(v_t) - np.array(v_c)) * 1000.0
                tca_time_days = (step * step_minutes) / 1440.0

    return min_dist_m, tca_rel_speed, tca_time_days

def run_screening_pipeline():
    print("Fetching candidate pairs from DuckDB...")
    pairs_df = load_candidate_pairs("space_traffic.db")
    print(f"Propagating {len(pairs_df)} candidate pairs with SGP4...")

    start_time = datetime.now(timezone.utc)
    encounters = []

    for _, row in pairs_df.iterrows():
        miss_dist_m, rel_speed_mps, tca_days = propagate_pair(row, start_time)

        if miss_dist_m <= 50000.0 and tca_days >= 2.0:
            pos_sigma = 500.0
            encounters.append({
                "target_norad_id": row["target_norad_id"],
                "target_name": row["target_name"],
                "chaser_norad_id": row["chaser_norad_id"],
                "chaser_name": row["chaser_name"],
                "miss_distance": miss_dist_m,
                "relative_speed": rel_speed_mps,
                "time_to_tca_days": tca_days,
                "combined_pos_sigma": pos_sigma,
                "miss_to_sigma_ratio": miss_dist_m / pos_sigma,
                "collision_span_to_miss_ratio": 10.0 / (miss_dist_m + 1e-3),
                "log_mahalanobis": np.log10(max(miss_dist_m / pos_sigma, 1e-6)),
                "log_target_pos_det": 8.0,
                "log_chaser_pos_det": 8.0,
                "is_chaser_payload": 1,
                "is_chaser_debris": 0,
                "is_chaser_unknown": 0,
            })

    if not encounters:
        print("No close conjunctions (< 50 km) detected in this screening window.")
        return

    eval_df = pd.DataFrame(encounters)

    probabilities = model.predict_proba(eval_df[features])[:, 1]
    eval_df["collision_risk_prob"] = probabilities
    eval_df["alert_triggered"] = (probabilities >= threshold).astype(int)

    alerts = eval_df[eval_df["alert_triggered"] == 1]
    print(f"Total pairs evaluated: {len(pairs_df)}")
    print(f"Close encounters (< 50 km): {len(eval_df)}")
    print(f"Critical risk alerts flagged: {len(alerts)} (Threshold >= {threshold:.4f})")

    if len(alerts) > 0:
        display_cols = ["target_name", "chaser_name", "miss_distance", "time_to_tca_days", "collision_risk_prob"]
        print("\nActive Critical Alerts:")
        print(alerts[display_cols].to_string(index=False))

if __name__ == "__main__":
    run_screening_pipeline()