CREATE OR REPLACE TABLE product.daily_anomaly_alerts AS

WITH historical AS (

    SELECT
        *,

        COUNT(*) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS baseline_days,

        AVG(search_to_book_conversion_pct) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS conversion_avg_28d,

        STDDEV_SAMP(search_to_book_conversion_pct) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS conversion_sd_28d,

        AVG(zero_result_rate_pct) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS zero_result_avg_28d,

        STDDEV_SAMP(zero_result_rate_pct) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS zero_result_sd_28d,

        AVG(checkout_error_rate_pct) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS checkout_error_avg_28d,

        STDDEV_SAMP(checkout_error_rate_pct) OVER (
            ORDER BY metric_date
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS checkout_error_sd_28d

    FROM analytics.daily_funnel
),

scored AS (

    SELECT
        *,

        CASE
            WHEN conversion_sd_28d > 0
            THEN (
                search_to_book_conversion_pct
                - conversion_avg_28d
            ) / conversion_sd_28d
        END AS conversion_zscore,

        CASE
            WHEN zero_result_sd_28d > 0
            THEN (
                zero_result_rate_pct
                - zero_result_avg_28d
            ) / zero_result_sd_28d
        END AS zero_result_zscore,

        CASE
            WHEN checkout_error_sd_28d > 0
            THEN (
                checkout_error_rate_pct
                - checkout_error_avg_28d
            ) / checkout_error_sd_28d
        END AS checkout_error_zscore

    FROM historical
)

SELECT
    *,

    CASE
        WHEN baseline_days >= 14
            AND (
                conversion_zscore <= -2.5
                OR zero_result_zscore >= 2.5
                OR checkout_error_zscore >= 2.5
            )
        THEN 1
        ELSE 0
    END AS alert_flag,

    concat_ws(
        '; ',

        CASE
            WHEN conversion_zscore <= -2.5
            THEN 'Conversion decline'
        END,

        CASE
            WHEN zero_result_zscore >= 2.5
            THEN 'Zero-result spike'
        END,

        CASE
            WHEN checkout_error_zscore >= 2.5
            THEN 'Checkout-error spike'
        END

    ) AS alert_reason

FROM scored

ORDER BY metric_date;
