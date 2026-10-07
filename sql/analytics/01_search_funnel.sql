CREATE OR REPLACE TABLE analytics.search_funnel AS

WITH selected_results AS (

    SELECT
        search_id,

        MAX(selected_flag) AS selected_flag,

        MAX(
            CASE
                WHEN selected_flag = 1
                THEN result_id
            END
        ) AS selected_result_id,

        MAX(
            CASE
                WHEN selected_flag = 1
                THEN operator
            END
        ) AS selected_operator,

        MAX(
            CASE
                WHEN selected_flag = 1
                THEN fare
            END
        ) AS selected_fare,

        MAX(
            CASE
                WHEN selected_flag = 1
                THEN duration_minutes
            END
        ) AS selected_duration_minutes,

        MAX(
            CASE
                WHEN selected_flag = 1
                THEN changes
            END
        ) AS selected_changes

    FROM staging.journey_results

    GROUP BY search_id
),

checkout_summary AS (

    SELECT
        search_id,
        1 AS checkout_started_flag,
        MAX(checkout_id) AS checkout_id,
        MAX(payment_method) AS payment_method,
        MAX(checkout_error_flag) AS checkout_error_flag,
        MAX(error_type) AS error_type,
        MAX(payment_failure_flag) AS payment_failure_flag,
        MAX(checkout_completed_flag) AS checkout_completed_flag

    FROM staging.checkout

    GROUP BY search_id
),

booking_summary AS (

    SELECT
        search_id,
        1 AS booked_flag,
        MAX(booking_id) AS booking_id,
        SUM(total_revenue) AS revenue

    FROM staging.bookings

    GROUP BY search_id
)

SELECT
    q.search_id,
    q.session_id,
    s.customer_id,

    q.search_date,
    q.searched_at,
    q.search_hour,

    s.device_type,
    s.operating_system,
    s.acquisition_channel,
    s.customer_type,
    s.country,
    s.is_logged_in,

    q.origin_station,
    q.destination_station,
    q.route,
    q.travel_date,
    q.days_before_travel,

    q.passengers,
    q.journey_type,
    q.railcard_used,

    q.results_count,
    q.search_latency_ms,
    q.zero_results_flag,

    CASE
        WHEN q.results_count > 0 THEN 1
        ELSE 0
    END AS results_available_flag,

    COALESCE(r.selected_flag, 0) AS selected_flag,
    r.selected_result_id,
    r.selected_operator,
    r.selected_fare,
    r.selected_duration_minutes,
    r.selected_changes,

    COALESCE(c.checkout_started_flag, 0)
        AS checkout_started_flag,

    c.checkout_id,
    c.payment_method,

    COALESCE(c.checkout_error_flag, 0)
        AS checkout_error_flag,

    c.error_type,

    COALESCE(c.payment_failure_flag, 0)
        AS payment_failure_flag,

    COALESCE(c.checkout_completed_flag, 0)
        AS checkout_completed_flag,

    CASE
        WHEN COALESCE(c.checkout_started_flag, 0) = 1
            AND COALESCE(c.checkout_error_flag, 0) = 0
            AND COALESCE(c.payment_failure_flag, 0) = 0
            AND COALESCE(c.checkout_completed_flag, 0) = 0
        THEN 1
        ELSE 0
    END AS checkout_abandoned_flag,

    COALESCE(b.booked_flag, 0) AS booked_flag,
    b.booking_id,
    COALESCE(b.revenue, 0.0) AS revenue,

    CASE
        WHEN COALESCE(b.booked_flag, 0) = 1
            THEN 'Booked'
        WHEN COALESCE(c.checkout_started_flag, 0) = 1
            THEN 'Checkout'
        WHEN COALESCE(r.selected_flag, 0) = 1
            THEN 'Selected'
        WHEN q.results_count > 0
            THEN 'Results'
        ELSE 'Search'
    END AS furthest_funnel_stage

FROM staging.searches q

LEFT JOIN staging.sessions s
    ON q.session_id = s.session_id

LEFT JOIN selected_results r
    ON q.search_id = r.search_id

LEFT JOIN checkout_summary c
    ON q.search_id = c.search_id

LEFT JOIN booking_summary b
    ON q.search_id = b.search_id;
