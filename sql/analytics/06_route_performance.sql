CREATE OR REPLACE TABLE analytics.route_performance AS

SELECT
    route,
    origin_station,
    destination_station,

    COUNT(*) AS searches,

    SUM(zero_results_flag) AS zero_result_searches,

    SUM(booked_flag) AS bookings,

    ROUND(SUM(revenue), 2) AS revenue,

    ROUND(
        AVG(search_latency_ms),
        2
    ) AS avg_search_latency_ms,

    ROUND(
        100.0
        * SUM(zero_results_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS zero_result_rate_pct,

    ROUND(
        100.0
        * SUM(booked_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS conversion_rate_pct

FROM analytics.search_funnel

GROUP BY
    route,
    origin_station,
    destination_station

HAVING COUNT(*) >= 100

ORDER BY searches DESC;
