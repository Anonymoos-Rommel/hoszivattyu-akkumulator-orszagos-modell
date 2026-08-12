"""Validate the bootstrap registry contracts using only the Python standard library."""

from __future__ import annotations

import csv
import re
import sys
from datetime import date
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
    "datasets.csv": [
        "dataset_id",
        "module_id",
        "title",
        "institution",
        "source_id",
        "access_method",
        "source_version",
        "dataflow_id",
        "metadata_endpoint",
        "data_endpoint",
        "geography_grain",
        "reference_period",
        "dimensions",
        "measure_id",
        "unit",
        "evidence_status",
        "retrieved_at",
        "license",
        "snapshot_policy",
        "raw_storage_path",
        "notes",
    ],
    "archetype_dimensions.csv": [
        "dimension_id",
        "module_id",
        "name",
        "source_dataset_ids",
        "source_dimension_ids",
        "role",
        "canonical_grain",
        "observability",
        "required",
        "aggregation_rule",
        "unknown_policy",
        "status",
        "notes",
    ],
}

ALLOWED_MODULE_STATUS = {"NOT_STARTED", "IN_PROGRESS", "BLOCKED", "VALIDATED"}
ALLOWED_EVIDENCE_STATUS = {"OBS", "DER", "ASS", "SCN", "POL", "Q"}
ALLOWED_SOURCE_TIERS = {"P1", "P2", "P3", "P4"}
ALLOWED_RELIABILITY = {"HIGH", "MEDIUM", "LOW"}
ALLOWED_QUESTION_PRIORITY = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
ALLOWED_QUESTION_STATUS = {"OPEN", "BLOCKED", "RESOLVED"}
ALLOWED_DIMENSION_OBSERVABILITY = {"OBS", "MODELLED", "Q"}
ALLOWED_DIMENSION_REQUIRED = {"yes", "no"}
ALLOWED_DIMENSION_STATUS = {"CONTRACTED", "PROPOSED", "GAP"}
ALLOWED_DIMENSION_ROLES = {
    "archetype_key",
    "baseline_flag",
    "eligibility_input",
    "energy_input",
    "stratifier",
    "universe_filter",
}
ALLOWED_DATASET_ACCESS_METHODS = {"KSH_CENSUS_API", "EMBEDDED_HTML"}

MODULE_ID_PATTERN = re.compile(r"B(?:0[1-9]|1[0-9]|20)")
SOURCE_ID_PATTERN = re.compile(r"SRC-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
VARIABLE_ID_PATTERN = re.compile(r"VAR-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
QUESTION_ID_PATTERN = re.compile(r"Q-(B(?:0[1-9]|1[0-9]|20))-\d{3}")
DATASET_ID_PATTERN = re.compile(r"DATA-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
DIMENSION_ID_PATTERN = re.compile(r"DIM-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
SOURCE_VERSION_PATTERN = re.compile(r"(?:V\d+|\d{4}-\d{2}-\d{2})")
FORMULA_ID_PATTERN = re.compile(r"FORM-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


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
        if not MODULE_ID_PATTERN.fullmatch(module_id):
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

    source_path = REGISTRY / "sources.csv"
    source_ids: set[str] = set()
    if source_path.is_file():
        _, source_rows = read_csv(source_path)
        all_source_ids = [row["source_id"] for row in source_rows]
        duplicates = duplicate_values(all_source_ids)
        if duplicates:
            errors.append(f"duplicate source IDs: {duplicates!r}")
        source_ids = set(all_source_ids)

        for row in source_rows:
            source_id = row["source_id"]
            match = SOURCE_ID_PATTERN.fullmatch(source_id)
            if not match:
                errors.append(f"invalid source ID: {source_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"source/module mismatch: {source_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown source module for {source_id}: {row['module_id']!r}")
            for field in (
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
                "notes",
            ):
                if not row[field].strip():
                    errors.append(f"missing {field} for source {source_id}")
            if not row["url"].startswith(("https://", "http://")):
                errors.append(f"invalid source URL for {source_id}: {row['url']!r}")
            if row["published_at"] != "undated" and not is_iso_date(row["published_at"]):
                errors.append(f"invalid published_at for {source_id}: {row['published_at']!r}")
            if not is_iso_date(row["retrieved_at"]):
                errors.append(f"invalid retrieved_at for {source_id}: {row['retrieved_at']!r}")
            if row["source_tier"] not in ALLOWED_SOURCE_TIERS:
                errors.append(f"invalid source tier for {source_id}: {row['source_tier']!r}")
            if row["evidence_status"] not in ALLOWED_EVIDENCE_STATUS:
                errors.append(
                    f"invalid source evidence status for {source_id}: {row['evidence_status']!r}"
                )
            if row["reliability"] not in ALLOWED_RELIABILITY:
                errors.append(f"invalid reliability for {source_id}: {row['reliability']!r}")
            snapshot = row["local_snapshot_sha256"]
            if snapshot and not re.fullmatch(r"[0-9a-f]{64}", snapshot):
                errors.append(f"invalid snapshot SHA-256 for {source_id}")

    variable_ids_set: set[str] = set()
    variable_path = REGISTRY / "variables.csv"
    if variable_path.is_file():
        _, variable_rows = read_csv(variable_path)
        variable_ids = [row["variable_id"] for row in variable_rows]
        variable_ids_set = set(variable_ids)
        duplicates = duplicate_values(variable_ids)
        if duplicates:
            errors.append(f"duplicate variable IDs: {duplicates!r}")

        for row in variable_rows:
            variable_id = row["variable_id"]
            match = VARIABLE_ID_PATTERN.fullmatch(variable_id)
            if not match:
                errors.append(f"invalid variable ID: {variable_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"variable/module mismatch: {variable_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown variable module for {variable_id}: {row['module_id']!r}")
            for field in ("name", "definition", "unit", "status", "updated_at", "notes"):
                if not row[field].strip():
                    errors.append(f"missing {field} for variable {variable_id}")
            if row["status"] not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid variable status for {variable_id}: {row['status']!r}")
            if not is_iso_date(row["updated_at"]):
                errors.append(f"invalid updated_at for {variable_id}: {row['updated_at']!r}")
            referenced_sources = [item for item in row["source_ids"].split(";") if item]
            unknown_sources = [item for item in referenced_sources if item not in source_ids]
            if unknown_sources:
                errors.append(f"unknown source references for {variable_id}: {unknown_sources!r}")
            if row["status"] in {"OBS", "DER"} and not referenced_sources:
                errors.append(f"{row['status']} variable has no source for {variable_id}")

    formula_path = REGISTRY / "formulas.csv"
    if formula_path.is_file():
        _, formula_rows = read_csv(formula_path)
        formula_ids = [row["formula_id"] for row in formula_rows]
        duplicates = duplicate_values(formula_ids)
        if duplicates:
            errors.append(f"duplicate formula IDs: {duplicates!r}")

        for row in formula_rows:
            formula_id = row["formula_id"]
            match = FORMULA_ID_PATTERN.fullmatch(formula_id)
            if not match:
                errors.append(f"invalid formula ID: {formula_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"formula/module mismatch: {formula_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown formula module for {formula_id}: {row['module_id']!r}")
            for field in (
                "output_variable_id",
                "expression",
                "input_variable_ids",
                "output_unit",
                "status",
                "notes",
            ):
                if not row[field].strip():
                    errors.append(f"missing {field} for formula {formula_id}")
            if row["output_variable_id"] not in variable_ids_set:
                errors.append(
                    f"unknown output variable for {formula_id}: {row['output_variable_id']!r}"
                )
            inputs = [item for item in row["input_variable_ids"].split(";") if item]
            unknown_inputs = [item for item in inputs if item not in variable_ids_set]
            if unknown_inputs:
                errors.append(f"unknown input variables for {formula_id}: {unknown_inputs!r}")
            if row["status"] != "DER":
                errors.append(f"formula status must be DER for {formula_id}")

    dataset_ids: set[str] = set()
    dataset_path = REGISTRY / "datasets.csv"
    if dataset_path.is_file():
        _, dataset_rows = read_csv(dataset_path)
        all_dataset_ids = [row["dataset_id"] for row in dataset_rows]
        duplicates = duplicate_values(all_dataset_ids)
        if duplicates:
            errors.append(f"duplicate dataset IDs: {duplicates!r}")
        dataset_ids = set(all_dataset_ids)

        for row in dataset_rows:
            dataset_id = row["dataset_id"]
            match = DATASET_ID_PATTERN.fullmatch(dataset_id)
            if not match:
                errors.append(f"invalid dataset ID: {dataset_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"dataset/module mismatch: {dataset_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown dataset module for {dataset_id}: {row['module_id']!r}")
            for field in (
                "title",
                "institution",
                "source_id",
                "access_method",
                "source_version",
                "dataflow_id",
                "metadata_endpoint",
                "data_endpoint",
                "geography_grain",
                "reference_period",
                "dimensions",
                "measure_id",
                "unit",
                "evidence_status",
                "retrieved_at",
                "license",
                "snapshot_policy",
                "raw_storage_path",
                "notes",
            ):
                if not row[field].strip():
                    errors.append(f"missing {field} for dataset {dataset_id}")
            if row["source_id"] not in source_ids:
                errors.append(f"unknown source for dataset {dataset_id}: {row['source_id']!r}")
            if row["access_method"] not in ALLOWED_DATASET_ACCESS_METHODS:
                errors.append(
                    f"invalid access method for dataset {dataset_id}: {row['access_method']!r}"
                )
            if not SOURCE_VERSION_PATTERN.fullmatch(row["source_version"]):
                errors.append(
                    f"invalid source version for dataset {dataset_id}: {row['source_version']!r}"
                )
            if not row["metadata_endpoint"].startswith("https://"):
                errors.append(f"invalid metadata endpoint for dataset {dataset_id}")
            if not row["data_endpoint"].startswith("https://"):
                errors.append(f"invalid data endpoint for dataset {dataset_id}")
            if row["evidence_status"] not in ALLOWED_EVIDENCE_STATUS:
                errors.append(f"invalid evidence status for dataset {dataset_id}")
            if not is_iso_date(row["retrieved_at"]):
                errors.append(f"invalid retrieved_at for dataset {dataset_id}")
            if not row["raw_storage_path"].startswith("data/raw/"):
                errors.append(f"dataset raw path must be under data/raw for {dataset_id}")

    dimension_path = REGISTRY / "archetype_dimensions.csv"
    if dimension_path.is_file():
        _, dimension_rows = read_csv(dimension_path)
        dimension_ids = [row["dimension_id"] for row in dimension_rows]
        duplicates = duplicate_values(dimension_ids)
        if duplicates:
            errors.append(f"duplicate dimension IDs: {duplicates!r}")

        for row in dimension_rows:
            dimension_id = row["dimension_id"]
            match = DIMENSION_ID_PATTERN.fullmatch(dimension_id)
            if not match:
                errors.append(f"invalid dimension ID: {dimension_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"dimension/module mismatch: {dimension_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown dimension module for {dimension_id}: {row['module_id']!r}")
            for field in (
                "name",
                "role",
                "canonical_grain",
                "observability",
                "required",
                "aggregation_rule",
                "unknown_policy",
                "status",
                "notes",
            ):
                if not row[field].strip():
                    errors.append(f"missing {field} for dimension {dimension_id}")
            referenced_datasets = [item for item in row["source_dataset_ids"].split(";") if item]
            unknown_datasets = [item for item in referenced_datasets if item not in dataset_ids]
            if unknown_datasets:
                errors.append(f"unknown dataset references for {dimension_id}: {unknown_datasets!r}")
            if row["status"] == "CONTRACTED" and not referenced_datasets:
                errors.append(f"contracted dimension has no dataset for {dimension_id}")
            if row["role"] not in ALLOWED_DIMENSION_ROLES:
                errors.append(f"invalid role for {dimension_id}: {row['role']!r}")
            if row["observability"] not in ALLOWED_DIMENSION_OBSERVABILITY:
                errors.append(f"invalid observability for {dimension_id}: {row['observability']!r}")
            if row["required"] not in ALLOWED_DIMENSION_REQUIRED:
                errors.append(f"invalid required flag for {dimension_id}: {row['required']!r}")
            if row["status"] not in ALLOWED_DIMENSION_STATUS:
                errors.append(f"invalid dimension status for {dimension_id}: {row['status']!r}")

    question_path = REGISTRY / "open_questions.csv"
    if question_path.is_file():
        _, question_rows = read_csv(question_path)
        question_ids = [row["question_id"] for row in question_rows]
        duplicates = duplicate_values(question_ids)
        if duplicates:
            errors.append(f"duplicate question IDs: {duplicates!r}")

        for row in question_rows:
            question_id = row["question_id"]
            match = QUESTION_ID_PATTERN.fullmatch(question_id)
            if not match:
                errors.append(f"invalid question ID: {question_id!r}")
            elif match.group(1) != row["module_id"]:
                errors.append(f"question/module mismatch: {question_id!r} -> {row['module_id']!r}")
            if row["module_id"] not in known_ids:
                errors.append(f"unknown question module for {question_id}: {row['module_id']!r}")
            for field in ("question", "decision_impact", "evidence_needed", "status", "owner", "notes"):
                if not row[field].strip():
                    errors.append(f"missing {field} for question {question_id}")
            if row["priority"] not in ALLOWED_QUESTION_PRIORITY:
                errors.append(f"invalid priority for {question_id}: {row['priority']!r}")
            if row["status"] not in ALLOWED_QUESTION_STATUS:
                errors.append(f"invalid question status for {question_id}: {row['status']!r}")

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
