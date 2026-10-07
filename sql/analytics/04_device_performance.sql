CREATE OR REPLACE TABLE analytics.device_performance AS

SELECT
    device_type,

    COUNT(*) AS searches,

    COUNT(DISTINCT session_id) AS sessions,

    SUM(zero_results_flag) AS zero_result_searches,

    SUM(checkout_started_flag) AS checkout_attempts,

    SUM(checkout_error_flag) AS checkout_errors,

    SUM(payment_failure_flag) AS payment_failures,

    SUM(booked_flag) AS bookings,

    ROUND(SUM(revenue), 2) AS revenue,

    ROUND(
        100.0
        * SUM(booked_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS conversion_rate_pct,

    ROUND(
        100.0
        * SUM(checkout_error_flag)
        / NULLIF(SUM(checkout_started_flag), 0),
        2
    ) AS checkout_error_rate_pct

FROM analytics.search_funnel

GROUP BY device_type

ORDER BY searches DESC;
