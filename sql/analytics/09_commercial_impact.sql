CREATE OR REPLACE TABLE analytics.commercial_impact AS

WITH average_value AS (

    SELECT
        AVG(total_revenue) AS avg_order_value

    FROM staging.bookings
),

issue_counts AS (

    SELECT
        'Zero-result searches' AS issue_type,
        SUM(zero_results_flag) AS affected_searches
    FROM analytics.search_funnel

    UNION ALL

    SELECT
        'Checkout errors',
        SUM(checkout_error_flag)
    FROM analytics.search_funnel

    UNION ALL

    SELECT
        'Payment failures',
        SUM(payment_failure_flag)
    FROM analytics.search_funnel

    UNION ALL

    SELECT
        'Checkout abandonment',
        SUM(checkout_abandoned_flag)
    FROM analytics.search_funnel
)

SELECT
    issue_type,

    affected_searches,

    ROUND(
        avg_order_value,
        2
    ) AS benchmark_avg_order_value,

    ROUND(
        affected_searches * avg_order_value,
        2
    ) AS estimated_revenue_at_risk

FROM issue_counts

CROSS JOIN average_value

ORDER BY estimated_revenue_at_risk DESC;
