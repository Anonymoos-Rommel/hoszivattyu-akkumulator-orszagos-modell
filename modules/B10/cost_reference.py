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
    records = data["observations"]
    _require(isinstance(records, list) and len(records) == len(EXPECTED_IDS) and
             {r.get("observation_id") for r in records} == EXPECTED_IDS,
             "exactly the seven bounded observation identities required")
    bindings = manifest.get("record_bindings", [])
    _require(len(bindings) == len(EXPECTED_IDS) and
             {b.get("observation_id") for b in bindings} == EXPECTED_IDS, "record bindings required")
    bindings = {b["observation_id"]: b for b in bindings}
    for row in records:
        _require(set(row) == _RECORD_FIELDS, "unexpected or missing record fields")
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
        _require(set(row["unknowns"]) == UNKNOWN_FIELDS and
                 all(v is None for v in row["unknowns"].values()), "unknowns must remain null, never zero-filled")
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
    )
