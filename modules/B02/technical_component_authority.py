"""B02-P4 cross-module authority gate for real technical-eligibility evidence.

B02-P2 owns the generic admission logic. B02-P4 additionally validates that a
real PASS/FAIL component claim is produced by a repository module permitted to
author that claim. Missing evidence remains Q and needs no producer.
"""

from __future__ import annotations

import csv
from pathlib import Path

from modules.B02.technical_eligibility_contract import (
    Q,
    REQUIRED_TECHNICAL_COMPONENTS,
    TechnicalEligibilityRecord,
    TechnicalEligibilityDecision,
    assess_technical_eligibility,
)

ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_PATH = ROOT / "registry" / "b02_technical_component_authority.csv"


class B02ComponentAuthorityError(ValueError):
    """Raised when a technical component claim crosses an authority boundary."""


def load_component_authority() -> dict[str, frozenset[str]]:
    with AUTHORITY_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    by_component: dict[str, frozenset[str]] = {}
    for row in rows:
        component_id = row["component_id"].strip()
        if component_id in by_component:
            raise B02ComponentAuthorityError(f"duplicate authority row: {component_id}")
        producers = frozenset(
            item.strip()
            for item in row["permitted_producer_modules"].split(";")
            if item.strip()
        )
        if row["consumer_module"].strip() != "B02":
            raise B02ComponentAuthorityError(f"{component_id} consumer must remain B02")
        if not producers:
            raise B02ComponentAuthorityError(f"{component_id} has no permitted producer")
        if row["required_evidence_statuses"].strip() != "OBS;DER":
            raise B02ComponentAuthorityError(
                f"{component_id} evidence-status contract drifted"
            )
        by_component[component_id] = producers

    expected = set(REQUIRED_TECHNICAL_COMPONENTS)
    actual = set(by_component)
    if actual != expected:
        raise B02ComponentAuthorityError(
            f"authority component set must be exact; missing={sorted(expected-actual)} extra={sorted(actual-expected)}"
        )
    return by_component


def validate_component_authority(
    record: TechnicalEligibilityRecord,
    producer_modules: dict[str, str],
) -> None:
    """Validate producer-module authority without converting Q into PASS/FAIL."""
    record.validate()
    authority = load_component_authority()
    component_by_id = {item.component_id: item for item in record.components}

    extra = set(producer_modules) - set(REQUIRED_TECHNICAL_COMPONENTS)
    if extra:
        raise B02ComponentAuthorityError(f"unknown producer-module keys: {sorted(extra)}")

    for component_id in REQUIRED_TECHNICAL_COMPONENTS:
        component = component_by_id[component_id]
        producer = producer_modules.get(component_id, "").strip()

        if component.decision == Q:
            if producer:
                raise B02ComponentAuthorityError(
                    f"{component_id} is Q and must not carry an authority producer"
                )
            continue

        if not producer:
            raise B02ComponentAuthorityError(
                f"{component_id} PASS/FAIL requires an explicit producer module"
            )
        if producer not in authority[component_id]:
            raise B02ComponentAuthorityError(
                f"{producer} is not permitted to author {component_id}; allowed={sorted(authority[component_id])}"
            )


def assess_authoritative_technical_eligibility(
    record: TechnicalEligibilityRecord,
    producer_modules: dict[str, str],
) -> TechnicalEligibilityDecision:
    """Canonical real-record entry point for P4 cross-module eligibility assessment."""
    validate_component_authority(record, producer_modules)
    return assess_technical_eligibility(record)
