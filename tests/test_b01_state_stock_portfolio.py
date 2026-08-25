from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

from modules.B01 import engine as b01


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "b01_state_stock_scn.json"


def fixture_inputs():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    records = tuple(b01._record_from_payload(row) for row in payload["households"])
    candidates = tuple(b01._candidate_from_payload(row) for row in payload["candidates"])
    policy = b01._policy_from_payload(payload["policy"])
    constraints = b01._constraints_from_payload(payload["constraints"])
    decisions = tuple(
        b01.assess_candidate(record, candidate)
        for record in records
        for candidate in candidates
        if record.household_id == candidate.household_id
    )
    return payload, records, candidates, policy, constraints, decisions


class B01StateStockPortfolioTests(unittest.TestCase):
    def test_canonical_record_and_transition_contract_are_parseable(self) -> None:
        model = json.loads((ROOT / "registry" / "household_state_model.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [
                "household_id", "archetype_id", "region_id", "truth_context", "current_state", "evidence_refs",
                "state_as_of", "owner", "next_gate", "blocked_reason", "eligibility_status",
                "eligibility_evidence_status",
            ],
            model["household_record_schema"]["required"],
        )
        self.assertEqual(
            ["S0_TO_S1", "S1_TO_S2", "S2_TO_S3", "S3_TO_S4", "S4_TO_S5"],
            [row["transition_id"] for row in model["transition_contract"]],
        )

    def test_transition_gate_semantics_align_with_state_exit_gates(self) -> None:
        model = json.loads((ROOT / "registry" / "household_state_model.json").read_text(encoding="utf-8"))
        exits = {row["state_id"]: row["exit_gate"] for row in model["states"]}
        for transition in model["transition_contract"]:
            with self.subTest(transition=transition["transition_id"]):
                self.assertEqual(exits[transition["from_state"]], transition["source_exit_gate"])
                self.assertEqual(exits[transition["to_state"]], transition["target_completion_gate"])
                self.assertEqual(
                    [transition["source_exit_gate"], transition["target_completion_gate"]],
                    transition["required_gates"],
                )

    def test_scn_transition_label_mismatch_fails_closed(self) -> None:
        for status in ("OBS", "DER", "ASS", "Q"):
            with self.subTest(status=status):
                evidence = b01.TransitionEvidence(
                    "S0_TO_S1", status, ("SCN-EVIDENCE",), True,
                    "2026-01-01", "SCN-fixture", truth_context="SCN",
                )
                with self.assertRaises(b01.B01ContractError):
                    evidence.validate()

    def test_real_transition_rejects_scn_ass_and_q_completion(self) -> None:
        for status in ("SCN", "ASS", "Q"):
            with self.subTest(status=status):
                evidence = b01.TransitionEvidence(
                    "S0_TO_S1", status, ("E0",), True,
                    "2026-01-01", "tester",
                )
                with self.assertRaises(b01.B01ContractError):
                    evidence.validate()

    def test_scn_fixture_remains_scn_truth(self) -> None:
        payload, records, candidates, _, _, _ = fixture_inputs()
        self.assertEqual("SCN", payload["truth_context"])
        self.assertTrue(all(record.truth_context == "SCN" for record in records))
        self.assertTrue(all(record.eligibility_evidence_status in {"SCN", "Q"} for record in records))
        self.assertTrue(
            all(evidence.truth_context == "SCN" and evidence.status == "SCN" for record in records for evidence in record.transition_evidence)
        )
        self.assertTrue(all(candidate.truth_context == "SCN" for candidate in candidates))
        self.assertTrue(all(candidate.required_gate_status == "SCN" for candidate in candidates))

    def test_scn_fixture_runs_without_observed_evidence_fabrication(self) -> None:
        output = b01.run_fixture(FIXTURE)
        self.assertEqual("SCN", output.status)
        self.assertEqual(2, len(output.selected_transitions))
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertFalse(
            any(
                evidence.get("status") in {"OBS", "DER"}
                for household in payload["households"]
                for evidence in household.get("transition_evidence", [])
            )
        )

    def test_candidate_gate_matches_canonical_contract(self) -> None:
        _, _, candidates, _, _, _ = fixture_inputs()
        candidate = next(item for item in candidates if item.intervention_id == "SCN-INT-002")
        transition = b01._transition_for(candidate.from_state, candidate.target_state)
        self.assertEqual(transition["target_completion_gate"], candidate.required_gate)
        candidate.validate()

    def test_candidate_gate_mismatch_fails_closed(self) -> None:
        _, _, candidates, _, _, _ = fixture_inputs()
        candidate = next(item for item in candidates if item.intervention_id == "SCN-INT-002")
        with self.assertRaises(b01.B01ContractError):
            replace(candidate, required_gate="audit_complete").validate()

    def test_fixture_candidate_gates_are_canonical(self) -> None:
        _, _, candidates, _, _, _ = fixture_inputs()
        for candidate in candidates:
            with self.subTest(candidate=candidate.intervention_id):
                transition = b01._transition_for(candidate.from_state, candidate.target_state)
                self.assertEqual(transition["target_completion_gate"], candidate.required_gate)
                self.assertIn(candidate.required_gate, transition["required_gates"])

    def test_missing_transition_evidence_is_blocked_q(self) -> None:
        record = b01.HouseholdStateRecord(
            "HH-1", "ARCH-1", "R1", "S1", ("E1",), "2026-01-01", "tester",
            "technical_readiness_complete", "", "ELIGIBLE", "OBS",
            (b01.TransitionEvidence("S0_TO_S1", "OBS", ("E0",), True, "2026-01-01", "tester"),),
        )
        decision = b01.evaluate_next_transition(record)
        self.assertEqual("BLOCKED", decision.status)
        self.assertEqual("Q", decision.evidence_status)

    def test_ass_and_scn_cannot_complete_transition(self) -> None:
        for status in ("ASS", "SCN"):
            with self.subTest(status=status):
                evidence = b01.TransitionEvidence("S0_TO_S1", status, ("E0",), True, "2026-01-01", "tester")
                with self.assertRaises(b01.B01ContractError):
                    evidence.validate()

    def test_existing_heat_pump_marker_does_not_promote_state(self) -> None:
        record = b01.HouseholdStateRecord(
            "HH-HP", "HP_PRESENT", "R1", "S0", ("E0",), "2026-01-01", "tester",
            "audit_complete", "", "BLOCKED", "Q",
        )
        self.assertEqual("S0", b01.determine_current_state(record))

    def test_skipped_state_requires_explicit_satisfied_gate(self) -> None:
        evidence = b01.TransitionEvidence(
            "S0_TO_S1", "OBS", ("E0",), True, "2026-01-01", "tester", skipped=True,
        )
        with self.assertRaises(b01.B01ContractError):
            evidence.validate()

    def test_state_cannot_move_backward_or_skip_predecessor(self) -> None:
        record = b01.HouseholdStateRecord(
            "HH-2", "ARCH-1", "R1", "S2", ("E2",), "2026-01-01", "tester",
            "heat_pump_operational_and_qa_complete", "", "ELIGIBLE", "DER",
            (b01.TransitionEvidence("S1_TO_S2", "DER", ("E2",), True, "2026-01-01", "tester"),),
        )
        with self.assertRaises(b01.B01ContractError):
            b01.determine_current_state(record)

    def test_missing_policy_weight_fails_closed(self) -> None:
        _, _, _, policy, _, decisions = fixture_inputs()
        eligible = [decision.candidate for decision in decisions if decision.status == "ELIGIBLE"]
        missing = dict(policy)
        missing.pop("SOCIAL_NEED")
        with self.assertRaises(b01.B01ContractError):
            b01.mcda_order(eligible, missing)

    def test_hidden_default_weight_is_prohibited(self) -> None:
        _, _, _, policy, _, decisions = fixture_inputs()
        eligible = [decision.candidate for decision in decisions if decision.status == "ELIGIBLE"]
        invalid = dict(policy)
        invalid["SOCIAL_NEED"] = replace(policy["SOCIAL_NEED"], weight=None, weight_status="Q")
        with self.assertRaises(b01.B01ContractError):
            b01.mcda_order(eligible, invalid)

    def test_missing_component_is_not_treated_as_zero(self) -> None:
        _, _, _, policy, _, decisions = fixture_inputs()
        candidate = next(decision.candidate for decision in decisions if decision.status == "ELIGIBLE")
        scores = dict(candidate.scores)
        statuses = dict(candidate.score_statuses)
        scores["SOCIAL_NEED"] = None
        statuses["SOCIAL_NEED"] = "Q"
        broken = replace(candidate, scores=scores, score_statuses=statuses)
        with self.assertRaises(b01.B01ContractError):
            b01.mcda_order([broken], policy)

    def test_missing_capacity_is_not_infinite(self) -> None:
        _, _, _, policy, constraints, decisions = fixture_inputs()
        eligible = [decision.candidate for decision in decisions if decision.status == "ELIGIBLE"]
        ordered = b01.mcda_order(eligible, policy)
        broken = list(constraints)
        broken[0] = replace(broken[0], available=None, status="Q")
        with self.assertRaises(b01.B01ContractError):
            b01.select_with_capacity(ordered, broken)

    def test_fixture_selection_respects_annual_constraint(self) -> None:
        output = b01.run_fixture(FIXTURE)
        self.assertEqual("SCN", output.status)
        self.assertEqual(2026, output.plan_year)
        self.assertEqual(2, len(output.selected_transitions))
        self.assertEqual("installer_FTE", output.binding_constraint)
        self.assertEqual(("SCN-INT-004",), output.waiting_candidates)

    def test_state_stock_conservation_and_regional_sum(self) -> None:
        output = b01.run_fixture(FIXTURE)
        self.assertEqual(6, sum(output.state_counts.values()))
        for state_id in b01.STATE_ORDER:
            self.assertEqual(
                output.state_counts[state_id],
                sum(region[state_id] for region in output.regional_state_counts.values()),
            )

    def test_deterministic_tie_break(self) -> None:
        _, _, _, policy, _, decisions = fixture_inputs()
        candidates = [decision.candidate for decision in decisions if decision.status == "ELIGIBLE"][:2]
        equal_scores = dict(candidates[0].scores)
        second = replace(candidates[1], scores=equal_scores)
        ordered = b01.mcda_order([second, candidates[0]], policy)
        self.assertEqual(tuple(sorted((candidates[0].household_id, second.household_id))), tuple(item.household_id for item in ordered))

    def test_lexicographic_method_requires_explicit_contract(self) -> None:
        _, _, _, policy, _, decisions = fixture_inputs()
        candidates = [decision.candidate for decision in decisions if decision.status == "ELIGIBLE"]
        ordered = b01.lexicographic_order(candidates, policy, b01.PORTFOLIO_COMPONENTS)
        self.assertEqual(3, len(ordered))

    def test_stress_test_requires_explicit_alternative_policy(self) -> None:
        _, _, _, policy, _, decisions = fixture_inputs()
        candidates = [decision.candidate for decision in decisions if decision.status == "ELIGIBLE"]
        alternative = dict(policy)
        alternative["SOCIAL_NEED"] = replace(policy["SOCIAL_NEED"], weight=2.0)
        orders = b01.stress_test_orders(candidates, (policy, alternative))
        self.assertEqual(2, len(orders))

    def test_policy_target_is_not_eligible_stock_and_b02_q_stays_q(self) -> None:
        feasible = b01.bounded_feasible_stock(
            b01.EvidenceValue(5, "POL", "policy"),
            b01.EvidenceValue(3, "SCN", "fixture-eligible"),
            b01.EvidenceValue(2, "SCN", "selected"),
        )
        self.assertEqual(2, feasible.value)
        unknown = b01.bounded_feasible_stock(
            b01.EvidenceValue(5, "POL", "policy"),
            b01.EvidenceValue(None, "Q", "B02-Q"),
            b01.EvidenceValue(2, "SCN", "selected"),
        )
        self.assertIsNone(unknown.value)
        self.assertEqual("Q", unknown.status)

    def test_b05_b07_physical_inputs_do_not_create_policy_eligibility(self) -> None:
        _, records, candidates, _, _, decisions = fixture_inputs()
        blocked = next(decision for decision in decisions if decision.candidate.intervention_id == "SCN-INT-001")
        self.assertEqual("BLOCKED", blocked.status)
        self.assertIn("Eligibility", blocked.reason)
        self.assertEqual("BLOCKED", records[0].eligibility_status)
        self.assertEqual("SCN", candidates[0].evidence_status)

    def test_explanation_fields_are_required_and_populated(self) -> None:
        output = b01.run_fixture(FIXTURE)
        required = {"intervention_id", "why_now", "why_here", "binding_constraint", "next_missing_gate"}
        self.assertTrue(output.explanations)
        self.assertTrue(all(required.issubset(set(item)) for item in output.explanations))


if __name__ == "__main__":
    unittest.main()
