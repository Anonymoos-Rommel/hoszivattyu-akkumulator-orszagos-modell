"""Validate privacy-minimised OÉNY double-blind annotation JSONL batches."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "oeny_heat_emitter_annotation.schema.json"

REQUIRED_FIELDS = {
    "schema_version",
    "annotation_id",
    "document_id",
    "redacted_source_sha256",
    "annotation_role",
    "annotator_id",
    "emitter_status",
    "emitter_types",
    "emitter_evidence",
    "temperature_status",
    "supply_temperature_c",
    "return_temperature_c",
    "temperature_basis",
    "page_references",
    "review_flags",
    "pii_check",
    "adjudication_of",
}

EMITTER_TYPES = {
    "RADIATOR",
    "FLOOR_HEATING",
    "WALL_HEATING",
    "CEILING_HEATING",
    "FAN_COIL",
    "AIR_HEATING",
    "DIRECT_ELECTRIC",
    "OTHER",
    "NOT_STATED",
    "UNREADABLE",
}
EMITTER_EVIDENCE = {
    "TEXT_EXPLICIT",
    "TABLE_EXPLICIT",
    "SCHEMATIC_EXPLICIT",
    "PHOTO_EXPLICIT",
    "NONE",
}
TEMPERATURE_BASIS = {
    "DESIGN_EXPLICIT",
    "CALCULATION_INPUT",
    "OPERATING_MEASURED",
    "REFERENCE_ASSUMPTION",
    "NOT_STATED",
}
REVIEW_FLAGS = {
    "OTHER_NEEDS_CODEBOOK",
    "MULTIPLE_SYSTEMS",
    "SOURCE_CONFLICT",
    "OCR_UNCERTAIN",
}
EVIDENCE_KINDS = {"EMITTER", "TEMPERATURE", "EMITTER_AND_TEMPERATURE"}
ROLES = {"ANNOTATOR_A", "ANNOTATOR_B", "ADJUDICATOR"}
DIRECT_EMITTER_EVIDENCE = EMITTER_EVIDENCE - {"NONE"}
DIRECT_TEMPERATURE_BASIS = TEMPERATURE_BASIS - {
    "REFERENCE_ASSUMPTION",
    "NOT_STATED",
}

ANNOTATION_ID = re.compile(r"ANN-[A-F0-9]{16}")
DOCUMENT_ID = re.compile(r"DOC-[A-F0-9]{32}")
RATER_ID = re.compile(r"RATER-[A-Z0-9]{4,16}")
SHA256 = re.compile(r"[a-f0-9]{64}")

# These keys have no legitimate place in the public annotation contract.  Checking
# recursively also rejects attempted additions inside page-reference objects.
PROHIBITED_KEYS = {
    "address",
    "cim",
    "email",
    "het_id",
    "helyrajzi_szam",
    "name",
    "nev",
    "phone",
    "record_id",
    "source_filename",
    "tanusitvany_azonosito",
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _duplicates(values: list[Any]) -> bool:
    return len(values) != len(set(values))


def _find_prohibited_keys(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in PROHIBITED_KEYS:
                errors.append(f"{path}: prohibited direct-identifier key {key!r}")
            errors.extend(_find_prohibited_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_find_prohibited_keys(child, f"{path}[{index}]"))
    return errors


def _validate_enum_list(
    record: dict[str, Any], field: str, allowed: set[str], prefix: str
) -> list[str]:
    value = record.get(field)
    if not isinstance(value, list) or not value:
        return [f"{prefix}.{field}: must be a non-empty array"]
    errors: list[str] = []
    if any(not isinstance(item, str) or item not in allowed for item in value):
        errors.append(f"{prefix}.{field}: contains an unsupported value")
    if all(isinstance(item, str) for item in value) and _duplicates(value):
        errors.append(f"{prefix}.{field}: duplicate values are not allowed")
    return errors


def validate_record(record: Any, index: int = 1) -> list[str]:
    prefix = f"record {index}"
    if not isinstance(record, dict):
        return [f"{prefix}: must be a JSON object"]

    errors = _find_prohibited_keys(record, prefix)
    missing = sorted(REQUIRED_FIELDS - set(record))
    extra = sorted(set(record) - REQUIRED_FIELDS)
    if missing:
        errors.append(f"{prefix}: missing fields {missing!r}")
    if extra:
        errors.append(f"{prefix}: unsupported fields {extra!r}")
    if missing:
        return errors

    if record["schema_version"] != "1.0":
        errors.append(f"{prefix}.schema_version: expected '1.0'")
    for field, pattern in (
        ("annotation_id", ANNOTATION_ID),
        ("document_id", DOCUMENT_ID),
        ("annotator_id", RATER_ID),
        ("redacted_source_sha256", SHA256),
    ):
        value = record[field]
        if not isinstance(value, str) or pattern.fullmatch(value) is None:
            errors.append(f"{prefix}.{field}: invalid pseudonymous identifier")

    if record["annotation_role"] not in ROLES:
        errors.append(f"{prefix}.annotation_role: unsupported role")
    if record["pii_check"] != "PASS":
        errors.append(f"{prefix}.pii_check: must be PASS")
    if record["emitter_status"] not in {"OBS", "Q"}:
        errors.append(f"{prefix}.emitter_status: must be OBS or Q")
    if record["temperature_status"] not in {"OBS", "Q"}:
        errors.append(f"{prefix}.temperature_status: must be OBS or Q")

    errors.extend(_validate_enum_list(record, "emitter_types", EMITTER_TYPES, prefix))
    errors.extend(
        _validate_enum_list(record, "emitter_evidence", EMITTER_EVIDENCE, prefix)
    )

    emitter_types = record["emitter_types"]
    emitter_evidence = record["emitter_evidence"]
    if isinstance(emitter_types, list):
        unknown_markers = {"NOT_STATED", "UNREADABLE"} & set(emitter_types)
        if unknown_markers and len(emitter_types) != 1:
            errors.append(
                f"{prefix}.emitter_types: NOT_STATED/UNREADABLE must stand alone"
            )
        if record["emitter_status"] == "OBS" and unknown_markers:
            errors.append(f"{prefix}.emitter_status: unknown emitter cannot be OBS")
        if record["emitter_status"] == "Q" and not unknown_markers:
            errors.append(f"{prefix}.emitter_status: Q requires NOT_STATED or UNREADABLE")
        if "OTHER" in emitter_types and "OTHER_NEEDS_CODEBOOK" not in record["review_flags"]:
            errors.append(
                f"{prefix}.review_flags: OTHER requires OTHER_NEEDS_CODEBOOK"
            )
    if isinstance(emitter_evidence, list):
        if "NONE" in emitter_evidence and len(emitter_evidence) != 1:
            errors.append(f"{prefix}.emitter_evidence: NONE must stand alone")
        if record["emitter_status"] == "OBS" and not (
            set(emitter_evidence) & DIRECT_EMITTER_EVIDENCE
        ):
            errors.append(f"{prefix}.emitter_evidence: OBS requires explicit evidence")
        if record["emitter_status"] == "Q" and emitter_evidence != ["NONE"]:
            errors.append(f"{prefix}.emitter_evidence: Q requires only NONE")

    supply = record["supply_temperature_c"]
    ret = record["return_temperature_c"]
    if (supply is None) != (ret is None):
        errors.append(f"{prefix}: supply and return temperatures must form a pair")
    for field, value in (
        ("supply_temperature_c", supply),
        ("return_temperature_c", ret),
    ):
        if value is not None and (not _is_number(value) or not -50 <= value <= 150):
            errors.append(f"{prefix}.{field}: must be null or a number from -50 to 150")
    if _is_number(supply) and _is_number(ret) and supply <= ret:
        errors.append(f"{prefix}: heating supply temperature must exceed return")
    basis = record["temperature_basis"]
    if basis not in TEMPERATURE_BASIS:
        errors.append(f"{prefix}.temperature_basis: unsupported value")
    if record["temperature_status"] == "OBS":
        if supply is None or basis not in DIRECT_TEMPERATURE_BASIS:
            errors.append(
                f"{prefix}: OBS temperature requires an explicit numeric pair and direct basis"
            )
    else:
        if supply is not None or basis not in {"REFERENCE_ASSUMPTION", "NOT_STATED"}:
            errors.append(
                f"{prefix}: Q temperature requires no numeric pair and a non-observed basis"
            )

    page_refs = record["page_references"]
    if not isinstance(page_refs, list):
        errors.append(f"{prefix}.page_references: must be an array")
    else:
        for ref_index, reference in enumerate(page_refs, start=1):
            ref_prefix = f"{prefix}.page_references[{ref_index}]"
            if not isinstance(reference, dict):
                errors.append(f"{ref_prefix}: must be an object")
                continue
            if set(reference) != {"page", "evidence_kind"}:
                errors.append(f"{ref_prefix}: invalid fields")
                continue
            if not isinstance(reference["page"], int) or isinstance(
                reference["page"], bool
            ) or reference["page"] < 1:
                errors.append(f"{ref_prefix}.page: must be a positive integer")
            if reference["evidence_kind"] not in EVIDENCE_KINDS:
                errors.append(f"{ref_prefix}.evidence_kind: unsupported value")
    if (record["emitter_status"] == "OBS" or record["temperature_status"] == "OBS") and not page_refs:
        errors.append(f"{prefix}.page_references: OBS evidence requires a page")

    flags = record["review_flags"]
    if not isinstance(flags, list):
        errors.append(f"{prefix}.review_flags: must be an array")
    elif any(not isinstance(flag, str) or flag not in REVIEW_FLAGS for flag in flags):
        errors.append(f"{prefix}.review_flags: contains an unsupported value")
    elif _duplicates(flags):
        errors.append(f"{prefix}.review_flags: duplicate values are not allowed")

    adjudication = record["adjudication_of"]
    if not isinstance(adjudication, list):
        errors.append(f"{prefix}.adjudication_of: must be an array")
    elif any(not isinstance(item, str) or ANNOTATION_ID.fullmatch(item) is None for item in adjudication):
        errors.append(f"{prefix}.adjudication_of: invalid annotation ID")
    elif _duplicates(adjudication):
        errors.append(f"{prefix}.adjudication_of: duplicate IDs are not allowed")
    if record["annotation_role"] == "ADJUDICATOR" and (
        not isinstance(adjudication, list) or len(adjudication) != 2
    ):
        errors.append(f"{prefix}.adjudication_of: adjudicator must reference two records")
    if record["annotation_role"] != "ADJUDICATOR" and adjudication != []:
        errors.append(f"{prefix}.adjudication_of: primary annotator list must be empty")

    return errors


def decision_signature(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record["emitter_status"],
        tuple(sorted(record["emitter_types"])),
        record["temperature_status"],
        record["supply_temperature_c"],
        record["return_temperature_c"],
        record["temperature_basis"],
    )


def validate_batch(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = [record.get("annotation_id") for record in records]
    duplicate_ids = sorted({item for item in ids if ids.count(item) > 1})
    if duplicate_ids:
        errors.append(f"batch: duplicate annotation IDs {duplicate_ids!r}")

    by_document: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        document_id = record.get("document_id")
        if isinstance(document_id, str):
            by_document[document_id].append(record)

    for document_id, group in sorted(by_document.items()):
        by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in group:
            by_role[record.get("annotation_role", "")].append(record)
        for role in ("ANNOTATOR_A", "ANNOTATOR_B"):
            if len(by_role[role]) != 1:
                errors.append(f"{document_id}: expected exactly one {role}")
        if len(by_role["ADJUDICATOR"]) > 1:
            errors.append(f"{document_id}: at most one ADJUDICATOR is allowed")
        if len(by_role["ANNOTATOR_A"]) != 1 or len(by_role["ANNOTATOR_B"]) != 1:
            continue

        first = by_role["ANNOTATOR_A"][0]
        second = by_role["ANNOTATOR_B"][0]
        hashes = {record["redacted_source_sha256"] for record in group}
        if len(hashes) != 1:
            errors.append(f"{document_id}: all roles must use the same redacted source hash")
        raters = [record["annotator_id"] for record in group]
        if len(raters) != len(set(raters)):
            errors.append(f"{document_id}: annotator identities must be independent")

        disagrees = decision_signature(first) != decision_signature(second)
        adjudicators = by_role["ADJUDICATOR"]
        if disagrees and len(adjudicators) != 1:
            errors.append(f"{document_id}: disagreement requires one ADJUDICATOR")
        if not disagrees and adjudicators:
            errors.append(f"{document_id}: agreement must not be overwritten by adjudication")
        if adjudicators:
            expected = {first["annotation_id"], second["annotation_id"]}
            actual = set(adjudicators[0]["adjudication_of"])
            if actual != expected:
                errors.append(
                    f"{document_id}: adjudication_of must reference the A and B records"
                )
    return errors


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
                continue
            records.append(value)
    if not records and not errors:
        errors.append("input contains no annotation records")
    return records, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    parser.add_argument(
        "--records-only",
        action="store_true",
        help="validate individual records without requiring a complete A/B batch",
    )
    args = parser.parse_args()

    records, errors = load_jsonl(args.jsonl)
    for index, record in enumerate(records, start=1):
        errors.extend(validate_record(record, index))
    if not errors and not args.records_only:
        errors.extend(validate_batch(records))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    mode = "records" if args.records_only else "double-blind batch"
    print(f"VALID: {len(records)} OÉNY annotation {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
