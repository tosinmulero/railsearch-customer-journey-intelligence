CREATE OR REPLACE TABLE staging.station_reference AS

SELECT
    CAST(station_code AS VARCHAR) AS station_code,
    CAST(station_name AS VARCHAR) AS station_name,
    CAST(region AS VARCHAR) AS region,
    CAST(annual_entries_exits AS BIGINT) AS annual_entries_exits,
    CAST(interchange_volume AS BIGINT) AS interchange_volume

FROM raw.station_reference;
