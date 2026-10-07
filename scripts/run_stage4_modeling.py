# ruff: noqa: E501

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

RANDOM_STATE = 42

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "data" / "processed" / "railsearch.duckdb"

REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODEL_DIR = ARTIFACTS_DIR / "models"

SUMMARY_PATH = REPORTS_DIR / "stage4_model_summary.json"

REPORT_PATH = REPORTS_DIR / "STAGE4_MODEL_REPORT.md"

MODEL_PATH = MODEL_DIR / "railsearch_conversion_model.joblib"

PREDICTIONS_PATH = ARTIFACTS_DIR / "stage4_test_predictions.parquet"

CATEGORICAL_FEATURES = [
    "device_type",
    "operating_system",
    "acquisition_channel",
    "customer_type",
    "country",
    "origin_station",
    "destination_station",
    "journey_type",
]

NUMERIC_FEATURES = [
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

FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

TARGET = "booked_flag"


def banner(title: str) -> None:
    print()
    print("=" * 76)
    print(title)
    print("=" * 76)


def ensure_directories() -> None:
    for path in [
        REPORTS_DIR,
        FIGURES_DIR,
        TABLES_DIR,
        ARTIFACTS_DIR,
        MODEL_DIR,
    ]:
        path.mkdir(
            parents=True,
            exist_ok=True,
        )


def load_dataset() -> pd.DataFrame:
    banner("1. LOAD LEAKAGE-SAFE MODELLING DATA")

    if not DB_PATH.exists():
        raise FileNotFoundError(f"DuckDB warehouse not found: {DB_PATH}")

    connection = duckdb.connect(
        str(DB_PATH),
        read_only=True,
    )

    query = """
        SELECT
            f.search_id,

            CAST(
                s.searched_at AS TIMESTAMP
            ) AS searched_at,

            CAST(
                f.booked_flag AS INTEGER
            ) AS booked_flag,

            sess.device_type,
            sess.operating_system,
            sess.acquisition_channel,
            sess.customer_type,
            sess.country,

            CAST(
                sess.is_logged_in AS INTEGER
            ) AS is_logged_in,

            s.origin_station,
            s.destination_station,

            CAST(
                s.passengers AS INTEGER
            ) AS passengers,

            s.journey_type,

            CAST(
                s.railcard_used AS INTEGER
            ) AS railcard_used,

            CAST(
                s.results_count AS INTEGER
            ) AS results_count,

            CAST(
                s.search_latency_ms AS DOUBLE
            ) AS search_latency_ms,

            CAST(
                s.zero_results_flag AS INTEGER
            ) AS zero_results_flag,

            date_diff(
                'day',
                CAST(s.searched_at AS DATE),
                CAST(s.travel_date AS DATE)
            ) AS days_before_travel,

            CAST(
                EXTRACT(
                    'hour'
                    FROM s.searched_at
                )
                AS INTEGER
            ) AS search_hour,

            CAST(
                EXTRACT(
                    'dow'
                    FROM s.searched_at
                )
                AS INTEGER
            ) AS day_of_week,

            CAST(
                EXTRACT(
                    'month'
                    FROM s.searched_at
                )
                AS INTEGER
            ) AS search_month

        FROM analytics.search_funnel AS f

        INNER JOIN staging.searches AS s
            ON f.search_id = s.search_id

        INNER JOIN staging.sessions AS sess
            ON s.session_id = sess.session_id

        ORDER BY s.searched_at
    """

    data = connection.execute(query).fetchdf()

    connection.close()

    required = [
        "search_id",
        "searched_at",
        TARGET,
        *FEATURES,
    ]

    missing = [column for column in required if column not in data.columns]

    if missing:
        raise RuntimeError(f"Required modelling columns missing: {missing}")

    if data["search_id"].duplicated().any():
        raise RuntimeError("Duplicate search_id values detected.")

    if not set(data[TARGET].dropna().unique()).issubset({0, 1}):
        raise RuntimeError("Target must be binary.")

    print(f"Rows loaded       : {len(data):,}")

    print(f"Features          : {len(FEATURES)}")

    print("Prediction point  : after search results, before journey selection")

    print("Target            : eventual booking")

    print()
    print("MODELLING DATA : PASS")

    return data


def temporal_split(
    data: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    banner("2. TEMPORAL TRAIN / VALIDATION / TEST SPLIT")

    data = data.copy()

    data["searched_at"] = pd.to_datetime(data["searched_at"])

    train = data.loc[data["searched_at"] < pd.Timestamp("2026-05-01")].copy()

    validation = data.loc[
        (data["searched_at"] >= pd.Timestamp("2026-05-01"))
        & (data["searched_at"] < pd.Timestamp("2026-06-01"))
    ].copy()

    test = data.loc[data["searched_at"] >= pd.Timestamp("2026-06-01")].copy()

    splits = {
        "Train": train,
        "Validation": validation,
        "Test": test,
    }

    for name, frame in splits.items():
        if frame.empty:
            raise RuntimeError(f"{name} split is empty.")

        rate = 100 * frame[TARGET].mean()

        print(f"{name:<12}{len(frame):>10,} rows  booking rate = {rate:>6.2f}%")

    if train["searched_at"].max() >= validation["searched_at"].min():
        raise RuntimeError("Temporal leakage detected between training and validation.")

    if validation["searched_at"].max() >= test["searched_at"].min():
        raise RuntimeError("Temporal leakage detected between validation and test.")

    print()
    print("TEMPORAL SPLIT : PASS")

    return (
        train,
        validation,
        test,
    )


def build_models() -> dict[str, Pipeline]:
    categorical_logistic = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore"),
            ),
        ]
    )

    numeric_logistic = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    logistic_preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                categorical_logistic,
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                numeric_logistic,
                NUMERIC_FEATURES,
            ),
        ],
    )

    logistic = Pipeline(
        steps=[
            (
                "preprocessor",
                logistic_preprocessor,
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    solver="saga",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    categorical_tree = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OrdinalEncoder(
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                ),
            ),
        ]
    )

    numeric_tree = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
        ]
    )

    tree_preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                categorical_tree,
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                numeric_tree,
                NUMERIC_FEATURES,
            ),
        ]
    )

    gradient_boosting = Pipeline(
        steps=[
            (
                "preprocessor",
                tree_preprocessor,
            ),
            (
                "classifier",
                HistGradientBoostingClassifier(
                    learning_rate=0.08,
                    max_iter=250,
                    max_leaf_nodes=31,
                    min_samples_leaf=40,
                    l2_regularization=0.5,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    dummy = Pipeline(
        steps=[
            (
                "classifier",
                DummyClassifier(strategy="prior"),
            )
        ]
    )

    return {
        "Dummy Baseline": dummy,
        "Logistic Regression": logistic,
        "Histogram Gradient Boosting": gradient_boosting,
    }


def evaluate_probabilities(
    y_true: pd.Series,
    probabilities: np.ndarray,
) -> dict[str, float]:
    predictions = (probabilities >= 0.50).astype(int)

    return {
        "roc_auc": float(
            roc_auc_score(
                y_true,
                probabilities,
            )
        ),
        "pr_auc": float(
            average_precision_score(
                y_true,
                probabilities,
            )
        ),
        "log_loss": float(
            log_loss(
                y_true,
                probabilities,
            )
        ),
        "brier_score": float(
            brier_score_loss(
                y_true,
                probabilities,
            )
        ),
        "accuracy": float(
            accuracy_score(
                y_true,
                predictions,
            )
        ),
        "precision_050": float(
            precision_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),
        "recall_050": float(
            recall_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),
        "f1_050": float(
            f1_score(
                y_true,
                predictions,
                zero_division=0,
            )
        ),
    }


def train_validation_models(
    train: pd.DataFrame,
    validation: pd.DataFrame,
) -> tuple[
    dict[str, Pipeline],
    pd.DataFrame,
    str,
]:
    banner("3. TRAIN + VALIDATE CANDIDATE MODELS")

    models = build_models()

    x_train = train[FEATURES]
    y_train = train[TARGET]

    x_validation = validation[FEATURES]
    y_validation = validation[TARGET]

    results = []

    fitted_models = {}

    for name, model in models.items():
        print()
        print(f"Training {name}...")

        model.fit(
            x_train,
            y_train,
        )

        probabilities = model.predict_proba(x_validation)[:, 1]

        metrics = evaluate_probabilities(
            y_validation,
            probabilities,
        )

        results.append(
            {
                "model": name,
                **metrics,
            }
        )

        fitted_models[name] = model

        print(f"ROC-AUC : {metrics['roc_auc']:.4f}")

        print(f"PR-AUC  : {metrics['pr_auc']:.4f}")

        print(f"Log Loss: {metrics['log_loss']:.4f}")

    comparison = pd.DataFrame(results).sort_values(
        [
            "pr_auc",
            "roc_auc",
        ],
        ascending=False,
    )

    best_model_name = comparison.iloc[0]["model"]

    comparison.to_csv(
        TABLES_DIR / "stage4_model_comparison.csv",
        index=False,
    )

    print()
    print(f"Selected model : {best_model_name}")

    print()
    print("MODEL VALIDATION : PASS")

    return (
        fitted_models,
        comparison,
        best_model_name,
    )


def refit_best_model(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    fitted_models: dict[str, Pipeline],
    best_model_name: str,
) -> Pipeline:
    banner("4. REFIT CHAMPION MODEL")

    champion_template = fitted_models[best_model_name]

    champion = clone(champion_template)

    train_validation = pd.concat(
        [
            train,
            validation,
        ],
        ignore_index=True,
    )

    champion.fit(
        train_validation[FEATURES],
        train_validation[TARGET],
    )

    joblib.dump(
        champion,
        MODEL_PATH,
    )

    print(f"Champion model : {best_model_name}")

    print(f"Saved model    : {MODEL_PATH}")

    print()
    print("CHAMPION REFIT : PASS")

    return champion


def evaluate_test_set(
    champion: Pipeline,
    test: pd.DataFrame,
) -> tuple[
    np.ndarray,
    dict[str, float],
]:
    banner("5. LOCKED TEST-SET EVALUATION")

    x_test = test[FEATURES]
    y_test = test[TARGET]

    probabilities = champion.predict_proba(x_test)[:, 1]

    metrics = evaluate_probabilities(
        y_test,
        probabilities,
    )

    for name, value in metrics.items():
        print(f"{name:<18}: {value:.4f}")

    predictions = test[
        [
            "search_id",
            "searched_at",
            TARGET,
        ]
    ].copy()

    predictions["booking_probability"] = probabilities

    predictions["predicted_booking_050"] = (probabilities >= 0.50).astype(int)

    predictions.to_parquet(
        PREDICTIONS_PATH,
        index=False,
    )

    pd.DataFrame(
        [
            {
                "metric": key,
                "value": value,
            }
            for key, value in metrics.items()
        ]
    ).to_csv(
        TABLES_DIR / "stage4_test_metrics.csv",
        index=False,
    )

    print()
    print("LOCKED TEST EVALUATION : PASS")

    return (
        probabilities,
        metrics,
    )


def create_threshold_analysis(
    y_true: pd.Series,
    probabilities: np.ndarray,
) -> pd.DataFrame:
    thresholds = np.arange(
        0.10,
        0.81,
        0.05,
    )

    rows = []

    for threshold in thresholds:
        predictions = (probabilities >= threshold).astype(int)

        rows.append(
            {
                "threshold": round(
                    float(threshold),
                    2,
                ),
                "predicted_positive_rate_pct": round(
                    float(100 * predictions.mean()),
                    2,
                ),
                "precision": float(
                    precision_score(
                        y_true,
                        predictions,
                        zero_division=0,
                    )
                ),
                "recall": float(
                    recall_score(
                        y_true,
                        predictions,
                        zero_division=0,
                    )
                ),
                "f1": float(
                    f1_score(
                        y_true,
                        predictions,
                        zero_division=0,
                    )
                ),
            }
        )

    table = pd.DataFrame(rows)

    table.to_csv(
        TABLES_DIR / "stage4_threshold_analysis.csv",
        index=False,
    )

    return table


def create_ranking_analysis(
    test: pd.DataFrame,
    probabilities: np.ndarray,
) -> dict[str, float]:
    ranked = test[
        [
            "search_id",
            TARGET,
        ]
    ].copy()

    ranked["booking_probability"] = probabilities

    ranked = ranked.sort_values(
        "booking_probability",
        ascending=False,
    ).reset_index(drop=True)

    ranked["decile"] = pd.qcut(
        ranked.index,
        q=10,
        labels=[
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
        ],
    )

    deciles = (
        ranked.groupby(
            "decile",
            observed=True,
        )
        .agg(
            searches=(
                "search_id",
                "count",
            ),
            bookings=(
                TARGET,
                "sum",
            ),
            actual_booking_rate=(
                TARGET,
                "mean",
            ),
            avg_predicted_probability=(
                "booking_probability",
                "mean",
            ),
        )
        .reset_index()
    )

    deciles["actual_booking_rate_pct"] = 100 * deciles["actual_booking_rate"]

    deciles["avg_predicted_probability_pct"] = 100 * deciles["avg_predicted_probability"]

    deciles.to_csv(
        TABLES_DIR / "stage4_decile_analysis.csv",
        index=False,
    )

    overall_rate = float(ranked[TARGET].mean())

    top_decile = ranked.iloc[
        : max(
            1,
            int(len(ranked) * 0.10),
        )
    ]

    top_decile_rate = float(top_decile[TARGET].mean())

    lift = top_decile_rate / overall_rate if overall_rate > 0 else 0.0

    return {
        "overall_test_booking_rate_pct": round(
            100 * overall_rate,
            2,
        ),
        "top_decile_booking_rate_pct": round(
            100 * top_decile_rate,
            2,
        ),
        "top_decile_lift": round(
            lift,
            3,
        ),
    }


def calculate_permutation_importance(
    champion: Pipeline,
    test: pd.DataFrame,
) -> pd.DataFrame:
    banner("6. MODEL EXPLAINABILITY")

    sample_size = min(
        25_000,
        len(test),
    )

    sample = test.sample(
        n=sample_size,
        random_state=RANDOM_STATE,
    )

    result = permutation_importance(
        champion,
        sample[FEATURES],
        sample[TARGET],
        scoring="average_precision",
        n_repeats=3,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    importance = pd.DataFrame(
        {
            "feature": FEATURES,
            "importance_mean": (result.importances_mean),
            "importance_std": (result.importances_std),
        }
    ).sort_values(
        "importance_mean",
        ascending=False,
    )

    importance.to_csv(
        TABLES_DIR / "stage4_feature_importance.csv",
        index=False,
    )

    print(f"Permutation sample : {sample_size:,}")

    print()
    print("Top features:")

    print(importance.head(10).to_string(index=False))

    print()
    print("EXPLAINABILITY : PASS")

    return importance


def create_calibration_table(
    y_true: pd.Series,
    probabilities: np.ndarray,
) -> pd.DataFrame:
    observed, predicted = calibration_curve(
        y_true,
        probabilities,
        n_bins=10,
        strategy="quantile",
    )

    calibration = pd.DataFrame(
        {
            "mean_predicted_probability": (predicted),
            "observed_booking_rate": (observed),
        }
    )

    calibration.to_csv(
        TABLES_DIR / "stage4_calibration.csv",
        index=False,
    )

    return calibration


def create_figures(
    y_test: pd.Series,
    probabilities: np.ndarray,
    importance: pd.DataFrame,
    calibration: pd.DataFrame,
) -> None:
    banner("7. CREATE MODEL FIGURES")

    fpr, tpr, _ = roc_curve(
        y_test,
        probabilities,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.plot(
        fpr,
        tpr,
        label=(f"Champion ROC-AUC = {roc_auc:.3f}"),
    )

    ax.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        label="Random baseline",
    )

    ax.set_xlabel("False positive rate")

    ax.set_ylabel("True positive rate")

    ax.set_title("RailSearch Conversion Model — ROC Curve")

    ax.legend()

    fig.tight_layout()

    fig.savefig(
        FIGURES_DIR / "stage4_roc_curve.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    precision, recall, _ = precision_recall_curve(
        y_test,
        probabilities,
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities,
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.plot(
        recall,
        precision,
        label=(f"Champion PR-AUC = {pr_auc:.3f}"),
    )

    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")

    ax.set_title("RailSearch Conversion Model — Precision-Recall Curve")

    ax.legend()

    fig.tight_layout()

    fig.savefig(
        FIGURES_DIR / "stage4_precision_recall_curve.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.plot(
        calibration["mean_predicted_probability"],
        calibration["observed_booking_rate"],
        marker="o",
        label="Champion model",
    )

    ax.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        label="Perfect calibration",
    )

    ax.set_xlabel("Mean predicted booking probability")

    ax.set_ylabel("Observed booking rate")

    ax.set_title("RailSearch Conversion Model — Calibration")

    ax.legend()

    fig.tight_layout()

    fig.savefig(
        FIGURES_DIR / "stage4_calibration_curve.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    top = importance.head(12).sort_values("importance_mean")

    fig, ax = plt.subplots(figsize=(10, 7))

    ax.barh(
        top["feature"],
        top["importance_mean"],
    )

    ax.set_xlabel("Decrease in PR-AUC after permutation")

    ax.set_ylabel("Feature")

    ax.set_title("RailSearch Conversion Model — Feature Importance")

    fig.tight_layout()

    fig.savefig(
        FIGURES_DIR / "stage4_feature_importance.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    print("MODEL FIGURES : PASS")


def python_value(value):
    if isinstance(
        value,
        np.generic,
    ):
        return value.item()

    return value


def build_report(
    best_model_name: str,
    comparison: pd.DataFrame,
    metrics: dict[str, float],
    ranking: dict[str, float],
    importance: pd.DataFrame,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
) -> None:
    best_validation = comparison.loc[comparison["model"] == best_model_name].iloc[0]

    top_features = "\n".join(
        [f"- {row.feature}: {row.importance_mean:.5f}" for row in importance.head(10).itertuples()]
    )

    report = f"""
# RailSearch — Stage 4 Predictive Conversion Modelling

## Objective

Predict whether a rail search will ultimately result in a booking.

The prediction point is immediately after search results are returned and before the customer selects a journey.

This prevents leakage from downstream events such as journey selection, checkout errors, payment failures, checkout completion and revenue.

## Dataset

- Training observations: {len(train):,}
- Validation observations: {len(validation):,}
- Locked test observations: {len(test):,}
- Prediction features: {len(FEATURES)}
- Target: eventual booking
- Split strategy: temporal

Training covers January–April 2026, validation covers May 2026, and the locked test set covers June 2026.

## Champion model

Selected model: **{best_model_name}**

Validation PR-AUC: {best_validation["pr_auc"]:.4f}

Validation ROC-AUC: {best_validation["roc_auc"]:.4f}

The model was selected using validation performance only. The test period remained locked until model selection was complete.

## Locked test performance

- ROC-AUC: {metrics["roc_auc"]:.4f}
- PR-AUC: {metrics["pr_auc"]:.4f}
- Log loss: {metrics["log_loss"]:.4f}
- Brier score: {metrics["brier_score"]:.4f}
- Accuracy at 0.50: {metrics["accuracy"]:.4f}
- Precision at 0.50: {metrics["precision_050"]:.4f}
- Recall at 0.50: {metrics["recall_050"]:.4f}
- F1 at 0.50: {metrics["f1_050"]:.4f}

## Ranking value

- Overall test booking rate: {ranking["overall_test_booking_rate_pct"]:.2f}%
- Top predicted decile booking rate: {ranking["top_decile_booking_rate_pct"]:.2f}%
- Top-decile lift: {ranking["top_decile_lift"]:.3f}x

This demonstrates whether the model can meaningfully rank customer searches by likelihood to convert.

## Most influential features

{top_features}

Permutation importance is calculated against PR-AUC on a held-out test sample.

## Product interpretation

The model is designed as a reusable decision-support component rather than an automated customer decision system.

Potential product applications include:

1. identifying search contexts with unusually low conversion propensity;
2. prioritising customer-journey investigations;
3. comparing predicted versus observed conversion by route or device;
4. supporting experimentation and intervention targeting;
5. detecting changing customer behaviour through model monitoring.

## Leakage controls

The model excludes downstream variables including:

- journey selected flag;
- checkout started flag;
- checkout error flag;
- payment failure flag;
- checkout completion flag;
- checkout abandonment flag;
- booking revenue.

Search-result availability is retained because the prediction point occurs after search results are returned.

## Limitations

RailSearch uses synthetic customer-journey data created for portfolio demonstration.

The model therefore demonstrates methodology, engineering discipline and product-science workflow. Its performance must not be interpreted as Trainline production performance or actual commercial behaviour.
"""

    REPORT_PATH.write_text(
        report.strip() + "\n",
        encoding="utf-8",
    )


def verify_outputs() -> None:
    required = [
        MODEL_PATH,
        PREDICTIONS_PATH,
        REPORT_PATH,
        SUMMARY_PATH,
        TABLES_DIR / "stage4_model_comparison.csv",
        TABLES_DIR / "stage4_test_metrics.csv",
        TABLES_DIR / "stage4_threshold_analysis.csv",
        TABLES_DIR / "stage4_decile_analysis.csv",
        TABLES_DIR / "stage4_feature_importance.csv",
        TABLES_DIR / "stage4_calibration.csv",
        FIGURES_DIR / "stage4_roc_curve.png",
        FIGURES_DIR / "stage4_precision_recall_curve.png",
        FIGURES_DIR / "stage4_calibration_curve.png",
        FIGURES_DIR / "stage4_feature_importance.png",
    ]

    missing = [path for path in required if not (path.exists() and path.stat().st_size > 0)]

    if missing:
        raise RuntimeError("Missing Stage 4 outputs:\n" + "\n".join(str(path) for path in missing))


def main() -> None:
    ensure_directories()

    banner("RAILSEARCH — STAGE 4 PREDICTIVE CONVERSION MODELLING")

    data = load_dataset()

    train, validation, test = temporal_split(data)

    fitted_models, comparison, best_model_name = train_validation_models(
        train,
        validation,
    )

    champion = refit_best_model(
        train,
        validation,
        fitted_models,
        best_model_name,
    )

    probabilities, test_metrics = evaluate_test_set(
        champion,
        test,
    )

    threshold_table = create_threshold_analysis(
        test[TARGET],
        probabilities,
    )

    ranking = create_ranking_analysis(
        test,
        probabilities,
    )

    importance = calculate_permutation_importance(
        champion,
        test,
    )

    calibration = create_calibration_table(
        test[TARGET],
        probabilities,
    )

    create_figures(
        test[TARGET],
        probabilities,
        importance,
        calibration,
    )

    build_report(
        best_model_name,
        comparison,
        test_metrics,
        ranking,
        importance,
        train,
        validation,
        test,
    )

    summary = {
        "champion_model": (best_model_name),
        "prediction_point": ("after search results and before journey selection"),
        "features": FEATURES,
        "train_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "test_rows": int(len(test)),
        "test_metrics": {key: python_value(value) for key, value in test_metrics.items()},
        "ranking": ranking,
        "best_f1_threshold": float(
            threshold_table.loc[
                threshold_table["f1"].idxmax(),
                "threshold",
            ]
        ),
        "top_features": (
            importance.head(10)[
                [
                    "feature",
                    "importance_mean",
                ]
            ].to_dict(orient="records")
        ),
    }

    SUMMARY_PATH.write_text(
        json.dumps(
            summary,
            indent=2,
            default=python_value,
        ),
        encoding="utf-8",
    )

    verify_outputs()

    banner("RAILSEARCH — STAGE 4 RESULTS")

    print(f"Champion model       : {best_model_name}")

    print(f"Test ROC-AUC         : {test_metrics['roc_auc']:.4f}")

    print(f"Test PR-AUC          : {test_metrics['pr_auc']:.4f}")

    print(f"Test Log Loss        : {test_metrics['log_loss']:.4f}")

    print(f"Test Brier Score     : {test_metrics['brier_score']:.4f}")

    print(f"Top-decile lift      : {ranking['top_decile_lift']:.3f}x")

    print(f"Best F1 threshold    : {summary['best_f1_threshold']:.2f}")

    print()
    print(f"Model artifact       : {MODEL_PATH}")

    print(f"Executive report     : {REPORT_PATH}")

    print(f"Test predictions     : {PREDICTIONS_PATH}")

    print()
    print("TEMPORAL VALIDATION       : PASS")

    print("LEAKAGE CONTROL           : PASS")

    print("MODEL COMPARISON          : PASS")

    print("LOCKED TEST EVALUATION    : PASS")

    print("MODEL EXPLAINABILITY      : PASS")

    print("CALIBRATION ANALYSIS      : PASS")

    print("COMMERCIAL RANKING        : PASS")

    print("STAGE 4                   : PASS")

    print("=" * 76)


if __name__ == "__main__":
    main()
