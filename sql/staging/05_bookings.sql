CREATE OR REPLACE TABLE staging.bookings AS

SELECT
    CAST(booking_id AS VARCHAR) AS booking_id,
    CAST(session_id AS VARCHAR) AS session_id,
    CAST(search_id AS VARCHAR) AS search_id,
    CAST(checkout_id AS VARCHAR) AS checkout_id,
    CAST(booked_at AS TIMESTAMP) AS booked_at,
    CAST(booked_at AS DATE) AS booking_date,
    CAST(ticket_value AS DOUBLE) AS ticket_value,
    CAST(booking_fee AS DOUBLE) AS booking_fee,
    CAST(total_revenue AS DOUBLE) AS total_revenue,
    CAST(passengers AS INTEGER) AS passengers,
    CAST(operator AS VARCHAR) AS operator,
    CAST(origin_station AS VARCHAR) AS origin_station,
    CAST(destination_station AS VARCHAR) AS destination_station

FROM raw.bookings;
