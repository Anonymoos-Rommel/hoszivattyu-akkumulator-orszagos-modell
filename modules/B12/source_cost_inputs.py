"""Pinned offer -> qualified, quantity/event-scoped native Cost inputs.

Offer observations are available independently of target admission. No quantity,
architecture, cash date, VAT split, annual frequency or full CAPEX is defaulted.
The use-review contract implements the existing E1/E2 policy, not owner approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_EVEN
import hashlib
import json
from pathlib import Path

from .input_accounting_contract import (
    B12ContractError, Cost, MissingInput, MoneyBasis, Period, Reference, Scalar,
    _shape, _require, _text,
)

E2_CRITERIA = (
    "defined_quantity", "unit_grain_boundary_period", "direct_support",
    "target_applicability", "no_stronger_contradiction", "reproducible_derivation",
    "registered_validation_debt", "provisional_label",
)
_COST_FIELDS = (
    "cost_id", "event_id", "product", "leg", "component_id", "asset_generation_id",
    "phase_ref", "category", "scope_ref", "payer", "payee", "settlement_ref",
    "inclusion_scope", "attribution_ref", "price_basis_ref", "applicability_ref",
    "scope_event_id",
)


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("utf-8")).hexdigest()


def offer_evidence_revision(offer):
    """Exact active offer, metadata and evidence-pin revision, not an ID alias.

    Per-offer scope avoids revoking a review for an unrelated catalogue addition.
    The normalization pin includes any separately justified qualification proof.
    """
    return _digest(offer)


def normalization_input_revision(offer):
    return _digest({key: offer.get(key) for key in (
        "offer_id", "source_id", "product", "unit", "fact_pin", "qualifier_pin",
        "scope_pin", "period_pin", "package_pin",
    )})


def normalize_price_kind(value):
    return {"OBSERVED_PRICE_OR_FEE": "EXACT_PRICE", "DISTANCE_RATE": "UNIT_RATE",
            "CURRENT_OBSERVATION": "EXACT_PRICE"}.get(value, value)


def _raw_price_kind(fact, qualifier):
    if qualifier.get("price_kind"):
        return qualifier["price_kind"]
    if fact.get("price_kind"):
        return fact["price_kind"]
    # A current-price field identifies the observed point; tax/applicability and
    # all explicit starting-price labels remain separate and cannot be erased.
    return "CURRENT_OBSERVATION" if "current_price" in fact else "Q"


def _validate_normalization(root, offer, fact, qualifier):
    classification = _pin(root, offer["normalization_pin"])
    _require(classification["input_revision"] == normalization_input_revision(offer),
             "normalization evidence revision changed")
    normalized = {k: offer[k] for k in ("tax_basis", "price_kind", "reference_period", "inclusions")}
    _require(classification["normalized"] == normalized, "normalized offer classification changed")
    # The period is read from active source/retrieval metadata, not a free label.
    day = _pin(root, offer["period_pin"])
    _require(type(day) is str, "source observation date evidence required")
    day = date.fromisoformat(day[:10]).isoformat()
    _require(offer["reference_period"] == [day, day], "source reference period changed")
    if offer.get("package_pin"):
        package = _pin(root, offer["package_pin"])
        contents = package.get("inclusion_scope", package.get("inclusions", package.get("includes_roles")))
        _require(contents == offer["inclusions"], "package inclusion evidence changed")
    fact_tax = fact.get("tax_basis", fact.get("tax"))
    qualifier_tax = qualifier.get("tax_basis", qualifier.get("tax"))
    raw_tax = qualifier_tax if qualifier_tax is not None else fact_tax
    raw_tax = raw_tax if raw_tax is not None else "Q"
    raw_kind = _raw_price_kind(fact, qualifier)
    _require(offer["original_price_kind"] == raw_kind, "raw price-kind evidence changed")
    differences = {}
    if offer["tax_basis"] != raw_tax or (fact_tax is not None and fact_tax != offer["tax_basis"]):
        differences["tax_basis"] = offer["tax_basis"]
    fact_kind = fact.get("price_kind")
    # A qualifier may conservatively retain/add a non-point restriction, but
    # cannot turn a restricted raw fact into a payable point/rate by itself.
    # Use the existing scoped qualification proof for that contradiction.
    raw_limit_erased = (
        fact_kind is not None
        and normalize_price_kind(fact_kind) not in {"EXACT_PRICE", "UNIT_RATE"}
        and offer["price_kind"] in {"EXACT_PRICE", "UNIT_RATE"}
    )
    if offer["price_kind"] != normalize_price_kind(raw_kind) or raw_limit_erased:
        differences["price_kind"] = offer["price_kind"]
    justification_pin = classification.get("qualification_pin")
    if not differences:
        _require(justification_pin is None, "unused qualification evidence is ambiguous")
        return
    _require(justification_pin is not None, "tax/price-kind normalization contradicts pinned observation")
    qualification = _pin(root, justification_pin)
    _require(qualification["input_revision"] == normalization_input_revision(offer) and
             qualification["claims"] == differences, "qualification does not bind active evidence/claims")
    _text(qualification["reason"], "scoped qualification reason")
    supports = qualification["evidence_pins"]
    _require(bool(supports), "independent qualification evidence required")
    supported = set()
    for evidence_pin in supports:
        evidence = _pin(root, evidence_pin)
        _require(evidence.get("product") == offer["product"], "qualification product mismatch")
        _text(evidence.get("source_id"), "qualification source identity")
        _text(evidence.get("original_url"), "qualification source URL")
        supported.update(k for k, v in differences.items() if evidence.get(k) == v)
    _require(supported == set(differences), "qualification claim lacks pinned supporting content")


def _json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise B12ContractError(f"invalid source/review artifact: {path}") from exc


def _file(root, relative):
    _text(relative, "relative evidence path")
    path = (root / relative).resolve()
    _require(path.is_relative_to(root.resolve()), "evidence path outside pinned package")
    return path


def _pin(root, pin):
    """Resolve content as well as identifier; a source-ID string is insufficient."""
    path = _file(root, pin["path"])
    _require(path.is_file() and _hash(path) == pin["sha256"], "evidence bytes changed")
    value = _json(path)
    for key in pin.get("pointer", ()):
        try:
            value = value[int(key)] if isinstance(value, list) else value[key]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise B12ContractError("evidence pointer does not resolve") from exc
    _require(value == pin["expected"], "evidence pointer content mismatch")
    return value


@dataclass(frozen=True)
class SourceCatalogue:
    root: Path
    manifest_path: str
    manifest_sha256: str


def load_source_catalogue(root, manifest_path, *, expected_sha256):
    catalogue = SourceCatalogue(Path(root).resolve(), manifest_path, expected_sha256)
    try:
        _read(catalogue)
    except B12ContractError:
        raise
    except (OSError, KeyError, IndexError, TypeError, ValueError, AttributeError) as exc:
        raise B12ContractError(f"malformed source catalogue: {exc}") from exc
    return catalogue


def _read(catalogue):
    _require(type(catalogue) is SourceCatalogue, "verified source catalogue required")
    path = _file(catalogue.root, catalogue.manifest_path)
    _require(path.is_file() and _hash(path) == catalogue.manifest_sha256,
             "source catalogue revision mismatch")
    data = _json(path)
    _require(data.get("schema_version") == 2, "source cost catalogue schema")
    offers = {}
    for offer in data["offers"]:
        _text(offer["offer_id"], "offer ID")
        _require(offer["offer_id"] not in offers, "duplicate offer ID")
        fact = _pin(catalogue.root, offer["fact_pin"])
        _require(type(fact) is dict, "source fact must be an object")
        _require(fact.get(offer["amount_field"]) == offer["value"], "offer amount changed")
        qualifier = fact
        if offer.get("qualifier_pin"):
            qualifier = _pin(catalogue.root, offer["qualifier_pin"])
            _require(qualifier["value"] == offer["value"], "fact/qualifier amount changed")
        _validate_normalization(catalogue.root, offer, fact, qualifier)
        if fact.get("product"):
            _require(fact["product"] == offer["product"], "source product cannot be renamed")
        if fact.get("model"):
            _require(fact["model"] == offer["product"], "source model cannot be renamed")
        source_identity = fact.get("source_id", fact.get("id"))
        if source_identity:
            _require(source_identity == offer["source_id"], "source identity changed")
        if fact.get("unit"):
            unit = fact["unit"] if "/" in fact["unit"] else f"{fact.get('currency')}/{fact['unit']}"
            _require(unit == offer["unit"], "source unit changed")
        if offer.get("scope_field"):
            _require(fact[offer["scope_field"]] == offer["use_scope"], "source use scope changed")
        scope = _pin(catalogue.root, offer["scope_pin"])
        _require(type(scope) is dict, "source functional scope must be an object")
        if scope.get("category"):
            _require(scope["category"] == offer["category"], "pinned device/install/O&M category changed")
        if scope.get("component_id"):
            _require(scope["component_id"] in offer["function_ids"], "pinned functional component mismatch")
        if scope.get("function_ids"):
            _require(scope["function_ids"] == offer["function_ids"], "pinned function scope mismatch")
        offers[offer["offer_id"]] = offer
    uses = _pin(catalogue.root, data["use_reviews_pin"])
    _require(type(uses) is list, "use reviews must be a list")
    _require(len({r["review_id"] for r in uses}) == len(uses), "duplicate use review ID")
    return offers, {r["review_id"]: r for r in uses}


def _number(value):
    _require(type(value) in {str, int}, "decimal string/integer required, never float/bool")
    try:
        value = Decimal(value)
    except InvalidOperation as exc:
        raise B12ContractError("invalid monetary number") from exc
    _require(value.is_finite() and value >= 0, "finite nonnegative amount required")
    return value


def _period(value):
    _require(type(value) is list and len(value) == 2, "explicit reference/cash period required")
    try:
        return Period(*(date.fromisoformat(x) for x in value))
    except (TypeError, ValueError) as exc:
        raise B12ContractError("invalid exact dates") from exc


def _scalar(data):
    return Scalar(
        None if data["value"] is None else _number(data["value"]), data["unit"], data["truth"],
        _period(data["reference_period"]), data["basis_id"], tuple(data["source_ids"]),
        data["scenario_ref"], data["evidence_tier"], data["admission_ref"],
        data["reason"], data["acquisition_ref"],
    )


def _unknown(unit, basis, period, reason):
    return Scalar(None, unit, "Q", period, basis, (), None, None, None, reason, "B12-D01")


def _reference(value):
    return Reference("EXTERNAL_ADMISSION", value, None, None)


@dataclass(frozen=True)
class OfferObservation:
    offer_id: str
    product: str
    category: str
    price: Scalar
    tax_basis: str
    price_kind: str
    use_scope: str


@dataclass(frozen=True)
class CostResolution:
    observations: tuple[OfferObservation, ...]
    costs: tuple[Cost, ...]
    missing: tuple[MissingInput, ...]
    # Deliberately partial: never infer total installed CAPEX from source coverage.
    full_capex: None = None


def case_cost_context(case):
    return dict(case_id=case.case_id, intervention_id=case.intervention_id,
                archetype_id=case.archetype_id, region_id=case.region_id,
                transition_ref=case.transition_ref, scope_id=case.scope.scope_id,
                household_id=case.scope.household_id, service_basis_ref=case.service_basis_ref)


def resolve_cost_inputs(catalogue, bindings, monetary_basis, *, case_context=None):
    """Read pinned evidence afresh and resolve exact reviewed bindings into Cost.

    Q is returned for missing evidence. Malformed/contradictory claims raise the
    native B12ContractError. Qualified-use reviews bind every target/cash field;
    callers cannot relabel071->072 or attach a reviewed price to a different use.
    """
    try:
        return _resolve(catalogue, bindings, monetary_basis, case_context)
    except B12ContractError:
        raise
    except (OSError, KeyError, IndexError, TypeError, ValueError, AttributeError, InvalidOperation) as exc:
        raise B12ContractError(f"malformed source cost inputs: {exc}") from exc


def _resolve(catalogue, bindings, basis, context):
    if basis is not None:
        _shape(basis, MoneyBasis)
        _require(basis.nominal_real == "NOMINAL", "cost inputs require nominal money")
    offers, uses = _read(catalogue)
    _require(type(bindings) is tuple, "immutable binding tuple required")
    observations = []
    for offer in offers.values():
        period = _period(offer["reference_period"])
        price = (_unknown(offer["unit"], offer["basis_id"], period, "source price not acquired")
                 if offer["value"] is None else
                 Scalar(_number(offer["value"]), offer["unit"], "OBS", period,
                        offer["basis_id"], (offer["source_id"],), None, "E2",
                        f"PRICE_OBSERVATION:{offer['offer_id']}:{offer['fact_pin']['sha256']}", None, None))
        observations.append(OfferObservation(offer["offer_id"], offer["product"], offer["category"],
                                             price, offer["tax_basis"], offer["price_kind"], offer["use_scope"]))
    missing, costs = [], []
    row_ids, events, inclusions, family_events = set(), set(), set(), set()
    for n, binding in enumerate(bindings):
        prefix = f"cost_bindings[{n}]"
        def gap(field, reason):
            missing.append(MissingInput(f"{prefix}.{field}", reason, "B12-D01"))
        offer_id = binding["offer_id"]
        _require(offer_id in offers, "unknown source offer")
        offer = offers[offer_id]
        row_id = binding["cost_id"]
        _text(row_id, "cost ID")
        _require(row_id not in row_ids, "duplicate cost binding")
        row_ids.add(row_id)
        if binding.get("product") is not None:
            _require(binding["product"] == offer["product"], "exact product mismatch")
        if binding.get("category") is not None:
            _require(binding["category"] == offer["category"], "device/install/O&M category mismatch")
        quantity = _scalar(binding["quantity"])
        _require(quantity.unit == offer["quantity_unit"], "quantity/price denominator mismatch")
        _require(quantity.value is None or quantity.value > 0, "positive cost quantity required")
        if quantity.value is None:
            gap("quantity", "target quantity remains Q; offer denominator is not quantity1")
        if offer["value"] is None:
            gap("price", "no exact source price")
        if offer["tax_basis"] not in {"GROSS", "GROSS_WITH_PUBLISHED_ROUNDED_NET"}:
            gap("tax_basis", "full payable gross not established; no VAT inference")
        if offer["price_kind"] not in {"EXACT_PRICE", "UNIT_RATE"}:
            gap("price_kind", "starting/minimum/indicative/policy cap is not an exact payable price")
        if offer["use_scope"] not in {"EXACT_PRODUCT_PART_PRICE", "CONDITIONAL_COMPONENT_PRICE",
                                      "GENERIC_MAINTENANCE_VISIT", "TRAVEL_RULE_ONLY"}:
            gap("applicability", "comparison/background observation not admitted to target")
        if offer.get("package_pin") is None:
            gap("inclusions", "priced package/function content evidence remains Q")
        for field in _COST_FIELDS:
            if not binding.get(field):
                gap(field, "explicit source/quantity/scope/cash binding missing")
        if binding.get("cash_period") is None:
            gap("cash_period", "price retrieval day does not supply a settlement date")
        if binding.get("category") == "O_AND_M" and binding.get("service_period") is None:
            gap("service_period", "visit/hour/km fee does not establish an annual service interval")
        elif binding.get("service_period") is not None:
            _period(binding["service_period"])
        review = uses.get(binding.get("review_id"))
        if review is None or review.get("status") != "QUALIFIED":
            gap("review_id", "target use evidence review remains unresolved")
        elif basis is None:
            gap("monetary_basis", "target monetary basis remains unselected")
        elif context is None:
            gap("case_context", "target archetype/region/intervention/service context remains Q")
        else:
            _require(review["offer_evidence_revision"] == offer_evidence_revision(offer),
                     "reviewed offer evidence revision changed")
            _require(review["binding"] == binding, "reviewed target binding changed")
            _require(review["case_context"] == context, "reviewed target case context changed")
            _require(set(context) == {"case_id", "intervention_id", "archetype_id", "region_id",
                                    "transition_ref", "scope_id", "household_id", "service_basis_ref"},
                     "complete target case context required")
            for value in context.values():
                _text(value, "target case context")
            _require(binding["scope_ref"] == context["scope_id"] and binding["payer"] == context["household_id"]
                     and binding["phase_ref"] == context["transition_ref"], "target payer/scope/phase changed")
            _require(review["offer_id"] == offer_id and review["source_id"] == offer["source_id"],
                     "use review source mismatch")
            _require(review["monetary_basis"] == {
                "basis_id": basis.basis_id, "currency": basis.currency,
                "nominal_real": basis.nominal_real, "price_date": basis.price_date.isoformat()},
                "unbridged price-date/currency/basis change")
            _require(review["evidence_tier"] in {"E1", "E2"}, "E3 cannot admit observed target costs")
            _require(review["service_scope"] == "SPACE_HEATING_ONLY", "target service scope changed")
            _require(review["function_ids"] == offer["function_ids"], "function/scope mismatch")
            _require(review["price_use"] == "EXPLICIT_FROZEN_SOURCE_SNAPSHOT_NOT_REAL_INVOICE",
                     "offer snapshot cannot become observed paid invoice")
            _require(not review["known_stronger_contradiction"], "contradictory target evidence")
            for criterion in E2_CRITERIA:
                _text(review["criteria"][criterion], f"use review:{criterion}")
            _require(bool(review["validation_debt"]) or review["evidence_tier"] == "E1",
                     "E2 validation debt required")
            for pin in review["evidence_pins"]:
                _pin(catalogue.root, pin)
            _require(bool(review["evidence_pins"]), "resolved review evidence required")
            _require(_pin(catalogue.root, review["binding_evidence_pin"]) == binding,
                     "target quantity/cash/scope evidence does not bind this row")
            _require(set(binding["inclusion_scope"]) == set(offer["inclusions"]),
                     "package inclusions cannot be discarded")
        if any(m.path.startswith(prefix + ".") for m in missing):
            continue
        _require(binding["leg"] in {"baseline", "programme"}, "cost leg")
        cash = _period(binding["cash_period"])
        event_key = (binding["leg"], binding["event_id"])
        _require(event_key not in events, "duplicate economic event")
        events.add(event_key)
        family_key = (binding["leg"], offer["family_id"], offer["fact_pin"]["sha256"],
                      tuple(offer["fact_pin"].get("pointer", ())), binding["asset_generation_id"],
                      binding["scope_event_id"])
        _require(family_key not in family_events, "same source-family service/purchase counted twice")
        family_events.add(family_key)
        for component in binding["inclusion_scope"]:
            # One evidenced purchase/service cannot be counted twice by moving cash dates.
            key = (binding["leg"], binding["asset_generation_id"], binding["category"],
                   binding["scope_event_id"], component)
            _require(key not in inclusions, "bundle/component overlap across cash dates")
            inclusions.add(key)
        with localcontext() as ctx:
            ctx.prec = 50
            ctx.rounding = ROUND_HALF_EVEN
            value = _number(offer["value"]) * quantity.value
        evidence_tier = review["evidence_tier"]
        source_ids = tuple(dict.fromkeys((offer["source_id"],) + quantity.source_ids))
        truth = "DER" if quantity.truth in {"OBS", "DER"} else "SCN"
        gross = Scalar(value, basis.currency, truth, _period(offer["reference_period"]),
                       basis.basis_id, source_ids, None if truth == "DER" else quantity.scenario_ref,
                       evidence_tier, review["review_id"], None, None)
        _require(offer["unit"] == f"{basis.currency}/{quantity.unit}", "no implicit FX/unit conversion")
        q = lambda name: _unknown(basis.currency, basis.basis_id, gross.reference_period, name + " not established")
        cost = Cost(*(binding[name] for name in ("cost_id", "event_id", "leg", "component_id",
                    "asset_generation_id", "phase_ref", "category")), quantity, gross, q("net"), q("vat"),
                    "GROSS_ONLY", Reference("Q", None, "tax treatment not established", "B12-D01"),
                    q("eligible subset"), Reference("Q", None, "eligibility not established", "B12-D01"), (),
                    cash, binding["scope_ref"], binding["payer"], binding["payee"], binding["settlement_ref"],
                    tuple(binding["inclusion_scope"]), "PROCUREMENT", _reference(binding["attribution_ref"]))
        _shape(cost, Cost)
        costs.append(cost)
    return CostResolution(tuple(observations), tuple(costs), tuple(missing))
