import duckdb

def init_db():
    with duckdb.connect("space_traffic.db") as con:
        con.sql("CREATE TABLE IF NOT EXISTS celestrak (" \
            "OBJECT_ID VARCHAR(50), " \
            "OBJECT_NAME VARCHAR(255), " \
            "EPOCH TIMESTAMP, " \
            "MEAN_MOTION DOUBLE, " \
            "ECCENTRICITY DOUBLE, " \
            "INCLINATION DOUBLE, " \
            "RA_OF_ASC_NODE DOUBLE, " \
            "ARG_OF_PERICENTER DOUBLE, " \
            "MEAN_ANOMALY DOUBLE, " \
            "EPHEMERIS_TYPE INTEGER, " \
            "CLASSIFICATION_TYPE VARCHAR(10), " \
            "NORAD_CAT_ID INTEGER PRIMARY KEY, " \
            "ELEMENT_SET_NO INTEGER, " \
            "REV_AT_EPOCH INTEGER, " \
            "BSTAR DOUBLE, " \
            "MEAN_MOTION_DOT DOUBLE, " \
            "MEAN_MOTION_DDOT DOUBLE" \
        ")")
        con.sql("CREATE TABLE IF NOT EXISTS space_conjunctions (" \
                "split VARCHAR NOT NULL, " \
                "event_id BIGINT NOT NULL, " \
                "time_to_tca DOUBLE NOT NULL, " \
                "mission_id BIGINT, " \
                "risk DOUBLE, " \
                "max_risk_estimate DOUBLE, " \
                "max_risk_scaling DOUBLE, " \
                "miss_distance DOUBLE, " \
                "relative_speed DOUBLE, " \
                "relative_position_r DOUBLE, " \
                "relative_position_t DOUBLE, " \
                "relative_position_n DOUBLE, " \
                "relative_velocity_r DOUBLE, " \
                "relative_velocity_t DOUBLE, " \
                "relative_velocity_n DOUBLE, " \
                "t_time_lastob_start DOUBLE, " \
                "t_time_lastob_end DOUBLE, " \
                "t_recommended_od_span DOUBLE, " \
                "t_actual_od_span DOUBLE, " \
                "t_obs_available BIGINT, " \
                "t_obs_used BIGINT, " \
                "t_residuals_accepted DOUBLE, " \
                "t_weighted_rms DOUBLE, " \
                "t_rcs_estimate DOUBLE, " \
                "t_cd_area_over_mass DOUBLE, " \
                "t_cr_area_over_mass DOUBLE, " \
                "t_sedr DOUBLE, " \
                "t_j2k_sma DOUBLE, " \
                "t_j2k_ecc DOUBLE, " \
                "t_j2k_inc DOUBLE, " \
                "t_ct_r DOUBLE, " \
                "t_cn_r DOUBLE, " \
                "t_cn_t DOUBLE, " \
                "t_crdot_r DOUBLE, " \
                "t_crdot_t DOUBLE, " \
                "t_crdot_n DOUBLE, " \
                "t_ctdot_r DOUBLE, " \
                "t_ctdot_t DOUBLE, " \
                "t_ctdot_n DOUBLE, " \
                "t_ctdot_rdot DOUBLE, " \
                "t_cndot_r DOUBLE, " \
                "t_cndot_t DOUBLE, " \
                "t_cndot_n DOUBLE, " \
                "t_cndot_rdot DOUBLE, " \
                "t_cndot_tdot DOUBLE, " \
                "c_object_type VARCHAR, " \
                "c_time_lastob_start DOUBLE, " \
                "c_time_lastob_end DOUBLE, " \
                "c_recommended_od_span DOUBLE, " \
                "c_actual_od_span DOUBLE, " \
                "c_obs_available BIGINT, " \
                "c_obs_used BIGINT, " \
                "c_residuals_accepted DOUBLE, " \
                "c_weighted_rms DOUBLE, " \
                "c_rcs_estimate DOUBLE, " \
                "c_cd_area_over_mass DOUBLE, " \
                "c_cr_area_over_mass DOUBLE, " \
                "c_sedr DOUBLE, " \
                "c_j2k_sma DOUBLE, " \
                "c_j2k_ecc DOUBLE, " \
                "c_j2k_inc DOUBLE, " \
                "c_ct_r DOUBLE, " \
                "c_cn_r DOUBLE, " \
                "c_cn_t DOUBLE, " \
                "c_crdot_r DOUBLE, " \
                "c_crdot_t DOUBLE, " \
                "c_crdot_n DOUBLE, " \
                "c_ctdot_r DOUBLE, " \
                "c_ctdot_t DOUBLE, " \
                "c_ctdot_n DOUBLE, " \
                "c_ctdot_rdot DOUBLE, " \
                "c_cndot_r DOUBLE, " \
                "c_cndot_t DOUBLE, " \
                "c_cndot_n DOUBLE, " \
                "c_cndot_rdot DOUBLE, " \
                "c_cndot_tdot DOUBLE, " \
                "t_span DOUBLE, " \
                "c_span DOUBLE, " \
                "t_h_apo DOUBLE, " \
                "t_h_per DOUBLE, " \
                "c_h_apo DOUBLE, " \
                "c_h_per DOUBLE, " \
                "geocentric_latitude DOUBLE, " \
                "azimuth DOUBLE, " \
                "elevation DOUBLE, " \
                "mahalanobis_distance DOUBLE, " \
                "t_position_covariance_det DOUBLE, " \
                "c_position_covariance_det DOUBLE, " \
                "t_sigma_r DOUBLE, " \
                "c_sigma_r DOUBLE, " \
                "t_sigma_t DOUBLE, " \
                "c_sigma_t DOUBLE, " \
                "t_sigma_n DOUBLE, " \
                "c_sigma_n DOUBLE, " \
                "t_sigma_rdot DOUBLE, " \
                "c_sigma_rdot DOUBLE, " \
                "t_sigma_tdot DOUBLE, " \
                "c_sigma_tdot DOUBLE, " \
                "t_sigma_ndot DOUBLE, " \
                "c_sigma_ndot DOUBLE, " \
                "F10 DOUBLE, " \
                "F3M DOUBLE, " \
                "SSN DOUBLE, " \
                "AP DOUBLE, " \
                "PRIMARY KEY (event_id, time_to_tca, split)"
        ")")

if __name__ == "__main__":
    init_db()

