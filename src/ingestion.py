import csv
import duckdb
import requests
import json
import os
import time

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = os.fspath(PROJECT_ROOT / "dataset" / "celestrak_cache" / "celestrak_data.json")
CACHE_TTL_SECONDS = 7200

def is_cache_expired(file_path, ttl_seconds):
    if not os.path.exists(file_path):
        return True
    
    file_age_seconds = time.time() - os.path.getmtime(file_path)
    return file_age_seconds > ttl_seconds

def download_celestrak_data(group: str = "active"):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    if not is_cache_expired(CACHE_FILE, CACHE_TTL_SECONDS):
        return True

    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=JSON"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(CACHE_FILE, "w") as f:
            json.dump(response.json(), f)
        return True
    return False

def ingest_api_data(con):
    if download_celestrak_data() and os.path.exists(CACHE_FILE):
        con.execute(f"INSERT INTO celestrak SELECT * FROM read_json_auto('{CACHE_FILE}') ON CONFLICT (NORAD_CAT_ID) DO NOTHING")

def ingest_csv_data(con):
    train_csv = os.fspath(PROJECT_ROOT / "dataset" / "train_data.csv").replace("\\", "/")
    test_csv = os.fspath(PROJECT_ROOT / "dataset" / "test_data.csv").replace("\\", "/")

    if os.path.exists(train_csv):
        con.execute(f"insert into space_conjunctions select 'train' as split,* from read_csv_auto('{train_csv}') on conflict (event_id, time_to_tca, split) do nothing")

    if os.path.exists(test_csv):
        con.execute(f"insert into space_conjunctions select 'test' as split,* from read_csv_auto('{test_csv}') on conflict (event_id, time_to_tca, split) do nothing")

def run_ingestion(db_path: str = "space_traffic.db") -> dict:
    with duckdb.connect(db_path) as con:
        ingest_csv_data(con)
        ingest_api_data(con)

        celestrak_count = con.execute("select count(*) from celestrak").fetchone()[0]
        cdm_count = con.execute("select count(*) from space_conjunctions").fetchone()[0]

    return {
        "celestrak_satellites_total": int(celestrak_count),
        "esa_cdms_total": int(cdm_count)
    }

if __name__ == "__main__":
    metrics = run_ingestion()