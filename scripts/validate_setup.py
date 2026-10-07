import sys

import duckdb
import numpy as np
import pandas as pd
import sklearn
import yaml

from railsearch.config import PROJECT_ROOT, ensure_directories


def main() -> None:
    """Validate the RailSearch Stage 1 project setup."""

    ensure_directories()

    required_paths = [
        "data/raw",
        "data/interim",
        "data/processed",
        "data/external",
        "src/railsearch",
        "src/railsearch/data",
        "src/railsearch/features",
        "src/railsearch/analytics",
        "src/railsearch/models",
        "src/railsearch/utils",
        "sql/staging",
        "sql/analytics",
        "sql/product",
        "tests",
        "docs",
        "reports/figures",
        "config/data_contract.yml",
        "docs/PROJECT_SCOPE.md",
        "docs/METRIC_DEFINITIONS.md",
        "README.md",
        "pyproject.toml",
        "requirements.txt",
    ]

    missing = [path for path in required_paths if not (PROJECT_ROOT / path).exists()]

    contract_path = PROJECT_ROOT / "config" / "data_contract.yml"

    with contract_path.open(encoding="utf-8-sig") as file:
        contract = yaml.safe_load(file)

    expected_datasets = {
        "sessions",
        "searches",
        "journey_results",
        "checkout",
        "bookings",
        "station_reference",
    }

    actual_datasets = set(contract.get("datasets", {}).keys())

    print()
    print("=" * 70)
    print("RAILSEARCH — STAGE 1 VALIDATION")
    print("=" * 70)

    print(f"Project root     : {PROJECT_ROOT}")
    print(f"Python           : {sys.version.split()[0]}")
    print(f"Pandas           : {pd.__version__}")
    print(f"NumPy            : {np.__version__}")
    print(f"Scikit-learn     : {sklearn.__version__}")
    print(f"DuckDB           : {duckdb.__version__}")
    print(f"Datasets defined : {len(actual_datasets)}")

    print()

    if missing:
        print("PROJECT STRUCTURE : FAIL")
        print()
        print("Missing:")
        for path in missing:
            print(f"  - {path}")
        raise SystemExit(1)

    print("PROJECT STRUCTURE : PASS")

    if actual_datasets != expected_datasets:
        print("DATA CONTRACT     : FAIL")
        print(f"Expected: {sorted(expected_datasets)}")
        print(f"Actual  : {sorted(actual_datasets)}")
        raise SystemExit(1)

    print("DATA CONTRACT     : PASS")
    print("PYTHON IMPORTS    : PASS")
    print("STAGE 1           : PASS")

    print("=" * 70)


if __name__ == "__main__":
    main()
