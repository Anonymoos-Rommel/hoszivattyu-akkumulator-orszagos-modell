"""B10-P14 national DSO operator inventory and territorial-grain contract.

P14 proves the current six-operator Hungarian electricity DSO inventory and fixes
DSO_SERVICE_AREA as the canonical B10 network-regional grain. It deliberately
keeps administrative geography, service-area membership crosswalks and exact
electrical topology as separate authorities.

Core rule:

    NATIONAL DSO OPERATOR INVENTORY
    != SERVICE-AREA MEMBERSHIP CROSSWALK
    != EXACT DSO NODE INVENTORY
    != HOUSEHOLD -> EXACT NODE MAPPING
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from modules.B10.spatial_authority_contract import DSO_SERVICE_AREA


class B10DsoTerritorialCoverageError(ValueError):
    """Raised when national DSO coverage or territorial grain is overstated."""


NATIONAL_DSO_OPERATOR_INVENTORY_PROVEN = "NATIONAL_DSO_OPERATOR_INVENTORY_PROVEN"
Q_NATIONAL_DSO_OPERATOR_INVENTORY = "Q_NATIONAL_DSO_OPERATOR_INVENTORY"
Q_SERVICE_AREA_MEMBERSHIP_CROSSWALK = "Q_SERVICE_AREA_MEMBERSHIP_CROSSWALK"
Q_EXACT_DSO_NODE_INVENTORY = "Q_EXACT_DSO_NODE_INVENTORY"

ADMINISTRATIVE_REPORTING_GRAIN = "ADMINISTRATIVE_REGION"
CANONICAL_NETWORK_REGIONAL_GRAIN = DSO_SERVICE_AREA

DSO_LICENSEE_INVENTORY = "DSO_LICENSEE_INVENTORY"
DSO_SERVICE_AREA_REGION_LABEL = "DSO_SERVICE_AREA_REGION_LABEL"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
SERVICE_AREA_ID_PREFIX = "SERVICE_AREA_ID:"
SERVICE_AREA_LABEL_PREFIX = "SERVICE_AREA_LABEL:"

EVIDENCE_STATUSES = {"OBS", "DER", "Q"}

EXPECTED_DSO_OPERATORS = {
    "ELMU": "ELMŰ Hálózati Kft.",
    "EON_DDASZ": "E.ON Dél-dunántúli Áramhálózati Zrt.",
    "EON_EDASZ": "E.ON Észak-dunántúli Áramhálózati Zrt.",
    "MVM_DEMASZ": "MVM Démász Áramhálózati Kft.",
    "MVM_EMASZ": "MVM Émász Áramhálózati Kft.",
    "OPUS_TITASZ": "OPUS TITÁSZ Áramhálózati Zrt.",
}

EXPECTED_SERVICE_AREA_IDS = {
    operator_id: f"{operator_id}:SERVICE_AREA" for operator_id in EXPECTED_DSO_OPERATORS
}


@dataclass(frozen=True)
class DsoTerritorialEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise B10DsoTerritorialCoverageError("source_id is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10DsoTerritorialCoverageError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10DsoTerritorialCoverageError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10DsoTerritorialCoverageError("supports must be a collection")
        if any(not isinstance(claim, str) or not claim.strip() for claim in self.supports):
            raise B10DsoTerritorialCoverageError("supports cannot contain blanks")


@dataclass(frozen=True)
class DsoServiceAreaInventoryRecord:
    operator_id: str
    network_operator: str
    service_area_id: str
    service_area_label: str
    source_refs: tuple[str, ...]
    evidence: tuple[DsoTerritorialEvidence, ...]

    def __post_init__(self) -> None:
        for name in ("operator_id", "network_operator", "service_area_id", "service_area_label"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise B10DsoTerritorialCoverageError(f"{name} is required")
        if self.operator_id not in EXPECTED_DSO_OPERATORS:
            raise B10DsoTerritorialCoverageError("unknown Hungarian electricity DSO operator_id")
        if self.network_operator != EXPECTED_DSO_OPERATORS[self.operator_id]:
            raise B10DsoTerritorialCoverageError("network_operator does not match canonical operator identity")
        if self.service_area_id != EXPECTED_SERVICE_AREA_IDS[self.operator_id]:
            raise B10DsoTerritorialCoverageError("service_area_id does not match canonical DSO service area identity")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10DsoTerritorialCoverageError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10DsoTerritorialCoverageError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10DsoTerritorialCoverageError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[DsoTerritorialEvidence, ...]:
        refs = set(dict.fromkeys(self.source_refs))
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class NationalDsoTerritorialCoverageDecision:
    operator_inventory_status: str
    operator_ids: tuple[str, ...]
    canonical_network_regional_grain: str
    administrative_reporting_grain: str
    service_area_membership_crosswalk_status: str
    exact_dso_node_inventory_status: str
    source_refs: tuple[str, ...]
    evidence_status: str
    reason: str

    def __post_init__(self) -> None:
        if self.operator_inventory_status not in {
            NATIONAL_DSO_OPERATOR_INVENTORY_PROVEN,
            Q_NATIONAL_DSO_OPERATOR_INVENTORY,
        }:
            raise B10DsoTerritorialCoverageError("invalid operator inventory status")
        if self.canonical_network_regional_grain != DSO_SERVICE_AREA:
            raise B10DsoTerritorialCoverageError("B10 canonical network grain must remain DSO_SERVICE_AREA")
        if self.administrative_reporting_grain != ADMINISTRATIVE_REPORTING_GRAIN:
            raise B10DsoTerritorialCoverageError("administrative reporting grain mismatch")
        if self.service_area_membership_crosswalk_status != Q_SERVICE_AREA_MEMBERSHIP_CROSSWALK:
            raise B10DsoTerritorialCoverageError("P14 cannot promote a national service-area membership crosswalk")
        if self.exact_dso_node_inventory_status != Q_EXACT_DSO_NODE_INVENTORY:
            raise B10DsoTerritorialCoverageError("P14 cannot promote an exact DSO node inventory")


def _has_claim(record: DsoServiceAreaInventoryRecord, claim: str, *, max_authority_level: int) -> bool:
    return any(
        item.authority_level <= max_authority_level
        and item.truth_status in {"OBS", "DER"}
        and claim in item.supports
        for item in record.referenced_evidence
    )


def _record_inventory_proven(record: DsoServiceAreaInventoryRecord) -> bool:
    required = {
        DSO_LICENSEE_INVENTORY,
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
    }
    return any(
        item.authority_level <= 2
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
        for item in record.referenced_evidence
    )


def _record_region_label_proven(record: DsoServiceAreaInventoryRecord) -> bool:
    required = {
        DSO_SERVICE_AREA_REGION_LABEL,
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{SERVICE_AREA_ID_PREFIX}{record.service_area_id}",
        f"{SERVICE_AREA_LABEL_PREFIX}{record.service_area_label}",
    }
    return any(
        item.authority_level <= 3
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
        for item in record.referenced_evidence
    )


def assess_national_dso_territorial_coverage(
    records: tuple[DsoServiceAreaInventoryRecord, ...] | list[DsoServiceAreaInventoryRecord],
) -> NationalDsoTerritorialCoverageDecision:
    """Assess the national operator inventory without inventing a spatial crosswalk."""

    if isinstance(records, str) or not records:
        raise B10DsoTerritorialCoverageError("records must be a non-empty collection")
    if any(not isinstance(record, DsoServiceAreaInventoryRecord) for record in records):
        raise B10DsoTerritorialCoverageError("records must contain DsoServiceAreaInventoryRecord values")

    operator_ids = [record.operator_id for record in records]
    if len(operator_ids) != len(set(operator_ids)):
        raise B10DsoTerritorialCoverageError("duplicate DSO operator inventory record")

    exact_operator_set = set(operator_ids) == set(EXPECTED_DSO_OPERATORS)
    inventory_proven = exact_operator_set and all(_record_inventory_proven(record) for record in records)
    labels_proven = exact_operator_set and all(_record_region_label_proven(record) for record in records)

    statuses = {
        item.truth_status
        for record in records
        for item in record.referenced_evidence
    }
    if not inventory_proven or "Q" in statuses:
        evidence_status = "Q"
    elif statuses == {"OBS"}:
        evidence_status = "OBS"
    else:
        evidence_status = "DER"

    source_refs = tuple(
        dict.fromkeys(
            ref
            for record in records
            for ref in record.source_refs
        )
    )

    if inventory_proven and labels_proven:
        reason = (
            "the current six Hungarian electricity DSO operators and their broad source-published service-area labels are covered; "
            "DSO_SERVICE_AREA is the canonical B10 network-regional grain, while settlement/county membership and exact topology remain separate Q authorities"
        )
    elif inventory_proven:
        reason = (
            "the current six Hungarian electricity DSO operators are covered, but one or more broad service-area labels lack referenced authority; "
            "no membership crosswalk or topology is inferred"
        )
    else:
        reason = (
            "the supplied records do not prove the exact current six-operator Hungarian electricity DSO inventory; "
            "national coverage remains Q"
        )

    return NationalDsoTerritorialCoverageDecision(
        operator_inventory_status=(
            NATIONAL_DSO_OPERATOR_INVENTORY_PROVEN
            if inventory_proven
            else Q_NATIONAL_DSO_OPERATOR_INVENTORY
        ),
        operator_ids=tuple(sorted(operator_ids)),
        canonical_network_regional_grain=CANONICAL_NETWORK_REGIONAL_GRAIN,
        administrative_reporting_grain=ADMINISTRATIVE_REPORTING_GRAIN,
        service_area_membership_crosswalk_status=Q_SERVICE_AREA_MEMBERSHIP_CROSSWALK,
        exact_dso_node_inventory_status=Q_EXACT_DSO_NODE_INVENTORY,
        source_refs=source_refs,
        evidence_status=evidence_status,
        reason=reason,
    )


def load_canonical_dso_inventory(path: str | Path) -> tuple[DsoServiceAreaInventoryRecord, ...]:
    """Load the P14 six-row registry with fixed source claims.

    The CSV records source-published operator/service-area identities. It is not a
    settlement polygon, county crosswalk, feeder list or substation inventory.
    """

    path = Path(path)
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    records: list[DsoServiceAreaInventoryRecord] = []
    for row in rows:
        source_refs = tuple(ref for ref in row["source_ids"].split(";") if ref)
        evidence = (
            DsoTerritorialEvidence(
                source_id="SRC-B10-HU-DSO-CURRENT-LIST-2026",
                authority_level=2,
                truth_status="OBS",
                supports=(
                    DSO_LICENSEE_INVENTORY,
                    f"{NETWORK_OPERATOR_PREFIX}{row['network_operator']}",
                ),
            ),
            DsoTerritorialEvidence(
                source_id="SRC-B10-HU-DSO-REGION-LABELS-2026",
                authority_level=2,
                truth_status="OBS",
                supports=(
                    DSO_SERVICE_AREA_REGION_LABEL,
                    f"{NETWORK_OPERATOR_PREFIX}{row['network_operator']}",
                    f"{SERVICE_AREA_ID_PREFIX}{row['service_area_id']}",
                    f"{SERVICE_AREA_LABEL_PREFIX}{row['service_area_label']}",
                ),
            ),
        )
        records.append(
            DsoServiceAreaInventoryRecord(
                operator_id=row["operator_id"],
                network_operator=row["network_operator"],
                service_area_id=row["service_area_id"],
                service_area_label=row["service_area_label"],
                source_refs=source_refs,
                evidence=evidence,
            )
        )
    return tuple(records)


def require_national_dso_operator_inventory(
    decision: NationalDsoTerritorialCoverageDecision,
) -> tuple[str, ...]:
    """Return the six operator IDs only when the national operator inventory is proven."""

    if not isinstance(decision, NationalDsoTerritorialCoverageDecision):
        raise B10DsoTerritorialCoverageError("decision must be NationalDsoTerritorialCoverageDecision")
    if decision.operator_inventory_status != NATIONAL_DSO_OPERATOR_INVENTORY_PROVEN:
        raise B10DsoTerritorialCoverageError("complete national DSO operator inventory authority is required")
    return decision.operator_ids


__all__ = [
    "ADMINISTRATIVE_REPORTING_GRAIN",
    "B10DsoTerritorialCoverageError",
    "CANONICAL_NETWORK_REGIONAL_GRAIN",
    "DSO_LICENSEE_INVENTORY",
    "DSO_SERVICE_AREA_REGION_LABEL",
    "DsoServiceAreaInventoryRecord",
    "DsoTerritorialEvidence",
    "EXPECTED_DSO_OPERATORS",
    "EXPECTED_SERVICE_AREA_IDS",
    "NATIONAL_DSO_OPERATOR_INVENTORY_PROVEN",
    "NationalDsoTerritorialCoverageDecision",
    "Q_EXACT_DSO_NODE_INVENTORY",
    "Q_NATIONAL_DSO_OPERATOR_INVENTORY",
    "Q_SERVICE_AREA_MEMBERSHIP_CROSSWALK",
    "assess_national_dso_territorial_coverage",
    "load_canonical_dso_inventory",
    "require_national_dso_operator_inventory",
]
