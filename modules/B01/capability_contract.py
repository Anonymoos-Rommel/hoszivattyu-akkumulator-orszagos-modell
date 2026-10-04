"""Record-scoped, dated component assessment; no installation-order inference.

This consumes qualified evidence assertions, not raw sources or household cash
flows. A PASS means the declared condition is supported by the supplied record
at the requested date. It neither grants a permission nor selects/funds work.
Rules live in household_capability_contract.json. The historical S0-S5 APIs are
deliberately not called here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CONTRACT_PATH = Path(__file__).resolve().parents[2] / "registry/household_capability_contract.json"


class CapabilityContractError(ValueError):
    """Malformed, mixed-scope or ambiguous evidence cannot be evaluated."""


def _text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CapabilityContractError(f"{field} must be nonempty text")


def _date(value: str) -> date:
    _text(value, "date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise CapabilityContractError(f"invalid ISO date: {value!r}") from exc
    if parsed.isoformat() != value:
        raise CapabilityContractError("dates must use YYYY-MM-DD")
    return parsed


@dataclass(frozen=True)
class EvidenceIdentity:
    household_id: str
    site_id: str
    basis_id: str
    truth_context: str
    evidence_scope: str

    def validate(self) -> None:
        for field in ("household_id", "site_id", "basis_id"):
            _text(getattr(self, field), field)
        if self.truth_context not in {"REAL", "SCN"}:
            raise CapabilityContractError("truth_context must be REAL or SCN")
        if self.evidence_scope != "INDIVIDUAL_RECORD":
            raise CapabilityContractError("population evidence cannot certify a household/site")


@dataclass(frozen=True)
class CompletionEvent:
    evidence_id: str
    identity: EvidenceIdentity
    component_id: str
    completed_on: str
    origin: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    scope_note: str


@dataclass(frozen=True)
class DatedAssertion:
    evidence_id: str
    identity: EvidenceIdentity
    claim_id: str
    result: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    valid_from: str
    valid_until: str
    scope_note: str
    applies_to: tuple[str, ...] = ()


@dataclass(frozen=True)
class LegacyProvenance:
    """Opaque historical input; never consumed as component/gate evidence."""

    contract_version: str
    original_record_json: str


@dataclass(frozen=True)
class CapabilitySnapshot:
    identity: EvidenceIdentity
    as_of: str
    completion_events: tuple[CompletionEvent, ...] = ()
    assertions: tuple[DatedAssertion, ...] = ()
    legacy: LegacyProvenance | None = None


@dataclass(frozen=True)
class ConditionResult:
    status: str
    evidence_status: str
    input_statuses: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    unknown: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComponentAssessment:
    component_id: str
    completion_history: ConditionResult
    currently_available: ConditionResult


@dataclass(frozen=True)
class ActionAssessment:
    action_id: str
    technical_prerequisites: ConditionResult
    programme_preconditions: ConditionResult


@dataclass(frozen=True)
class OperationAssessment:
    operation_id: str
    permission_conditions: ConditionResult
    programme_preconditions: ConditionResult


@dataclass(frozen=True)
class HouseholdCapabilityAssessment:
    contract_version: str
    identity: EvidenceIdentity
    as_of: str
    components: tuple[ComponentAssessment, ...]
    actions: tuple[ActionAssessment, ...]
    complete_triple: ConditionResult
    subsidy_exit_conditions: ConditionResult
    operations: tuple[OperationAssessment, ...]
    completion_history: tuple[CompletionEvent, ...]
    legacy: LegacyProvenance | None
    selected_or_funded: bool = False


def load_contract() -> dict:
    """Read the versioned rules; no mutable module-global rules object."""
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("schema_version") != "1.0.0":
        raise CapabilityContractError("unsupported capability contract version")
    claims = contract["claims"]
    components = contract["components"]
    if set(components) != {"HEAT_PUMP", "BATTERY", "INSULATION"}:
        raise CapabilityContractError("the complete programme requires all three named components")
    for row in components.values():
        if row["availability_claim"] not in claims:
            raise CapabilityContractError("unknown component availability claim")
    for row in contract["actions"].values():
        if row["component_id"] not in components or not row["technical_prerequisites"]:
            raise CapabilityContractError("action requires a component and technical prerequisites")
    groups = [row["technical_prerequisites"] for row in contract["actions"].values()]
    groups += [contract["programme_action_claims"], contract["triple_claims"], contract["exit_claims"]]
    groups += [row["claims"] for row in contract["operations"].values()]
    if any(not group or len(group) != len(set(group)) or set(group) - set(claims) for group in groups):
        raise CapabilityContractError("empty, repeated or unknown gate in contract")
    expected_subjects = set(contract["actions"]) | set(contract["operations"]) | {"SUBSIDY_EXIT"}
    if set(contract["programme_subjects"]) != expected_subjects or set(contract["subject_scoped_claims"]) != set(contract["programme_action_claims"]):
        raise CapabilityContractError("programme applicability must cover exact declared subjects and shared claims")
    return contract


def _evidence(item: CompletionEvent | DatedAssertion, identity: EvidenceIdentity, *, unknown: bool = False) -> None:
    _text(item.evidence_id, "evidence_id")
    _text(item.scope_note, "scope_note")
    item.identity.validate()
    if item.identity != identity:
        raise CapabilityContractError("evidence household/site/basis/context differs from snapshot")
    if not isinstance(item.evidence_refs, tuple) or any(not isinstance(ref, str) or not ref.strip() for ref in item.evidence_refs):
        raise CapabilityContractError("evidence_refs must be an immutable tuple of nonempty references")
    if len(set(item.evidence_refs)) != len(item.evidence_refs):
        raise CapabilityContractError("duplicate evidence reference")
    if unknown:
        if item.evidence_status != "Q":
            raise CapabilityContractError("UNKNOWN requires Q, without promoting an assumption")
    else:
        allowed = {"OBS", "DER"} if identity.truth_context == "REAL" else {"SCN"}
        if item.evidence_status not in allowed or not item.evidence_refs:
            raise CapabilityContractError("known conditions need matching record evidence and truth context")


def _validate(snapshot: CapabilitySnapshot, contract: dict) -> None:
    if not isinstance(snapshot, CapabilitySnapshot) or not isinstance(snapshot.identity, EvidenceIdentity):
        raise CapabilityContractError("assessment needs a typed snapshot and identity")
    snapshot.identity.validate()
    as_of = _date(snapshot.as_of)
    if not isinstance(snapshot.completion_events, tuple) or not isinstance(snapshot.assertions, tuple):
        raise CapabilityContractError("snapshot collections must be immutable tuples")
    ids: set[str] = set()
    for item in (*snapshot.completion_events, *snapshot.assertions):
        if item.evidence_id in ids:
            raise CapabilityContractError("duplicate evidence_id, including across history and assertions")
        ids.add(item.evidence_id)
    for item in snapshot.completion_events:
        _evidence(item, snapshot.identity)
        if item.component_id not in contract["components"]:
            raise CapabilityContractError("unknown completed component")
        if item.origin not in contract["components"][item.component_id]["completion_origins"]:
            raise CapabilityContractError("unsupported component completion origin")
        if _date(item.completed_on) > as_of:
            raise CapabilityContractError("future completion cannot be recorded in an earlier snapshot")
    intervals: dict[str, list[tuple[date, date, tuple[str, ...]]]] = {}
    for item in snapshot.assertions:
        if item.claim_id not in contract["claims"] or item.result not in {"PASS", "FAIL", "UNKNOWN"}:
            raise CapabilityContractError("unknown claim or non-enumerated result; no truthy coercion")
        _evidence(item, snapshot.identity, unknown=item.result == "UNKNOWN")
        if not isinstance(item.applies_to, tuple) or any(not isinstance(value, str) for value in item.applies_to):
            raise CapabilityContractError("applicability must be an immutable tuple of declared subjects")
        if len(set(item.applies_to)) != len(item.applies_to):
            raise CapabilityContractError("duplicate applicability subject")
        if item.claim_id in contract["subject_scoped_claims"]:
            if not item.applies_to or set(item.applies_to) - set(contract["programme_subjects"]):
                raise CapabilityContractError("programme evidence needs explicit action/operation/exit applicability")
        elif item.applies_to:
            raise CapabilityContractError("only shared programme claims take explicit applicability subjects")
        start, stop = _date(item.valid_from), _date(item.valid_until)
        if start >= stop or start > as_of:
            raise CapabilityContractError("assertion interval must be nonempty and start no later than snapshot")
        for previous_start, previous_stop, previous_subjects in intervals.setdefault(item.claim_id, []):
            same_subject = not item.applies_to or bool(set(item.applies_to) & set(previous_subjects))
            if same_subject and max(start, previous_start) < min(stop, previous_stop):
                raise CapabilityContractError("overlapping claim assertions require explicit resolution")
        intervals[item.claim_id].append((start, stop, item.applies_to))
    if snapshot.legacy is not None:
        if not isinstance(snapshot.legacy, LegacyProvenance):
            raise CapabilityContractError("legacy provenance must be immutable and explicit")
        _text(snapshot.legacy.contract_version, "legacy contract version")
        if not isinstance(json.loads(snapshot.legacy.original_record_json), dict):
            raise CapabilityContractError("legacy record must be a JSON object")


def _combine(results: tuple[ConditionResult, ...], context: str) -> ConditionResult:
    statuses = {item.status for item in results}
    status = "FAIL" if "FAIL" in statuses else "UNKNOWN" if "UNKNOWN" in statuses else "PASS"
    union = lambda field: tuple(sorted({value for item in results for value in getattr(item, field)}))
    return ConditionResult(status, "SCN" if context == "SCN" else "Q" if status == "UNKNOWN" else "DER",
                           union("input_statuses"), union("evidence_ids"), union("evidence_refs"),
                           union("unknown"), union("failed"))


def _unknown(claim: str, context: str) -> ConditionResult:
    return ConditionResult("UNKNOWN", "SCN" if context == "SCN" else "Q", ("Q",), (), (), (claim,))


def assess_snapshot(snapshot: CapabilitySnapshot) -> HouseholdCapabilityAssessment:
    """Compose independent physical, action, programme and permission results."""
    contract = load_contract()
    _validate(snapshot, contract)
    context = snapshot.identity.truth_context
    when = _date(snapshot.as_of)

    def claim(name: str, subject: str | None = None) -> ConditionResult:
        scoped = name in contract["subject_scoped_claims"]
        label = f"{name}@{subject}" if scoped else name
        matches = [item for item in snapshot.assertions if item.claim_id == name
                   and (not scoped or subject in item.applies_to)
                   and _date(item.valid_from) <= when < _date(item.valid_until)]
        if not matches:
            return _unknown(label, context)
        item = matches[0]
        return ConditionResult(item.result, item.evidence_status, (item.evidence_status,),
                               (item.evidence_id,), tuple(sorted(item.evidence_refs)),
                               (label,) if item.result == "UNKNOWN" else (),
                               (label,) if item.result == "FAIL" else ())

    def claims(names: list[str], subject: str | None = None) -> ConditionResult:
        return _combine(tuple(claim(name, subject) for name in names), context)

    components = []
    for name, row in contract["components"].items():
        events = tuple(item for item in snapshot.completion_events if item.component_id == name)
        if events:
            history = ConditionResult("PASS", "DER" if context == "REAL" else "SCN",
                                      tuple(sorted({item.evidence_status for item in events})),
                                      tuple(sorted(item.evidence_id for item in events)),
                                      tuple(sorted({ref for item in events for ref in item.evidence_refs})))
        else:
            history = _unknown(f"{name}_ACCEPTED_COMPLETION", context)
        available = _combine((history, claim(row["availability_claim"])), context)
        components.append(ComponentAssessment(name, history, available))
    component_map = {item.component_id: item for item in components}
    actions = []
    for name, row in contract["actions"].items():
        technical = claims(row["technical_prerequisites"])
        programme = _combine((technical, claims(contract["programme_action_claims"], name)), context)
        actions.append(ActionAssessment(name, technical, programme))
    triple = _combine(tuple(item.currently_available for item in components) + (claims(contract["triple_claims"]),), context)
    exit_conditions = _combine((triple, claims(contract["exit_claims"], "SUBSIDY_EXIT")), context)
    operations = []
    for name, row in contract["operations"].items():
        permission = _combine((component_map[row["component_id"]].currently_available, claims(row["claims"])), context)
        programme = _combine((permission, claims(contract["programme_action_claims"], name)), context)
        operations.append(OperationAssessment(name, permission, programme))
    return HouseholdCapabilityAssessment(contract["schema_version"], snapshot.identity, snapshot.as_of,
                                         tuple(components), tuple(actions), triple, exit_conditions,
                                         tuple(operations), tuple(sorted(snapshot.completion_events,
                                                                  key=lambda event: (event.completed_on, event.evidence_id))),
                                         snapshot.legacy)


def snapshot_from_payload(payload: dict) -> CapabilitySnapshot:
    """Strict structural decoding; enum/date/evidence validation happens at assessment."""
    if not isinstance(payload, dict) or set(payload) - {"identity", "as_of", "completion_events", "assertions"} or not {"identity", "as_of"} <= set(payload):
        raise CapabilityContractError("snapshot has unknown or missing fields; legacy data requires the explicit adapter")

    def collection(value):
        if not isinstance(value, (list, tuple)):
            raise CapabilityContractError("record collections must be arrays")
        return value

    def identity(value: dict) -> EvidenceIdentity:
        if not isinstance(value, dict) or set(value) != {"household_id", "site_id", "basis_id", "truth_context", "evidence_scope"}:
            raise CapabilityContractError("identity requires all five explicit fields, including evidence scope")
        return EvidenceIdentity(**value)

    def refs(value) -> tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            raise CapabilityContractError("evidence_refs must be a collection, not a string")
        return tuple(value)

    def event(value: dict) -> CompletionEvent:
        return CompletionEvent(**{**value, "identity": identity(value["identity"]), "evidence_refs": refs(value["evidence_refs"])})

    def assertion(value: dict) -> DatedAssertion:
        return DatedAssertion(**{**value, "identity": identity(value["identity"]), "evidence_refs": refs(value["evidence_refs"]), "applies_to": tuple(collection(value.get("applies_to", [])))})

    return CapabilitySnapshot(identity(payload["identity"]), payload["as_of"],
                              tuple(event(item) for item in collection(payload.get("completion_events", []))),
                              tuple(assertion(item) for item in collection(payload.get("assertions", []))))
