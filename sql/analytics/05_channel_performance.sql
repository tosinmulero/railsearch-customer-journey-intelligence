CREATE OR REPLACE TABLE analytics.channel_performance AS

SELECT
    acquisition_channel,

    COUNT(*) AS searches,

    COUNT(DISTINCT session_id) AS sessions,

    SUM(booked_flag) AS bookings,

    ROUND(SUM(revenue), 2) AS revenue,

    ROUND(
        100.0
        * SUM(booked_flag)
        / NULLIF(COUNT(*), 0),
        2
    ) AS conversion_rate_pct,

    ROUND(
        SUM(revenue)
        / NULLIF(COUNT(DISTINCT session_id), 0),
        2
    ) AS revenue_per_session

FROM analytics.search_funnel

GROUP BY acquisition_channel

ORDER BY revenue DESC;
