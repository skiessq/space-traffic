{{ config(materialized='view') }}

select
    norad_cat_id,
    international_designator,
    object_name,
    classification_type,
    epoch_timestamp,
    inclination_deg,
    orbit_eccentricity,
    right_ascension_ascending_node_deg,
    argument_of_pericenter_deg,
    mean_anomaly_deg,
    mean_motion_revs_per_day,
    bstar_drag_term,
    power(398600.4418 / power((mean_motion_revs_per_day * 2.0 * pi() / 86400.0), 2), 1.0 / 3.0) as semi_major_axis_km,
    (semi_major_axis_km * (1.0 - orbit_eccentricity)) - 6378.137 as perigee_altitude_km,
    (semi_major_axis_km * (1.0 + orbit_eccentricity)) - 6378.137 as apogee_altitude_km,
    1440.0 / nullif(mean_motion_revs_per_day, 0) as orbital_period_minutes,
    bstar_drag_term * 12.74 as ballistic_drag_proxy_sqm_per_kg
from {{ ref('stg_celestrak_satellites') }}