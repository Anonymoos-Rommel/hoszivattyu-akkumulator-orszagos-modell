"""Seven bounded B10-D02 procurement references, never a national cost base.

Only source-native facts and named within-record arithmetic are exposed. Every
returned value retains its source, scope, price basis and correlation cluster.
This adapter does not populate P3/P5/P11/P32 or qualify P67 national inference.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data/processed/b10/cost_reference_observations.json"
MANIFEST_PATH = ROOT / "registry/b10_cost_reference_manifest.json"
EXACT_REFERENCE_ONLY = "EXACT_REFERENCE_ONLY"
SUPPLY = "AWARDED_TRANSFORMER_SUPPLY"
CONNECTION = "AWARDED_STORAGE_CONNECTION_PACKAGE"
SUBSTATION = "AWARDED_SUBSTATION_WORKS_PACKAGE"
BILL_ITEM = "AMENDED_BILL_ITEM_ALLOCATION"
REJECTED_PRICE_KINDS = frozenset({
    "FRAMEWORK_MAXIMUM_CEILING", "LIFECYCLE_BID_SCORE", "UNRESOLVED_RESERVE_FIELD",
})
PRICE_KINDS = frozenset({SUPPLY, CONNECTION, SUBSTATION, BILL_ITEM}) | REJECTED_PRICE_KINDS
ORGOVANY_I = "B10-REF-TED-438132-2026-LOT-0001"
CONTRACT_SOURCE = "SRC-B10-V1-EKR-SZ0176453-CONTRACT-20260610"
BOQ_SOURCE = "SRC-B10-V1-EKR-SZ0176453-BOQ-20251202"
ANNEX_SOURCE = "SRC-B10-V1-EKR-SZ0176453-ANNEX-BUNDLE-20260722"
SUPPLEMENT_SOURCES = frozenset({CONTRACT_SOURCE, BOQ_SOURCE, ANNEX_SOURCE})
EKR_URL = "https://ekr.gov.hu/ekr-szerzodestar/hu/szerzodes/1204237"

# Only these reviewed facts are admitted for this exact lot. Dates, conditions
# and unresolved actuals remain typed metadata, never inferred numeric costs.
_SUPPLEMENT_FACTS = {
    "contract_net_amount": ("HUF", CONTRACT_SOURCE, "BASE_LUMP_SUM_EXCLUDING_RESERVE"),
    "conditional_reserve_amount": ("HUF", CONTRACT_SOURCE, "CONDITIONAL_RESERVE_NOT_COST_OR_FORECAST"),
    "reserve_percentage_as_printed": ("percent", CONTRACT_SOURCE, "PRINTED_PERCENT_NOT_RECOMPUTED_AMOUNT"),
    "boq_anyag_total": ("HUF", BOQ_SOURCE, "SOURCE_NATIVE_ANYAG_COLUMN"),
    "boq_dij_total": ("HUF", BOQ_SOURCE, "SOURCE_NATIVE_DIJ_COLUMN"),
    "boq_net_total": ("HUF", BOQ_SOURCE, "SAME_BASE_PACKAGE_NOT_ADDITIONAL_COST"),
    "route_a_header_length": ("m_route_header_A", BOQ_SOURCE, "DISTINCT_FROM_NOTICE_AND_CABLE_ITEM_LENGTHS"),
    "route_b_header_length": ("m_route_header_B", BOQ_SOURCE, "DISTINCT_ROUTE_HEADER"),
    "maximum_duration_after_site_handover": ("calendar_day_planned", CONTRACT_SOURCE, "CONDITIONAL_CONTRACT_SCHEDULE"),
    "site_handover_after_effectiveness": ("working_day_planned", CONTRACT_SOURCE, "CONDITIONAL_CONTRACT_SCHEDULE"),
    "telecontrol_before_final_deadline": ("calendar_day_before_planned_final", CONTRACT_SOURCE, "CONDITIONAL_CONTRACT_SCHEDULE"),
    "base_invoice_count": ("invoice_contractual", CONTRACT_SOURCE, "AFTER_CERTIFIED_PERFORMANCE"),
    "invoice_issuance_after_certificate": ("calendar_day_contractual", CONTRACT_SOURCE, "AFTER_SIGNED_PERFORMANCE_CERTIFICATE"),
    "advance_payment_after_request": ("calendar_day_contractual", CONTRACT_SOURCE, "ONLY_IF_VALID_ADVANCE_REQUEST"),
    "payment_after_invoice_without_subcontractor": ("calendar_day_contractual", CONTRACT_SOURCE, "ONLY_WITHOUT_SUBCONTRACTOR"),
}
_SUPPLEMENT_UNKNOWNS = frozenset({
    "actual_reserve_used_huf", "actual_advance_huf", "actual_effectiveness_date",
    "actual_site_handover_date", "actual_completion_date", "actual_paid_huf",
    "annual_cashflow_huf", "economic_price_base_date", "normalized_2026_huf",
    "complete_purchaser_free_issue_schedule", "national_programme_attribution",
})
_SUPPLEMENT_BOUNDARIES = {
    "reserve_addition_to_cost_or_forecast_allowed": False,
    "pure_material_labour_deflator_buckets": False,
    "contract_schedule_is_actual_cashflow": False,
    "generic_unit_price_conversion_allowed": False,
    "granular_component_prices_admitted": False,
    "complete_free_issue_schedule_observed": False,
}

# These are admission boundaries, not duplicated monetary inputs.
_SOURCE_SPECS = {
    "SRC-B10-V1-TED-777208-2025":
        (SUPPLY, "EKR001295922025", "EUR", "NET_PRICE_ELEMENT",
         "2025-09_CONTRACT_PRICE_FIXATION_UNKNOWN", ("LOT-0001", "LOT-0002")),
    "SRC-B10-V1-TED-438132-2026":
        (CONNECTION, "EKR001158812025", "HUF", "NET_EXCLUDING_VAT",
         "2026-06_CONTRACT_NOMINAL", ("LOT-0001", "LOT-0002", "LOT-0003")),
    "SRC-B10-V1-TED-761369-2025":
        (SUBSTATION, "EKR000003612025", "HUF", "NET_EXCLUDING_VAT",
         "2025-11_CONTRACT_PRICE_FIXATION_UNKNOWN", ("LOT-0001",)),
    "SRC-B10-V1-TED-373350-2026":
        (BILL_ITEM, "EKR000373342022", "HUF", "NET_CONTRACT_ALLOCATION",
         "2026-04_AMENDMENT_ECONOMIC_VINTAGE_UNKNOWN", ("122236",)),
}
EXPECTED_IDS = frozenset(
    f"B10-REF-TED-{source.removeprefix('SRC-B10-V1-TED-')}-{lot}"
    for source, spec in _SOURCE_SPECS.items() for lot in spec[-1]
)
UNKNOWN_FIELDS = frozenset({
    "usable_capacity_increment_mw", "programme_incremental_capex_huf",
    "installed_project_total_huf", "actual_paid_huf", "actual_completion_date",
    "annual_cashflow_huf", "normalized_2026_huf", "economic_price_base_date",
    "equipment_supply_free_issue_split", "reserve_included", "exact_network_node",
    "cohort_weight",
})
_RECORD_FIELDS = frozenset({
    "observation_id", "source_id", "source_locator", "document_revision",
    "procurement_family_id", "correlation_cluster_id", "lot_or_item_id",
    "observation_kind", "currency", "vat_basis", "price_basis", "contract_date",
    "amendment_date", "publication_date", "buyer_context", "supplier_context",
    "geography", "geography_semantics", "source_nuts_label", "geography_warning",
    "technical_scope", "scope_qualification", "evidence_tier", "permitted_use",
    "national_input_status", "facts", "unknowns", "limitations",
})


class CostReferenceError(ValueError):
    """Unsupported evidence, scope, transformation or reference request."""


def _require(condition, message):
    if not condition:
        raise CostReferenceError(message)


def _digest(record):
    return hashlib.sha256(json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def _number(value):
    _require(isinstance(value, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value),
             "facts require finite positive decimal strings, not floats or booleans")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise CostReferenceError("invalid numeric fact") from exc
    _require(number.is_finite() and number > 0, "fact must be positive and finite")
    return number


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _units(kind, lot):
    if kind == SUPPLY:
        return dict(lot_amount="EUR", asset_count="transformer", nameplate_per_asset="MVA",
                    planned_duration="month_planned")
    if kind == CONNECTION:
        units = dict(lot_amount="HUF", contracted_storage_power="MW_storage",
                     contracted_storage_energy="MWh_storage", transformer_count="transformer",
                     transformer_per_asset="kVA", mv_cable_length="m",
                     mv_cable_cross_section="mm2", planned_duration="calendar_day_planned")
        if lot == "LOT-0003":
            units["overhead_source_quantity"] = "km_source_declared_1x3_conductor_scope"
        return units
    if kind == SUBSTATION:
        return dict(lot_amount="HUF", planned_duration="calendar_day_planned",
                    notice_duration_display="month_planned")
    return dict(quantity="m_bill_item", unit_price="HUF/m_bill_item", line_total="HUF")


def _validate_supplement(row, supplemental_sources):
    supplement = row["contract_supplement"]
    _require(set(supplement) == {"status", "facts", "reserve_included", "dates",
                                "conditions", "boundaries", "unknowns"},
             "unexpected contract supplement fields")
    _require(supplement["status"] == "ORGOVANY_I_ONLY_REVIEWED_AGGREGATES",
             "supplement cannot broaden its lot or publication scope")
    _require(supplement["boundaries"] == _SUPPLEMENT_BOUNDARIES and
             all(type(v) is bool for v in supplement["boundaries"].values()),
             "conditional reserve, native columns and schedule boundaries required")
    _require(set(supplement["unknowns"]) == _SUPPLEMENT_UNKNOWNS and
             all(v is None for v in supplement["unknowns"].values()),
             "supplement actuals, normalization and attribution must remain unknown")
    reserve = supplement["reserve_included"]
    _require(set(reserve) == {"value", "truth_status", "source_id", "source_locator"} and
             reserve["value"] is False and reserve["truth_status"] == "OBS" and
             reserve["source_id"] == CONTRACT_SOURCE and bool(reserve["source_locator"]),
             "only signed-contract exclusion of reserve is admitted")
    _require(set(supplement["facts"]) == set(_SUPPLEMENT_FACTS),
             "unreviewed or missing supplemental facts")
    for name, fact in supplement["facts"].items():
        unit, sid, role = _SUPPLEMENT_FACTS[name]
        _require(set(fact) == {"value", "unit", "truth_status", "source_id", "source_locator", "role"} and
                 (fact["unit"], fact["source_id"], fact["role"]) == (unit, sid, role) and
                 fact["truth_status"] == "OBS" and bool(fact["source_locator"]),
                 "supplement fact source, truth, unit or role mismatch")
        _number(fact["value"])
    dates = supplement["dates"]
    _require(set(dates) == {"latest_visible_signature", "boq_cover_date"},
             "only observed signature and cover dates admitted")
    for name, sid, meaning in (
        ("latest_visible_signature", CONTRACT_SOURCE, "VISIBLE_SIGNING_DATE_CRYPTOGRAPHIC_VALIDITY_NOT_TESTED"),
        ("boq_cover_date", BOQ_SOURCE, "OBSERVED_COVER_DATE_NOT_PROVEN_ECONOMIC_PRICE_BASE"),
    ):
        fact = dates[name]
        _require(set(fact) == {"value", "truth_status", "source_id", "source_locator", "semantics"} and
                 fact["source_id"] == sid and fact["truth_status"] == "OBS" and
                 fact["value"] == supplemental_sources[sid]["document_date"] and
                 fact["semantics"] == meaning and bool(fact["source_locator"]),
                 "date observation cannot become an economic price-fixation assumption")
    conditions = supplement["conditions"]
    expected_conditions = {
        "reserve_use": CONTRACT_SOURCE, "effectiveness": CONTRACT_SOURCE,
        "planned_timing": CONTRACT_SOURCE, "payment": CONTRACT_SOURCE,
        "native_columns": BOQ_SOURCE, "hardware_inclusion": BOQ_SOURCE,
        "route_denominators": BOQ_SOURCE, "crosshatched_cells": BOQ_SOURCE,
    }
    _require(set(conditions) == set(expected_conditions), "source-bound conditions required")
    for name, sid in expected_conditions.items():
        condition = conditions[name]
        _require(set(condition) == {"summary", "source_id", "source_locator"} and
                 condition["source_id"] == sid and bool(condition["source_locator"]) and
                 isinstance(condition["summary"], str) and bool(condition["summary"].strip()),
                 "condition requires source-bound summary")
    facts = supplement["facts"]
    with localcontext() as context:
        context.prec = 40
        amount = _number(row["facts"]["lot_amount"]["value"])
        _require(amount == _number(facts["contract_net_amount"]["value"]) ==
                 _number(facts["boq_net_total"]["value"]), "TED/contract/BoQ base mismatch")
        _require(_number(facts["boq_anyag_total"]["value"]) +
                 _number(facts["boq_dij_total"]["value"]) == amount,
                 "source-native column reconciliation mismatch")


def validate_payload(data, manifest):
    """Validate bounded semantics and per-record provenance before consumption.

    The loader additionally checks the exact data-file digest. Hashes establish
    revision identity, not truth; source review and the external-PDF verifier are
    separate checks. New records require an explicit reviewed adapter revision.
    """
    _require(set(data) == {"schema_version", "admission_status", "slice_id", "observations"},
             "unexpected data fields, including unsupported normalizations")
    _require(type(data["schema_version"]) is int and data["schema_version"] == 1,
             "unsupported data schema")
    _require(data["admission_status"] == "E1_REFERENCE_ONLY" and data["slice_id"] == "B10-D02",
             "reference-only admission required")
    _require(manifest.get("schema_version") == 1 and
             manifest.get("status") == "BOUNDED_REFERENCE_INTAKE", "invalid manifest")
    _require(manifest.get("data_path") == "data/processed/b10/cost_reference_observations.json",
             "canonical data identity mismatch")
    _require(set(manifest.get("excluded_price_kinds", {})) == REJECTED_PRICE_KINDS,
             "excluded price kinds must remain explicit")
    sources = manifest.get("sources", [])
    _require(len(sources) == len(_SOURCE_SPECS) and
             {s.get("source_id") for s in sources} == set(_SOURCE_SPECS),
             "four distinct claim-bearing TED PDF sources required")
    source_map = {s["source_id"]: s for s in sources}
    for sid, source in source_map.items():
        revision = sid.removeprefix("SRC-B10-V1-TED-")
        _require(source.get("document_revision") == revision and source.get("original_url") ==
                 f"https://ted.europa.eu/hu/notice/{revision}/pdf", "source rendition mismatch")
        _require(re.fullmatch(r"[0-9a-f]{64}", source.get("sha256", "")), "source SHA256 required")
        _require(source.get("repo_snapshot_path") is None and source.get("reuse_status") ==
                 "EXTERNAL_ONLY", "raw source material must remain external-only")
        _require(source.get("source_tier") == "P1" and source.get("evidence_status") == "OBS",
                 "primary observed source authority required")
        try:
            date.fromisoformat(source["document_date"])
            datetime.fromisoformat(source["retrieved_at"])
        except (KeyError, ValueError, TypeError) as exc:
            raise CostReferenceError("source dates required") from exc
    supplemental_sources = manifest.get("supplemental_sources", [])
    _require(len(supplemental_sources) == len(SUPPLEMENT_SOURCES) and
             {s.get("source_id") for s in supplemental_sources} == SUPPLEMENT_SOURCES,
             "exact contract, priced-bill and parent-archive provenance required")
    supplemental_sources = {s["source_id"]: s for s in supplemental_sources}
    for sid, source in supplemental_sources.items():
        _require(source.get("original_url") == EKR_URL and
                 source.get("observation_id") == ORGOVANY_I and
                 source.get("correlation_cluster_id") == "EKR001158812025" and
                 source.get("source_tier") == "P1" and source.get("evidence_status") == "OBS",
                 "supplement provenance must bind this exact EKR contract and lot")
        _require(re.fullmatch(r"[0-9a-f]{64}", source.get("sha256", "")) and
                 source.get("repo_snapshot_path") is None and source.get("reuse_status") == "EXTERNAL_ONLY" and
                 source.get("curated_reuse_scope") == "REVIEWED_NONPERSONAL_AGGREGATES_AND_CONDITIONS_ONLY",
                 "supplement source identity and narrow reuse boundary required")
        try:
            date.fromisoformat(source["document_date"])
            datetime.fromisoformat(source["retrieved_at"])
        except (KeyError, ValueError, TypeError) as exc:
            raise CostReferenceError("supplement source dates required") from exc
    _require(supplemental_sources[BOQ_SOURCE].get("parent_source_id") == ANNEX_SOURCE and
             bool(supplemental_sources[BOQ_SOURCE].get("zip_member")), "priced-bill archive lineage required")
    records = data["observations"]
    _require(isinstance(records, list) and len(records) == len(EXPECTED_IDS) and
             {r.get("observation_id") for r in records} == EXPECTED_IDS,
             "exactly the seven bounded observation identities required")
    bindings = manifest.get("record_bindings", [])
    _require(len(bindings) == len(EXPECTED_IDS) and
             {b.get("observation_id") for b in bindings} == EXPECTED_IDS, "record bindings required")
    bindings = {b["observation_id"]: b for b in bindings}
    for row in records:
        refined = row["observation_id"] == ORGOVANY_I
        expected_fields = _RECORD_FIELDS | {"contract_supplement"} if refined else _RECORD_FIELDS
        _require(set(row) == expected_fields, "unexpected or missing record fields")
        sid = row["source_id"]
        _require(sid in _SOURCE_SPECS, "source not admitted")
        kind, family, currency, vat, basis, lots = _SOURCE_SPECS[sid]
        _require(row["observation_kind"] == kind, "price kind not admitted for source")
        _require(row["lot_or_item_id"] in lots and row["observation_id"] ==
                 f"B10-REF-TED-{row['document_revision']}-{row['lot_or_item_id']}", "lot identity mismatch")
        _require(row["document_revision"] == source_map[sid]["document_revision"] and
                 row["publication_date"] == source_map[sid]["document_date"], "revision/date mismatch")
        _require(row["procurement_family_id"] == row["correlation_cluster_id"] == family,
                 "correlated lots cannot be relabelled as independent draws")
        _require((row["currency"], row["vat_basis"], row["price_basis"]) == (currency, vat, basis),
                 "native currency/VAT/price basis must be preserved")
        _require(row["evidence_tier"] == "E1" and row["permitted_use"] == EXACT_REFERENCE_ONLY and
                 row["national_input_status"] == "Q_INSUFFICIENT_APPLICABILITY_AND_COHORT",
                 "reference evidence cannot promote national applicability")
        unknown_fields = UNKNOWN_FIELDS - {"reserve_included"} if refined else UNKNOWN_FIELDS
        _require(set(row["unknowns"]) == unknown_fields and
                 all(v is None for v in row["unknowns"].values()), "unknowns must remain null, never zero-filled")
        if refined:
            _validate_supplement(row, supplemental_sources)
        for field in ("source_locator", "technical_scope", "scope_qualification", "geography",
                      "geography_semantics", "buyer_context", "supplier_context"):
            _require(isinstance(row[field], str) and row[field].strip(), f"missing {field}")
        _require(isinstance(row["limitations"], list) and len(row["limitations"]) >= 4,
                 "explicit limitations required")
        if kind == CONNECTION:
            _require(row["source_nuts_label"] == "Csongrád-Csanád (HU333)" and
                     bool(row["geography_warning"]), "retain unresolved source-native geography")
        try:
            date.fromisoformat(row["contract_date"])
            if kind == BILL_ITEM:
                date.fromisoformat(row["amendment_date"])
            else:
                _require(row["amendment_date"] is None, "unobserved amendment")
        except (ValueError, TypeError) as exc:
            raise CostReferenceError("invalid contract/amendment date") from exc
        units = _units(kind, row["lot_or_item_id"])
        _require(set(row["facts"]) == set(units), "unadmitted or missing numeric facts")
        for name, fact in row["facts"].items():
            _require(set(fact) == {"value", "unit", "truth_status"} and
                     fact["truth_status"] == "OBS" and fact["unit"] == units[name],
                     "fact truth/unit mismatch")
            value = _number(fact["value"])
            if name in {"asset_count", "transformer_count"}:
                _require(value == value.to_integral_value(), "asset counts must be integral")
        if kind == BILL_ITEM:
            facts = row["facts"]
            with localcontext() as ctx:
                ctx.prec = 40
                _require(_number(facts["quantity"]["value"]) * _number(facts["unit_price"]["value"]) ==
                         _number(facts["line_total"]["value"]), "amended bill-item arithmetic mismatch")
        binding = bindings[row["observation_id"]]
        _require(binding.get("source_id") == sid and binding.get("record_sha256") == _digest(row),
                 "record revision/provenance digest mismatch")
        if refined:
            _require(binding.get("supplemental_source_ids") == sorted(SUPPLEMENT_SOURCES),
                     "supplement source bindings required")
        else:
            _require("supplemental_source_ids" not in binding, "other lots have no signed-contract supplement")


@dataclass(frozen=True)
class ReferenceValue:
    value: Decimal
    unit: str
    truth_status: str
    calculation: str | None
    input_facts: tuple[str, ...]
    metadata: Mapping[str, object]
    source: Mapping[str, object]


@dataclass(frozen=True)
class ReferenceCatalog:
    observations: Mapping[str, Mapping[str, object]]
    sources: Mapping[str, Mapping[str, object]]
    supplemental_sources: Mapping[str, Mapping[str, object]]

    def _record(self, observation_id, claim, price_basis):
        _require(claim == EXACT_REFERENCE_ONLY, "only exact reference use is admitted")
        _require(observation_id in self.observations, "unknown observation identity")
        row = self.observations[observation_id]
        _require(price_basis == row["price_basis"], "price-period conversion is not admitted")
        return row

    def read(self, observation_id, fact_name, *, unit, price_basis, claim=EXACT_REFERENCE_ONLY):
        """Read a literal fact; unit and native price basis must be acknowledged."""
        row = self._record(observation_id, claim, price_basis)
        _require(fact_name in row["facts"], "fact not admitted; unknowns cannot become numbers")
        fact = row["facts"][fact_name]
        _require(unit == fact["unit"], "currency/unit conversion is not admitted")
        return ReferenceValue(Decimal(fact["value"]), unit, "OBS", None, (fact_name,),
                              row, self.sources[row["source_id"]])

    def supplement(self, observation_id, *, price_basis, claim=EXACT_REFERENCE_ONLY):
        """Read reviewed contract conditions for Orgovány I only.

        Dates describe visible source dates; schedule/payment clauses describe
        conditional obligations. Neither is an observed cashflow or price base.
        """
        row = self._record(observation_id, claim, price_basis)
        _require(observation_id == ORGOVANY_I, "no contract supplement admitted for this lot")
        return row["contract_supplement"]

    def read_supplement_fact(self, observation_id, fact_name, *, unit, price_basis,
                             claim=EXACT_REFERENCE_ONLY):
        """Read a literal supplement fact with its own source and bounded role.

        Reserve is a conditional authorization amount, not a cost or forecast.
        Anyag/díj are source columns, not clean material/labour price-index bins.
        """
        supplement = self.supplement(observation_id, price_basis=price_basis, claim=claim)
        _require(fact_name in supplement["facts"], "supplement fact not admitted")
        fact = supplement["facts"][fact_name]
        _require(unit == fact["unit"], "supplement unit/currency conversion is not admitted")
        return ReferenceValue(Decimal(fact["value"]), unit, "OBS", None, (fact_name,),
                              self.observations[observation_id], self.supplemental_sources[fact["source_id"]])

    def derive(self, observation_id, calculation, *, unit, price_basis, claim=EXACT_REFERENCE_ONLY):
        """Only homogeneous supply-lot ratios or the exact amended-item product.

        A ratio is a within-lot descriptor. It cannot be transferred to a generic
        unit price, usable MW, installed package, or programme cost.
        """
        row = self._record(observation_id, claim, price_basis)
        facts = row["facts"]
        with localcontext() as ctx:
            ctx.prec = 40
            if row["observation_kind"] == SUPPLY and calculation in {
                    "SUPPLY_PER_TRANSFORMER", "SUPPLY_PER_NAMEPLATE_MVA"}:
                inputs = ("lot_amount", "asset_count")
                value = Decimal(facts["lot_amount"]["value"]) / Decimal(facts["asset_count"]["value"])
                result_unit = "EUR/transformer"
                if calculation == "SUPPLY_PER_NAMEPLATE_MVA":
                    inputs += ("nameplate_per_asset",)
                    value /= Decimal(facts["nameplate_per_asset"]["value"])
                    result_unit = "EUR/nameplate_MVA"
            elif row["observation_kind"] == BILL_ITEM and calculation == "BILL_LINE_RECONCILIATION":
                inputs = ("quantity", "unit_price")
                value = Decimal(facts["quantity"]["value"]) * Decimal(facts["unit_price"]["value"])
                result_unit = "HUF"
            else:
                raise CostReferenceError("calculation not admitted for this observation kind")
        _require(unit == result_unit, "derived unit/currency conversion is not admitted")
        return ReferenceValue(value, unit, "DER", calculation, inputs, row, self.sources[row["source_id"]])


def load_reference_catalog(data_path=DATA_PATH, manifest_path=MANIFEST_PATH):
    """Load pinned curated facts; never read or download source documents."""
    raw = Path(data_path).read_bytes()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    _require(hashlib.sha256(raw).hexdigest() == manifest.get("data_sha256"), "data revision digest mismatch")
    data = json.loads(raw)
    validate_payload(data, manifest)
    return ReferenceCatalog(
        _freeze({r["observation_id"]: r for r in data["observations"]}),
        _freeze({s["source_id"]: s for s in manifest["sources"]}),
        _freeze({s["source_id"]: s for s in manifest["supplemental_sources"]}),
    )
