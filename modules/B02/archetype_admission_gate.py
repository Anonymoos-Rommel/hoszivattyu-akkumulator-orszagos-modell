"""Fail-closed admission gates for B02 archetype claims.

B02-P9 separates three things that must not be conflated:

1. a contracted archetype dimension schema;
2. a populated current-stock archetype assignment;
3. technical-readiness enrichment of that stock assignment.

A contracted schema is repository architecture, not evidence that the required
joint population exists.  Missing joins, ASS-only building-type linkage, or
unlinked MODELLED energy information therefore remain Q.
"""

from __future__ import annotations

from dataclasses import dataclass


Q = "Q"
QUALIFIED = "QUALIFIED"
CONTRACTED = "CONTRACTED"

REAL_EVIDENCE = frozenset({"OBS", "DER"})
BUILDING_TYPE_LINK_OK = frozenset({"OBS", "DER", "APPROVED_CALIBRATED_MODEL"})
ENERGY_LINK_OK = frozenset({"OBS", "DER", "MODELLED_LINKED"})


@dataclass(frozen=True)
class AdmissionDecision:
    status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class StockArchetypeInputs:
    schema_status: str
    wbl_joint_complete: bool
    building_type_link_status: str
    primary_energy_link_status: str


def assess_stock_archetype(inputs: StockArchetypeInputs) -> AdmissionDecision:
    """Assess whether a populated current-stock archetype is authoritative."""

    blockers: list[str] = []
    if inputs.schema_status != CONTRACTED:
        blockers.append("SCHEMA_NOT_CONTRACTED")
    if not inputs.wbl_joint_complete:
        blockers.append("NO_COMPLETE_WBL_JOINT")
    if inputs.building_type_link_status not in BUILDING_TYPE_LINK_OK:
        blockers.append("NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY")
    if inputs.primary_energy_link_status not in ENERGY_LINK_OK:
        blockers.append("NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY")

    if blockers:
        return AdmissionDecision(Q, tuple(blockers))
    return AdmissionDecision(QUALIFIED, ())


def assess_technical_readiness_enrichment(
    stock_inputs: StockArchetypeInputs,
    *,
    heat_emitter_status: str,
    design_temperature_status: str,
) -> AdmissionDecision:
    """Require real current evidence for technical readiness enrichment."""

    stock = assess_stock_archetype(stock_inputs)
    blockers = list(stock.blockers)
    if heat_emitter_status not in REAL_EVIDENCE:
        blockers.append("NO_CURRENT_HEAT_EMITTER_EVIDENCE")
    if design_temperature_status not in REAL_EVIDENCE:
        blockers.append("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE")

    if blockers:
        return AdmissionDecision(Q, tuple(blockers))
    return AdmissionDecision(QUALIFIED, ())
