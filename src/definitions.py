import os
import duckdb
import joblib
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from dagster import asset, multi_asset, AssetOut, AssetKey, Definitions, AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets
from database import init_db
from screen_conjunctions import run_screening_pipeline
from score_cdms import run_scoring_pipeline
from ingestion import run_ingestion
from train import train_model

DBT_PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.fspath(DBT_PROJECT_DIR / "space_traffic.db")
MODEL_PATH = os.fspath(DBT_PROJECT_DIR / "models" / "lgbm_conjunction_model.pkl")

dbt_resource = DbtCliResource(project_dir=os.fspath(DBT_PROJECT_DIR))

dbt_manifest_path = (dbt_resource.cli(["--quiet", "parse"]).wait().target_path.joinpath("manifest.json"))

@asset
def raw_database_schema():
    init_db(DB_PATH)
    return True

@multi_asset(
    outs={
        "celestrak": AssetOut(key=AssetKey(["raw_space_traffic", "celestrak"])),
        "space_conjunctions": AssetOut(key=AssetKey(["raw_space_traffic", "space_conjunctions"])),
    },
    deps=[raw_database_schema],
)
def data_ingestion(context: AssetExecutionContext):
    metrics = run_ingestion(DB_PATH)
    context.add_output_metadata(
        {"celestrak_satellites_total": metrics["celestrak_satellites_total"]},
        output_name="celestrak",
    )
    context.add_output_metadata(
        {"esa_cdms_total": metrics["esa_cdms_total"]},
        output_name="space_conjunctions",
    )
    return None, None

@dbt_assets(manifest=dbt_manifest_path)
def run_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()

@asset(deps=[run_dbt_assets])
def screener_conjunction_alerts(context: AssetExecutionContext):
    metrics = run_screening_pipeline(DB_PATH)
    context.add_output_metadata(metrics)
    return metrics["critical_encounters_flagged"]

@asset(deps=[run_dbt_assets])
def conjunction_ml_model(context: AssetExecutionContext):
    metrics = train_model(DB_PATH, MODEL_PATH)
    context.add_output_metadata(metrics)
    return MODEL_PATH

@asset(deps=[conjunction_ml_model])
def cdm_risk_evaluations(context: AssetExecutionContext):
    metrics = run_scoring_pipeline(DB_PATH, MODEL_PATH)
    context.add_output_metadata(metrics)
    return metrics["critical_risk_predictions"]

defs = Definitions(
    assets=[
        raw_database_schema,
        data_ingestion,
        run_dbt_assets,
        screener_conjunction_alerts,
        conjunction_ml_model,
        cdm_risk_evaluations,
    ],
    resources={"dbt": dbt_resource},
)