# Space Traffic Management and Satellite Collision Risk Assessment

An end-to-end data engineering and machine learning system for space traffic management and satellite collision risk assessment. The project ingests orbital telemetry and Conjunction Data Messages (CDMs), models and enriches the data, propagates orbits using physical mechanics, and predicts high-risk close encounters using machine learning.

## Overview & Architecture

The pipeline processes data through five main stages:

1. **Ingestion**: Fetches active satellite Two-Line Element sets (TLEs) from CelesTrak and historical conjunction events from the European Space Agency (ESA) Collision Avoidance Challenge dataset into DuckDB.
2. **Data Modeling & Feature Engineering (dbt)**: Transforms raw telemetry into staging, intermediate, and dimensional feature marts. Models candidate conjunction pairs based on orbital geometry and constructs feature matrices covering relative positions, velocities, covariance determinants, and space weather indicators.
3. **Orbital Conjunction Screening**: Propagates satellite trajectories using the SGP4 (WGS72) analytical model to compute 3D relative distances, relative velocities, and TCA over a multi-day screening window.
4. **Collision Risk Evaluation (ML)**: Trains an imbalanced LightGBM classification model to assess collision probability from CDM parameters, precision-recall threshold optimization, and covariance matrices.
5. **Orchestration (Dagster)**: Automates the dependency graph and pipeline assets end-to-end, managing data lineage from raw feeds to final risk scores.

## Technical Highlights

- **Data Engineering**: Modern analytics stack using DuckDB for high-performance in-process querying and dbt for modular SQL transformations, data contracts, and lineage.
- **Machine Learning**: Binary classification with LightGBM, group-aware cross-validation by conjunction event, class imbalance handling, and precision-recall curve threshold tuning.
- **Pipeline Orchestration**: Asset-oriented data pipeline architecture built with Dagster and dagster-dbt.

## Technologies

- **Languages & Frameworks**: Python, SQL
- **Data Engineering**: DuckDB, dbt
- **Machine Learning**: LightGBM, Scikit-learn
- **Orchestration**: Dagster
- **Data Sources**: CelesTrak, ESA (European Space Agency)
