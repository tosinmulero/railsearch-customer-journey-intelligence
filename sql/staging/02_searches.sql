CREATE OR REPLACE TABLE staging.searches AS

SELECT
    CAST(search_id AS VARCHAR) AS search_id,
    CAST(session_id AS VARCHAR) AS session_id,
    CAST(searched_at AS TIMESTAMP) AS searched_at,
    CAST(searched_at AS DATE) AS search_date,
    CAST(
        EXTRACT(hour FROM searched_at)
        AS INTEGER
    ) AS search_hour,

    CAST(origin_station AS VARCHAR) AS origin_station,
    CAST(destination_station AS VARCHAR) AS destination_station,

    origin_station
        || ' → '
        || destination_station
        AS route,

    CAST(travel_date AS DATE) AS travel_date,

    datediff(
        'day',
        CAST(searched_at AS DATE),
        CAST(travel_date AS DATE)
    ) AS days_before_travel,

    CAST(passengers AS INTEGER) AS passengers,
    CAST(journey_type AS VARCHAR) AS journey_type,
    CAST(railcard_used AS INTEGER) AS railcard_used,
    CAST(results_count AS INTEGER) AS results_count,
    CAST(search_latency_ms AS INTEGER) AS search_latency_ms,
    CAST(zero_results_flag AS INTEGER) AS zero_results_flag

FROM raw.searches;
