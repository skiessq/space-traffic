import csv
import duckdb
import requests
import json
import os

def check_celestrak_cache_folder():
    dir_name = './dataset/celestrak_cache'
    if os.path.isdir(dir_name):
        if not os.listdir(dir_name):
            print("Directory is empty. Downloading JSON Data.")
            return True
        else:    
            print("Directory is not empty. JSON Data cached")
            return False
    else:
        os.mkdir(dir_name)
        print("Directory created. Downloading JSON Data.")
        return True
 
def download_celestrak_data(group="ACTIVE"):
    output_file = "./dataset/celestrak_cache/celestrak_data.json"
    url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=JSON"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    request = requests.get(url, headers=headers)
    if request.status_code == 200:
        with open(output_file, 'w') as f:
            json.dump(request.json(), f)
        print("Downloaded JSON data from Celestrak and saved to celestrak_data.json")
        return True

    print("Failed to download JSON data from Celestrak. Status code:", request.status_code)
    return False

def ingest_api_data(con):
    cache_file = './dataset/celestrak_cache/celestrak_data.json'

    if check_celestrak_cache_folder():
        if not download_celestrak_data():
            return
        
    con.sql(f"INSERT INTO celestrak SELECT * FROM read_json_auto('{cache_file}') ON CONFLICT (NORAD_CAT_ID) DO NOTHING")
    print("Ingested Celestrak data into the database.")

def ingest_csv_data(con):
    if not os.path.exists('./dataset/train_data.csv'):
            print("Train data CSV file not found. Please ensure the file exists at './dataset/train_data.csv'.")
            print("Links are provided in dataset/dataset.txt to download the train data.")
            return
    
    if not os.path.exists('./dataset/test_data.csv'):
        print("Test data CSV file not found. Please ensure the file exists at './dataset/test_data.csv'.")
        print("Links are provided in dataset/dataset.txt to download the test data.")
        return

    con.sql("INSERT INTO space_conjunctions SELECT 'train' AS split,* FROM read_csv_auto('./dataset/train_data.csv') ON CONFLICT (event_id, time_to_tca, split) DO NOTHING")
    print("Ingested train data into the database.")

    con.sql("INSERT INTO space_conjunctions SELECT 'test' AS split,* FROM read_csv_auto('./dataset/test_data.csv') ON CONFLICT (event_id, time_to_tca, split) DO NOTHING")
    print("Ingested test data into the database.")

def run_ingestion():
  with duckdb.connect("space_traffic.db") as con:
    ingest_csv_data(con)
    ingest_api_data(con)

if __name__ == "__main__":
    run_ingestion()