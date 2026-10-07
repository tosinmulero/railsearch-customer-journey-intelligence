# ruff: noqa: E501

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

GENERATOR = SCRIPTS_DIR / "generate_synthetic_events.py"
STAGE2B = SCRIPTS_DIR / "build_stage2b_warehouse.py"
STAGE3 = SCRIPTS_DIR / "run_stage3_investigation.py"
VALIDATOR = SCRIPTS_DIR / "validate_setup.py"

DATABASE = PROCESSED_DIR / "railsearch.duckdb"
STAGE2B_SUMMARY = PROCESSED_DIR / "stage2b_warehouse_summary.json"

REQUIRED_RAW_FILES = [
    RAW_DIR / "station_reference.parquet",
    RAW_DIR / "sessions.parquet",
    RAW_DIR / "searches.parquet",
    RAW_DIR / "journey_results.parquet",
    RAW_DIR / "checkout.parquet",
    RAW_DIR / "bookings.parquet",
]

EXPECTED_STAGE3_OUTPUTS = [
    REPORTS_DIR / "STAGE3_EXECUTIVE_FINDINGS.md",
    REPORTS_DIR / "stage3_investigation_summary.json",
    FIGURES_DIR / "daily_conversion_rate.png",
    FIGURES_DIR / "daily_zero_result_rate.png",
    FIGURES_DIR / "daily_checkout_error_rate.png",
    TABLES_DIR / "overall_funnel.csv",
    TABLES_DIR / "segment_performance.csv",
    TABLES_DIR / "supply_incident_comparison.csv",
    TABLES_DIR / "checkout_incident_comparison.csv",
    TABLES_DIR / "anomaly_alert_days.csv",
    TABLES_DIR / "route_opportunities.csv",
]


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


def force_delete_file(path: Path) -> None:
    if not path.exists():
        return

    try:
        path.chmod(stat.S_IWRITE | stat.S_IREAD)
    except OSError:
        pass

    try:
        path.unlink()
    except PermissionError:
        print(f"WARNING: Could not delete locked file: {path}")


def force_delete_tree(path: Path) -> None:
    if not path.exists():
        return

    def onerror(function, item, exc_info):
        del exc_info

        try:
            os.chmod(
                item,
                stat.S_IWRITE | stat.S_IREAD,
            )
            function(item)
        except OSError:
            pass

    try:
        shutil.rmtree(
            path,
            onerror=onerror,
        )
    except (PermissionError, OSError):
        print(f"WARNING: Windows would not remove {path}. It will be ignored.")


def verify_project_root() -> None:
    banner("1. VERIFY PROJECT ROOT")

    print(f"Repair script : {Path(__file__).resolve()}")
    print(f"Project root  : {PROJECT_ROOT}")

    expected = "railsearch-customer-journey-intelligence"

    if PROJECT_ROOT.name != expected:
        raise RuntimeError("This repair file is not inside the correct RailSearch scripts folder.")

    print()
    print("PROJECT ROOT : PASS")


def repair_script_locations() -> None:
    banner("2. REPAIR SCRIPT LOCATIONS")

    SCRIPTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    root_stage3 = PROJECT_ROOT / "run_stage3_investigation.py"

    root_generator = PROJECT_ROOT / "generate_synthetic_events.py"

    nested_stage3 = SCRIPTS_DIR / "scripts" / "run_stage3_investigation.py"

    nested_generator = SCRIPTS_DIR / "scripts" / "generate_synthetic_events.py"

    if not STAGE3.exists():
        if root_stage3.exists():
            shutil.copy2(
                root_stage3,
                STAGE3,
            )

        elif nested_stage3.exists():
            shutil.copy2(
                nested_stage3,
                STAGE3,
            )

    if not GENERATOR.exists():
        if root_generator.exists():
            shutil.copy2(
                root_generator,
                GENERATOR,
            )

        elif nested_generator.exists():
            shutil.copy2(
                nested_generator,
                GENERATOR,
            )

    required_scripts = [
        GENERATOR,
        STAGE2B,
        STAGE3,
        VALIDATOR,
    ]

    missing = [path for path in required_scripts if not path.exists()]

    if missing:
        raise FileNotFoundError(
            "Required scripts missing:\n" + "\n".join(str(path) for path in missing)
        )

    force_delete_file(root_stage3)

    force_delete_file(root_generator)

    force_delete_tree(SCRIPTS_DIR / "scripts")

    force_delete_tree(SCRIPTS_DIR / "data")

    print("SCRIPT LOCATIONS : PASS")


def patch_stage3() -> None:
    banner("3. PATCH STAGE 3")

    text = STAGE3.read_text(
        encoding="utf-8-sig",
    )

    project_root_pattern = re.compile(
        r"^PROJECT_ROOT\s*=.*$",
        flags=re.MULTILINE,
    )

    correct_project_root = "PROJECT_ROOT = Path(__file__).resolve().parents[1]"

    if project_root_pattern.search(text):
        text = project_root_pattern.sub(
            correct_project_root,
            text,
            count=1,
        )
    else:
        raise RuntimeError("Could not locate PROJECT_ROOT inside Stage 3.")

    if "# ruff: noqa: E501" not in text[:200]:
        text = "# ruff: noqa: E501\n\n" + text

    STAGE3.write_text(
        text,
        encoding="utf-8",
    )

    print("PROJECT_ROOT = Path(__file__).resolve().parents[1]")

    print("STAGE 3 PATCH : PASS")


def verify_raw_data() -> None:
    banner("4. VERIFY RAW DATA")

    missing = []

    for path in REQUIRED_RAW_FILES:
        if path.exists() and path.stat().st_size > 0:
            size_mb = path.stat().st_size / 1_048_576

            print(f"{path.name:<30}PASS  {size_mb:>8.2f} MB")

        else:
            missing.append(path)

            print(f"{path.name:<30}MISSING")

    if missing:
        print()
        print("Raw datasets are incomplete.")

        print("Regenerating Stage 2A automatically...")

        run(
            [
                sys.executable,
                str(GENERATOR),
            ]
        )

    for path in REQUIRED_RAW_FILES:
        if not path.exists():
            raise FileNotFoundError(f"Still missing after regeneration: {path}")

    print()
    print("RAW DATA : PASS")


def prepare_report_directories() -> None:
    banner("5. PREPARE REPORT DIRECTORIES")

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TABLES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Existing report directories retained.")

    print("No directory deletion will be attempted.")

    print("New Stage 3 outputs will overwrite their existing files.")

    print()
    print("REPORT DIRECTORIES : PASS")


def format_and_lint() -> None:
    banner("6. FORMAT + LINT")

    files = [
        GENERATOR,
        STAGE2B,
        STAGE3,
        VALIDATOR,
    ]

    for path in files:
        run(
            [
                sys.executable,
                "-m",
                "ruff",
                "format",
                str(path),
            ]
        )

    for path in files:
        run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                str(path),
                "--fix",
            ]
        )

    for path in files:
        run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                str(path),
            ]
        )

    print("RUFF : PASS")


def rebuild_stage2b() -> None:
    banner("7. REBUILD STAGE 2B")

    run(
        [
            sys.executable,
            str(STAGE2B),
        ]
    )

    if not DATABASE.exists():
        raise FileNotFoundError(f"DuckDB warehouse missing: {DATABASE}")

    print()
    print(f"DATABASE: {DATABASE}")
    print("STAGE 2B REBUILD : PASS")


def run_stage3() -> None:
    banner("8. RUN STAGE 3")

    run(
        [
            sys.executable,
            str(STAGE3),
        ]
    )

    print("STAGE 3 EXECUTION : PASS")


def verify_stage3_outputs() -> None:
    banner("9. VERIFY STAGE 3 OUTPUTS")

    missing = []

    for path in EXPECTED_STAGE3_OUTPUTS:
        if path.exists() and path.stat().st_size > 0:
            print(f"PASS : {path.relative_to(PROJECT_ROOT)}")

        else:
            missing.append(path)

            print(f"MISS : {path.relative_to(PROJECT_ROOT)}")

    if missing:
        raise RuntimeError("Stage 3 did not generate all expected project outputs.")

    print()
    print("STAGE 3 OUTPUTS : PASS")


def count_stage3_anomalies() -> int:
    path = TABLES_DIR / "anomaly_alert_days.csv"

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return sum(1 for _ in csv.DictReader(handle))


def reconcile_stage2b_stage3() -> None:
    banner("10. RECONCILE STAGE 2B + STAGE 3")

    if not STAGE2B_SUMMARY.exists():
        raise FileNotFoundError(f"Missing summary: {STAGE2B_SUMMARY}")

    summary = json.loads(
        STAGE2B_SUMMARY.read_text(
            encoding="utf-8",
        )
    )

    stage2b_count = int(summary["anomaly_alert_days"])

    stage3_count = count_stage3_anomalies()

    print(f"Stage 2B anomaly days : {stage2b_count}")

    print(f"Stage 3 anomaly rows  : {stage3_count}")

    if stage2b_count != stage3_count:
        raise RuntimeError(
            f"Anomaly reconciliation failed. Stage 2B={stage2b_count}, Stage 3={stage3_count}"
        )

    print()
    print("ANOMALY RECONCILIATION : PASS")


def verify_paths() -> None:
    banner("11. VERIFY FINAL PATHS")

    expected_root = PROJECT_ROOT.resolve()

    expected_database = DATABASE.resolve()

    print(f"PROJECT ROOT : {expected_root}")

    print(f"DATABASE     : {expected_database}")

    print(f"REPORTS      : {REPORTS_DIR.resolve()}")

    print(f"STAGE 3      : {STAGE3.resolve()}")

    if expected_root.name != "railsearch-customer-journey-intelligence":
        raise RuntimeError("Final project path is incorrect.")

    if expected_root not in expected_database.parents:
        raise RuntimeError("DuckDB is outside the RailSearch project.")

    if expected_root not in REPORTS_DIR.resolve().parents:
        raise RuntimeError("Reports directory is outside the RailSearch project.")

    print()
    print("FINAL PATH VALIDATION : PASS")


def clean_obsolete_repair_file() -> None:
    banner("12. CLEAN OLD REPAIR FILE")

    old_repair = SCRIPTS_DIR / "fix_railsearch_project.py"

    if old_repair.exists() and old_repair.resolve() != Path(__file__).resolve():
        force_delete_file(old_repair)

        print("Old broken repair script removed.")

    else:
        print("No obsolete repair script found.")

    print("REPAIR SCRIPT CLEANUP : PASS")


def final_status() -> None:
    banner("RAILSEARCH — FINAL REPAIR STATUS")

    print("PROJECT ROOT             : PASS")
    print("SCRIPT LOCATIONS         : PASS")
    print("STAGE 2A RAW DATA        : PASS")
    print("STAGE 2B WAREHOUSE       : PASS")
    print("STAGE 3 PROJECT ROOT     : PASS")
    print("STAGE 3 ANALYSIS         : PASS")
    print("RUFF                     : PASS")
    print("ANOMALY RECONCILIATION   : PASS")
    print("REPORT OUTPUT PATHS      : PASS")
    print("PROJECT STRUCTURE        : PASS")

    print()
    print("=" * 76)
    print("RAILSEARCH FULL REPAIR : PASS")
    print("=" * 76)


def main() -> None:
    verify_project_root()
    repair_script_locations()
    patch_stage3()
    verify_raw_data()
    prepare_report_directories()
    format_and_lint()
    rebuild_stage2b()
    run_stage3()
    verify_stage3_outputs()
    reconcile_stage2b_stage3()
    verify_paths()
    clean_obsolete_repair_file()
    final_status()


if __name__ == "__main__":
    main()
