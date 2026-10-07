from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_SESSIONS = 150_000

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RNG = np.random.default_rng(SEED)

START = pd.Timestamp("2026-01-01 00:00:00")
END = pd.Timestamp("2026-06-30 23:59:59")

STATIONS = [
    "London Waterloo",
    "London Victoria",
    "London Liverpool Street",
    "London Bridge",
    "London Paddington",
    "London Euston",
    "London King's Cross",
    "Manchester Piccadilly",
    "Birmingham New Street",
    "Leeds",
    "Glasgow Central",
    "Edinburgh Waverley",
    "Liverpool Lime Street",
    "Bristol Temple Meads",
    "Cardiff Central",
    "Reading",
    "Brighton",
    "York",
    "Cambridge",
    "Oxford",
    "Nottingham",
    "Sheffield",
    "Newcastle",
    "Southampton Central",
    "Clapham Junction",
    "East Croydon",
    "Gatwick Airport",
    "Stansted Airport",
    "Luton",
    "Milton Keynes Central",
]

OPERATORS = [
    "Avanti West Coast",
    "CrossCountry",
    "Great Western Railway",
    "Greater Anglia",
    "LNER",
    "Northern",
    "Southeastern",
    "Southern",
    "Thameslink",
    "TransPennine Express",
]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def random_timestamps(n: int) -> pd.Series:
    seconds = int((END - START).total_seconds())
    offsets = RNG.integers(0, seconds + 1, size=n)
    return pd.Series(START + pd.to_timedelta(offsets, unit="s"))


def make_station_reference() -> pd.DataFrame:
    regions = [
        "London",
        "London",
        "London",
        "London",
        "London",
        "London",
        "London",
        "North West",
        "West Midlands",
        "Yorkshire",
        "Scotland",
        "Scotland",
        "North West",
        "South West",
        "Wales",
        "South East",
        "South East",
        "Yorkshire",
        "East of England",
        "South East",
        "East Midlands",
        "Yorkshire",
        "North East",
        "South East",
        "London",
        "South East",
        "South East",
        "East of England",
        "East of England",
        "South East",
    ]

    usage = RNG.integers(
        500_000,
        55_000_000,
        size=len(STATIONS),
    )

    return pd.DataFrame(
        {
            "station_code": [f"RS{i:03d}" for i in range(1, len(STATIONS) + 1)],
            "station_name": STATIONS,
            "region": regions,
            "annual_entries_exits": usage,
            "interchange_volume": (
                usage
                * RNG.uniform(
                    0.02,
                    0.22,
                    len(STATIONS),
                )
            ).astype(int),
        }
    )


def make_sessions() -> pd.DataFrame:
    started = random_timestamps(N_SESSIONS)

    device = RNG.choice(
        [
            "Desktop Web",
            "Mobile Web",
            "iOS App",
            "Android App",
        ],
        N_SESSIONS,
        p=[0.24, 0.21, 0.30, 0.25],
    )

    customer_type = RNG.choice(
        ["New", "Returning"],
        N_SESSIONS,
        p=[0.38, 0.62],
    )

    operating_system = np.empty(
        N_SESSIONS,
        dtype=object,
    )

    for device_type in np.unique(device):
        mask = device == device_type

        if device_type == "Desktop Web":
            operating_system[mask] = RNG.choice(
                ["Windows", "macOS", "Linux"],
                mask.sum(),
                p=[0.68, 0.29, 0.03],
            )

        elif device_type == "Mobile Web":
            operating_system[mask] = RNG.choice(
                ["iOS", "Android"],
                mask.sum(),
                p=[0.52, 0.48],
            )

        elif device_type == "iOS App":
            operating_system[mask] = "iOS"

        else:
            operating_system[mask] = "Android"

    logged_probability = np.where(
        customer_type == "Returning",
        0.82,
        0.28,
    )

    return pd.DataFrame(
        {
            "session_id": [f"S{i:09d}" for i in range(1, N_SESSIONS + 1)],
            "customer_id": [
                f"C{x:08d}"
                for x in RNG.integers(
                    1,
                    80_001,
                    N_SESSIONS,
                )
            ],
            "session_started_at": started,
            "device_type": device,
            "operating_system": operating_system,
            "acquisition_channel": RNG.choice(
                [
                    "Organic Search",
                    "Direct",
                    "Paid Search",
                    "Email",
                    "Affiliate",
                    "Social",
                ],
                N_SESSIONS,
                p=[
                    0.28,
                    0.27,
                    0.18,
                    0.10,
                    0.09,
                    0.08,
                ],
            ),
            "customer_type": customer_type,
            "country": RNG.choice(
                [
                    "United Kingdom",
                    "France",
                    "Germany",
                    "Spain",
                    "Other",
                ],
                N_SESSIONS,
                p=[
                    0.79,
                    0.06,
                    0.05,
                    0.04,
                    0.06,
                ],
            ),
            "is_logged_in": (RNG.random(N_SESSIONS) < logged_probability).astype("int8"),
        }
    )


def make_searches(
    sessions: pd.DataFrame,
) -> pd.DataFrame:
    searches_per_session = RNG.choice(
        [1, 2, 3, 4],
        len(sessions),
        p=[0.48, 0.34, 0.14, 0.04],
    )

    index = np.repeat(
        np.arange(len(sessions)),
        searches_per_session,
    )

    base = sessions.iloc[index].reset_index(drop=True)

    n = len(base)

    searched_at = base["session_started_at"] + pd.to_timedelta(
        RNG.integers(0, 61, n),
        unit="m",
    )

    origin = RNG.choice(
        STATIONS,
        n,
    )

    destination = RNG.choice(
        STATIONS,
        n,
    )

    same_station = origin == destination

    while same_station.any():
        destination[same_station] = RNG.choice(
            STATIONS,
            same_station.sum(),
        )

        same_station = origin == destination

    days_ahead = np.clip(
        RNG.gamma(
            2.2,
            5.5,
            n,
        ).astype(int),
        0,
        60,
    )

    travel_date = searched_at.dt.normalize() + pd.to_timedelta(
        days_ahead,
        unit="D",
    )

    passengers = RNG.choice(
        [1, 2, 3, 4, 5],
        n,
        p=[
            0.64,
            0.25,
            0.06,
            0.04,
            0.01,
        ],
    )

    railcard = (RNG.random(n) < 0.31).astype("int8")

    zero_logit = np.full(
        n,
        -2.85,
    )

    zero_logit += np.where(
        days_ahead == 0,
        0.30,
        0.0,
    )

    zero_logit += np.where(
        passengers >= 4,
        0.20,
        0.0,
    )

    difficult_route = np.isin(
        origin,
        [
            "Stansted Airport",
            "Luton",
            "Southampton Central",
        ],
    ) & np.isin(
        destination,
        [
            "Glasgow Central",
            "Edinburgh Waverley",
            "Newcastle",
        ],
    )

    zero_logit += np.where(
        difficult_route,
        1.00,
        0.0,
    )

    supply_incident = (
        (searched_at >= pd.Timestamp("2026-03-09"))
        & (searched_at < pd.Timestamp("2026-03-16"))
        & (
            np.isin(
                origin,
                [
                    "London Euston",
                    "Manchester Piccadilly",
                ],
            )
            | np.isin(
                destination,
                [
                    "London Euston",
                    "Manchester Piccadilly",
                ],
            )
        )
    )

    zero_logit += np.where(
        supply_incident,
        1.50,
        0.0,
    )

    zero_results = (RNG.random(n) < sigmoid(zero_logit)).astype("int8")

    results_count = np.where(
        zero_results == 1,
        0,
        RNG.integers(
            3,
            8,
            n,
        ),
    ).astype("int16")

    search_latency = (
        RNG.normal(
            760,
            170,
            n,
        )
        + np.where(
            base["device_type"].to_numpy() == "Mobile Web",
            180,
            0,
        )
        + np.where(
            zero_results == 1,
            320,
            0,
        )
        + np.where(
            supply_incident,
            260,
            0,
        )
    )

    search_latency = np.maximum(
        search_latency,
        180,
    ).astype("int32")

    return pd.DataFrame(
        {
            "search_id": [f"Q{i:010d}" for i in range(1, n + 1)],
            "session_id": base["session_id"].to_numpy(),
            "searched_at": searched_at,
            "origin_station": origin,
            "destination_station": destination,
            "travel_date": travel_date,
            "passengers": passengers.astype("int8"),
            "journey_type": RNG.choice(
                ["Single", "Return"],
                n,
                p=[0.53, 0.47],
            ),
            "railcard_used": railcard,
            "results_count": results_count,
            "search_latency_ms": search_latency,
            "zero_results_flag": zero_results,
        }
    )


def make_journey_results(
    searches: pd.DataFrame,
) -> pd.DataFrame:
    viable = searches.loc[searches["results_count"] > 0].reset_index(drop=True)

    counts = viable["results_count"].to_numpy(dtype=int)

    index = np.repeat(
        np.arange(len(viable)),
        counts,
    )

    expanded = viable.iloc[index].reset_index(drop=True)

    n = len(expanded)

    result_position = np.concatenate(
        [
            np.arange(
                1,
                count + 1,
                dtype=np.int16,
            )
            for count in counts
        ]
    )

    distance_factor = RNG.uniform(
        0.7,
        3.4,
        len(viable),
    )

    repeated_distance = np.repeat(
        distance_factor,
        counts,
    )

    duration = np.clip(
        (
            25
            + repeated_distance
            * RNG.normal(
                68,
                14,
                n,
            )
            + result_position
            * RNG.normal(
                2.5,
                1.0,
                n,
            )
        ),
        20,
        420,
    ).astype("int16")

    changes = RNG.choice(
        [0, 1, 2],
        n,
        p=[0.64, 0.29, 0.07],
    ).astype("int8")

    fare = (
        7
        + repeated_distance
        * RNG.normal(
            23,
            4.5,
            n,
        )
        + changes * 2
        + result_position
        * RNG.uniform(
            0.2,
            1.5,
            n,
        )
    )

    days_before_travel = (
        pd.to_datetime(expanded["travel_date"])
        - pd.to_datetime(expanded["searched_at"]).dt.normalize()
    ).dt.days.to_numpy()

    fare *= np.where(
        days_before_travel >= 7,
        0.84,
        1.0,
    )

    fare *= np.where(
        expanded["railcard_used"].to_numpy() == 1,
        0.67,
        1.0,
    )

    fare = np.maximum(
        fare,
        3.50,
    ).round(2)

    departure = (
        pd.to_datetime(expanded["travel_date"])
        + pd.to_timedelta(
            RNG.integers(
                5,
                23,
                n,
            ),
            unit="h",
        )
        + pd.to_timedelta(
            RNG.choice(
                np.arange(
                    0,
                    60,
                    5,
                ),
                n,
            ),
            unit="m",
        )
    )

    arrival = departure + pd.to_timedelta(
        duration,
        unit="m",
    )

    selection_probability = sigmoid(
        -0.15
        + 0.45 * viable["railcard_used"].to_numpy()
        - 0.18 * (viable["passengers"].to_numpy() >= 4)
    )

    selected_search = RNG.random(len(viable)) < selection_probability

    selected_position = np.floor(RNG.random(len(viable)) * counts).astype(int) + 1

    selected_position = np.where(
        selected_search,
        selected_position,
        0,
    )

    selected_flag = (
        result_position
        == np.repeat(
            selected_position,
            counts,
        )
    ).astype("int8")

    return pd.DataFrame(
        {
            "result_id": [
                f"R{i:011d}"
                for i in range(
                    1,
                    n + 1,
                )
            ],
            "search_id": expanded["search_id"].to_numpy(),
            "operator": RNG.choice(
                OPERATORS,
                n,
            ),
            "departure_time": departure,
            "arrival_time": arrival,
            "duration_minutes": duration,
            "changes": changes,
            "fare": fare,
            "fare_type": RNG.choice(
                [
                    "Advance",
                    "Off-Peak",
                    "Anytime",
                ],
                n,
                p=[
                    0.47,
                    0.38,
                    0.15,
                ],
            ),
            "result_position": result_position,
            "selected_flag": selected_flag,
        }
    )


def make_checkout(
    sessions: pd.DataFrame,
    searches: pd.DataFrame,
    results: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = results.loc[
        results["selected_flag"] == 1,
        [
            "search_id",
            "operator",
            "fare",
        ],
    ].copy()

    selected = selected.merge(
        searches[
            [
                "search_id",
                "session_id",
                "searched_at",
                "origin_station",
                "destination_station",
                "passengers",
            ]
        ],
        on="search_id",
        how="left",
        validate="one_to_one",
    )

    selected = selected.merge(
        sessions[
            [
                "session_id",
                "device_type",
                "customer_type",
                "is_logged_in",
            ]
        ],
        on="session_id",
        how="left",
        validate="many_to_one",
    )

    n = len(selected)

    checkout_started = pd.to_datetime(selected["searched_at"]) + pd.to_timedelta(
        RNG.integers(
            2,
            19,
            n,
        ),
        unit="m",
    )

    payment_method = RNG.choice(
        [
            "Debit Card",
            "Credit Card",
            "Apple Pay",
            "Google Pay",
            "PayPal",
        ],
        n,
        p=[
            0.34,
            0.27,
            0.17,
            0.13,
            0.09,
        ],
    )

    error_logit = np.full(
        n,
        -3.10,
    )

    error_logit += np.where(
        selected["device_type"].to_numpy() == "Mobile Web",
        0.60,
        0.0,
    )

    checkout_incident = (
        (checkout_started >= pd.Timestamp("2026-04-13"))
        & (checkout_started < pd.Timestamp("2026-04-20"))
        & np.isin(
            selected["device_type"],
            [
                "Mobile Web",
                "Android App",
            ],
        )
    )

    error_logit += np.where(
        checkout_incident,
        1.45,
        0.0,
    )

    checkout_error = (RNG.random(n) < sigmoid(error_logit)).astype("int8")

    possible_errors = RNG.choice(
        [
            "Session Timeout",
            "Fare Changed",
            "Inventory Unavailable",
            "Technical Error",
        ],
        n,
        p=[
            0.24,
            0.23,
            0.22,
            0.31,
        ],
    )

    error_type = np.where(
        checkout_error == 1,
        possible_errors,
        "None",
    )

    payment_logit = (
        -3.35
        + np.where(
            payment_method == "Credit Card",
            0.22,
            0.0,
        )
        + np.where(
            payment_method == "PayPal",
            0.30,
            0.0,
        )
        + np.where(
            selected["customer_type"].to_numpy() == "New",
            0.20,
            0.0,
        )
    )

    payment_failure = ((checkout_error == 0) & (RNG.random(n) < sigmoid(payment_logit))).astype(
        "int8"
    )

    abandonment_logit = (
        -1.85
        + 0.017 * selected["fare"].to_numpy()
        + np.where(
            selected["customer_type"].to_numpy() == "New",
            0.28,
            0.0,
        )
        + np.where(
            selected["is_logged_in"].to_numpy() == 0,
            0.22,
            0.0,
        )
    )

    abandoned = (
        (checkout_error == 0)
        & (payment_failure == 0)
        & (
            RNG.random(n)
            < sigmoid(
                np.clip(
                    abandonment_logit,
                    -4,
                    2.2,
                )
            )
        )
    )

    completed = ((checkout_error == 0) & (payment_failure == 0) & (~abandoned)).astype("int8")

    checkout = pd.DataFrame(
        {
            "checkout_id": [
                f"H{i:010d}"
                for i in range(
                    1,
                    n + 1,
                )
            ],
            "session_id": selected["session_id"].to_numpy(),
            "search_id": selected["search_id"].to_numpy(),
            "checkout_started_at": checkout_started,
            "device_type": selected["device_type"].to_numpy(),
            "payment_method": payment_method,
            "checkout_error_flag": checkout_error,
            "error_type": error_type,
            "payment_failure_flag": payment_failure,
            "checkout_completed_flag": completed,
        }
    )

    selected_meta = selected[
        [
            "search_id",
            "operator",
            "fare",
            "origin_station",
            "destination_station",
            "passengers",
        ]
    ].copy()

    return checkout, selected_meta


def make_bookings(
    checkout: pd.DataFrame,
    selected_meta: pd.DataFrame,
) -> pd.DataFrame:
    completed = checkout.loc[checkout["checkout_completed_flag"] == 1].copy()

    completed = completed.merge(
        selected_meta,
        on="search_id",
        how="left",
        validate="one_to_one",
    )

    n = len(completed)

    ticket_value = (completed["fare"].to_numpy() * completed["passengers"].to_numpy()).round(2)

    booking_fee = np.where(
        ticket_value >= 100,
        0.0,
        RNG.choice(
            [
                0.0,
                0.99,
                1.49,
            ],
            n,
            p=[
                0.78,
                0.15,
                0.07,
            ],
        ),
    )

    total_revenue = (ticket_value + booking_fee).round(2)

    booked_at = pd.to_datetime(completed["checkout_started_at"]) + pd.to_timedelta(
        RNG.integers(
            1,
            8,
            n,
        ),
        unit="m",
    )

    return pd.DataFrame(
        {
            "booking_id": [
                f"B{i:010d}"
                for i in range(
                    1,
                    n + 1,
                )
            ],
            "session_id": completed["session_id"].to_numpy(),
            "search_id": completed["search_id"].to_numpy(),
            "checkout_id": completed["checkout_id"].to_numpy(),
            "booked_at": booked_at,
            "ticket_value": ticket_value,
            "booking_fee": booking_fee.round(2),
            "total_revenue": total_revenue,
            "passengers": completed["passengers"].to_numpy(),
            "operator": completed["operator"].to_numpy(),
            "origin_station": completed["origin_station"].to_numpy(),
            "destination_station": completed["destination_station"].to_numpy(),
        }
    )


def validate(
    sessions: pd.DataFrame,
    searches: pd.DataFrame,
    results: pd.DataFrame,
    checkout: pd.DataFrame,
    bookings: pd.DataFrame,
) -> None:
    assert sessions["session_id"].is_unique

    assert searches["search_id"].is_unique

    assert results["result_id"].is_unique

    assert checkout["checkout_id"].is_unique

    assert bookings["booking_id"].is_unique

    assert searches["session_id"].isin(sessions["session_id"]).all()

    assert results["search_id"].isin(searches["search_id"]).all()

    assert checkout["search_id"].isin(searches["search_id"]).all()

    assert bookings["checkout_id"].isin(checkout["checkout_id"]).all()

    assert (searches["zero_results_flag"] == (searches["results_count"] == 0).astype("int8")).all()

    selected_per_search = results.groupby(
        "search_id",
        sort=False,
    )["selected_flag"].sum()

    assert (selected_per_search <= 1).all()


def save_table(
    df: pd.DataFrame,
    name: str,
) -> None:
    path = RAW_DIR / f"{name}.parquet"

    df.to_parquet(
        path,
        index=False,
        compression="snappy",
    )

    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"Failed to write {path}")

    print(f"{name:<20} {len(df):>12,} rows  {path.stat().st_size / 1_048_576:>8.2f} MB")


def main() -> None:
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 72)
    print("RAILSEARCH — STAGE 2A SYNTHETIC CUSTOMER JOURNEY GENERATOR")
    print("=" * 72)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Raw output   : {RAW_DIR}")
    print(f"Seed         : {SEED}")
    print(f"Sessions     : {N_SESSIONS:,}")
    print()

    station_reference = make_station_reference()

    sessions = make_sessions()

    searches = make_searches(sessions)

    results = make_journey_results(searches)

    checkout, selected_meta = make_checkout(
        sessions,
        searches,
        results,
    )

    bookings = make_bookings(
        checkout,
        selected_meta,
    )

    validate(
        sessions,
        searches,
        results,
        checkout,
        bookings,
    )

    print("REFERENTIAL INTEGRITY : PASS")
    print()

    print("Writing Parquet datasets...")

    save_table(
        station_reference,
        "station_reference",
    )

    save_table(
        sessions,
        "sessions",
    )

    save_table(
        searches,
        "searches",
    )

    save_table(
        results,
        "journey_results",
    )

    save_table(
        checkout,
        "checkout",
    )

    save_table(
        bookings,
        "bookings",
    )

    session_conversion = bookings["session_id"].nunique() / sessions["session_id"].nunique()

    search_conversion = len(bookings) / len(searches)

    total_revenue = float(bookings["total_revenue"].sum())

    summary = {
        "seed": SEED,
        "sessions": len(sessions),
        "searches": len(searches),
        "journey_results": len(results),
        "checkout_attempts": len(checkout),
        "bookings": len(bookings),
        "session_conversion_rate": round(
            float(session_conversion),
            6,
        ),
        "search_to_book_conversion_rate": round(
            float(search_conversion),
            6,
        ),
        "zero_result_rate": round(
            float(searches["zero_results_flag"].mean()),
            6,
        ),
        "checkout_error_rate": round(
            float(checkout["checkout_error_flag"].mean()),
            6,
        ),
        "payment_failure_rate": round(
            float(checkout["payment_failure_flag"].mean()),
            6,
        ),
        "total_revenue": round(
            total_revenue,
            2,
        ),
    }

    summary_path = PROCESSED_DIR / "synthetic_generation_summary.json"

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("RAILSEARCH — GENERATION SUMMARY")
    print("=" * 72)

    for key, value in summary.items():
        if isinstance(
            value,
            float,
        ):
            print(f"{key:<34}: {value:,.4f}")
        else:
            print(f"{key:<34}: {value:,}")

    required = [
        "station_reference.parquet",
        "sessions.parquet",
        "searches.parquet",
        "journey_results.parquet",
        "checkout.parquet",
        "bookings.parquet",
    ]

    missing = [filename for filename in required if not (RAW_DIR / filename).exists()]

    if missing:
        raise RuntimeError(f"Output verification failed: {missing}")

    print()
    print("DATA GENERATION       : PASS")
    print("REFERENTIAL INTEGRITY : PASS")
    print("OUTPUT FILES          : PASS")
    print("STAGE 2A              : PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
