CREATE OR REPLACE TABLE analytics.checkout_failure_analysis AS

SELECT
    device_type,
    payment_method,
    COALESCE(error_type, 'None') AS error_type,

    COUNT(*) AS checkout_attempts,

    SUM(checkout_error_flag) AS checkout_errors,

    SUM(payment_failure_flag) AS payment_failures,

    SUM(checkout_abandoned_flag) AS checkout_abandonments,

    SUM(booked_flag) AS bookings,

    ROUND(
        100.0
        * SUM(checkout_error_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS checkout_error_rate_pct,

    ROUND(
        100.0
        * SUM(payment_failure_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS payment_failure_rate_pct,

    ROUND(
        100.0
        * SUM(booked_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS checkout_to_booking_rate_pct

FROM analytics.search_funnel

WHERE checkout_started_flag = 1

GROUP BY
    device_type,
    payment_method,
    COALESCE(error_type, 'None')

ORDER BY checkout_attempts DESC;
