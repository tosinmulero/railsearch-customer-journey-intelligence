CREATE OR REPLACE TABLE analytics.daily_funnel AS

SELECT
    search_date AS metric_date,

    COUNT(*) AS searches,

    COUNT(DISTINCT session_id) AS sessions,

    SUM(zero_results_flag) AS zero_result_searches,

    SUM(results_available_flag) AS searches_with_results,

    SUM(selected_flag) AS selected_searches,

    SUM(checkout_started_flag) AS checkout_attempts,

    SUM(checkout_error_flag) AS checkout_errors,

    SUM(payment_failure_flag) AS payment_failures,

    SUM(checkout_abandoned_flag) AS checkout_abandonments,

    SUM(booked_flag) AS bookings,

    ROUND(
        SUM(revenue),
        2
    ) AS revenue,

    ROUND(
        100.0
        * SUM(zero_results_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS zero_result_rate_pct,

    ROUND(
        100.0
        * SUM(selected_flag)
        / NULLIF(SUM(results_available_flag), 0),
        2
    ) AS result_selection_rate_pct,

    ROUND(
        100.0
        * SUM(checkout_error_flag)
        / NULLIF(SUM(checkout_started_flag), 0),
        2
    ) AS checkout_error_rate_pct,

    ROUND(
        100.0
        * SUM(payment_failure_flag)
        / NULLIF(SUM(checkout_started_flag), 0),
        2
    ) AS payment_failure_rate_pct,

    ROUND(
        100.0
        * SUM(booked_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS search_to_book_conversion_pct

FROM analytics.search_funnel

GROUP BY search_date

ORDER BY search_date;
