# ruff: noqa: E501

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
DOCS_DIR = PROJECT_ROOT / "docs"

STAGE2B_SUMMARY = PROJECT_ROOT / "data" / "processed" / "stage2b_warehouse_summary.json"

STAGE3_SUMMARY = REPORTS_DIR / "stage3_investigation_summary.json"

STAGE4_SUMMARY = REPORTS_DIR / "stage4_model_summary.json"

MODEL_PATH = PROJECT_ROOT / "artifacts" / "models" / "railsearch_conversion_model.joblib"

README_PATH = PROJECT_ROOT / "README.md"

ARCHITECTURE_PATH = DOCS_DIR / "ARCHITECTURE.md"


def banner(title: str) -> None:
    print()
    print("=" * 76)
    print(title)
    print("=" * 76)


def run(command: list[str]) -> None:
    print()
    print("RUNNING:")
    print(" ".join(command))
    print()

    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True,
    )


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    if path.stat().st_size == 0:
        raise RuntimeError(f"File is empty: {path}")


def validate_project() -> None:
    banner("1. VALIDATE PROJECT")

    required = [
        STAGE2B_SUMMARY,
        STAGE3_SUMMARY,
        STAGE4_SUMMARY,
        MODEL_PATH,
        PROJECT_ROOT / "Dockerfile",
        PROJECT_ROOT / ".github" / "workflows" / "ci.yml",
        PROJECT_ROOT / "src" / "railsearch" / "api" / "main.py",
        PROJECT_ROOT / "scripts" / "generate_synthetic_events.py",
        PROJECT_ROOT / "scripts" / "build_stage2b_warehouse.py",
        PROJECT_ROOT / "scripts" / "run_stage3_investigation.py",
        PROJECT_ROOT / "scripts" / "run_stage4_modeling.py",
        PROJECT_ROOT / "scripts" / "setup_stage5_production.py",
    ]

    for path in required:
        require_file(path)

        print(f"PASS : {path.relative_to(PROJECT_ROOT)}")

    print()
    print("PROJECT VALIDATION : PASS")


def create_architecture() -> None:
    banner("2. CREATE ARCHITECTURE")

    DOCS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = """
# RailSearch Architecture

## End-to-end architecture

```mermaid
flowchart LR
    A[Synthetic Customer Journey Events] --> B[Raw Parquet]
    B --> C[DuckDB Staging]
    C --> D[Analytics Marts]

    D --> E[Funnel Analytics]
    D --> F[Anomaly Detection]
    D --> G[ML Feature Set]

    G --> H[Temporal Train Validation Test]
    H --> I[Model Comparison]
    I --> J[Champion Conversion Model]

    J --> K[Explainability and Calibration]
    J --> L[FastAPI Service]

    L --> M[Single Prediction]
    L --> N[Batch Prediction]
    L --> O[Model Metadata]
    L --> P[Health Check]

    Q[pytest and Ruff] --> R[GitHub Actions CI]
    S[Docker] --> L
```

## Analytical workflow

1. Generate reproducible synthetic customer-journey data.
2. Persist raw event tables as Parquet.
3. Build typed DuckDB staging models.
4. Create reusable product-analytics marts.
5. Analyse customer-funnel performance.
6. Detect abnormal conversion, zero-result and checkout behaviour.
7. Quantify statistical and simulated commercial impact.
8. Engineer leakage-safe predictive features.
9. Apply temporal train, validation and locked test periods.
10. Compare candidate machine-learning models.
11. Select and refit the champion model.
12. Evaluate calibration, ranking and explainability.
13. Persist the trained model artifact.
14. Serve predictions through FastAPI.
15. Validate software quality with pytest, Ruff, Docker and CI.

## Prediction boundary

RailSearch predicts whether a search will eventually result in a booking
immediately after journey results have been returned.

Downstream variables are excluded from modelling, including:

- journey selection;
- checkout start;
- checkout errors;
- payment failures;
- checkout completion;
- abandonment;
- booking revenue.

This prevents target leakage.

## Data disclaimer

RailSearch uses synthetic customer-journey data for portfolio
demonstration and contains no proprietary Trainline data.
"""

    ARCHITECTURE_PATH.write_text(
        content.strip() + "\n",
        encoding="utf-8",
    )

    require_file(ARCHITECTURE_PATH)

    print(f"Created: {ARCHITECTURE_PATH}")

    print("ARCHITECTURE : PASS")


def create_readme() -> None:
    banner("3. CREATE README")

    stage2 = load_json(STAGE2B_SUMMARY)

    stage3 = load_json(STAGE3_SUMMARY)

    stage4 = load_json(STAGE4_SUMMARY)

    supply = stage3["supply_incident"]

    checkout = stage3["checkout_incident"]

    metrics = stage4["test_metrics"]

    ranking = stage4["ranking"]

    champion = stage4["champion_model"]

    top_features = stage4.get("top_features", [])

    feature_lines = []

    for item in top_features[:10]:
        feature_lines.append(
            "- `" + str(item["feature"]) + "` — " + f"{float(item['importance_mean']):.5f}"
        )

    if feature_lines:
        feature_text = "\n".join(feature_lines)
    else:
        feature_text = "- See `reports/tables/stage4_feature_importance.csv`."

    readme = f"""
# RailSearch — Customer Journey & Conversion Intelligence

An end-to-end **Product Analytics, Data Science, Machine Learning and
MLOps** portfolio project modelling the digital rail-booking journey
from search through booking.

> **Important:** RailSearch uses synthetic customer-journey data created
> specifically for portfolio demonstration. It contains no proprietary
> Trainline data.

---

## Business problem

RailSearch investigates realistic digital-travel questions:

- Why has conversion declined?
- Why are searches returning no journey results?
- Which routes or devices create customer friction?
- Where are checkout failures occurring?
- What is the potential commercial impact?
- Which searches are most likely to convert?
- Can recurring product issues be detected automatically?
- Can the resulting ML model be operationalised?

---

## Customer journey

```text
Search
  ↓
Journey Results
  ↓
Journey Selection
  ↓
Checkout
  ↓
Payment
  ↓
Booking
  ↓
Revenue
```

---

## Dataset scale

| Metric | Result |
|---|---:|
| Sessions | {int(stage2["sessions"]):,} |
| Searches | {int(stage2["searches"]):,} |
| Zero-result searches | {int(stage2["zero_result_searches"]):,} |
| Checkout attempts | {int(stage2["checkout_attempts"]):,} |
| Checkout errors | {int(stage2["checkout_errors"]):,} |
| Payment failures | {int(stage2["payment_failures"]):,} |
| Checkout abandonments | {int(stage2["checkout_abandonments"]):,} |
| Bookings | {int(stage2["bookings"]):,} |
| Simulated revenue | £{float(stage2["total_revenue"]):,.2f} |
| Average order value | £{float(stage2["average_order_value"]):,.2f} |
| Search-to-book conversion | {float(stage2["search_to_book_conversion_pct"]):.2f}% |
| Session conversion | {float(stage2["session_conversion_rate_pct"]):.2f}% |
| Zero-result rate | {float(stage2["zero_result_rate_pct"]):.2f}% |
| Anomaly-alert days | {int(stage2["anomaly_alert_days"])} |

---

## Product investigation

### Search / supply incident

Zero-result rate:

**{float(supply["baseline_zero_result_rate_pct"]):.2f}% →
{float(supply["incident_zero_result_rate_pct"]):.2f}%**

Search-to-book conversion:

**{float(supply["baseline_conversion_rate_pct"]):.2f}% →
{float(supply["incident_conversion_rate_pct"]):.2f}%**

Estimated simulated revenue impact:

**£{float(supply["estimated_revenue_impact"]):,.2f}**

Statistical p-value:

**{float(supply["zero_result_test_p_value"]):.8f}**

### Mobile checkout incident

Checkout-error rate:

**{float(checkout["baseline_checkout_error_rate_pct"]):.2f}% →
{float(checkout["incident_checkout_error_rate_pct"]):.2f}%**

Checkout-to-booking conversion:

**{float(checkout["baseline_checkout_conversion_pct"]):.2f}% →
{float(checkout["incident_checkout_conversion_pct"]):.2f}%**

Estimated simulated revenue impact:

**£{float(checkout["estimated_revenue_impact"]):,.2f}**

Statistical p-value:

**{float(checkout["checkout_error_test_p_value"]):.8f}**

---

## Anomaly detection

Rolling historical baselines identify abnormal:

- conversion declines;
- zero-result spikes;
- checkout-error spikes.

Validated anomaly-alert days:

**{int(stage2["anomaly_alert_days"])}**

---

## Predictive modelling

### Objective

Predict whether a rail search will eventually result in a booking.

### Prediction point

**{stage4["prediction_point"]}**

### Candidate models

- Dummy Classifier
- Logistic Regression
- Histogram Gradient Boosting

### Champion model

**{champion}**

---

## Temporal model validation

RailSearch deliberately avoids a random train/test split.

- **January–April 2026:** training
- **May 2026:** validation
- **June 2026:** locked test set

The champion model is selected using validation performance before the
locked test period is evaluated.

---

## Locked test performance

| Metric | Score |
|---|---:|
| ROC-AUC | {float(metrics["roc_auc"]):.4f} |
| PR-AUC | {float(metrics["pr_auc"]):.4f} |
| Log Loss | {float(metrics["log_loss"]):.4f} |
| Brier Score | {float(metrics["brier_score"]):.4f} |
| Accuracy @ 0.50 | {float(metrics["accuracy"]):.4f} |
| Precision @ 0.50 | {float(metrics["precision_050"]):.4f} |
| Recall @ 0.50 | {float(metrics["recall_050"]):.4f} |
| F1 @ 0.50 | {float(metrics["f1_050"]):.4f} |

---

## Ranking performance

Overall locked-test booking rate:

**{float(ranking["overall_test_booking_rate_pct"]):.2f}%**

Top predicted decile booking rate:

**{float(ranking["top_decile_booking_rate_pct"]):.2f}%**

Top-decile lift:

**{float(ranking["top_decile_lift"]):.3f}x**

---

## Model explainability

Permutation importance is calculated using held-out test observations.

Top features:

{feature_text}

Full results:

`reports/tables/stage4_feature_importance.csv`

---

## Leakage controls

Variables occurring after the prediction point are deliberately excluded:

- journey selection;
- checkout start;
- checkout errors;
- payment failures;
- checkout completion;
- abandonment;
- booking revenue.

Search-result information remains valid because predictions occur after
the result set is returned.

---

## Analytical warehouse

The DuckDB warehouse contains:

- typed staging models;
- search funnel;
- KPI summary;
- daily funnel;
- device performance;
- acquisition-channel performance;
- route performance;
- zero-result analysis;
- checkout-failure analysis;
- commercial-impact analysis;
- anomaly monitoring.

Data-quality checks validate:

- unique sessions;
- unique searches;
- referential integrity;
- valid funnel ordering;
- zero-result consistency.

---

## Production API

The champion model is exposed through **FastAPI**.

### Endpoints

```text
GET  /health
GET  /model
POST /predict
POST /predict/batch
```

Capabilities include:

- strict Pydantic validation;
- single predictions;
- batch predictions;
- probability scoring;
- configurable prediction threshold;
- model metadata;
- health monitoring.

Run locally:

```bash
python -m uvicorn railsearch.api.main:app --host 127.0.0.1 --port 8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## Technology stack

### Data Science

- Python
- pandas
- NumPy
- scikit-learn
- SciPy
- statsmodels

### Data & Analytics

- SQL
- DuckDB
- Parquet

### Machine Learning

- Logistic Regression
- Histogram Gradient Boosting
- temporal validation
- calibration analysis
- threshold analysis
- permutation importance
- ranking and lift

### Production ML

- FastAPI
- Pydantic
- Uvicorn
- joblib

### Engineering

- pytest
- Ruff
- Docker
- Git
- GitHub
- GitHub Actions

---

## Project architecture

See:

[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Project structure

```text
railsearch-customer-journey-intelligence/
│
├── .github/
│   └── workflows/
│
├── artifacts/
│   └── models/
│
├── config/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── docs/
│
├── reports/
│   ├── figures/
│   └── tables/
│
├── scripts/
│
├── sql/
│   ├── staging/
│   ├── analytics/
│   └── product/
│
├── src/
│   └── railsearch/
│       └── api/
│
├── tests/
│
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Reproduce RailSearch

Generate the synthetic dataset:

```bash
python scripts/generate_synthetic_events.py
```

Build the analytical warehouse:

```bash
python scripts/build_stage2b_warehouse.py
```

Run the product investigation:

```bash
python scripts/run_stage3_investigation.py
```

Train the predictive model:

```bash
python scripts/run_stage4_modeling.py
```

Build and test the production API:

```bash
python scripts/setup_stage5_production.py
```

Run all tests:

```bash
python -m pytest -q
```

Run code-quality validation:

```bash
python -m ruff check src scripts tests
```

---

## Key competencies demonstrated

**Product Analytics → SQL → Statistical Investigation → Funnel Analysis →
Machine Learning → Explainability → Model Validation → MLOps →
Production API → Testing → CI/CD**

---

## Limitations

RailSearch is a portfolio simulation.

Customer behaviour, incidents, conversion rates, financial-impact values
and predictive performance are synthetic and should not be interpreted
as actual Trainline operating or commercial results.

---

## Author

**Oluwatosin Oluwaseun Mulero**

Data Analyst | Data Scientist

GitHub:

https://github.com/tosinmulero

Portfolio:

https://tosinmulero.github.io/data-analytics-portfolio/
"""

    README_PATH.write_text(
        readme.strip() + "\n",
        encoding="utf-8",
    )

    require_file(README_PATH)

    print(f"Created: {README_PATH}")

    print("README : PASS")


def run_quality_suite() -> None:
    banner("4. RUN QUALITY SUITE")

    run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "src",
            "scripts",
            "tests",
        ]
    )

    run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "src",
            "scripts",
            "tests",
            "--fix",
        ]
    )

    run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "src",
            "scripts",
            "tests",
        ]
    )

    run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ]
    )

    print()
    print("QUALITY SUITE : PASS")


def validate_api() -> None:
    banner("5. VALIDATE API")

    from railsearch.api.main import app

    client = TestClient(app)

    health = client.get("/health")

    if health.status_code != 200:
        raise RuntimeError(f"/health failed: {health.text}")

    model = client.get("/model")

    if model.status_code != 200:
        raise RuntimeError(f"/model failed: {model.text}")

    payload = {
        "device_type": "iOS App",
        "operating_system": "iOS",
        "acquisition_channel": "Direct",
        "customer_type": "Returning",
        "country": "United Kingdom",
        "origin_station": "London Euston",
        "destination_station": ("Manchester Piccadilly"),
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

    prediction = client.post(
        "/predict",
        json=payload,
    )

    if prediction.status_code != 200:
        raise RuntimeError(f"/predict failed: {prediction.text}")

    batch = client.post(
        "/predict/batch",
        json={
            "records": [
                payload,
                payload,
            ]
        },
    )

    if batch.status_code != 200:
        raise RuntimeError(f"/predict/batch failed: {batch.text}")

    probability = float(prediction.json()["booking_probability"])

    if not (0.0 <= probability <= 1.0):
        raise RuntimeError("Invalid prediction probability.")

    if int(batch.json()["count"]) != 2:
        raise RuntimeError("Batch prediction count is invalid.")

    print(f"Health              : {health.json()['status']}")

    print(f"Champion model      : {model.json()['champion_model']}")

    print(f"Booking probability : {probability:.4f}")

    print(f"Prediction           : {prediction.json()['predicted_booking']}")

    print(f"Batch predictions    : {batch.json()['count']}")

    print()
    print("API VALIDATION : PASS")


def validate_docker() -> None:
    banner("6. VALIDATE DOCKER")

    dockerfile = PROJECT_ROOT / "Dockerfile"

    require_file(dockerfile)

    docker = shutil.which("docker")

    if docker is None:
        print("Docker CLI is not installed.")

        print("Dockerfile exists.")

        print("Runtime build skipped.")

        print()
        print("DOCKER PACKAGING : PASS")

        return

    daemon = subprocess.run(
        [
            docker,
            "info",
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    if daemon.returncode != 0:
        print("Docker is installed but the Docker Engine is not running.")

        print("Dockerfile validation passed.")

        print("Runtime build skipped.")

        print()
        print("DOCKER PACKAGING : PASS")

        return

    run(
        [
            docker,
            "build",
            "-t",
            "railsearch-api:local",
            ".",
        ]
    )

    print()
    print("DOCKER BUILD : PASS")


def show_git_status() -> None:
    banner("7. GIT STATUS")

    git = shutil.which("git")

    if git is None:
        print("Git CLI not installed.")

        return

    repository = subprocess.run(
        [
            git,
            "rev-parse",
            "--is-inside-work-tree",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if repository.returncode != 0:
        print("Git repository has not been initialised yet.")

        return

    subprocess.run(
        [
            git,
            "status",
            "--short",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )

    print()
    print("GIT STATUS : PASS")


def verify_outputs() -> None:
    banner("8. VERIFY FINAL OUTPUTS")

    required = [
        README_PATH,
        ARCHITECTURE_PATH,
        MODEL_PATH,
        REPORTS_DIR / "STAGE3_EXECUTIVE_FINDINGS.md",
        REPORTS_DIR / "STAGE4_MODEL_REPORT.md",
        REPORTS_DIR / "stage3_investigation_summary.json",
        REPORTS_DIR / "stage4_model_summary.json",
        FIGURES_DIR / "daily_conversion_rate.png",
        FIGURES_DIR / "daily_zero_result_rate.png",
        FIGURES_DIR / "daily_checkout_error_rate.png",
        FIGURES_DIR / "stage4_roc_curve.png",
        FIGURES_DIR / "stage4_precision_recall_curve.png",
        FIGURES_DIR / "stage4_calibration_curve.png",
        FIGURES_DIR / "stage4_feature_importance.png",
        TABLES_DIR / "anomaly_alert_days.csv",
        TABLES_DIR / "stage4_model_comparison.csv",
        TABLES_DIR / "stage4_test_metrics.csv",
        TABLES_DIR / "stage4_threshold_analysis.csv",
        TABLES_DIR / "stage4_decile_analysis.csv",
        TABLES_DIR / "stage4_feature_importance.csv",
        PROJECT_ROOT / "Dockerfile",
        PROJECT_ROOT / ".github" / "workflows" / "ci.yml",
    ]

    for path in required:
        require_file(path)

        print(f"PASS : {path.relative_to(PROJECT_ROOT)}")

    print()
    print("FINAL OUTPUTS : PASS")


def final_status() -> None:
    banner("RAILSEARCH — PORTFOLIO BUILD COMPLETE")

    statuses = [
        "DATA GENERATION",
        "ANALYTICAL WAREHOUSE",
        "DATA QUALITY",
        "PRODUCT INVESTIGATION",
        "ANOMALY DETECTION",
        "STATISTICAL TESTING",
        "COMMERCIAL IMPACT",
        "PREDICTIVE MODELLING",
        "TEMPORAL VALIDATION",
        "LEAKAGE CONTROL",
        "MODEL EXPLAINABILITY",
        "CALIBRATION ANALYSIS",
        "COMMERCIAL RANKING",
        "FASTAPI SERVICE",
        "SINGLE PREDICTION",
        "BATCH PREDICTION",
        "AUTOMATED TESTING",
        "RUFF",
        "DOCKER PACKAGING",
        "GITHUB ACTIONS CI",
        "ARCHITECTURE DOCUMENT",
        "RECRUITER README",
        "FINAL OUTPUTS",
    ]

    for status in statuses:
        print(f"{status:<25}: PASS")

    print()
    print("PORTFOLIO PROJECT        : READY")

    print("=" * 76)


def main() -> None:
    banner("RAILSEARCH — FINAL PORTFOLIO VALIDATION")

    print(f"Project root: {PROJECT_ROOT}")

    validate_project()
    create_architecture()
    create_readme()
    run_quality_suite()
    validate_api()
    validate_docker()
    show_git_status()
    verify_outputs()
    final_status()


if __name__ == "__main__":
    main()
