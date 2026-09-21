import unittest

from modules.B02.transition_set_propagation import (
    ACTIONS,
    ActionCandidate,
    OutcomeCoefficientBound,
    action_count_bounds,
    assess_action_candidate,
    build_transition_action_envelope,
    propagate_metric_bounds,
)


class B02P66TransitionSetPropagationTests(unittest.TestCase):
    def test_structural_action_envelope_uses_calibrated_convector_floor(self):
        e = build_transition_action_envelope()
        self.assertEqual(e.occupied_dwellings, 4_008_541)
        self.assertAlmostEqual(e.add_or_replace_lower, 0.233)
        self.assertAlmostEqual(e.non_keep_lower, 0.233)
        for action in ("KEEP", "UPSIZE", "CHANGE"):
            self.assertAlmostEqual(e.action_bounds[action].upper, 0.767)

    def test_keep_only_candidate_is_rejected(self):
        result = assess_action_candidate(ActionCandidate(1.0, 0.0, 0.0, 0.0, 0.0))
        self.assertFalse(result.admissible)
        self.assertIn(
            "ADD_OR_REPLACE_BELOW_GAS_CONVECTOR_TRANSITION_FLOOR",
            result.blockers,
        )

    def test_floor_candidate_is_admissible(self):
        result = assess_action_candidate(
            ActionCandidate(0.767, 0.0, 0.0, 0.233, 0.0)
        )
        self.assertTrue(result.admissible)

    def test_action_shares_must_form_exclusive_simplex(self):
        result = assess_action_candidate(
            ActionCandidate(0.50, 0.20, 0.10, 0.20, 0.20)
        )
        self.assertFalse(result.admissible)
        self.assertIn("ACTION_SHARES_MUST_SUM_TO_ONE", result.blockers)

    def test_expected_non_keep_count_has_calibrated_lower_bound(self):
        bounds = action_count_bounds()
        self.assertAlmostEqual(bounds["NON_KEEP"][0], 4_008_541 * 0.233)
        self.assertAlmostEqual(bounds["ADD_OR_REPLACE"][0], 4_008_541 * 0.233)
        self.assertEqual(bounds["NON_KEEP"][1], 4_008_541)

    def test_complete_nonmonetary_response_bounds_are_propagated(self):
        rows = tuple(
            OutcomeCoefficientBound(
                action=action,
                metric="COP_PROXY",
                lower=value,
                upper=value + 0.2,
                evidence_status="SCN",
            )
            for action, value in zip(ACTIONS, (4.0, 3.8, 3.5, 3.2, 3.0))
        )
        result = propagate_metric_bounds(rows, "COP_PROXY")
        self.assertEqual(result.status, "SET_BOUNDED")
        self.assertIsNotNone(result.lower)
        self.assertIsNotNone(result.upper)
        self.assertLessEqual(result.lower, result.upper)

    def test_missing_response_bound_fails_closed(self):
        rows = (
            OutcomeCoefficientBound(
                action="KEEP",
                metric="COP",
                lower=3.0,
                upper=4.0,
                evidence_status="DER",
            ),
        )
        result = propagate_metric_bounds(rows, "COP")
        self.assertEqual(result.status, "Q")
        self.assertIn("COMPLETE_ACTION_OUTCOME_BOUNDS_REQUIRED", result.blockers)

    def test_q_response_fails_closed(self):
        rows = tuple(
            OutcomeCoefficientBound(
                action=action,
                metric="UNITS",
                lower=0.0,
                upper=1.0,
                evidence_status="Q" if action == "CHANGE" else "DER",
            )
            for action in ACTIONS
        )
        result = propagate_metric_bounds(rows, "UNITS")
        self.assertEqual(result.status, "Q")
        self.assertIn("Q_OUTCOME_BOUND:CHANGE", result.blockers)

    def test_monetary_metric_requires_price_authority(self):
        rows = tuple(
            OutcomeCoefficientBound(
                action=action,
                metric="CAPEX_HUF",
                lower=0.0,
                upper=1_000_000.0,
                evidence_status="DER",
                monetary=True,
                price_authority_status="Q",
            )
            for action in ACTIONS
        )
        result = propagate_metric_bounds(rows, "CAPEX_HUF")
        self.assertEqual(result.status, "Q")
        self.assertTrue(any(x.startswith("NO_PRICE_AUTHORITY:") for x in result.blockers))


if __name__ == "__main__":
    unittest.main()
