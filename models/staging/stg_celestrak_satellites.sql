{{ config(materialized = 'view') }}

select
    norad_cat_id,
    object_id as international_designator,
    object_name,
    classification_type,
    epoch as epoch_timestamp,
    rev_at_epoch as revolution_number_at_epoch,
    element_set_no as element_set_number,
    ephemeris_type,
    inclination as inclination_deg,
    eccentricity as orbit_eccentricity,
    ra_of_asc_node as right_ascension_ascending_node_deg,
    arg_of_pericenter as argument_of_pericenter_deg,
    mean_anomaly as mean_anomaly_deg,
    mean_motion as mean_motion_revs_per_day,
    bstar as bstar_drag_term,
    mean_motion_dot as mean_motion_first_derivative,
    mean_motion_ddot as mean_motion_second_derivative
from {{ source('raw_space_traffic', 'celestrak') }}