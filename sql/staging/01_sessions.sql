CREATE OR REPLACE TABLE staging.sessions AS

SELECT
    CAST(session_id AS VARCHAR) AS session_id,
    CAST(customer_id AS VARCHAR) AS customer_id,
    CAST(session_started_at AS TIMESTAMP) AS session_started_at,
    CAST(session_started_at AS DATE) AS session_date,
    CAST(
        EXTRACT(hour FROM session_started_at)
        AS INTEGER
    ) AS session_hour,
    CAST(device_type AS VARCHAR) AS device_type,
    CAST(operating_system AS VARCHAR) AS operating_system,
    CAST(acquisition_channel AS VARCHAR) AS acquisition_channel,
    CAST(customer_type AS VARCHAR) AS customer_type,
    CAST(country AS VARCHAR) AS country,
    CAST(is_logged_in AS INTEGER) AS is_logged_in
FROM raw.sessions;
