"""Programme-sufficiency contract for the B02 radiator branch.

B02 is not complete merely because one radiator-equipped dwelling can pass a
technical sizing check.  The programme also needs stock quantities and retrofit
need so B06 can later size replacement emitters and calculate CAPEX.

This module therefore separates:

- record-level radiator feasibility;
- stock-level radiator quantity/type characterization;
- stock-level reuse/upgrade requirement;
- B06 replacement-quantity handoff.

A technical PASS cannot substitute for missing programme quantities.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Q = "Q"
QUALIFIED = "QUALIFIED"
REAL_OR_MODELLED_EVIDENCE = frozenset({"OBS", "DER", "ASS", "MODELLED"})


@dataclass(frozen=True)
class RadiatorProgrammeStockCandidate:
    scope_id: str
    represented_dwellings: int | None
    current_radiator_dwellings: int | None
    current_radiator_units: int | None
    stock_evidence_status: str
    stock_authority_status: str
    type_size_distribution_complete: bool
    type_size_authority_status: str
    retrofit_need_classification_complete: bool
    retrofit_need_authority_status: str
    replacement_units_required: int | None
    replacement_quantity_authority_status: str
    uncertainty_documented: bool
    reproducible_repository_binding: bool


@dataclass(frozen=True)
class RadiatorProgrammeStockDecision:
    status: str
    reasons: tuple[str, ...]


def assess_radiator_programme_stock(
    candidate: RadiatorProgrammeStockCandidate,
) -> RadiatorProgrammeStockDecision:
    """Admit a radiator result only when it is usable for programme planning.

    The function intentionally does not decide *which replacement product* B06
    should select.  It proves only that B02 can say how much radiator stock is
    represented, how many units exist, what type/size distribution is known,
    how much of the stock needs emitter intervention, and how many replacement
    units must be handed to B06 for engineering/product/CAPEX selection.
    """

    reasons: list[str] = []
    if not candidate.scope_id.strip():
        reasons.append("RADIATOR_STOCK_SCOPE_ID_MISSING")

    represented = candidate.represented_dwellings
    radiator_dwellings = candidate.current_radiator_dwellings
    radiator_units = candidate.current_radiator_units
    replacement_units = candidate.replacement_units_required

    if represented is None or represented <= 0:
        reasons.append("REPRESENTED_DWELLING_COUNT_MISSING_OR_INVALID")
    if radiator_dwellings is None or radiator_dwellings < 0:
        reasons.append("CURRENT_RADIATOR_DWELLING_COUNT_MISSING_OR_INVALID")
    if (
        represented is not None
        and represented > 0
        and radiator_dwellings is not None
        and radiator_dwellings > represented
    ):
        reasons.append("RADIATOR_DWELLINGS_EXCEED_SCOPE")
    if radiator_units is None or radiator_units < 0:
        reasons.append("CURRENT_RADIATOR_UNIT_COUNT_MISSING_OR_INVALID")
    if (
        radiator_dwellings is not None
        and radiator_dwellings > 0
        and radiator_units is not None
        and radiator_units < radiator_dwellings
    ):
        reasons.append("RADIATOR_UNIT_COUNT_BELOW_RADIATOR_DWELLING_COUNT")

    if candidate.stock_evidence_status not in REAL_OR_MODELLED_EVIDENCE:
        reasons.append("RADIATOR_STOCK_EVIDENCE_STATUS_INVALID")
    if candidate.stock_authority_status != QUALIFIED:
        reasons.append("RADIATOR_STOCK_AUTHORITY_NOT_ADMITTED")

    if not candidate.type_size_distribution_complete:
        reasons.append("RADIATOR_TYPE_SIZE_DISTRIBUTION_INCOMPLETE")
    if candidate.type_size_authority_status != QUALIFIED:
        reasons.append("RADIATOR_TYPE_SIZE_AUTHORITY_NOT_ADMITTED")

    if not candidate.retrofit_need_classification_complete:
        reasons.append("RADIATOR_RETROFIT_NEED_CLASSIFICATION_INCOMPLETE")
    if candidate.retrofit_need_authority_status != QUALIFIED:
        reasons.append("RADIATOR_RETROFIT_NEED_AUTHORITY_NOT_ADMITTED")

    if replacement_units is None or replacement_units < 0:
        reasons.append("REPLACEMENT_RADIATOR_UNIT_COUNT_MISSING_OR_INVALID")
    if candidate.replacement_quantity_authority_status != QUALIFIED:
        reasons.append("REPLACEMENT_QUANTITY_AUTHORITY_NOT_ADMITTED")

    if not candidate.uncertainty_documented:
        reasons.append("RADIATOR_STOCK_UNCERTAINTY_NOT_DOCUMENTED")
    if not candidate.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_RADIATOR_STOCK_BINDING")

    # Avoid accidentally accepting NaN-like values if future callers pass
    # numeric subclasses instead of plain ints.
    for value, reason in (
        (represented, "REPRESENTED_DWELLING_COUNT_NONFINITE"),
        (radiator_dwellings, "CURRENT_RADIATOR_DWELLING_COUNT_NONFINITE"),
        (radiator_units, "CURRENT_RADIATOR_UNIT_COUNT_NONFINITE"),
        (replacement_units, "REPLACEMENT_RADIATOR_UNIT_COUNT_NONFINITE"),
    ):
        if value is not None and not isfinite(float(value)):
            reasons.append(reason)

    if reasons:
        return RadiatorProgrammeStockDecision(Q, tuple(reasons))
    return RadiatorProgrammeStockDecision(QUALIFIED, ())
