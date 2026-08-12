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
}

ALLOWED_MODULE_STATUS = {"NOT_STARTED", "IN_PROGRESS", "BLOCKED", "VALIDATED"}
ALLOWED_EVIDENCE_STATUS = {"OBS", "DER", "ASS", "SCN", "POL", "Q"}
ALLOWED_SOURCE_TIERS = {"P1", "P2", "P3", "P4"}
ALLOWED_RELIABILITY = {"HIGH", "MEDIUM", "LOW"}
ALLOWED_QUESTION_PRIORITY = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
ALLOWED_QUESTION_STATUS = {"OPEN", "BLOCKED", "RESOLVED"}

MODULE_ID_PATTERN = re.compile(r"B(?:0[1-9]|1[0-9]|20)")
SOURCE_ID_PATTERN = re.compile(r"SRC-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
VARIABLE_ID_PATTERN = re.compile(r"VAR-(B(?:0[1-9]|1[0-9]|20))-[A-Z0-9-]+")
QUESTION_ID_PATTERN = re.compile(r"Q-(B(?:0[1-9]|1[0-9]|20))-\d{3}")


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

    variable_path = REGISTRY / "variables.csv"
    if variable_path.is_file():
        _, variable_rows = read_csv(variable_path)
        variable_ids = [row["variable_id"] for row in variable_rows]
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
