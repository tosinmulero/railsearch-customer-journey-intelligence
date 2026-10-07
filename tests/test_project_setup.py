import yaml

from railsearch.config import PROJECT_ROOT


def test_project_root_exists() -> None:
    assert PROJECT_ROOT.exists()


def test_required_directories_exist() -> None:
    expected_directories = [
        "data/raw",
        "data/interim",
        "data/processed",
        "data/external",
        "docs",
        "reports",
        "reports/figures",
        "sql",
        "sql/staging",
        "sql/analytics",
        "sql/product",
        "src/railsearch",
        "src/railsearch/data",
        "src/railsearch/features",
        "src/railsearch/analytics",
        "src/railsearch/models",
        "src/railsearch/utils",
    ]

    for directory in expected_directories:
        assert (PROJECT_ROOT / directory).exists(), f"Missing directory: {directory}"


def test_required_documentation_exists() -> None:
    expected_files = [
        "README.md",
        "pyproject.toml",
        "requirements.txt",
        "config/data_contract.yml",
        "docs/PROJECT_SCOPE.md",
        "docs/METRIC_DEFINITIONS.md",
    ]

    for file_path in expected_files:
        assert (PROJECT_ROOT / file_path).exists(), f"Missing file: {file_path}"


def test_data_contract_contains_core_datasets() -> None:
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

    assert set(contract["datasets"].keys()) == expected_datasets


def test_customer_journey_tables_have_primary_keys() -> None:
    contract_path = PROJECT_ROOT / "config" / "data_contract.yml"

    with contract_path.open(encoding="utf-8-sig") as file:
        contract = yaml.safe_load(file)

    datasets = contract["datasets"]

    for dataset_name in [
        "sessions",
        "searches",
        "journey_results",
        "checkout",
        "bookings",
        "station_reference",
    ]:
        assert "primary_key" in datasets[dataset_name]
        assert datasets[dataset_name]["primary_key"]
