"""Read-only 2026-10-01 KEHOP rules/status snapshot, never funding availability.

Explicit programme, structural-rule scope and as-of are required on every read.
No household approval, cash-flow result, policy default or cost estimation is
implemented. Raw source bytes remain outside the repository.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, localcontext
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data/processed/b14/funding_reference_snapshot.json"
CAPS_PATH = ROOT / "data/processed/b14/eligible_cost_caps_417.csv"
MANIFEST_PATH = ROOT / "registry/b14_funding_reference_manifest.json"
AS_OF = "2026-10-01"
TERMS_REVISION = "2025-10-15"
PROGRAMME_417 = "KEHOP Plusz-4.1.7-24"
PROGRAMME_418 = "KEHOP Plusz-4.1.8-24"
DATED_RULE_REFERENCE = "DATED_RULE_REFERENCE"
DATED_INTAKE_STATUS = "DATED_INTAKE_STATUS"
GROSS_POLICY_UNIT_CAP = "GROSS_POLICY_UNIT_CAP"
SCOPES = MappingProxyType({
    PROGRAMME_417: "HU_EXCLUDING_BUDAPEST_FAMILY_HOUSE_RULES",
    PROGRAMME_418: "BUDAPEST_FAMILY_HOUSE_RULES",
})
CALL_SOURCES = MappingProxyType({
    PROGRAMME_417: "SRC-B06-HU-KEHOP-417-COMPLETION-2025",
    PROGRAMME_418: "SRC-B02-HU-KEHOP-418-COMPLETION-INDICATORS-2025",
})
FAQ_SOURCE = "SRC-B14-MFB-KEHOP-PROCESSING-FAQ-202609"
PROCEDURE_SOURCE = "SRC-B14-MFB-RETAIL-PROCEDURE-20251015"
EXPECTED_SOURCE_IDS = frozenset(CALL_SOURCES.values()) | {
    FAQ_SOURCE, PROCEDURE_SOURCE, "SRC-B02-HU-KEHOP-417-PROGRAMME-2026",
    "SRC-B14-MFB-KEHOP-418-STATUS-20261001",
    "SRC-B14-FAIR-KEHOP-417-DOCUMENT-LIST-20261001",
    "SRC-B14-FAIR-KEHOP-418-DOCUMENT-LIST-20261001",
    "SRC-B14-FAIR-KEHOP-417-NHH-SUSPENSION-20260414",
    "SRC-B14-FAIR-KEHOP-417-LHH-SUSPENSION-20260420",
    "SRC-B14-FAIR-KEHOP-418-SUSPENSION-20260414",
}
UNKNOWN_FIELDS = frozenset({
    "remaining_funds", "reserved_application_amount", "committed_amount", "paid_amount",
    "confirmed_project_grant", "university_pilot_funding", "national_programme_allocation",
})
_MONEY_FACTS = frozenset({
    "original_envelope", "finance_min", "finance_max", "own_source_example_at_max_finance",
    "preparation_total_cap", "opening_HET_and_plan_cap", "other_costs_total_cap",
    "closing_HET_cap", "HET_total_cap", "cash_advice_cap",
})
_MONTH_FACTS = frozenset({
    "availability_min", "availability_max", "availability_extension_max",
    "grace_after_availability", "execution_max", "execution_extension_max",
})
_DENOMINATORS = {
    "grant_share": "FINANCING_AMOUNT",
    "own_source_min_share": "ELIGIBLE_PROJECT_COST",
    "supplier_advance_max_share": "SUPPLIER_AND_TOTAL_FINANCING_LIMITS",
    "primary_energy_saving_min_share": "BASELINE_HET_ANNUAL_PRIMARY_ENERGY",
    "original_envelope_reserved_regional_share": "ORIGINAL_PROGRAMME_ENVELOPE",
}
_FACT_UNITS = {**dict.fromkeys(_MONEY_FACTS, "HUF"), **dict.fromkeys(_MONTH_FACTS, "month"),
               **dict.fromkeys(_DENOMINATORS, "ratio"), "loan_interest": "percent_per_year",
               "execution_extension_count_max": "count", "loan_maturity_max": "year"}
_CAP_FIELDS = frozenset({
    "cap_id", "programme_id", "scope", "source_id", "source_locator", "terms_revision",
    "truth_status", "currency", "vat_basis", "unit", "category", "variant", "material_cap",
    "labour_cap", "combined_cap", "combined_truth_status", "meaning",
})
_GATES = {
    "applicant": "RECORD_LEVEL_NATURAL_PERSON_CITIZENSHIP_RESIDENCE_RIGHTS_CREDIT_AND_LEGAL_CHECKS",
    "property": "RECORD_LEVEL_OCCUPIED_PRE2007_FAMILY_HOUSE_DEFINITION_AND_LOCATION",
    "technical": "RECORD_LEVEL_HET_PRIMARY_ENERGY_PRODUCTS_AND_DELIVERED_SCOPE",
    "cumulation": "RECORD_AND_COST_LINE_PRIOR_SUPPORT_HEM_CHECKS",
    "university_or_pilot": "NOT_ESTABLISHED_BY_HOUSEHOLD_CALL",
    "national_programme": "NO_ALLOCATION_ESTABLISHED",
}
_OPERATIONAL_CLAIMS = {
    "pre_suspension_application": "APPROVAL_WAITLIST_OR_REJECTION_DEPENDING_ON_RULES_AND_RESOURCES",
    "waitlist": "ELIGIBLE_BUT_NO_RESOURCE_AT_DECISION_TIME",
    "envelope_expansion_information": "DATED_UNKNOWN_NOT_ZERO_OR_REFUSAL",
    "successor_programme_information": "DATED_UNKNOWN_NOT_ABSENCE_OF_FUTURE_PROGRAMME",
    "normal_processing_deadline": "REPORTED_EXCEEDED_NOT_GUARANTEED_TIMING",
}
_PROGRAMME_FIELDS = frozenset({
    "programme_id", "scope", "as_of", "evidence_tier", "terms_revision", "currency", "finance_form",
    "call_source_id", "current_status_source_id", "document_list_source_id", "facts", "dates",
    "intake", "unknowns", "eligible_total_hard_cap", "gates", "scope_labels", "activity_labels",
    "exclusion_labels", "cumulation_labels", "cost_cap_source_status", "limitations",
    "financing_constraint_labels", "cost_constraint_labels", "scope_rule_locators",
})


class FundingReferenceError(ValueError):
    """An unadmitted scope, revision, meaning or availability claim was requested."""


def _require(ok, message):
    if not ok:
        raise FundingReferenceError(message)


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _number(value):
    _require(isinstance(value, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value),
             "numeric facts require finite nonnegative decimal strings")
    return Decimal(value)


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def validate_snapshot(data, caps, manifest):
    """Check reviewed identities, semantics, unknowns and content bindings.

    File digests are additionally checked by load_funding_reference. Neither
    hashes nor these invariants replace source interpretation and review.
    """
    _require(set(data) == {"schema_version", "slice_id", "status", "as_of", "programmes",
                           "operational_observations", "unresolved"}, "unexpected snapshot fields")
    _require(type(data["schema_version"]) is int and data["schema_version"] == 1,
             "unsupported snapshot schema")
    _require(data["status"] == manifest.get("status") == "BOUNDED_DATED_RULE_REFERENCE" and
             data["slice_id"] == "B14-L01" and data["as_of"] == manifest.get("as_of") == AS_OF,
             "dated reference-only admission required")
    _require(type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1,
             "unsupported manifest schema")
    _require(manifest.get("data_path") == str(DATA_PATH.relative_to(ROOT)) and
             manifest.get("caps_path") == str(CAPS_PATH.relative_to(ROOT)), "data identity mismatch")
    sources = manifest.get("sources", [])
    _require(len(sources) == len(EXPECTED_SOURCE_IDS) and
             {s.get("source_id") for s in sources} == EXPECTED_SOURCE_IDS,
             "exact primary-source set required")
    for source in sources:
        _require(source.get("source_tier") == "P1" and source.get("reuse_status") == "EXTERNAL_ONLY"
                 and source.get("repo_snapshot_path") is None, "source rights/tier boundary violated")
        _require(source.get("evidence_family") == "MFB_KEHOP_HOUSEHOLD_PROGRAMME",
                 "mirrors and documents are not independent samples")
        _require(re.fullmatch(r"[0-9a-f]{64}", source.get("sha256", "")), "source digest required")
        _require(source.get("original_url", "").startswith(("https://www.palyazat.gov.hu/",
                 "https://ginapp-api.fair.gov.hu/", "https://www.mfb.hu/",
                 "https://mfb.hu/", "https://cms.mfb.hu/")), "official origin required")
        _require(source.get("retrieved_at", "").startswith(AS_OF + "T") and
                 bool(source.get("document_date_or_revision")), "retrieval/revision required")
        if source["source_id"] in CALL_SOURCES.values():
            _require(source.get("mirror_byte_identity") is True and
                     bool(source.get("existing_mirror_url")), "preserve identical mirror lineage")
    programmes = data["programmes"]
    _require(len(programmes) == 2 and {p.get("programme_id") for p in programmes} == set(SCOPES),
             "exact programme pair required")
    bindings = manifest.get("programme_bindings", [])
    _require(len(bindings) == 2 and {b.get("programme_id") for b in bindings} == set(SCOPES),
             "programme bindings required")
    bindings = {b["programme_id"]: b["sha256"] for b in bindings}
    for row in programmes:
        _require(set(row) == _PROGRAMME_FIELDS, "unexpected programme fields")
        pid = row["programme_id"]
        _require(row["scope"] == SCOPES[pid] and row["as_of"] == AS_OF and
                 row["terms_revision"] == TERMS_REVISION and row["currency"] == "HUF" and
                 row["call_source_id"] == CALL_SOURCES[pid], "scope/date/currency/source mismatch")
        _require(row["evidence_tier"] == "E1_REFERENCE_ONLY" and row["finance_form"] ==
                 "COMBINED_GRANT_AND_INTEREST_FREE_LOAN", "funding result or instrument drift")
        units = dict(_FACT_UNITS)
        if pid == PROGRAMME_418:
            units.pop("original_envelope_reserved_regional_share")
        _require(set(row["facts"]) == set(units), "unadmitted numeric field")
        for name, unit in units.items():
            fact = row["facts"][name]
            fields = {"value", "unit", "truth_status", "source_id", "locator"}
            if name in _DENOMINATORS:
                fields.add("denominator")
            _require(set(fact) == fields and fact["unit"] == unit and fact["truth_status"] == "POL"
                     and fact["source_id"] == CALL_SOURCES[pid] and bool(fact["locator"]),
                     "rule fact provenance/unit mismatch")
            value = _number(fact["value"])
            _require(value > 0 or name == "loan_interest", "positive rule value required")
            if name in _DENOMINATORS:
                _require(fact["denominator"] == _DENOMINATORS[name] and value <= 1,
                         "ratio denominator or range changed")
            if unit in {"month", "year", "count", "HUF"}:
                _require(value == value.to_integral_value(), "integral source unit required")
        _require(_number(row["facts"]["loan_interest"]["value"]) == 0, "interest-free reference required")
        unknowns = row["unknowns"]
        _require(set(unknowns) == UNKNOWN_FIELDS and all(
            set(v) == {"value", "unit", "truth_status", "reason"} and v["value"] is None and
            v["unit"] == "HUF" and v["truth_status"] == "Q" and bool(v["reason"])
            for v in unknowns.values()), "unknown funding must stay null, never zero or envelope")
        cap = row["eligible_total_hard_cap"]
        _require(cap["value"] is None and cap["truth_status"] == "Q" and cap["reason"] ==
                 "FINANCE_CEILING_IS_NOT_ELIGIBLE_TOTAL_COST_CAP", "finance is not total-cost ceiling")
        _require(row["gates"] == _GATES, "record-specific gates cannot become household approvals")
        _require("LOAN_MATURITY_INCLUDES_AVAILABILITY_AND_GRACE" in row["financing_constraint_labels"]
                 and "EXECUTION_EXTENSION_ONCE_JUSTIFIED_NOT_AUTOMATIC" in row["financing_constraint_labels"]
                 and "AVAILABILITY_EXTENSION_JUSTIFIED_NOT_AUTOMATIC" in row["financing_constraint_labels"]
                 and "CAPS_ARE_NOT_ADDITIVE_ENTITLEMENTS" in row["cost_constraint_labels"]
                 and "MAX_ONE_HEM_GENERATION_AGREEMENT" in row["cumulation_labels"],
                 "finance, nested-cap and HEM qualifications required")
        dates = row["dates"]
        _require(set(dates) == {"nominal_submission_start", "nominal_submission_end",
                              "last_programme_payment_date"}, "unexpected date fields")
        for fact in dates.values():
            _require(set(fact) == {"value", "precision", "truth_status", "source_id", "locator"}
                     and fact["precision"] == "day" and fact["truth_status"] == "POL" and
                     re.fullmatch(r"\d{4}-\d{2}-\d{2}", fact["value"]), "date-grain rules required")
        intake = row["intake"]
        _require(intake["status"] == "SUSPENDED_FOR_ENVELOPE_EXHAUSTION" and
                 intake["truth_status"] == "OBS" and intake["checked_at"] == AS_OF,
                 "new intake cannot be marked open")
        expected_days = {"2026-04-17", "2026-04-23"} if pid == PROGRAMME_417 else {"2026-04-17"}
        _require(len(intake["windows"]) == len(expected_days) and
                 {w["last_submission_day"] for w in intake["windows"]} == expected_days,
                 "closing-date window mismatch")
        for window in intake["windows"]:
            _require(set(window) == {"regions", "announcement_date", "last_submission_day", "precision",
                     "cutoff", "source_id", "locator", "truth_status"} and
                     window["precision"] == "day" and window["cutoff"] ==
                     "BRANCH_CLOSING_TIME_NOT_OBSERVED_AS_CLOCK_TIME", "no invented cutoff time")
        _require(row["cost_cap_source_status"] == ("MATERIALIZED_39_RULE_ROWS" if pid == PROGRAMME_417
                 else "NOT_MATERIALIZED_DO_NOT_TRANSFER_417_TABLE"), "cap geography drift")
        _require(bindings[pid] == _digest(row), "programme content binding mismatch")
    operational = data["operational_observations"]
    _require(operational["source_id"] == FAQ_SOURCE and operational["document_revision"] == "2026-09"
             and operational["date_precision"] == "month" and
             operational["filename_date_not_effective_day"] is True,
             "FAQ must remain month-dated, not exact-day or present guarantee")
    _require(operational["claims"] == _OPERATIONAL_CLAIMS, "dated unknowns must not become positive or negative guarantees")
    _require(manifest.get("operational_observations_sha256") == _digest(operational),
             "operational-status binding mismatch")
    expected_caps = {f"KEHOP417-CAP-{i:02}" for i in range(1, 40)}
    _require(len(caps) == 39 and {r.get("cap_id") for r in caps} == expected_caps,
             "39 unique reviewed cap rows required")
    cap_bindings = manifest.get("cap_bindings", [])
    _require(len(cap_bindings) == 39 and {x.get("cap_id") for x in cap_bindings} == expected_caps,
             "39 cap bindings required")
    cap_bindings = {x["cap_id"]: x["sha256"] for x in cap_bindings}
    for row in caps:
        _require(set(row) == _CAP_FIELDS and row["programme_id"] == PROGRAMME_417 and
                 row["scope"] == SCOPES[PROGRAMME_417] and row["source_id"] == CALL_SOURCES[PROGRAMME_417]
                 and row["terms_revision"] == TERMS_REVISION, "cap scope/source/revision mismatch")
        _require(row["currency"] == "HUF" and row["vat_basis"] == "GROSS" and
                 row["unit"] in {"HUF/m2", "HUF/set"} and row["truth_status"] == "POL" and
                 row["combined_truth_status"] == "DER" and row["meaning"] ==
                 "MAX_ELIGIBLE_UNIT_COST_NOT_MARKET_PRICE", "policy cap cannot become price")
        with localcontext() as context:
            context.prec = 40
            material, labour, combined = (_number(row[k]) for k in ("material_cap", "labour_cap", "combined_cap"))
            _require(material > 0 and labour > 0 and material + labour == combined,
                     "separate cap components and exact sum required")
        _require(all(row[k] for k in ("source_locator", "category", "variant")), "cap labels/locator required")
        _require(cap_bindings[row["cap_id"]] == _digest(row), "cap content binding mismatch")


@dataclass(frozen=True)
class RuleFact:
    value: Decimal
    unit: str
    truth_status: str
    metadata: Mapping[str, object]
    source: Mapping[str, object]


@dataclass(frozen=True)
class FundingReference:
    programmes: Mapping[str, Mapping[str, object]]
    caps: Mapping[str, Mapping[str, object]]
    sources: Mapping[str, Mapping[str, object]]
    operational_observations: Mapping[str, object]

    def _programme(self, programme_id, scope, as_of):
        _require(programme_id in self.programmes, "programme not admitted")
        _require(as_of == AS_OF, "only exact 2026-10-01 snapshot; current/future extrapolation refused")
        _require(scope == SCOPES[programme_id], "explicit source structural-rule scope required")
        return self.programmes[programme_id]

    def read_programme(self, programme_id, *, scope, as_of, claim):
        _require(claim == DATED_RULE_REFERENCE, "only dated rule reference, never award/availability")
        return self._programme(programme_id, scope, as_of)

    def read_fact(self, programme_id, fact_name, *, scope, as_of, unit, claim):
        row = self.read_programme(programme_id, scope=scope, as_of=as_of, claim=claim)
        _require(fact_name in row["facts"], "unknown amount or unsupported fact cannot become numeric")
        fact = row["facts"][fact_name]
        _require(unit == fact["unit"], "no currency, unit, tax or ratio-denominator conversion")
        return RuleFact(_number(fact["value"]), unit, fact["truth_status"], fact,
                        self.sources[fact["source_id"]])

    def read_intake(self, programme_id, *, scope, as_of, claim):
        _require(claim == DATED_INTAKE_STATUS, "only dated intake status, never guaranteed resources")
        return self._programme(programme_id, scope, as_of)["intake"]

    def read_cap(self, cap_id, *, programme_id, scope, as_of, unit, vat_basis, claim):
        _require(claim == GROSS_POLICY_UNIT_CAP, "cap-as-price, expected CAPEX and financing claims refused")
        self._programme(programme_id, scope, as_of)
        _require(programme_id == PROGRAMME_417 and cap_id in self.caps,
                 "only reviewed 4.1.7 cap rows; Budapest transfer not admitted")
        row = self.caps[cap_id]
        _require(unit == row["unit"] and vat_basis == "GROSS", "source unit and gross VAT basis required")
        return row


def load_funding_reference(data_path=DATA_PATH, caps_path=CAPS_PATH, manifest_path=MANIFEST_PATH):
    """Load only the exact manifest-pinned fact snapshot; performs no network I/O."""
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        for path, key in ((data_path, "data_sha256"), (caps_path, "caps_sha256")):
            _require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == manifest.get(key),
                     f"file revision mismatch: {key}")
        data = json.loads(Path(data_path).read_text(encoding="utf-8"))
        with Path(caps_path).open(encoding="utf-8", newline="") as stream:
            caps = list(csv.DictReader(stream))
        validate_snapshot(data, caps, manifest)
    except FundingReferenceError:
        raise
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise FundingReferenceError(f"invalid reference input: {exc}") from exc
    return FundingReference(_freeze({p["programme_id"]: p for p in data["programmes"]}),
                            _freeze({c["cap_id"]: c for c in caps}),
                            _freeze({s["source_id"]: s for s in manifest["sources"]}),
                            _freeze(data["operational_observations"]))
