CREATE OR REPLACE TABLE analytics.zero_result_analysis AS

SELECT
    route,

    COUNT(*) AS searches,

    SUM(zero_results_flag) AS zero_result_searches,

    ROUND(
        100.0
        * SUM(zero_results_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS zero_result_rate_pct,

    ROUND(
        AVG(search_latency_ms),
        2
    ) AS avg_search_latency_ms,

    ROUND(
        AVG(days_before_travel),
        2
    ) AS avg_days_before_travel

FROM analytics.search_funnel

GROUP BY route

HAVING COUNT(*) >= 100

ORDER BY zero_result_rate_pct DESC;
