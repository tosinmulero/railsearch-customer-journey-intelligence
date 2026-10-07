CREATE OR REPLACE TABLE staging.checkout AS

SELECT
    CAST(checkout_id AS VARCHAR) AS checkout_id,
    CAST(session_id AS VARCHAR) AS session_id,
    CAST(search_id AS VARCHAR) AS search_id,
    CAST(checkout_started_at AS TIMESTAMP) AS checkout_started_at,
    CAST(checkout_started_at AS DATE) AS checkout_date,
    CAST(device_type AS VARCHAR) AS device_type,
    CAST(payment_method AS VARCHAR) AS payment_method,
    CAST(checkout_error_flag AS INTEGER) AS checkout_error_flag,
    CAST(error_type AS VARCHAR) AS error_type,
    CAST(payment_failure_flag AS INTEGER) AS payment_failure_flag,
    CAST(checkout_completed_flag AS INTEGER)
        AS checkout_completed_flag

FROM raw.checkout;
