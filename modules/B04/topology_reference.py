"""Dated, read-only H topology/legal reference; never a dispatch permission.

Each returned operation distinguishes reference-path applicability from its
researched OPEN actual-site legal status. This reader cannot certify as-built
wiring, enrol a device or turn source rules into household authorization.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

ROOT = Path(__file__).resolve().parents[2]
AS_OF = "2026-10-03"
DATA_RELATIVE = "data/processed/b04/topology_reference_20261003.json"
MANIFEST_RELATIVE = "registry/b04_topology_reference_manifest.json"
MANIFEST_SHA256 = "3afac7d2b29a51fc97abf3d1f7778a09b6a7478972db212374b825319f7ddfe2"
OPERATIONS = frozenset({
    "BATTERY_CHARGE_FROM_H", "BATTERY_DISCHARGE_INTO_OR_THROUGH_H",
    "EXPORT_FROM_H_OR_H_CHARGED_STORAGE", "VPP_AGGREGATION_CONTROL",
})
TOPOLOGIES = frozenset({
    "H-ONLY-DEDICATED", "NORMAL-A1", "BATTERY-NORMAL-ONLY",
    "BATTERY-H-SIDE", "HYBRID-COMMON-BUS", "HMKE-EXPORT",
})


class TopologyReferenceError(ValueError):
    """The requested reference is outside its exact verified scope."""


def _require(condition, message):
    if not condition:
        raise TopologyReferenceError(message)


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class TopologyReference:
    as_of: str
    topologies: Mapping
    claims: Mapping
    sources: Mapping
    conditional_source_exclusion: Mapping
    boundaries: Mapping
    dispatch_contract: Mapping

    def operation(self, topology_id: str, operation: str) -> Mapping:
        """Return the immutable reference disposition, not actual permission."""
        _require(isinstance(topology_id, str) and topology_id in self.topologies,
                 "An exact admitted topology ID is required")
        _require(isinstance(operation, str) and operation in OPERATIONS,
                 "An exact independent operation is required")
        return self.topologies[topology_id]["operations"][operation]

    def require_operation_permission(self, topology_id: str, operation: str):
        """Fail closed even for physically possible or non-exporting service."""
        row = self.operation(topology_id, operation)
        raise TopologyReferenceError(
            f"{topology_id}/{operation}: actual permission is {row['legal_status']}; "
            "the source reference cannot authorize pricing, dispatch or enrolment"
        )


def load_topology_reference(*, as_of: str, root: Path = ROOT) -> TopologyReference:
    """Read exact dated bytes, including relocated byte-identical copies.

    No default date, future-currentness inference, mutable source override,
    evidence Boolean, device value or household identifier is accepted.
    """
    _require(isinstance(as_of, str) and as_of == AS_OF,
             "Only the explicit 2026-10-03 research reference is admitted")
    root = Path(root)
    try:
        manifest_bytes = (root / MANIFEST_RELATIVE).read_bytes()
        _require(hashlib.sha256(manifest_bytes).hexdigest() == MANIFEST_SHA256,
                 "Topology source manifest identity mismatch")
        manifest = json.loads(manifest_bytes)
        artifact = manifest["artifact"]
        _require(artifact["path"] == DATA_RELATIVE, "Unexpected reference path")
        data_bytes = (root / DATA_RELATIVE).read_bytes()
        _require(len(data_bytes) == artifact["bytes"] and
                 hashlib.sha256(data_bytes).hexdigest() == artifact["sha256"],
                 "Topology reference byte identity mismatch")
        data = json.loads(data_bytes)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise TopologyReferenceError("Incomplete topology reference input") from exc
    _require(data["research_as_of"] == as_of, "Research date mismatch")
    sources = {source["source_id"]: source for source in manifest["sources"]}
    _require(len(sources) == manifest["source_count"] == 21,
             "Source inventory is incomplete or duplicated")
    topologies = {row["topology_id"]: row for row in data["topologies"]}
    _require(len(data["topologies"]) == 6 and set(topologies) == TOPOLOGIES,
             "Reference topology inventory mismatch")
    for topology in topologies.values():
        _require(topology["schematic_type"] ==
                 "REFERENCE_ONLY_NOT_AS_BUILT_NOT_INSTALLATION_APPROVAL" and
                 topology["actual_topology_status"] == "OPEN" and
                 topology["connection_point_to_pod_mapping_status"] == "OPEN",
                 "Reference wiring must not become actual-site evidence")
        _require(set(topology["operations"]) == OPERATIONS,
                 "Four independent operations are required")
        for row in topology["operations"].values():
            _require(row["legal_status"] == "OPEN" and
                     row["compatibility_registry_status"] == "Q" and
                     row["execution_authorized"] is False,
                     "No actual operation permission is admitted")
            _require(row["value_of_foregone_benefit"] is None and
                     row["foregone_benefit_status"] == "UNKNOWN_NOT_ZERO",
                     "Unknown foregone value must not become zero")
            _require(row["reason"] and row["evidence_route"] and row["source_ids"]
                     and set(row["source_ids"]) <= sources.keys(),
                     "Every OPEN disposition needs sources and an evidence route")
    claims = {row["claim_id"]: row for row in data["claims"]}
    _require(len(claims) == len(data["claims"]), "Duplicate claim ID")
    _require(all(set(row["source_ids"]) <= sources.keys() for row in claims.values()),
             "Unresolved claim source")
    return TopologyReference(
        as_of, _freeze(topologies), _freeze(claims), _freeze(sources),
        _freeze(data["conditional_source_exclusion"]), _freeze(data["boundaries"]),
        _freeze(data["dispatch_contract"]),
    )
