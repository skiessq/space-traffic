import duckdb
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from sgp4.api import Satrec, WGS72

CANDIDATES_LIMIT = 2000
SCREENING_HORIZON_DAYS = 3.0
TIME_STEP_MINUTES = 10.0
CRITICAL_DISTANCE_METERS = 50000.0

def load_candidate_pairs(db_path, limit = CANDIDATES_LIMIT):
    with duckdb.connect(db_path) as con:
        df = con.sql(f"SELECT * FROM mart_conjunction_candidates LIMIT {limit}").df()
    return df

def init_satrec(norad_id, epoch_val, inc_deg, ecc, raan_deg, argp_deg, ma_deg, mm_rev_day, bstar):
    sat = Satrec()
    epoch_dt = pd.to_datetime(epoch_val, utc=True)
    epoch_jd = 2440587.5 + (epoch_dt.timestamp() / 86400.0)
    epoch_sgp4 = epoch_jd - 2433281.5

    sat.sgp4init(
        WGS72,
        'i',
        int(norad_id),
        epoch_sgp4,
        float(bstar),
        0.0,
        0.0,
        float(ecc),
        np.radians(float(argp_deg)),
        np.radians(float(inc_deg)),
        np.radians(float(ma_deg)),
        float(mm_rev_day) * 2.0 * np.pi / 1440.0,
        np.radians(float(raan_deg))
    )
    return sat


def propagate_pair(row: pd.Series, start_time: datetime, duration_days: float, step_minutes: float):
    sat_t = init_satrec(
        row["target_norad_id"], row["target_epoch"], row["target_inc"], 
        row["target_ecc"], row["target_raan"], row["target_argp"], 
        row["target_ma"], row["target_mm"], row["target_bstar"]
    )
    sat_c = init_satrec(
        row["chaser_norad_id"], row["chaser_epoch"], row["chaser_inc"], 
        row["chaser_ecc"], row["chaser_raan"], row["chaser_argp"], 
        row["chaser_ma"], row["chaser_mm"], row["chaser_bstar"]
    )

    total_steps = int((duration_days * 1440.0) / step_minutes)
    min_dist_m = float("inf")
    tca_rel_speed = 0.0
    tca_time_days = 0.0
    tca_timestamp = None

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
                tca_timestamp = t

    return min_dist_m, tca_rel_speed, tca_time_days, tca_timestamp


def save_alerts_to_db(alerts_df, db_path):
    with duckdb.connect(db_path) as con:
        con.execute("INSERT INTO screener_conjunction_alerts SELECT * FROM alerts_df")

def run_screening_pipeline(db_path: str = "space_traffic.db") -> dict:
    pairs_df = load_candidate_pairs(db_path)
    start_time = datetime.now(timezone.utc)
    encounters = []

    for _, row in pairs_df.iterrows():
        miss_dist_m, rel_speed_mps, tca_days, tca_dt = propagate_pair(
            row, start_time, SCREENING_HORIZON_DAYS, TIME_STEP_MINUTES
        )

        if miss_dist_m <= CRITICAL_DISTANCE_METERS:
            encounters.append({
                "target_norad_id": int(row["target_norad_id"]),
                "target_name": row["target_name"],
                "chaser_norad_id": int(row["chaser_norad_id"]),
                "chaser_name": row["chaser_name"],
                "miss_distance_meters": round(miss_dist_m, 2),
                "relative_speed_mps": round(rel_speed_mps, 2),
                "time_to_tca_days": round(tca_days, 4),
                "tca_estimated_at": tca_dt,
                "screened_at": start_time
            })

    if encounters:
        alerts_df = pd.DataFrame(encounters)
        save_alerts_to_db(alerts_df, db_path)

    return {
        "candidate_pairs_screened": len(pairs_df),
        "critical_encounters_flagged": len(encounters)
    }

if __name__ == "__main__":
    metrics = run_screening_pipeline()
    print(metrics)