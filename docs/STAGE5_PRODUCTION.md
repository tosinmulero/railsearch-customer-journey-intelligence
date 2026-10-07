# RailSearch — Productionisation

## Purpose

Stage 5 exposes the Stage 4 search-to-book conversion model through a production-style FastAPI service.

The API accepts customer and search context available immediately after search results are returned.

Downstream funnel variables remain excluded to preserve the Stage 4 leakage-control boundary.

## Architecture

Client

→ FastAPI request validation

→ Pydantic schema

→ scikit-learn pipeline

→ booking probability

→ decision threshold

→ prediction response

## Endpoints

### GET /health

Operational service health and model-artifact availability.

### GET /model

Returns model metadata, feature list, threshold and locked test metrics.

### POST /predict

Scores one search context.

### POST /predict/batch

Scores up to 1,000 search contexts in one request.

## Model artifact

The API loads:

`artifacts/models/railsearch_conversion_model.joblib`

Metadata is loaded from:

`reports/stage4_model_summary.json`

## Validation

The service includes automated tests covering:

- health checks;
- model metadata;
- single predictions;
- batch predictions;
- schema validation;
- invalid search-result consistency.

## Containerisation

The Dockerfile packages the application with Python 3.12 and exposes port 8000.

## CI

GitHub Actions runs Ruff and pytest on pushes and pull requests.

## Data disclaimer

RailSearch uses synthetic customer-journey data.

The API demonstrates production ML architecture, software engineering and product-data-science methodology. It is not a Trainline production system.
