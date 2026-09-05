"""Resolved-only effective B10 service-area projection.

P63 turns the already materialized P20-P49 whole-settlement evidence into a
machine-usable current projection after applying the exact P62 supersessions.
The single P61 Tass usage-location membership is included as a separate partial
record.  This projection is deliberately not the canonical complete national
crosswalk: unresolved settlements and unresolved internal boundaries remain Q.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from modules.B10.effective_service_area_membership_contract import (
    EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP,
    WholeMembershipSupersession,
    classify_effective_whole_membership,
)


WHOLE_SETTLEMENT = "WHOLE_SETTLEMENT"
PARTIAL_SETTLEMENT = "PARTIAL_SETTLEMENT"
WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN = "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN"
USAGE_LOCATION_MEMBERSHIP_PROVEN = "USAGE_LOCATION_MEMBERSHIP_PROVEN"


@dataclass(frozen=True)
class EffectiveServiceAreaProjectionRow:
    ksh_settlement_code: str
    settlement_name: str
    operator_id: str
    network_operator: str
    service_area_id: str
    coverage_scope: str
    usage_location_id: str | None
    source_ids: tuple[str, ...]
    evidence_status: str
    status: str
    lineage: str


FULL_WHOLE_SURFACES = (
    "registry/dso_service_area_membership_crosswalk_tranche.csv",
    "registry/dso_service_area_membership_crosswalk_opus_p44.csv",
    "registry/dso_service_area_membership_crosswalk_demasz_p45.csv",
    "registry/dso_service_area_membership_crosswalk_elmu_p46.csv",
)

COMPACT_COMPLETION_SURFACES = (
    (
        "registry/dso_service_area_membership_emasz_p47_pairs.csv",
        "registry/dso_service_area_membership_emasz_p47_manifest.csv",
        "registry/dso_service_area_membership_emasz_p47_exceptions.csv",
    ),
    (
        "registry/dso_service_area_membership_ddasz_p48_pairs.csv",
        "registry/dso_service_area_membership_ddasz_p48_manifest.csv",
        "registry/dso_service_area_membership_ddasz_p48_exceptions.csv",
    ),
    (
        "registry/dso_service_area_membership_edasz_p49_pairs.csv",
        "registry/dso_service_area_membership_edasz_p49_manifest.csv",
        "registry/dso_service_area_membership_edasz_p49_exceptions.csv",
    ),
)

SUPERSESSION_SURFACE = "registry/dso_service_area_membership_p62_effective_supersessions.csv"
P61_USAGE_LOCATION_SURFACE = "registry/dso_service_area_membership_elmu_p61_usage_location.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _split_sources(value: str) -> tuple[str, ...]:
    return tuple(item for item in value.split(";") if item)


def _supersessions(root: Path) -> tuple[WholeMembershipSupersession, ...]:
    return tuple(
        WholeMembershipSupersession(
            settlement_name=row["settlement_name"],
            prior_operator_id=row["prior_operator_id"],
            conflict_operator_id=row["conflict_operator_id"],
            authority_source_id=row["conflict_authority_source_id"],
            reason=row["notes"],
        )
        for row in _rows(root / SUPERSESSION_SURFACE)
    )


def _effective_whole_row(
    *,
    ksh_settlement_code: str,
    settlement_name: str,
    operator_id: str,
    network_operator: str,
    service_area_id: str,
    source_ids: tuple[str, ...],
    evidence_status: str,
    lineage: str,
    supersessions: tuple[WholeMembershipSupersession, ...],
) -> EffectiveServiceAreaProjectionRow | None:
    decision = classify_effective_whole_membership(
        settlement_name=settlement_name,
        operator_id=operator_id,
        raw_status=WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN,
        supersessions=supersessions,
    )
    if decision.effective_status != EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP:
        return None
    return EffectiveServiceAreaProjectionRow(
        ksh_settlement_code=ksh_settlement_code,
        settlement_name=settlement_name,
        operator_id=operator_id,
        network_operator=network_operator,
        service_area_id=service_area_id,
        coverage_scope=WHOLE_SETTLEMENT,
        usage_location_id=None,
        source_ids=source_ids,
        evidence_status=evidence_status,
        status=EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP,
        lineage=lineage,
    )


def build_effective_service_area_projection(root: Path | None = None) -> tuple[EffectiveServiceAreaProjectionRow, ...]:
    """Build the exact resolved-only P63 projection from repository evidence."""

    if root is None:
        root = Path(__file__).resolve().parents[2]
    supersessions = _supersessions(root)
    projected: list[EffectiveServiceAreaProjectionRow] = []

    for relative in FULL_WHOLE_SURFACES:
        for row in _rows(root / relative):
            if row["status"] != WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN:
                continue
            effective = _effective_whole_row(
                ksh_settlement_code=row["ksh_settlement_code"],
                settlement_name=row["settlement_name"],
                operator_id=row["operator_id"],
                network_operator=row["network_operator"],
                service_area_id=row["service_area_id"],
                source_ids=_split_sources(row["source_ids"]),
                evidence_status=row["evidence_status"],
                lineage=relative,
                supersessions=supersessions,
            )
            if effective is not None:
                projected.append(effective)

    for pairs_relative, manifest_relative, exceptions_relative in COMPACT_COMPLETION_SURFACES:
        manifest_rows = _rows(root / manifest_relative)
        if len(manifest_rows) != 1:
            raise ValueError(f"{manifest_relative} must contain exactly one row")
        manifest = manifest_rows[0]
        exception_sources = {
            (row["ksh_settlement_code"], row["settlement_name"]): _split_sources(row["source_ids"])
            for row in _rows(root / exceptions_relative)
            if row["exception_class"] != "CROSS_DSO_WHOLE_CONFLICT_EXCLUDED"
        }
        ordinary_sources = _split_sources(manifest["normal_source_ids"])
        for pair in _rows(root / pairs_relative):
            key = (pair["ksh_settlement_code"], pair["settlement_name"])
            effective = _effective_whole_row(
                ksh_settlement_code=pair["ksh_settlement_code"],
                settlement_name=pair["settlement_name"],
                operator_id=manifest["operator_id"],
                network_operator=manifest["network_operator"],
                service_area_id=manifest["service_area_id"],
                source_ids=exception_sources.get(key, ordinary_sources),
                evidence_status=manifest["evidence_status"],
                lineage=pairs_relative,
                supersessions=supersessions,
            )
            if effective is not None:
                projected.append(effective)

    usage_rows = _rows(root / P61_USAGE_LOCATION_SURFACE)
    for row in usage_rows:
        if row["status"] != USAGE_LOCATION_MEMBERSHIP_PROVEN:
            raise ValueError("P61 usage-location surface may contribute only proven usage-location rows")
        projected.append(
            EffectiveServiceAreaProjectionRow(
                ksh_settlement_code=row["ksh_settlement_code"],
                settlement_name=row["settlement_name"],
                operator_id=row["operator_id"],
                network_operator=row["network_operator"],
                service_area_id=row["service_area_id"],
                coverage_scope=PARTIAL_SETTLEMENT,
                usage_location_id=row["usage_location_id"],
                source_ids=_split_sources(row["source_ids"]),
                evidence_status=row["evidence_status"],
                status=USAGE_LOCATION_MEMBERSHIP_PROVEN,
                lineage=P61_USAGE_LOCATION_SURFACE,
            )
        )

    whole_codes = [row.ksh_settlement_code for row in projected if row.coverage_scope == WHOLE_SETTLEMENT]
    if len(whole_codes) != len(set(whole_codes)):
        raise ValueError("effective whole-settlement projection must be globally unique by KSH code")

    record_keys = [
        (row.ksh_settlement_code, row.operator_id, row.coverage_scope, row.usage_location_id or "")
        for row in projected
    ]
    if len(record_keys) != len(set(record_keys)):
        raise ValueError("effective projection contains duplicate record keys")

    return tuple(
        sorted(
            projected,
            key=lambda row: (
                row.ksh_settlement_code,
                row.coverage_scope,
                row.operator_id,
                row.usage_location_id or "",
            ),
        )
    )
