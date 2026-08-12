"""Validate the bootstrap registry contracts using only the Python standard library."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"

EXPECTED_HEADERS = {
    "module_status.csv": [
        "module_id",
        "module_name",
        "depends_on",
        "status",
        "readiness_percent",
        "gate_note",
    ],
    "sources.csv": [
        "source_id",
        "module_id",
        "title",
        "institution",
        "url",
        "published_at",
        "retrieved_at",
        "reference_period",
        "source_tier",
        "evidence_status",
        "reliability",
        "license",
        "local_snapshot_sha256",
        "notes",
    ],
    "variables.csv": [
        "variable_id",
        "module_id",
        "name",
        "definition",
        "unit",
        "default_value",
        "min_value",
        "max_value",
        "status",
        "source_ids",
        "updated_at",
        "notes",
    ],
    "formulas.csv": [
        "formula_id",
        "module_id",
        "output_variable_id",
        "expression",
        "input_variable_ids",
        "output_unit",
        "status",
        "notes",
    ],
    "open_questions.csv": [
        "question_id",
        "module_id",
        "priority",
        "question",
        "decision_impact",
        "evidence_needed",
        "status",
        "owner",
        "notes",
    ],
}

ALLOWED_MODULE_STATUS = {"NOT_STARTED", "IN_PROGRESS", "BLOCKED", "VALIDATED"}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def validate() -> list[str]:
    errors: list[str] = []

    for filename, expected in EXPECTED_HEADERS.items():
        path = REGISTRY / filename
        if not path.is_file():
            errors.append(f"missing registry file: {path.relative_to(ROOT)}")
            continue
        headers, _ = read_csv(path)
        if headers != expected:
            errors.append(
                f"invalid headers in {path.relative_to(ROOT)}: expected={expected!r} actual={headers!r}"
            )

    module_path = REGISTRY / "module_status.csv"
    if not module_path.is_file():
        return errors

    _, rows = read_csv(module_path)
    expected_ids = [f"B{index:02d}" for index in range(1, 21)]
    actual_ids = [row["module_id"] for row in rows]
    if actual_ids != expected_ids:
        errors.append(f"module IDs must be exactly B01-B20 in order: actual={actual_ids!r}")

    known_ids = set(actual_ids)
    for row in rows:
        module_id = row["module_id"]
        if not re.fullmatch(r"B(?:0[1-9]|1[0-9]|20)", module_id):
            errors.append(f"invalid module ID: {module_id!r}")
        if row["status"] not in ALLOWED_MODULE_STATUS:
            errors.append(f"invalid status for {module_id}: {row['status']!r}")
        try:
            readiness = int(row["readiness_percent"])
        except ValueError:
            errors.append(f"readiness is not an integer for {module_id}")
        else:
            if not 0 <= readiness <= 100:
                errors.append(f"readiness is outside 0-100 for {module_id}: {readiness}")
        dependencies = [item for item in row["depends_on"].split(";") if item]
        unknown = [item for item in dependencies if item not in known_ids]
        if unknown:
            errors.append(f"unknown dependencies for {module_id}: {unknown!r}")
        if module_id in dependencies:
            errors.append(f"self dependency for {module_id}")

    b15 = next((row for row in rows if row["module_id"] == "B15"), None)
    if b15 and set(b15["depends_on"].split(";")) != {"B12", "B13", "B14"}:
        errors.append("B15 must depend exactly on B12, B13, and B14")

    b20 = next((row for row in rows if row["module_id"] == "B20"), None)
    if b20:
        expected_b20 = {f"B{index:02d}" for index in range(1, 20)}
        if set(b20["depends_on"].split(";")) != expected_b20:
            errors.append("B20 must depend on every module from B01 through B19")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VALID: registry contracts and B01-B20 dependency gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
