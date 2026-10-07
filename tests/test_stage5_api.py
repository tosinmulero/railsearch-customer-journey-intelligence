from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from railsearch.api.main import app
from railsearch.api.service import (
    MODEL_PATH,
    SUMMARY_PATH,
)

client = TestClient(app)


SAMPLE = {
    "device_type": "iOS App",
    "operating_system": "iOS",
    "acquisition_channel": "Direct",
    "customer_type": "Returning",
    "country": "United Kingdom",
    "origin_station": "London Euston",
    "destination_station": "Manchester Piccadilly",
    "journey_type": "Single",
    "is_logged_in": 1,
    "passengers": 1,
    "railcard_used": 0,
    "results_count": 5,
    "search_latency_ms": 720.0,
    "zero_results_flag": 0,
    "days_before_travel": 10,
    "search_hour": 9,
    "day_of_week": 2,
    "search_month": 6,
}


def artifact_available() -> bool:
    return MODEL_PATH.exists() and SUMMARY_PATH.exists()


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"

    assert body["service"] == "railsearch-conversion-api"


def test_model_metadata() -> None:
    response = client.get("/model")

    if not artifact_available():
        assert response.status_code == 503

        return

    assert response.status_code == 200

    body = response.json()

    assert body["feature_count"] == 18

    assert len(body["features"]) == 18

    assert 0.0 < body["threshold"] <= 1.0


@pytest.mark.skipif(
    not artifact_available(),
    reason=("Stage 4 model artifact is not available."),
)
def test_single_prediction() -> None:
    response = client.post(
        "/predict",
        json=SAMPLE,
    )

    assert response.status_code == 200

    body = response.json()

    assert 0.0 <= body["booking_probability"] <= 1.0

    assert body["predicted_booking"] in [0, 1]


@pytest.mark.skipif(
    not artifact_available(),
    reason=("Stage 4 model artifact is not available."),
)
def test_batch_prediction() -> None:
    response = client.post(
        "/predict/batch",
        json={
            "records": [
                SAMPLE,
                SAMPLE,
            ]
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 2

    assert len(body["predictions"]) == 2


def test_invalid_zero_result_payload() -> None:
    invalid = {
        **SAMPLE,
        "zero_results_flag": 1,
        "results_count": 5,
    }

    response = client.post(
        "/predict",
        json=invalid,
    )

    assert response.status_code == 422
