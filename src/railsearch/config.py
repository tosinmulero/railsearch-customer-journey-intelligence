from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
SQL_DIR = PROJECT_ROOT / "sql"
CONFIG_DIR = PROJECT_ROOT / "config"
DOCS_DIR = PROJECT_ROOT / "docs"


def ensure_directories() -> None:
    """Create required project directories when missing."""

    required_directories = [
        RAW_DATA_DIR,
        INTERIM_DATA_DIR,
        PROCESSED_DATA_DIR,
        EXTERNAL_DATA_DIR,
        REPORTS_DIR,
        FIGURES_DIR,
        ARTIFACTS_DIR,
        DASHBOARD_DIR,
        SQL_DIR,
        CONFIG_DIR,
        DOCS_DIR,
    ]

    for directory in required_directories:
        directory.mkdir(parents=True, exist_ok=True)
