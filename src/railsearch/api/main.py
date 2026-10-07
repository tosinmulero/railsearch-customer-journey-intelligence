from __future__ import annotations

from fastapi import FastAPI, HTTPException

from railsearch.api.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
)
from railsearch.api.service import (
    get_model_info,
    model_available,
    predict_records,
)

app = FastAPI(
    title="RailSearch Conversion Intelligence API",
    version="1.0.0",
    description=("Production-style API for the RailSearch search-to-book conversion model."),
)


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="railsearch-conversion-api",
        model_artifact_available=(model_available()),
    )


@app.get(
    "/model",
    response_model=ModelInfoResponse,
)
def model_info() -> ModelInfoResponse:
    if not model_available():
        raise HTTPException(
            status_code=503,
            detail=("RailSearch model artifact is unavailable."),
        )

    return ModelInfoResponse(**get_model_info())


@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def predict(
    request: PredictionRequest,
) -> PredictionResponse:
    if not model_available():
        raise HTTPException(
            status_code=503,
            detail=("RailSearch model artifact is unavailable."),
        )

    try:
        result = predict_records([request.model_dump()])[0]

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(f"Prediction failed: {exc}"),
        ) from exc

    return PredictionResponse(**result)


@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
)
def predict_batch(
    request: BatchPredictionRequest,
) -> BatchPredictionResponse:
    if not model_available():
        raise HTTPException(
            status_code=503,
            detail=("RailSearch model artifact is unavailable."),
        )

    try:
        records = [item.model_dump() for item in request.records]

        predictions = predict_records(records)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(f"Batch prediction failed: {exc}"),
        ) from exc

    return BatchPredictionResponse(
        count=len(predictions),
        predictions=[PredictionResponse(**prediction) for prediction in predictions],
    )
