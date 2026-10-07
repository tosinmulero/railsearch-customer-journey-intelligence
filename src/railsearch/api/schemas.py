from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_type: str
    operating_system: str
    acquisition_channel: str
    customer_type: str
    country: str

    origin_station: str
    destination_station: str
    journey_type: str

    is_logged_in: int = Field(
        ge=0,
        le=1,
    )

    passengers: int = Field(
        ge=1,
        le=20,
    )

    railcard_used: int = Field(
        ge=0,
        le=1,
    )

    results_count: int = Field(ge=0)

    search_latency_ms: float = Field(ge=0)

    zero_results_flag: int = Field(
        ge=0,
        le=1,
    )

    days_before_travel: int = Field(
        ge=0,
        le=365,
    )

    search_hour: int = Field(
        ge=0,
        le=23,
    )

    day_of_week: int = Field(
        ge=0,
        le=6,
    )

    search_month: int = Field(
        ge=1,
        le=12,
    )

    @model_validator(mode="after")
    def validate_result_consistency(
        self,
    ) -> PredictionRequest:
        if self.zero_results_flag == 1 and self.results_count != 0:
            raise ValueError("results_count must be 0 when zero_results_flag is 1.")

        if self.zero_results_flag == 0 and self.results_count == 0:
            raise ValueError("results_count must be greater than 0 when zero_results_flag is 0.")

        return self


class PredictionResponse(BaseModel):
    booking_probability: float
    predicted_booking: int
    threshold: float
    model_name: str


class BatchPredictionRequest(BaseModel):
    records: list[PredictionRequest] = Field(
        min_length=1,
        max_length=1000,
    )


class BatchPredictionResponse(BaseModel):
    count: int
    predictions: list[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    service: str
    model_artifact_available: bool


class ModelInfoResponse(BaseModel):
    champion_model: str
    prediction_point: str
    threshold: float
    feature_count: int
    features: list[str]
    test_metrics: dict[
        str,
        float,
    ]
