"""Read-only dated KEHOP rules/status snapshots, never funding availability.

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
COMPLETION_AS_OF = "2026-10-03"
COMPLETION_PATH = ROOT / "data/processed/b14/rule_completion_20261003.json"
CAPS_418_PATH = ROOT / "data/processed/b14/eligible_cost_caps_418.csv"
COMPLETION_MANIFEST_PATH = ROOT / "registry/b14_rule_completion_manifest.json"
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
    completed_programmes: Mapping[str, Mapping[str, object]]
    completed_caps: Mapping[str, Mapping[str, object]]

    def _programme(self, programme_id, scope, as_of):
        _require(programme_id in self.programmes, "programme not admitted")
        _require(as_of in (AS_OF, COMPLETION_AS_OF),
                 "only exact reviewed dates; current/future extrapolation refused")
        _require(scope == SCOPES[programme_id], "explicit source structural-rule scope required")
        return (self.programmes if as_of == AS_OF else self.completed_programmes)[programme_id]

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
        caps = self.caps if as_of == AS_OF else self.completed_caps
        _require(cap_id in caps and caps[cap_id]["programme_id"] == programme_id and
                 caps[cap_id]["scope"] == scope,
                 "exact reviewed programme cap required; no geographic or date transfer")
        row = caps[cap_id]
        _require(unit == row["unit"] and vat_basis == "GROSS", "source unit and gross VAT basis required")
        return row


def load_funding_reference(data_path=DATA_PATH, caps_path=CAPS_PATH, manifest_path=MANIFEST_PATH,
                           completion_path=COMPLETION_PATH, caps_418_path=CAPS_418_PATH,
                           completion_manifest_path=COMPLETION_MANIFEST_PATH):
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
        completed, completed_caps = _load_rule_completion(
            data, caps, manifest, completion_path, caps_418_path, completion_manifest_path,
            historical_paths=(data_path, caps_path, manifest_path))
    except FundingReferenceError:
        raise
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise FundingReferenceError(f"invalid reference input: {exc}") from exc
    return FundingReference(_freeze({p["programme_id"]: p for p in data["programmes"]}),
                            _freeze({c["cap_id"]: c for c in caps}),
                            _freeze({s["source_id"]: s for s in manifest["sources"]}),
                            _freeze(data["operational_observations"]),
                            _freeze(completed), _freeze(completed_caps))


def validate_rule_completion(data, caps, manifest, historical_data, historical_manifest):
    """Validate the independently sourced extension without rewriting old evidence.

    The programme references remain informational. These invariants deliberately
    do not implement eligibility, a legal decision engine or grant accounting.
    """
    _require(set(data) == {"schema_version", "status", "as_of", "historical_as_of",
                          "terms_revision", "claim_scope", "programme_rules_truth_status",
                          "not_a_household_eligibility_decision",
                          "programmes", "currentness"}, "unexpected completion fields")
    _require(type(data["schema_version"]) is int and data["schema_version"] == 1 and
             type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1,
             "unsupported completion schema")
    _require(data["status"] == manifest.get("status") == "BOUNDED_DATED_RULE_COMPLETION_REFERENCE"
             and data["as_of"] == manifest.get("as_of") == COMPLETION_AS_OF
             and data["historical_as_of"] == manifest.get("historical_as_of") == AS_OF
             and data["terms_revision"] == TERMS_REVISION, "separate exact dated references required")
    _require(data["claim_scope"] == "EXACT_NAMED_PROGRAMME_RULE_REFERENCE_ONLY" and
             data["not_a_household_eligibility_decision"] is True and
             data["programme_rules_truth_status"] == "POL" and
             manifest.get("source_original_publication") == "EXTERNAL_ONLY" and
             manifest.get("source_family") == "MFB_KEHOP_HOUSEHOLD_PROGRAMME" and
             manifest.get("full_old_eleven_source_reverification") is False and
             manifest.get("confers_registry_acceptance") is False,
             "source references cannot imply eligibility, new full source pass or acceptance")
    _require(manifest.get("data_path") == str(COMPLETION_PATH.relative_to(ROOT)) and
             manifest.get("caps_path") == str(CAPS_418_PATH.relative_to(ROOT)),
             "completion file identity mismatch")
    rows = data["programmes"]
    _require(len(rows) == 2 and {x["programme_id"] for x in rows} == set(SCOPES),
             "exact named programme pair required")
    bindings = manifest.get("programme_bindings", [])
    _require(len(bindings) == 2 and {x["programme_id"] for x in bindings} == set(SCOPES),
             "programme rule bindings required")
    bindings = {x["programme_id"]: x["sha256"] for x in bindings}
    for row in rows:
        pid = row["programme_id"]
        _require(row["scope"] == SCOPES[pid] and row["source_id"] == CALL_SOURCES[pid],
                 "rule geography/source mismatch")
        _require(row["issuer"]["name"] == "MFB Zrt." and
                 row["issuer"]["role"] == "CALL_DOCUMENT_ISSUER_AND_PROGRAMME_FINANCING_INSTITUTION"
                 and row["issuer"]["locator"] and row["issuer"]["evidence_basis"],
                 "source-stated issuer role required")
        _require(row["geography"]["country"] == "HU" and
                 row["geography"]["included"] == ("BUDAPEST" if pid == PROGRAMME_418 else
                                                   "HUNGARY_EXCLUDING_BUDAPEST") and
                 row["geography"]["basis"] == "PROJECT_IMPLEMENTATION_LOCATION",
                 "geographic rule cannot become population eligibility")
        for fact in [row["geography"]["max_implementation_locations_per_application"],
                     row["cumulation"]["in_current_programme"]["max_supported_applications"],
                     row["cumulation"]["cross_scheme"]["max_supported_applications"],
                     row["HEM"]["max_generation_agreements_in_programme"]]:
            _require(fact == {"value": "1", "unit": "count", "truth_status": "POL"},
                     "source-native one-count limit required")
        current = row["cumulation"]["in_current_programme"]
        cross = row["cumulation"]["cross_scheme"]
        _require(current["person_role"] == "BORROWER_FINAL_BENEFICIARY" and
                 current["application_state"] == "SUPPORTED_NOT_MERELY_SUBMITTED" and
                 cross["matching_scope_operator"] ==
                 "SAME_INDEPENDENT_BUILDING_UNIT_OR_SAME_FINAL_BENEFICIARY_OR_BOTH" and
                 cross["no_requirement_that_both_scopes_match"] is True,
                 "supported application and borrower/building OR scope must remain")
        schemes = cross["scheme_set"]
        _require(len(schemes) == 4 and {x["identifier"] for x in schemes} ==
                 {pid, "RRF-REP-10.13.1-24", "RRF-6.2.1", None} and
                 next(x for x in schemes if x["identifier"] is None).get("class") ==
                 "ALL_EU_FUNDED_ENERGY_PURPOSE_PROGRAMMES_ANNOUNCED_FOR_ENTERPRISES_FOR_2021_2027_PROGRAMMING_PERIOD",
                 "exact named cross-scheme scope required")
        pv = cross["pv_only_exception"]
        _require(pv["qualifying_investment_scope"] == "EXCLUSIVELY_PV_SYSTEM_INSTALLATION" and
                 pv["limited_effect"] == "EXCEPTION_TO_THIS_CROSS_SCHEME_SUPPORTED_APPLICATION_LIMIT_ONLY"
                 and pv["machine_decision_use"] ==
                 "REFERENCE_ONLY_REQUIRES_EXACT_PRIOR_AWARD_SCOPE_NO_AUTOMATIC_APPROVAL" and
                 pv["unlisted_scheme_extension"] == "NOT_INFERRED" and
                 set(pv["does_not_waive"]) == {"same-cost EU double funding prohibition",
                 "own-programme one-borrower limit", "property/applicant/technical rules",
                 "30percent primary-energy test excluding electricity-generation savings",
                 "current intake suspension"}, "PV exception cannot become broad eligibility or double funding")
        same = row["same_cost_funding"]
        _require(same["other_EU_funded_grant_prohibited"] is True and
                 same["other_EU_funded_repayable_aid_prohibited"] is True and
                 same["legal_title_does_not_remove_prohibition"] is True and
                 same["cost_scope"] == "COST_ITEMS_ACCOUNTED_FOR_AGAINST_THE_PROGRAMME_FINANCING",
                 "same-cost grant and repayable-aid prohibition required")
        hem = row["HEM"]
        _require(hem["mandatory_to_use_HEM"] is False and
                 hem["cash_plus_HEM_for_same_advice_or_subactivity_allowed"] is False and
                 hem["written_agreement_required_for_HEM_transfer_or_intention"] is True and
                 hem["adviser_extra_fee_in_HEM_agreement_allowed"] is False and
                 hem["advance_fee_also_prohibited"] is True and
                 hem["proportional_market_value_service_required"] is True and
                 hem["HEM_transfer_recipient_class"] == "EKR_OBLIGATED_PARTY" and
                 hem["no_HEM_cash_fee_ceiling"] == dict(value="140000", unit="HUF",
                                                        vat_basis="GROSS", truth_status="POL"),
                 "HEM optionality, fee, consideration and recipient restrictions required")
        invoice = row["invoice_endorsement"]
        _require(invoice["source_id"] == PROCEDURE_SOURCE and
                 invoice["evidence_state"] == "PRIOR_VERIFIED_V1_018_REVIEW_NOT_FRESHLY_REREAD" and
                 invoice["fresh_bytes_recovered"] is False and
                 invoice["old_reported_checks_not_repeated_here"] is True,
                 "historical source review must not become a fresh byte check")
        _require(row["cost_rule"]["finance_ceiling_is_total_eligible_cost_ceiling"] is False and
                 row["cost_rule"]["unit_cap_basis"] == "GROSS_SEPARATE_MATERIAL_AND_LABOUR_LIMITS"
                 and row["cost_rule"]["above_unit_cap"] == "EXTRA_NON_ELIGIBLE_OWN_FUNDS"
                 and row["eligible_activity_rules"]["PV_and_storage_as_eligible_activities"] ==
                 "NOT_LISTED_IN_V3_DO_NOT_INFER_ELIGIBILITY_FROM_PV_EXCEPTION",
                 "cost and activity scope must remain source-specific")
        _require(bindings[pid] == _digest(row), "completed rule content binding mismatch")
    expected_caps = {f"KEHOP418-CAP-{i:02}" for i in range(1, 40)}
    cap_bindings = manifest.get("cap_bindings", [])
    _require(len(caps) == len(cap_bindings) == 39 and
             {x["cap_id"] for x in caps} == {x["cap_id"] for x in cap_bindings} == expected_caps,
             "39 own-source Budapest caps required")
    cap_bindings = {x["cap_id"]: x["sha256"] for x in cap_bindings}
    for row in caps:
        _require(set(row) == _CAP_FIELDS and row["programme_id"] == PROGRAMME_418 and
                 row["scope"] == SCOPES[PROGRAMME_418] and row["source_id"] == CALL_SOURCES[PROGRAMME_418]
                 and row["terms_revision"] == TERMS_REVISION and row["currency"] == "HUF"
                 and row["vat_basis"] == "GROSS" and row["unit"] in {"HUF/m2", "HUF/set"}
                 and row["truth_status"] == "POL" and row["combined_truth_status"] == "DER"
                 and row["meaning"] == "MAX_ELIGIBLE_UNIT_COST_NOT_MARKET_PRICE"
                 and all(row[k] for k in ("source_locator", "category", "variant")),
                 "Budapest cap source, unit, meaning and locator required")
        with localcontext() as context:
            context.prec = 40
            material, labour, combined = (_number(row[k]) for k in
                                          ("material_cap", "labour_cap", "combined_cap"))
            _require(material > 0 and labour > 0 and material + labour == combined,
                     "source component cap sum mismatch")
        _require(cap_bindings[row["cap_id"]] == _digest(row), "Budapest cap binding mismatch")
    fresh = data["currentness"]
    _require(fresh["as_of"] == COMPLETION_AS_OF and fresh["historical_as_of_unchanged"] == AS_OF
             and manifest["currentness_sha256"] == _digest(fresh), "currentness binding/date mismatch")
    observations = fresh["observations"]
    expected = {f"SRC-B14-{provider}-KEHOP-{pid}-{kind}-20261003"
                for pid in ("417", "418") for provider, kind in
                (("MFB", "STATUS"), ("FAIR", "DOCUMENT-LIST"))}
    _require(len(observations) == 4 and {x["source_id"] for x in observations} == expected,
             "four distinct fresh observation identities required")
    sources = {x["source_id"]: x for x in historical_manifest["sources"]}
    obs = {x["source_id"]: x for x in observations}
    for observation in observations:
        _require(observation["retrieved_at"].startswith(COMPLETION_AS_OF + "T") and
                 observation["truth_status"] == "OBS" and observation["source_tier"] == "P1"
                 and observation["reuse_status"] == "EXTERNAL_ONLY" and
                 observation["repo_snapshot_path"] is None and
                 type(observation["bytes"]) is int and observation["bytes"] > 0 and
                 re.fullmatch(r"[0-9a-f]{64}", observation["sha256"]),
                 "fresh source timestamp/hash/rights required")
    for pid, number in ((PROGRAMME_417, "417"), (PROGRAMME_418, "418")):
        index = obs[f"SRC-B14-FAIR-KEHOP-{number}-DOCUMENT-LIST-20261003"]
        status = obs[f"SRC-B14-MFB-KEHOP-{number}-STATUS-20261003"]
        source = sources[CALL_SOURCES[pid]]
        _require(index["original_url"] == sources[index["lineage_historical_source_id"]]["original_url"]
                 and status["original_url"] == sources[status["lineage_historical_source_id"]]["original_url"],
                 "official source lineage required")
        selected = index["selected_call"]
        _require(selected["source_id"] == CALL_SOURCES[pid] and
                 selected["official_download_url"] == source["original_url"] and
                 selected["_id"] == source["original_url"].rsplit("/", 1)[-1] and
                 selected["size"] == source["bytes"] and "20251015" in selected["title"],
                 "new selected call cannot silently inherit old facts")
        procedure = index["selected_common_procedure"]
        _require(procedure["byte_recovery_this_pass"] == "NOT_RECOVERED" and
                 procedure["scope_of_index_proof"] == "CURRENT_SELECTION_ID_TITLE_SIZE_NOT_NEW_EXACT_BYTE_CHECK"
                 and "20251015" in procedure["title"] and
                 procedure["size"] == sources[PROCEDURE_SOURCE]["bytes"],
                 "procedure index is not a new PDF identity proof")
        expected_days = {"2026-04-17", "2026-04-23"} if pid == PROGRAMME_417 else {"2026-04-17"}
        _require(status["claims"]["intake"] == "SUSPENDED_FOR_ENVELOPE_EXHAUSTION" and
                 set(status["claims"]["dates"]) == expected_days and
                 status["claims"]["FAQ_link_present"] is True and
                 status["claims"]["current_processing_FAQ_url"] == sources[FAQ_SOURCE]["original_url"],
                 "dated new suspension/FAQ observation required")
    _require(set(fresh["claims_allowed"]) == {"EXACT_SELECTED_RULE_REFERENCE", "DATED_INTAKE_STATUS"}
             and set(fresh["claims_excluded"]) == {"HOUSEHOLD_APPROVAL", "CURRENT_AVAILABLE_BALANCE",
                 "PROJECT_AWARD", "FUTURE_OR_LIVE_STATUS_EXTRAPOLATION"},
             "dated observations cannot admit funding or eligibility")
    reliance = fresh["prior_review_reliance"]
    prior_ids = {PROCEDURE_SOURCE} | {sid for sid in sources if "SUSPENSION" in sid}
    _require(len(reliance) == 4 and {x["source_id"] for x in reliance} == prior_ids,
             "explicit prior-review source set required")
    for item in reliance:
        old = sources[item["source_id"]]
        _require(item["sha256"] == old["sha256"] and item["bytes"] == old["bytes"] and
                 item["original_url"] == old["original_url"] and
                 item["historical_retrieved_at"] == old["retrieved_at"] and
                 item["fresh_recovery"] is False and item["fresh_full_eleven_source_pass"] is False,
                 "prior review reliance cannot be relabelled fresh evidence")
    recovered = fresh["fresh_exact_call_recovery"] + [fresh["fresh_processing_FAQ_recovery"]]
    _require(len(recovered) == 3 and {x["source_id"] for x in recovered} ==
             set(CALL_SOURCES.values()) | {FAQ_SOURCE}, "exact recovered call/FAQ set required")
    for item in recovered:
        old = sources[item["source_id"]]
        _require(item["sha256"] == old["sha256"] and item["bytes"] == old["bytes"] and
                 item["original_url"] == old["original_url"] and
                 item["exact_historical_byte_identity"] is True and
                 item["historical_retrieved_at"] == old["retrieved_at"] and
                 item["retrieved_at"].startswith(COMPLETION_AS_OF + "T"),
                 "source recovery must retain exact old identity and separate new retrieval")


def _load_rule_completion(historical, old_caps, old_manifest, data_path, caps_path, manifest_path,
                          *, historical_paths):
    import copy
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    for path, key in ((data_path, "data_sha256"), (caps_path, "caps_sha256")):
        _require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == manifest.get(key),
                 f"completion file revision mismatch: {key}")
    pins = manifest.get("historical_input_sha256", {})
    _require(set(pins) == {str(p.relative_to(ROOT)) for p in (DATA_PATH, CAPS_PATH, MANIFEST_PATH)},
             "exact historical input identity set required")
    # Bind the bytes actually consumed, including supported caller overrides.
    # Checking ROOT here would let a re-bound alternative historical dataset
    # inherit the authority of an unchanged default completion manifest.
    names = (str(p.relative_to(ROOT)) for p in (DATA_PATH, CAPS_PATH, MANIFEST_PATH))
    for name, actual_path in zip(names, historical_paths):
        _require(hashlib.sha256(Path(actual_path).read_bytes()).hexdigest() == pins[name],
                 "consumed historical dated evidence changed")
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    with Path(caps_path).open(encoding="utf-8", newline="") as stream:
        caps = list(csv.DictReader(stream))
    validate_rule_completion(data, caps, manifest, historical, old_manifest)
    details = {x["programme_id"]: x for x in data["programmes"]}
    observations = {x["source_id"]: x for x in data["currentness"]["observations"]}
    completed = {}
    for old in historical["programmes"]:
        row = copy.deepcopy(old)
        pid = row["programme_id"]
        number = "417" if pid == PROGRAMME_417 else "418"
        status_id = f"SRC-B14-MFB-KEHOP-{number}-STATUS-20261003"
        index_id = f"SRC-B14-FAIR-KEHOP-{number}-DOCUMENT-LIST-20261003"
        row.update(as_of=COMPLETION_AS_OF, current_status_source_id=status_id,
                   document_list_source_id=index_id, rule_details=details[pid],
                   rule_details_truth_status=data["programme_rules_truth_status"],
                   cost_cap_source_status="MATERIALIZED_39_OWN_PROGRAMME_RULE_ROWS",
                   historical_reference_as_of=AS_OF,
                   currentness_observations={k: observations[k] for k in (status_id, index_id)},
                   prior_review_reliance=data["currentness"]["prior_review_reliance"],
                   processing_FAQ_recovery=data["currentness"]["fresh_processing_FAQ_recovery"])
        row["intake"].update(checked_at=COMPLETION_AS_OF, source_id=status_id,
                            locator=observations[status_id]["source_locator"],
                            historical_window_notices="PRIOR_REVIEWED_NOTICE_BYTES_NOT_FRESHLY_RECOVERED")
        completed[pid] = row
    return completed, {x["cap_id"]: x for x in old_caps + caps}
