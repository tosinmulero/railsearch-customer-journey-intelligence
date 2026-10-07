CREATE OR REPLACE TABLE analytics.kpi_summary AS

WITH session_conversion AS (

    SELECT
        AVG(session_booked) * 100.0
            AS session_conversion_rate_pct

    FROM (
        SELECT
            session_id,
            MAX(booked_flag) AS session_booked
        FROM analytics.search_funnel
        GROUP BY session_id
    )
)

SELECT
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

    ROUND(SUM(revenue), 2) AS total_revenue,

    ROUND(
        AVG(revenue)
        FILTER (WHERE booked_flag = 1),
        2
    ) AS average_order_value,

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
        * SUM(booked_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS search_to_book_conversion_pct,

    ROUND(
        (
            SELECT
                session_conversion_rate_pct
            FROM session_conversion
        ),
        2
    ) AS session_conversion_rate_pct

FROM analytics.search_funnel;
