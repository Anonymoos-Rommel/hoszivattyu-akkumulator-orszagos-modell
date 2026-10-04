from __future__ import annotations

import json
import unittest
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path

from modules.B01 import engine
from modules.B01.capability_contract import (
    CapabilityContractError, CapabilitySnapshot, CompletionEvent, DatedAssertion,
    EvidenceIdentity, load_contract, snapshot_from_payload,
)


ROOT = Path(__file__).resolve().parents[1]
IDENTITY = EvidenceIdentity("HH-TEST", "SITE-TEST", "PACKAGE-AND-BASELINE-v1", "REAL", "INDIVIDUAL_RECORD")
DATE = "2028-01-15"
RULES = load_contract()


def event(component, *, identity=IDENTITY, status="OBS", date="2028-01-10", origin=None):
    origin = origin or ("EXISTING_SCOPE_QUALIFIED" if component == "INSULATION" else "COMMISSIONED_ACCEPTED")
    return CompletionEvent("EVENT-" + component, identity, component, date, origin, status,
                           ("RECORD-ACCEPTANCE-" + component,), "Qualified named component scope at this household/site.")


def assertion(claim, result="PASS", *, identity=IDENTITY, status=None, start="2028-01-10", stop="2028-02-01", suffix="", applies_to=None):
    status = status or ("Q" if result == "UNKNOWN" else "OBS")
    return DatedAssertion("ASSERT-" + claim + suffix, identity, claim, result, status,
                          () if result == "UNKNOWN" else ("RECORD-" + claim,), start, stop,
                          "Claim-specific qualified evidence for the declared package, service, baseline and period.",
                          tuple(RULES["programme_subjects"]) if applies_to is None and claim in RULES["subject_scoped_claims"] else tuple(applies_to or ()))


def snapshot(components=(), claims=(), *, identity=IDENTITY):
    return CapabilitySnapshot(identity, DATE, tuple(event(name, identity=identity) for name in components),
                              tuple(assertion(name, identity=identity) for name in claims))


def assess(record):
    return engine.assess_household_capabilities(record)


def component(result, name):
    return next(item for item in result.components if item.component_id == name)


def action(result, name):
    return next(item for item in result.actions if item.action_id == name)


def operation_permissions(result):
    return {item.operation_id: item.permission_conditions for item in result.operations}


def complete_snapshot():
    return snapshot(tuple(RULES["components"]), tuple(RULES["claims"]))


class B01CapabilityContractTests(unittest.TestCase):
    def test_battery_first_without_hp_envelope_or_pv(self):
        result = assess(snapshot(("BATTERY",), ("BATTERY_AVAILABLE",)))
        self.assertEqual("PASS", component(result, "BATTERY").currently_available.status)
        self.assertEqual("UNKNOWN", component(result, "HEAT_PUMP").currently_available.status)
        self.assertEqual("UNKNOWN", result.complete_triple.status)
        self.assertEqual("UNKNOWN", result.subsidy_exit_conditions.status)
        self.assertTrue(all(value.status == "UNKNOWN" for value in operation_permissions(result).values()))
        self.assertFalse(result.selected_or_funded)

    def test_hp_readiness_requires_own_prerequisites_without_prior_envelope(self):
        names = RULES["actions"]["COMMISSION_HEAT_PUMP"]["technical_prerequisites"]
        result = assess(snapshot(claims=names))
        hp = action(result, "COMMISSION_HEAT_PUMP")
        self.assertEqual("PASS", hp.technical_prerequisites.status)
        self.assertEqual("UNKNOWN", hp.programme_preconditions.status)
        self.assertEqual("UNKNOWN", component(result, "HEAT_PUMP").completion_history.status)

    def test_hp_actual_unmet_design_blocks_only_relevant_action(self):
        record = complete_snapshot()
        record = replace(record, assertions=tuple(replace(item, result="FAIL") if item.claim_id == "HP_DESIGN_MATCH" else item for item in record.assertions))
        result = assess(record)
        self.assertEqual("FAIL", action(result, "COMMISSION_HEAT_PUMP").technical_prerequisites.status)
        self.assertEqual("PASS", action(result, "COMMISSION_BATTERY").technical_prerequisites.status)

    def test_observed_hp_before_insulation_is_preserved(self):
        result = assess(snapshot(("HEAT_PUMP",), ("HP_AVAILABLE",)))
        self.assertEqual("PASS", component(result, "HEAT_PUMP").currently_available.status)
        self.assertEqual("UNKNOWN", result.complete_triple.status)

    def test_existing_qualified_envelope_needs_no_new_window_replacement(self):
        result = assess(snapshot(("INSULATION",), ("INSULATION_ADEQUATE",)))
        self.assertEqual("PASS", component(result, "INSULATION").currently_available.status)
        self.assertEqual("EXISTING_SCOPE_QUALIFIED", result.completion_history[0].origin)
        self.assertEqual("UNKNOWN", component(result, "BATTERY").completion_history.status)

    def test_unqualified_not_required_is_not_envelope_completion(self):
        record = snapshot(("INSULATION",))
        for origin in ("NOT_REQUIRED", "DEMAND_REDUCED", "S1", "EXISTING_SCOPE_QUALIFIED_GENERIC"):
            with self.subTest(origin=origin), self.assertRaises(CapabilityContractError):
                assess(replace(record, completion_events=(replace(record.completion_events[0], origin=origin),)))

    def test_input_order_does_not_change_output(self):
        record = complete_snapshot()
        self.assertEqual(assess(record), assess(replace(record, completion_events=tuple(reversed(record.completion_events)), assertions=tuple(reversed(record.assertions)))))

    def test_readiness_does_not_mark_completion_or_mutate_input(self):
        record = snapshot(claims=tuple(RULES["claims"]))
        before = asdict(record)
        result = assess(record)
        self.assertEqual("PASS", action(result, "COMMISSION_BATTERY").programme_preconditions.status)
        self.assertEqual("UNKNOWN", component(result, "BATTERY").completion_history.status)
        self.assertFalse(result.selected_or_funded)
        self.assertEqual(before, asdict(record))

    def test_installed_physical_fact_survives_unknown_and_failed_finance(self):
        for finance in ("UNKNOWN", "FAIL"):
            record = snapshot(("BATTERY",), ("BATTERY_AVAILABLE",))
            record = replace(record, assertions=record.assertions + (assertion("HOUSEHOLD_CASHFLOW_PROTECTED", finance),))
            result = assess(record)
            self.assertEqual("PASS", component(result, "BATTERY").currently_available.status)
            self.assertNotEqual("PASS", result.subsidy_exit_conditions.status)

    def test_each_missing_component_prevents_triple_even_if_every_other_claim_passes(self):
        for missing in RULES["components"]:
            with self.subTest(missing=missing):
                record = complete_snapshot()
                record = replace(record, completion_events=tuple(item for item in record.completion_events if item.component_id != missing))
                self.assertEqual("UNKNOWN", assess(record).complete_triple.status)

    def test_complete_triple_does_not_imply_exit_or_rights(self):
        result = assess(snapshot(tuple(RULES["components"]), ("HP_AVAILABLE", "BATTERY_AVAILABLE", "INSULATION_ADEQUATE", "PROGRAMME_TECHNICAL_QA")))
        self.assertEqual("PASS", result.complete_triple.status)
        self.assertEqual("UNKNOWN", result.subsidy_exit_conditions.status)
        self.assertTrue(all(value.status == "UNKNOWN" for value in operation_permissions(result).values()))

    def test_every_exit_gate_is_independent_and_cannot_be_offset(self):
        for gate in RULES["exit_claims"]:
            for state in ("UNKNOWN", "FAIL"):
                with self.subTest(gate=gate, state=state):
                    record = complete_snapshot()
                    record = replace(record, assertions=tuple(assertion(gate, state) if item.claim_id == gate else item for item in record.assertions))
                    result = assess(record)
                    self.assertEqual("PASS", result.complete_triple.status)
                    self.assertEqual(state, result.subsidy_exit_conditions.status)

    def test_joint_qa_required_even_with_three_components(self):
        record = complete_snapshot()
        record = replace(record, assertions=tuple(item for item in record.assertions if item.claim_id != "PROGRAMME_TECHNICAL_QA"))
        self.assertEqual("UNKNOWN", assess(record).complete_triple.status)

    def test_all_qualified_conditions_pass_without_creating_selection_or_funding(self):
        result = assess(complete_snapshot())
        self.assertEqual("PASS", result.subsidy_exit_conditions.status)
        self.assertEqual("DER", result.subsidy_exit_conditions.evidence_status)
        self.assertFalse(result.selected_or_funded)

    def test_nonexport_state_service_does_not_imply_export(self):
        record = snapshot(("BATTERY",), ("BATTERY_AVAILABLE", "STATE_SERVICE_PERMISSION", "STATE_CONTROL_READY"))
        results = operation_permissions(assess(record))
        self.assertEqual("PASS", results["STATE_SERVICE"].status)
        self.assertEqual("UNKNOWN", results["GRID_EXPORT"].status)
        self.assertEqual("UNKNOWN", results["GRID_CHARGE"].status)

    def test_charge_discharge_export_permissions_are_separate(self):
        for claim, operation in (("GRID_CHARGE_PERMISSION", "GRID_CHARGE"), ("HOUSEHOLD_DISCHARGE_PERMISSION", "HOUSEHOLD_DISCHARGE"), ("GRID_EXPORT_PERMISSION", "GRID_EXPORT")):
            result = operation_permissions(assess(snapshot(("BATTERY",), ("BATTERY_AVAILABLE", claim))))
            self.assertEqual("PASS", result[operation].status)
            self.assertEqual(1, sum(value.status == "PASS" for value in result.values()))

    def test_expired_right_is_unknown_and_does_not_erase_completion(self):
        record = snapshot(("BATTERY",), ("BATTERY_AVAILABLE",))
        expired = assertion("GRID_EXPORT_PERMISSION", stop=DATE)
        result = assess(replace(record, assertions=record.assertions + (expired,)))
        self.assertEqual("UNKNOWN", operation_permissions(result)["GRID_EXPORT"].status)
        self.assertEqual("PASS", component(result, "BATTERY").completion_history.status)

    def test_withdrawal_preserves_history_but_disables_current_operation(self):
        old = assertion("BATTERY_AVAILABLE", stop=DATE)
        withdrawn = assertion("BATTERY_AVAILABLE", "FAIL", start=DATE, suffix="-WITHDRAWN")
        record = snapshot(("BATTERY",))
        result = assess(replace(record, assertions=(old, withdrawn, assertion("GRID_EXPORT_PERMISSION"))))
        self.assertEqual("PASS", component(result, "BATTERY").completion_history.status)
        self.assertEqual("FAIL", component(result, "BATTERY").currently_available.status)
        self.assertEqual("FAIL", operation_permissions(result)["GRID_EXPORT"].status)
        self.assertEqual(1, len(result.completion_history))

    def test_duplicate_ids_and_overlapping_assertions_rejected(self):
        item = assertion("BATTERY_AVAILABLE")
        for assertions in ((item, item), (item, replace(item, evidence_id="OTHER")), (item, replace(item, evidence_id="OTHER", result="FAIL"))):
            with self.assertRaises(CapabilityContractError):
                assess(replace(snapshot(), assertions=assertions))

    def test_completion_id_cannot_alias_assertion_id(self):
        record = snapshot(("BATTERY",), ("BATTERY_AVAILABLE",))
        with self.assertRaises(CapabilityContractError):
            assess(replace(record, assertions=(replace(record.assertions[0], evidence_id=record.completion_events[0].evidence_id),)))

    def test_later_conditions_cannot_establish_earlier_readiness(self):
        item = assertion("HP_DESIGN_MATCH", start="2028-01-16")
        with self.assertRaises(CapabilityContractError):
            assess(replace(snapshot(), assertions=(item,)))

    def test_future_completion_is_rejected(self):
        with self.assertRaises(CapabilityContractError):
            assess(replace(snapshot(), completion_events=(event("BATTERY", date="2028-01-16"),)))

    def test_invalid_or_empty_date_intervals_are_rejected(self):
        for start, stop in ((DATE, DATE), ("2028-02-30", "2028-03-01"), ("20280110", "2028-02-01")):
            with self.subTest(start=start), self.assertRaises(CapabilityContractError):
                assess(replace(snapshot(), assertions=(assertion("BATTERY_AVAILABLE", start=start, stop=stop),)))

    def test_wrong_household_site_basis_or_context_cannot_be_combined(self):
        for field, value in (("household_id", "OTHER"), ("site_id", "OTHER"), ("basis_id", "OTHER"), ("truth_context", "SCN")):
            with self.subTest(field=field), self.assertRaises(CapabilityContractError):
                assess(replace(snapshot(), assertions=(assertion("BATTERY_AVAILABLE", identity=replace(IDENTITY, **{field: value})),)))

    def test_population_scope_is_not_an_individual_gate(self):
        with self.assertRaises(CapabilityContractError):
            assess(snapshot(identity=replace(IDENTITY, evidence_scope="POPULATION_ESTIMATE")))

    def test_malformed_truthy_result_never_passes(self):
        for value in (True, False, "true", "false", 1, 0, None):
            with self.subTest(value=value), self.assertRaises(CapabilityContractError):
                assess(replace(snapshot(), assertions=(replace(assertion("BATTERY_AVAILABLE"), result=value),)))

    def test_missing_refs_and_assumption_policy_labels_cannot_certify_real_condition(self):
        for status in ("SCN", "ASS", "POL", "Q"):
            with self.subTest(status=status), self.assertRaises(CapabilityContractError):
                assess(replace(snapshot(), assertions=(assertion("BATTERY_AVAILABLE", status=status),)))
        with self.assertRaises(CapabilityContractError):
            assess(replace(snapshot(), completion_events=(replace(event("BATTERY"), evidence_refs=()),)))

    def test_der_input_lineage_is_not_relabelled_as_observed(self):
        record = snapshot(("BATTERY",), ("BATTERY_AVAILABLE",))
        record = replace(record, completion_events=(replace(record.completion_events[0], evidence_status="DER"),), assertions=(replace(record.assertions[0], evidence_status="DER"),))
        result = component(assess(record), "BATTERY")
        self.assertEqual("DER", result.currently_available.evidence_status)
        self.assertEqual(("DER",), result.currently_available.input_statuses)

    def test_scn_fixture_stays_scn_and_runs_through_engine(self):
        result = engine.run_capability_fixture(ROOT / "data/fixtures/b01_capability_scn.json")
        battery = component(result, "BATTERY")
        self.assertEqual("PASS", battery.currently_available.status)
        self.assertEqual("SCN", battery.currently_available.evidence_status)
        self.assertEqual("SCN", result.subsidy_exit_conditions.evidence_status)
        self.assertEqual("UNKNOWN", result.subsidy_exit_conditions.status)

    def test_scn_cannot_accept_real_evidence(self):
        identity = replace(IDENTITY, truth_context="SCN")
        with self.assertRaises(CapabilityContractError):
            assess(snapshot(("BATTERY",), identity=identity))

    def test_snapshots_and_nested_inputs_are_immutable(self):
        record = complete_snapshot()
        with self.assertRaises(FrozenInstanceError):
            record.as_of = "2029-01-01"
        with self.assertRaises(FrozenInstanceError):
            record.completion_events[0].origin = "OTHER"
        with self.assertRaises(CapabilityContractError):
            assess(replace(record, assertions=list(record.assertions)))

    def test_payload_does_not_split_reference_string_into_characters(self):
        payload = asdict(snapshot(("BATTERY",)))
        payload.pop("legacy")
        payload["completion_events"][0]["evidence_refs"] = "NOT-A-LIST"
        with self.assertRaises(CapabilityContractError):
            snapshot_from_payload(payload)

    def test_legacy_s1_s4_s5_adapter_never_infers_new_claims(self):
        payload = json.loads((ROOT / "data/fixtures/b01_state_stock_scn.json").read_text())
        records = [engine._record_from_payload(row) for row in payload["households"]]
        observed = set()
        for record in records:
            if record.current_state in {"S1", "S4", "S5"}:
                observed.add(record.current_state)
                migrated = engine.migrate_legacy_capability_record(record, site_id="SITE-LEGACY", basis_id="LEGACY-HISTORY-v1")
                result = assess(migrated)
                self.assertTrue(all(item.completion_history.status == "UNKNOWN" for item in result.components))
                self.assertEqual("UNKNOWN", result.complete_triple.status)
                self.assertEqual("UNKNOWN", result.subsidy_exit_conditions.status)
                self.assertEqual(json.loads(json.dumps(asdict(record))), json.loads(result.legacy.original_record_json))
        self.assertEqual({"S1", "S4", "S5"}, observed)

    def test_legacy_adapter_rejects_malformed_truthy_completion(self):
        payload = json.loads((ROOT / "data/fixtures/b01_state_stock_scn.json").read_text())
        record = next(engine._record_from_payload(row) for row in payload["households"] if row.get("transition_evidence"))
        record = replace(record, transition_evidence=(replace(record.transition_evidence[0], completed="false"),))
        with self.assertRaises(CapabilityContractError):
            engine.migrate_legacy_capability_record(record, site_id="SITE", basis_id="BASIS")

    def test_legacy_component_evidence_still_needs_matching_identity(self):
        payload = json.loads((ROOT / "data/fixtures/b01_state_stock_scn.json").read_text())
        record = engine._record_from_payload(payload["households"][0])
        with self.assertRaises(CapabilityContractError):
            engine.migrate_legacy_capability_record(record, site_id="SITE", basis_id="BASIS", completion_events=(event("BATTERY"),))

    def test_contract_has_no_numeric_policy_defaults_or_new_task_acceptance(self):
        self.assertEqual({}, RULES["policy_numeric_defaults"])
        self.assertEqual([], RULES["accepted_original_tasks"])
        self.assertEqual({"HEAT_PUMP", "BATTERY", "INSULATION"}, set(RULES["components"]))
        self.assertTrue(any("annual" in value for value in RULES["deferred"]))

    def test_payload_rejects_unknown_scope_and_legacy_instead_of_discarding_them(self):
        for key, value in (("evidence_scope", "POPULATION_ESTIMATE"), ("legacy", {"reported_state": "S5"}), ("invented_gate", True)):
            payload = asdict(complete_snapshot())
            payload.pop("legacy")
            payload[key] = value
            with self.subTest(key=key), self.assertRaises(CapabilityContractError):
                snapshot_from_payload(payload)

    def test_payload_requires_explicit_identity_scope(self):
        payload = asdict(snapshot())
        payload.pop("legacy")
        payload["identity"].pop("evidence_scope")
        with self.assertRaises(CapabilityContractError):
            snapshot_from_payload(payload)

    def test_payload_rejects_malformed_record_collections(self):
        for key in ("completion_events", "assertions"):
            for value in ("", "[]", {}, None, False):
                payload = asdict(snapshot())
                payload.pop("legacy")
                payload[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(CapabilityContractError):
                    snapshot_from_payload(payload)

    def test_hp_only_programme_evidence_cannot_qualify_battery_envelope_or_exit(self):
        record = complete_snapshot()
        record = replace(record, assertions=tuple(replace(item, applies_to=("COMMISSION_HEAT_PUMP",)) if item.claim_id in RULES["subject_scoped_claims"] else item for item in record.assertions))
        result = assess(record)
        self.assertEqual("PASS", action(result, "COMMISSION_HEAT_PUMP").programme_preconditions.status)
        self.assertEqual("UNKNOWN", action(result, "COMMISSION_BATTERY").programme_preconditions.status)
        self.assertEqual("UNKNOWN", action(result, "ACCEPT_ENVELOPE_SCOPE").programme_preconditions.status)
        self.assertEqual("UNKNOWN", result.subsidy_exit_conditions.status)
        self.assertTrue(all(item.programme_preconditions.status == "UNKNOWN" for item in result.operations))
        self.assertTrue(all(item.permission_conditions.status == "PASS" for item in result.operations))

    def test_failed_household_floor_preserves_right_but_blocks_programme_operation(self):
        record = complete_snapshot()
        record = replace(record, assertions=tuple(replace(item, result="FAIL") if item.claim_id == "HOUSEHOLD_CASHFLOW_PROTECTED" else item for item in record.assertions))
        result = assess(record)
        self.assertTrue(all(item.permission_conditions.status == "PASS" for item in result.operations))
        self.assertTrue(all(item.programme_preconditions.status == "FAIL" for item in result.operations))
        self.assertFalse(result.selected_or_funded)

    def test_shared_claim_requires_known_nonempty_explicit_subjects(self):
        for subjects in ((), ("ALL",), ("COMPLETE_PACKAGE",), ("COMMISSION_HEAT_PUMP", "COMMISSION_HEAT_PUMP")):
            with self.subTest(subjects=subjects), self.assertRaises(CapabilityContractError):
                assess(replace(snapshot(), assertions=(assertion("PROGRAMME_ELIGIBILITY", applies_to=subjects),)))

    def test_simultaneous_disjoint_programme_subjects_do_not_conflict(self):
        record = complete_snapshot()
        kept = tuple(item for item in record.assertions if item.claim_id != "HOUSEHOLD_CASHFLOW_PROTECTED")
        hp = assertion("HOUSEHOLD_CASHFLOW_PROTECTED", applies_to=("COMMISSION_HEAT_PUMP",), suffix="-HP")
        battery = assertion("HOUSEHOLD_CASHFLOW_PROTECTED", "FAIL", applies_to=("COMMISSION_BATTERY",), suffix="-BATTERY")
        result = assess(replace(record, assertions=kept + (hp, battery)))
        self.assertEqual("PASS", action(result, "COMMISSION_HEAT_PUMP").programme_preconditions.status)
        self.assertEqual("FAIL", action(result, "COMMISSION_BATTERY").programme_preconditions.status)
        self.assertEqual("UNKNOWN", action(result, "ACCEPT_ENVELOPE_SCOPE").programme_preconditions.status)
        with self.assertRaises(CapabilityContractError):
            assess(replace(record, assertions=kept + (hp, replace(battery, applies_to=("COMMISSION_HEAT_PUMP", "COMMISSION_BATTERY")))))


if __name__ == "__main__":
    unittest.main()
