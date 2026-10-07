from __future__ import annotations

import json
import textwrap
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MART_DIR = PROCESSED_DIR / "marts"

SQL_STAGING_DIR = PROJECT_ROOT / "sql" / "staging"
SQL_ANALYTICS_DIR = PROJECT_ROOT / "sql" / "analytics"
SQL_PRODUCT_DIR = PROJECT_ROOT / "sql" / "product"

DOCS_DIR = PROJECT_ROOT / "docs"

DB_PATH = PROCESSED_DIR / "railsearch.duckdb"


def sql_path(path: Path) -> str:
    """Return a SQL-safe absolute path."""
    return path.resolve().as_posix().replace("'", "''")


def write_sql(path: Path, sql: str) -> None:
    """Write formatted SQL using UTF-8 without BOM."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(sql).strip() + "\n",
        encoding="utf-8",
    )


def validate_raw_files() -> None:
    required = [
        "sessions.parquet",
        "searches.parquet",
        "journey_results.parquet",
        "checkout.parquet",
        "bookings.parquet",
        "station_reference.parquet",
    ]

    missing = [filename for filename in required if not (RAW_DIR / filename).exists()]

    if missing:
        raise FileNotFoundError(f"Missing raw RailSearch datasets: {missing}")


def create_sql_models() -> list[Path]:
    sql_files: list[Path] = []

    # ================================================================
    # RAW EXTERNAL VIEWS
    # ================================================================

    raw_views = f"""
    CREATE OR REPLACE VIEW raw.sessions AS
    SELECT *
    FROM read_parquet('{sql_path(RAW_DIR / "sessions.parquet")}');

    CREATE OR REPLACE VIEW raw.searches AS
    SELECT *
    FROM read_parquet('{sql_path(RAW_DIR / "searches.parquet")}');

    CREATE OR REPLACE VIEW raw.journey_results AS
    SELECT *
    FROM read_parquet('{sql_path(RAW_DIR / "journey_results.parquet")}');

    CREATE OR REPLACE VIEW raw.checkout AS
    SELECT *
    FROM read_parquet('{sql_path(RAW_DIR / "checkout.parquet")}');

    CREATE OR REPLACE VIEW raw.bookings AS
    SELECT *
    FROM read_parquet('{sql_path(RAW_DIR / "bookings.parquet")}');

    CREATE OR REPLACE VIEW raw.station_reference AS
    SELECT *
    FROM read_parquet('{sql_path(RAW_DIR / "station_reference.parquet")}');
    """

    path = SQL_STAGING_DIR / "00_raw_views.sql"
    write_sql(path, raw_views)
    sql_files.append(path)

    # ================================================================
    # STAGING — SESSIONS
    # ================================================================

    path = SQL_STAGING_DIR / "01_sessions.sql"

    write_sql(
        path,
        """
        CREATE OR REPLACE TABLE staging.sessions AS

        SELECT
            CAST(session_id AS VARCHAR) AS session_id,
            CAST(customer_id AS VARCHAR) AS customer_id,
            CAST(session_started_at AS TIMESTAMP) AS session_started_at,
            CAST(session_started_at AS DATE) AS session_date,
            CAST(
                EXTRACT(hour FROM session_started_at)
                AS INTEGER
            ) AS session_hour,
            CAST(device_type AS VARCHAR) AS device_type,
            CAST(operating_system AS VARCHAR) AS operating_system,
            CAST(acquisition_channel AS VARCHAR) AS acquisition_channel,
            CAST(customer_type AS VARCHAR) AS customer_type,
            CAST(country AS VARCHAR) AS country,
            CAST(is_logged_in AS INTEGER) AS is_logged_in
        FROM raw.sessions;
        """,
    )

    sql_files.append(path)

    # ================================================================
    # STAGING — SEARCHES
    # ================================================================

    path = SQL_STAGING_DIR / "02_searches.sql"

    write_sql(
        path,
        """
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
        """,
    )

    sql_files.append(path)

    # ================================================================
    # STAGING — JOURNEY RESULTS
    # ================================================================

    path = SQL_STAGING_DIR / "03_journey_results.sql"

    write_sql(
        path,
        """
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
        """,
    )

    sql_files.append(path)

    # ================================================================
    # STAGING — CHECKOUT
    # ================================================================

    path = SQL_STAGING_DIR / "04_checkout.sql"

    write_sql(
        path,
        """
        CREATE OR REPLACE TABLE staging.checkout AS

        SELECT
            CAST(checkout_id AS VARCHAR) AS checkout_id,
            CAST(session_id AS VARCHAR) AS session_id,
            CAST(search_id AS VARCHAR) AS search_id,
            CAST(checkout_started_at AS TIMESTAMP) AS checkout_started_at,
            CAST(checkout_started_at AS DATE) AS checkout_date,
            CAST(device_type AS VARCHAR) AS device_type,
            CAST(payment_method AS VARCHAR) AS payment_method,
            CAST(checkout_error_flag AS INTEGER) AS checkout_error_flag,
            CAST(error_type AS VARCHAR) AS error_type,
            CAST(payment_failure_flag AS INTEGER) AS payment_failure_flag,
            CAST(checkout_completed_flag AS INTEGER)
                AS checkout_completed_flag

        FROM raw.checkout;
        """,
    )

    sql_files.append(path)

    # ================================================================
    # STAGING — BOOKINGS
    # ================================================================

    path = SQL_STAGING_DIR / "05_bookings.sql"

    write_sql(
        path,
        """
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
        """,
    )

    sql_files.append(path)

    # ================================================================
    # STAGING — STATIONS
    # ================================================================

    path = SQL_STAGING_DIR / "06_station_reference.sql"

    write_sql(
        path,
        """
        CREATE OR REPLACE TABLE staging.station_reference AS

        SELECT
            CAST(station_code AS VARCHAR) AS station_code,
            CAST(station_name AS VARCHAR) AS station_name,
            CAST(region AS VARCHAR) AS region,
            CAST(annual_entries_exits AS BIGINT) AS annual_entries_exits,
            CAST(interchange_volume AS BIGINT) AS interchange_volume

        FROM raw.station_reference;
        """,
    )

    sql_files.append(path)

    # ================================================================
    # SEARCH-LEVEL CUSTOMER FUNNEL
    # ================================================================

    path = SQL_ANALYTICS_DIR / "01_search_funnel.sql"

    write_sql(
        path,
        """
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
        """,
    )

    sql_files.append(path)

    # ================================================================
    # KPI SUMMARY
    # ================================================================

    path = SQL_ANALYTICS_DIR / "02_kpi_summary.sql"

    write_sql(
        path,
        """
        CREATE OR REPLACE TABLE analytics.kpi_summary AS

        WITH session_conversion AS (

            SELECT
                AVG(session_booked) * 100.0
                    AS session_conversion_rate_pct

            FROM (
                SELECT
                    session_id,
                    MAX(booked_flag) AS session_booked
                FROM analytics.search_funnel
                GROUP BY session_id
            )
        )

        SELECT
            COUNT(*) AS searches,

            COUNT(DISTINCT session_id) AS sessions,

            SUM(zero_results_flag) AS zero_result_searches,

            SUM(results_available_flag) AS searches_with_results,

            SUM(selected_flag) AS selected_searches,

            SUM(checkout_started_flag) AS checkout_attempts,

            SUM(checkout_error_flag) AS checkout_errors,

            SUM(payment_failure_flag) AS payment_failures,

            SUM(checkout_abandoned_flag) AS checkout_abandonments,

            SUM(booked_flag) AS bookings,

            ROUND(SUM(revenue), 2) AS total_revenue,

            ROUND(
                AVG(revenue)
                FILTER (WHERE booked_flag = 1),
                2
            ) AS average_order_value,

            ROUND(
                100.0
                * SUM(zero_results_flag)
                / NULLIF(COUNT(*), 0),
                2
            ) AS zero_result_rate_pct,

            ROUND(
                100.0
                * SUM(selected_flag)
                / NULLIF(SUM(results_available_flag), 0),
                2
            ) AS result_selection_rate_pct,

            ROUND(
                100.0
                * SUM(booked_flag)
                / NULLIF(COUNT(*), 0),
                2
            ) AS search_to_book_conversion_pct,

            ROUND(
                (
                    SELECT
                        session_conversion_rate_pct
                    FROM session_conversion
                ),
                2
            ) AS session_conversion_rate_pct

        FROM analytics.search_funnel;
        """,
    )

    sql_files.append(path)

    # ================================================================
    # DAILY FUNNEL
    # ================================================================

    path = SQL_ANALYTICS_DIR / "03_daily_funnel.sql"

    write_sql(
        path,
        """
        CREATE OR REPLACE TABLE analytics.daily_funnel AS

        SELECT
            search_date AS metric_date,

            COUNT(*) AS searches,

            COUNT(DISTINCT session_id) AS sessions,

            SUM(zero_results_flag) AS zero_result_searches,

            SUM(results_available_flag) AS searches_with_results,

            SUM(selected_flag) AS selected_searches,

            SUM(checkout_started_flag) AS checkout_attempts,

            SUM(checkout_error_flag) AS checkout_errors,

            SUM(payment_failure_flag) AS payment_failures,

            SUM(checkout_abandoned_flag) AS checkout_abandonments,

            SUM(booked_flag) AS bookings,

            ROUND(
                SUM(revenue),
                2
            ) AS revenue,

            ROUND(
                100.0
                * SUM(zero_results_flag)
                / NULLIF(COUNT(*), 0),
                2
            ) AS zero_result_rate_pct,

            ROUND(
                100.0
                * SUM(selected_flag)
                / NULLIF(SUM(results_available_flag), 0),
                2
            ) AS result_selection_rate_pct,

            ROUND(
                100.0
                * SUM(checkout_error_flag)
                / NULLIF(SUM(checkout_started_flag), 0),
                2
            ) AS checkout_error_rate_pct,

            ROUND(
                100.0
                * SUM(payment_failure_flag)
                / NULLIF(SUM(checkout_started_flag), 0),
                2
            ) AS payment_failure_rate_pct,

            ROUND(
                100.0
                * SUM(booked_flag)
                / NULLIF(COUNT(*), 0),
                2
            ) AS search_to_book_conversion_pct

        FROM analytics.search_funnel

        GROUP BY search_date

        ORDER BY search_date;
        """,
    )

    sql_files.append(path)

    # ================================================================
    # DEVICE PERFORMANCE
    # ================================================================

    path = SQL_ANALYTICS_DIR / "04_device_performance.sql"

    write_sql(
        path,
        """
        CREATE OR REPLACE TABLE analytics.device_performance AS

        SELECT
            device_type,

            COUNT(*) AS searches,

            COUNT(DISTINCT session_id) AS sessions,

            SUM(zero_results_flag) AS zero_result_searches,

            SUM(checkout_started_flag) AS checkout_attempts,

            SUM(checkout_error_flag) AS checkout_errors,

            SUM(payment_failure_flag) AS payment_failures,

            SUM(booked_flag) AS bookings,

            ROUND(SUM(revenue), 2) AS revenue,

            ROUND(
                100.0
                * SUM(booked_flag)
                / NULLIF(COUNT(*), 0),
                2
            ) AS conversion_rate_pct,

            ROUND(
                100.0
                * SUM(checkout_error_flag)
                / NULLIF(SUM(checkout_started_flag), 0),
                2
            ) AS checkout_error_rate_pct

        FROM analytics.search_funnel

        GROUP BY device_type

        ORDER BY searches DESC;
        """,
    )

    sql_files.append(path)

    # ================================================================
    # ACQUISITION CHANNEL
    # ================================================================

    path = SQL_ANALYTICS_DIR / "05_channel_performance.sql"

    write_sql(
        path,
        """
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
        """,
    )

    sql_files.append(path)

    # ================================================================
    # ROUTE PERFORMANCE
    # ================================================================

    path = SQL_ANALYTICS_DIR / "06_route_performance.sql"

    write_sql(
        path,
        """
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
        """,
    )

    sql_files.append(path)

    # ================================================================
    # ZERO-RESULT ROOT-CAUSE MART
    # ================================================================

    path = SQL_ANALYTICS_DIR / "07_zero_result_analysis.sql"

    write_sql(
        path,
        """
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
        """,
    )

    sql_files.append(path)

    # ================================================================
    # CHECKOUT ROOT-CAUSE MART
    # ================================================================

    path = SQL_ANALYTICS_DIR / "08_checkout_failure_analysis.sql"

    write_sql(
        path,
        """
        CREATE OR REPLACE TABLE analytics.checkout_failure_analysis AS

        SELECT
            device_type,
            payment_method,
            COALESCE(error_type, 'None') AS error_type,

            COUNT(*) AS checkout_attempts,

            SUM(checkout_error_flag) AS checkout_errors,

            SUM(payment_failure_flag) AS payment_failures,

            SUM(checkout_abandoned_flag) AS checkout_abandonments,

            SUM(booked_flag) AS bookings,

            ROUND(
                100.0
                * SUM(checkout_error_flag)
                / NULLIF(COUNT(*), 0),
                2
            ) AS checkout_error_rate_pct,

            ROUND(
                100.0
                * SUM(payment_failure_flag)
                / NULLIF(COUNT(*), 0),
                2
            ) AS payment_failure_rate_pct,

            ROUND(
                100.0
                * SUM(booked_flag)
                / NULLIF(COUNT(*), 0),
                2
            ) AS checkout_to_booking_rate_pct

        FROM analytics.search_funnel

        WHERE checkout_started_flag = 1

        GROUP BY
            device_type,
            payment_method,
            COALESCE(error_type, 'None')

        ORDER BY checkout_attempts DESC;
        """,
    )

    sql_files.append(path)

    # ================================================================
    # COMMERCIAL IMPACT ESTIMATION
    # ================================================================

    path = SQL_ANALYTICS_DIR / "09_commercial_impact.sql"

    write_sql(
        path,
        """
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
        """,
    )

    sql_files.append(path)

    # ================================================================
    # PRODUCT ANOMALY / INVESTIGATION FRAMEWORK
    # ================================================================

    path = SQL_PRODUCT_DIR / "01_daily_anomaly_alerts.sql"

    write_sql(
        path,
        """
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
        """,
    )

    sql_files.append(path)

    return sql_files


def execute_sql_files(
    con: duckdb.DuckDBPyConnection,
    sql_files: list[Path],
) -> None:
    for path in sql_files:
        print(f"Executing {path.relative_to(PROJECT_ROOT)}")
        con.execute(path.read_text(encoding="utf-8"))


def run_quality_checks(
    con: duckdb.DuckDBPyConnection,
) -> dict[str, int]:
    checks = {
        "duplicate_sessions": """
            SELECT COUNT(*)
            FROM (
                SELECT session_id
                FROM staging.sessions
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
        """,
        "duplicate_searches": """
            SELECT COUNT(*)
            FROM (
                SELECT search_id
                FROM staging.searches
                GROUP BY search_id
                HAVING COUNT(*) > 1
            )
        """,
        "orphan_searches": """
            SELECT COUNT(*)
            FROM staging.searches q
            LEFT JOIN staging.sessions s
                ON q.session_id = s.session_id
            WHERE s.session_id IS NULL
        """,
        "orphan_results": """
            SELECT COUNT(*)
            FROM staging.journey_results r
            LEFT JOIN staging.searches q
                ON r.search_id = q.search_id
            WHERE q.search_id IS NULL
        """,
        "orphan_checkout": """
            SELECT COUNT(*)
            FROM staging.checkout c
            LEFT JOIN staging.searches q
                ON c.search_id = q.search_id
            WHERE q.search_id IS NULL
        """,
        "orphan_bookings": """
            SELECT COUNT(*)
            FROM staging.bookings b
            LEFT JOIN staging.checkout c
                ON b.checkout_id = c.checkout_id
            WHERE c.checkout_id IS NULL
        """,
        "invalid_funnel_order": """
            SELECT COUNT(*)
            FROM analytics.search_funnel
            WHERE
                selected_flag > results_available_flag
                OR checkout_started_flag > selected_flag
                OR booked_flag > checkout_completed_flag
        """,
        "zero_result_selected": """
            SELECT COUNT(*)
            FROM analytics.search_funnel
            WHERE
                zero_results_flag = 1
                AND selected_flag = 1
        """,
    }

    results: dict[str, int] = {}

    for name, sql in checks.items():
        value = int(con.execute(sql).fetchone()[0])
        results[name] = value

        status = "PASS" if value == 0 else "FAIL"

        print(f"{name:<28}: {status} ({value:,})")

    failures = {name: value for name, value in results.items() if value != 0}

    if failures:
        raise RuntimeError(f"Warehouse quality checks failed: {failures}")

    return results


def export_marts(
    con: duckdb.DuckDBPyConnection,
) -> None:
    MART_DIR.mkdir(parents=True, exist_ok=True)

    marts = [
        "analytics.search_funnel",
        "analytics.kpi_summary",
        "analytics.daily_funnel",
        "analytics.device_performance",
        "analytics.channel_performance",
        "analytics.route_performance",
        "analytics.zero_result_analysis",
        "analytics.checkout_failure_analysis",
        "analytics.commercial_impact",
        "product.daily_anomaly_alerts",
    ]

    for table in marts:
        filename = table.replace(".", "_") + ".parquet"
        output_path = MART_DIR / filename

        df = con.execute(f"SELECT * FROM {table}").fetchdf()

        df.to_parquet(
            output_path,
            index=False,
            compression="zstd",
        )

        print(f"{table:<40} {len(df):>10,} rows")


def create_documentation() -> None:
    documentation = """
    # RailSearch Analytical Warehouse

    ## Architecture

    Raw synthetic event data
    ↓
    DuckDB raw views
    ↓
    Staging models
    ↓
    Search-level customer funnel
    ↓
    Product analytics marts
    ↓
    Root-cause analysis
    ↓
    Anomaly detection
    ↓
    Power BI / Python / Machine Learning

    ## Schemas

    ### raw

    External views over immutable Parquet source datasets.

    ### staging

    Standardised and typed event tables with useful analytical fields.

    ### analytics

    Reusable customer-journey and commercial data marts.

    ### product

    Product-monitoring and investigation frameworks.

    ## Core marts

    - search_funnel
    - kpi_summary
    - daily_funnel
    - device_performance
    - channel_performance
    - route_performance
    - zero_result_analysis
    - checkout_failure_analysis
    - commercial_impact
    - daily_anomaly_alerts

    ## Commercial impact

    Revenue-at-risk values are analytical estimates based on average
    successful booking value.

    They are not actual Trainline financial results.

    ## Data disclaimer

    Customer journey data in RailSearch are synthetic.

    The project does not contain proprietary Trainline customer data.
    """

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    (DOCS_DIR / "WAREHOUSE_ARCHITECTURE.md").write_text(
        textwrap.dedent(documentation).strip() + "\n",
        encoding="utf-8",
    )


def create_summary(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    kpi = (
        con.execute(
            """
        SELECT *
        FROM analytics.kpi_summary
        """
        )
        .fetchdf()
        .iloc[0]
        .to_dict()
    )

    alert_count = int(
        con.execute(
            """
            SELECT COUNT(*)
            FROM product.daily_anomaly_alerts
            WHERE alert_flag = 1
            """
        ).fetchone()[0]
    )

    summary = {
        **{key: (value.item() if hasattr(value, "item") else value) for key, value in kpi.items()},
        "anomaly_alert_days": alert_count,
        "warehouse_path": str(DB_PATH),
    }

    output_path = PROCESSED_DIR / "stage2b_warehouse_summary.json"

    output_path.write_text(
        json.dumps(
            summary,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    return summary


def main() -> None:
    print()
    print("=" * 72)
    print("RAILSEARCH — STAGE 2B ANALYTICAL WAREHOUSE")
    print("=" * 72)

    validate_raw_files()

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MART_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    sql_files = create_sql_models()

    create_documentation()

    print()
    print("Creating DuckDB warehouse...")

    con = duckdb.connect(str(DB_PATH))

    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("CREATE SCHEMA IF NOT EXISTS staging")
    con.execute("CREATE SCHEMA IF NOT EXISTS analytics")
    con.execute("CREATE SCHEMA IF NOT EXISTS product")

    print()
    print("Building SQL models...")

    execute_sql_files(
        con,
        sql_files,
    )

    print()
    print("=" * 72)
    print("WAREHOUSE QUALITY CHECKS")
    print("=" * 72)

    run_quality_checks(con)

    print()
    print("=" * 72)
    print("EXPORTING ANALYTICAL MARTS")
    print("=" * 72)

    export_marts(con)

    summary = create_summary(con)

    print()
    print("=" * 72)
    print("RAILSEARCH — STAGE 2B SUMMARY")
    print("=" * 72)

    important_fields = [
        "searches",
        "sessions",
        "zero_result_searches",
        "selected_searches",
        "checkout_attempts",
        "checkout_errors",
        "payment_failures",
        "checkout_abandonments",
        "bookings",
        "total_revenue",
        "average_order_value",
        "zero_result_rate_pct",
        "result_selection_rate_pct",
        "search_to_book_conversion_pct",
        "session_conversion_rate_pct",
        "anomaly_alert_days",
    ]

    for field in important_fields:
        value = summary.get(field)

        if isinstance(value, float):
            print(f"{field:<34}: {value:,.2f}")
        else:
            print(f"{field:<34}: {value:,}" if isinstance(value, int) else f"{field:<34}: {value}")

    print()
    print(f"DuckDB warehouse : {DB_PATH}")
    print(f"Exported marts   : {MART_DIR}")

    con.close()

    print()
    print("WAREHOUSE BUILD       : PASS")
    print("DATA QUALITY          : PASS")
    print("ANALYTICAL MARTS      : PASS")
    print("PRODUCT ALERTING      : PASS")
    print("STAGE 2B              : PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
