"""B02-P67 foreign response and Hungarian official cost-ceiling authority.

P67 admits two evidence surfaces without silently transferring them beyond
their source scope:

1. DESNZ/BEIS Electrification of Heat (EoH) property/design/installation plus
   monitored-performance data as a foreign conditional physical-response
   envelope.
2. KEHOP Plusz-4.1.7-24 maximum eligible costs as Hungarian official upper
   cost bounds.

Canonical boundaries:

FOREIGN RESPONSE FREQUENCY != HUNGARIAN POPULATION WEIGHT
EMITTER MEASURE COUNT != P66 KEEP/UPSIZE/CHANGE/ADD/REPLACE LABEL
MEASURED SPF != DESIGN-POINT COP
OFFICIAL MAXIMUM ELIGIBLE COST != MARKET-TYPICAL COST
UPPER-BOUND AUTHORITY != CENTRAL ESTIMATE AUTHORITY
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite


Q = "Q"
QUALIFIED = "QUALIFIED"
QUALIFIED_VALIDATION_ONLY = "QUALIFIED_VALIDATION_ONLY"
QUALIFIED_OFFICIAL_UPPER_BOUND = "QUALIFIED_OFFICIAL_UPPER_BOUND"


@dataclass(frozen=True)
class ForeignResponseEnvelope:
    source_country: str
    scope_id: str
    installed_n: int
    emitter_measure_n: int
    emitter_measure_share: float
    emitter_units_p10: float
    emitter_units_p50: float
    emitter_units_p90: float
    mean_sh_flow_c_p10: float | None
    mean_sh_flow_c_p50: float | None
    mean_sh_flow_c_p90: float | None
    spfh4_p10: float | None
    spfh4_p50: float | None
    spfh4_p90: float | None


@dataclass(frozen=True)
class AuthorityDecision:
    status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class OfficialCostCeiling:
    cost_id: str
    material_max_huf: float
    labour_max_huf: float
    total_max_huf: float
    unit: str
    source_role: str = "OFFICIAL_MAXIMUM_ELIGIBLE_COST"


def _finite_nonnegative(value: float | None) -> bool:
    return value is not None and isfinite(float(value)) and float(value) >= 0.0


def _ordered(values: tuple[float | None, float | None, float | None]) -> bool:
    if any(v is None for v in values):
        return False
    a, b, c = (float(v) for v in values)
    return _finite_nonnegative(a) and a <= b <= c


def validate_foreign_response_envelope(
    envelope: ForeignResponseEnvelope,
    *,
    tolerance: float = 1e-9,
) -> AuthorityDecision:
    blockers: list[str] = []
    if envelope.source_country == "HU":
        blockers.append("P67_EXPECTS_FOREIGN_RESPONSE_SOURCE")
    if envelope.installed_n <= 0:
        blockers.append("INSTALLED_SAMPLE_EMPTY")
    if envelope.emitter_measure_n < 0 or envelope.emitter_measure_n > envelope.installed_n:
        blockers.append("EMITTER_MEASURE_COUNT_INVALID")
    if not 0.0 <= envelope.emitter_measure_share <= 1.0:
        blockers.append("EMITTER_MEASURE_SHARE_OUTSIDE_UNIT_INTERVAL")
    elif envelope.installed_n > 0 and not isclose(
        envelope.emitter_measure_share,
        envelope.emitter_measure_n / envelope.installed_n,
        abs_tol=tolerance,
    ):
        blockers.append("EMITTER_MEASURE_SHARE_DOES_NOT_RECONCILE")
    if not _ordered(
        (
            envelope.emitter_units_p10,
            envelope.emitter_units_p50,
            envelope.emitter_units_p90,
        )
    ):
        blockers.append("EMITTER_UNIT_QUANTILES_INVALID")

    flow = (
        envelope.mean_sh_flow_c_p10,
        envelope.mean_sh_flow_c_p50,
        envelope.mean_sh_flow_c_p90,
    )
    if any(v is not None for v in flow) and not _ordered(flow):
        blockers.append("FLOW_TEMPERATURE_QUANTILES_INVALID")

    spf = (envelope.spfh4_p10, envelope.spfh4_p50, envelope.spfh4_p90)
    if any(v is not None for v in spf) and not _ordered(spf):
        blockers.append("SPFH4_QUANTILES_INVALID")

    if blockers:
        return AuthorityDecision(Q, tuple(blockers))
    return AuthorityDecision(QUALIFIED_VALIDATION_ONLY, ())


def assess_hungarian_use(
    envelope: ForeignResponseEnvelope,
    *,
    requested_use: str,
    hungarian_reweighting_authority_status: str = Q,
    p66_action_crosswalk_status: str = Q,
) -> AuthorityDecision:
    """Gate source-bounded use of the foreign response envelope."""

    base = validate_foreign_response_envelope(envelope)
    if base.status == Q:
        return base

    blockers: list[str] = []
    if requested_use == "HUNGARIAN_POPULATION_PREVALENCE":
        blockers.append("FOREIGN_FREQUENCY_NOT_HUNGARIAN_WEIGHT")
    elif requested_use == "P66_ACTION_OUTCOME":
        if hungarian_reweighting_authority_status != QUALIFIED:
            blockers.append("NO_HUNGARIAN_P21_REWEIGHTING_AUTHORITY")
        if p66_action_crosswalk_status != QUALIFIED:
            blockers.append("NO_P66_ACTION_CROSSWALK")
    elif requested_use != "PHYSICAL_RESPONSE_VALIDATION":
        blockers.append("UNSUPPORTED_RESPONSE_USE")

    if blockers:
        return AuthorityDecision(Q, tuple(blockers))
    return AuthorityDecision(QUALIFIED_VALIDATION_ONLY, ())


def validate_official_cost_ceiling(
    ceiling: OfficialCostCeiling,
    *,
    tolerance: float = 1e-6,
) -> AuthorityDecision:
    blockers: list[str] = []
    for name, value in (
        ("material_max_huf", ceiling.material_max_huf),
        ("labour_max_huf", ceiling.labour_max_huf),
        ("total_max_huf", ceiling.total_max_huf),
    ):
        if not _finite_nonnegative(value):
            blockers.append(f"{name.upper()}_INVALID")
    if not ceiling.cost_id.strip():
        blockers.append("COST_ID_MISSING")
    if not ceiling.unit.strip():
        blockers.append("UNIT_MISSING")
    if ceiling.source_role != "OFFICIAL_MAXIMUM_ELIGIBLE_COST":
        blockers.append("SOURCE_ROLE_NOT_OFFICIAL_MAXIMUM")
    if not isclose(
        ceiling.material_max_huf + ceiling.labour_max_huf,
        ceiling.total_max_huf,
        abs_tol=tolerance,
    ):
        blockers.append("COST_COMPONENTS_DO_NOT_RECONCILE")

    if blockers:
        return AuthorityDecision(Q, tuple(blockers))
    return AuthorityDecision(QUALIFIED_OFFICIAL_UPPER_BOUND, ())


def assess_cost_use(
    ceiling: OfficialCostCeiling,
    *,
    requested_use: str,
) -> AuthorityDecision:
    base = validate_official_cost_ceiling(ceiling)
    if base.status == Q:
        return base
    if requested_use == "PROGRAMME_COST_UPPER_BOUND":
        return base
    if requested_use in {"MARKET_TYPICAL", "EXPECTED_REALIZED_COST", "LOWER_BOUND"}:
        return AuthorityDecision(Q, ("OFFICIAL_MAXIMUM_IS_NOT_MARKET_DISTRIBUTION",))
    return AuthorityDecision(Q, ("UNSUPPORTED_COST_USE",))
