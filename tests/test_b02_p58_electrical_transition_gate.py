import unittest

from modules.B02.electrical_transition_gate import (
    BLOCKED,
    DER,
    DSO_APPROVED,
    DSO_PENDING,
    DSO_REFUSED,
    Q,
    QUALIFIED,
    UPGRADE_CONNECTION,
    USE_EXISTING_CONNECTION,
    ElectricalTransitionCandidate,
    assess_electrical_transition,
)


def base_candidate(path=USE_EXISTING_CONNECTION):
    return ElectricalTransitionCandidate(
        record_id="REC-P58-001",
        transition_path=path,
        current_connection_evidence_status=DER,
        current_phase_count=3,
        current_available_current_a_per_phase=25.0,
        heat_pump_nominal_electrical_kw=3.2,
        auxiliary_electrical_kw=1.0,
        starting_current_or_inverter_basis_documented=True,
        required_phase_count=3,
        required_current_a_per_phase=20.0,
        meter_or_service_upgrade_scope_documented=True,
        dedicated_heat_pump_circuit_documented=True,
        dso_status=DSO_APPROVED,
        dso_evidence_refs_present=True,
        reproducible_repository_binding=True,
    )


class B02P58ElectricalTransitionGateTests(unittest.TestCase):
    def test_existing_connection_path_can_qualify(self):
        decision = assess_electrical_transition(base_candidate())
        self.assertEqual(QUALIFIED, decision.status)
        self.assertEqual((), decision.reasons)

    def test_upgrade_path_can_qualify(self):
        decision = assess_electrical_transition(base_candidate(UPGRADE_CONNECTION))
        self.assertEqual(QUALIFIED, decision.status)

    def test_pending_dso_status_is_q_not_fail(self):
        candidate = ElectricalTransitionCandidate(
            **{**base_candidate().__dict__, "dso_status": DSO_PENDING, "dso_evidence_refs_present": False}
        )
        decision = assess_electrical_transition(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("DSO_FEASIBILITY_PENDING", decision.reasons)

    def test_refused_dso_capacity_is_explicit_blocker(self):
        candidate = ElectricalTransitionCandidate(
            **{**base_candidate().__dict__, "dso_status": DSO_REFUSED}
        )
        decision = assess_electrical_transition(candidate)
        self.assertEqual(BLOCKED, decision.status)
        self.assertEqual(("DSO_CONNECTION_OR_CAPACITY_REFUSED",), decision.reasons)

    def test_upgrade_without_scope_fails_closed(self):
        candidate = ElectricalTransitionCandidate(
            **{
                **base_candidate(UPGRADE_CONNECTION).__dict__,
                "meter_or_service_upgrade_scope_documented": False,
            }
        )
        decision = assess_electrical_transition(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("METER_OR_SERVICE_UPGRADE_SCOPE_MISSING", decision.reasons)

    def test_missing_heat_pump_electrical_basis_fails_closed(self):
        candidate = ElectricalTransitionCandidate(
            **{
                **base_candidate().__dict__,
                "heat_pump_nominal_electrical_kw": None,
                "starting_current_or_inverter_basis_documented": False,
            }
        )
        decision = assess_electrical_transition(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("HEAT_PUMP_ELECTRICAL_POWER_INVALID", decision.reasons)
        self.assertIn("STARTING_CURRENT_OR_INVERTER_BASIS_MISSING", decision.reasons)


if __name__ == "__main__":
    unittest.main()
