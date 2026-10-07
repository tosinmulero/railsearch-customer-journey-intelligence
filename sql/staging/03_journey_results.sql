CREATE OR REPLACE TABLE staging.journey_results AS

SELECT
    CAST(result_id AS VARCHAR) AS result_id,
    CAST(search_id AS VARCHAR) AS search_id,
    CAST(operator AS VARCHAR) AS operator,
    CAST(departure_time AS TIMESTAMP) AS departure_time,
    CAST(arrival_time AS TIMESTAMP) AS arrival_time,
    CAST(duration_minutes AS INTEGER) AS duration_minutes,
    CAST(changes AS INTEGER) AS changes,
    CAST(fare AS DOUBLE) AS fare,
    CAST(fare_type AS VARCHAR) AS fare_type,
    CAST(result_position AS INTEGER) AS result_position,
    CAST(selected_flag AS INTEGER) AS selected_flag

FROM raw.journey_results;
