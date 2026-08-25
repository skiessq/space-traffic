{{ config(materialized='table') }}

select 
    t.norad_cat_id as target_norad_id,
    t.object_name as target_name,
    t.inclination_deg as target_inc,
    t.orbit_eccentricity as target_ecc,
    t.right_ascension_ascending_node_deg as target_raan,
    t.argument_of_pericenter_deg as target_argp,
    t.mean_anomaly_deg as target_ma,
    t.mean_motion_revs_per_day as target_mm,
    t.bstar_drag_term as target_bstar,
    t.semi_major_axis_km as target_sma,
    t.perigee_altitude_km as target_perigee,
    t.apogee_altitude_km as target_apogee,
    c.norad_cat_id as chaser_norad_id,
    c.object_name as chaser_name,
    c.inclination_deg as chaser_inc,
    c.orbit_eccentricity as chaser_ecc,
    c.right_ascension_ascending_node_deg as chaser_raan,
    c.argument_of_pericenter_deg as chaser_argp,
    c.mean_anomaly_deg as chaser_ma,
    c.mean_motion_revs_per_day as chaser_mm,
    c.bstar_drag_term as chaser_bstar,
    c.semi_major_axis_km as chaser_sma,
    c.perigee_altitude_km as chaser_perigee,
    c.apogee_altitude_km as chaser_apogee,
    abs(t.perigee_altitude_km - c.perigee_altitude_km) as delta_perigee_km
from {{ ref('int_celestrak_satellites') }} t
join {{ ref('int_celestrak_satellites') }} c on t.norad_cat_id < c.norad_cat_id
and c.perigee_altitude_km <= t.apogee_altitude_km + 25.0
and c.apogee_altitude_km >= t.perigee_altitude_km - 25.0