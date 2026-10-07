from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = PROJECT_ROOT / "artifacts" / "models" / "railsearch_conversion_model.joblib"

SUMMARY_PATH = PROJECT_ROOT / "reports" / "stage4_model_summary.json"

FEATURES = [
    "device_type",
    "operating_system",
    "acquisition_channel",
    "customer_type",
    "country",
    "origin_station",
    "destination_station",
    "journey_type",
    "is_logged_in",
    "passengers",
    "railcard_used",
    "results_count",
    "search_latency_ms",
    "zero_results_flag",
    "days_before_travel",
    "search_hour",
    "day_of_week",
    "search_month",
]


def model_available() -> bool:
    return MODEL_PATH.exists() and SUMMARY_PATH.exists()


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")

    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def load_summary() -> dict[str, Any]:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f"Model summary not found: {SUMMARY_PATH}")

    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def get_threshold() -> float:
    summary = load_summary()

    return float(
        summary.get(
            "best_f1_threshold",
            0.50,
        )
    )


def get_model_name() -> str:
    summary = load_summary()

    return str(
        summary.get(
            "champion_model",
            "Unknown",
        )
    )


def get_model_info() -> dict[str, Any]:
    summary = load_summary()

    features = summary.get(
        "features",
        FEATURES,
    )

    metrics = summary.get(
        "test_metrics",
        {},
    )

    return {
        "champion_model": str(
            summary.get(
                "champion_model",
                "Unknown",
            )
        ),
        "prediction_point": str(
            summary.get(
                "prediction_point",
                "Unknown",
            )
        ),
        "threshold": get_threshold(),
        "feature_count": len(features),
        "features": list(features),
        "test_metrics": {str(key): float(value) for key, value in metrics.items()},
    }


def records_to_frame(
    records: list[dict[str, Any]],
) -> pd.DataFrame:
    frame = pd.DataFrame(records)

    missing = [feature for feature in FEATURES if feature not in frame.columns]

    if missing:
        raise ValueError(f"Missing model features: {missing}")

    return frame[FEATURES].copy()


def predict_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    model = load_model()

    frame = records_to_frame(records)

    probabilities = model.predict_proba(frame)[:, 1]

    threshold = get_threshold()
    model_name = get_model_name()

    predictions = []

    for probability in probabilities:
        value = float(probability)

        predictions.append(
            {
                "booking_probability": value,
                "predicted_booking": int(value >= threshold),
                "threshold": threshold,
                "model_name": model_name,
            }
        )

    return predictions
