import unittest

from modules.B02.hydraulic_transition_gate import (
    DER,
    Q,
    QUALIFIED,
    REPLACE_DISTRIBUTION_HYDRAULICS,
    REUSE_EXISTING_HYDRAULICS,
    UPGRADE_EXISTING_HYDRAULICS,
    HydraulicTransitionCandidate,
    assess_hydraulic_transition,
)


def base_candidate(path=REUSE_EXISTING_HYDRAULICS):
    return HydraulicTransitionCandidate(
        record_id="REC-P57-001",
        transition_path=path,
        current_system_survey_status=DER,
        current_topology_known=True,
        current_pipe_or_manifold_basis_known=True,
        required_design_flow_rate_l_s=0.42,
        required_pump_head_pa=18000.0,
        system_volume_or_defrost_basis_documented=True,
        balancing_and_control_plan_documented=True,
        water_quality_flush_fill_plan_documented=True,
        commissioning_plan_documented=True,
        evidence_refs_present=True,
        reproducible_repository_binding=True,
    )


class B02P57HydraulicTransitionGateTests(unittest.TestCase):
    def test_reuse_path_can_qualify_with_complete_survey_and_design(self):
        decision = assess_hydraulic_transition(base_candidate())
        self.assertEqual(QUALIFIED, decision.status)
        self.assertEqual((), decision.reasons)

    def test_upgrade_path_can_qualify_with_complete_survey_and_design(self):
        decision = assess_hydraulic_transition(base_candidate(UPGRADE_EXISTING_HYDRAULICS))
        self.assertEqual(QUALIFIED, decision.status)

    def test_full_replacement_does_not_require_current_hydraulic_readiness(self):
        candidate = HydraulicTransitionCandidate(
            **{
                **base_candidate(REPLACE_DISTRIBUTION_HYDRAULICS).__dict__,
                "current_system_survey_status": Q,
                "current_topology_known": False,
                "current_pipe_or_manifold_basis_known": False,
            }
        )
        decision = assess_hydraulic_transition(candidate)
        self.assertEqual(QUALIFIED, decision.status)
        self.assertEqual((), decision.reasons)

    def test_reuse_without_current_survey_fails_closed(self):
        candidate = HydraulicTransitionCandidate(
            **{**base_candidate().__dict__, "current_system_survey_status": Q}
        )
        decision = assess_hydraulic_transition(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("CURRENT_HYDRAULIC_SURVEY_NOT_OBS_OR_DER", decision.reasons)

    def test_missing_finished_system_design_fails_closed(self):
        candidate = HydraulicTransitionCandidate(
            **{**base_candidate().__dict__, "balancing_and_control_plan_documented": False}
        )
        decision = assess_hydraulic_transition(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("BALANCING_AND_CONTROL_PLAN_MISSING", decision.reasons)

    def test_nonpositive_design_values_fail_closed(self):
        candidate = HydraulicTransitionCandidate(
            **{
                **base_candidate().__dict__,
                "required_design_flow_rate_l_s": 0.0,
                "required_pump_head_pa": -1.0,
            }
        )
        decision = assess_hydraulic_transition(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("REQUIRED_DESIGN_FLOW_RATE_INVALID", decision.reasons)
        self.assertIn("REQUIRED_PUMP_HEAD_INVALID", decision.reasons)


if __name__ == "__main__":
    unittest.main()
