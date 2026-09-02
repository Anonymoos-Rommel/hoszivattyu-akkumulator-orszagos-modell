import unittest

from modules.B10.project_delivery_timing_contract import (
    ACTUAL_COMPLETION,
    B10ProjectDeliveryTimingError,
    CURRENT_PAGE_ONLY,
    DER,
    EXPECTED_COMPLETION,
    EX_ANTE_VERIFIED,
    FULFILMENT_PROBABILITY_UNAVAILABLE,
    NOT_APPLICABLE,
    OBS,
    PLANNED_COMPLETION,
    Q,
    ProjectTimingEvidence,
    evaluate_project_delivery_timing,
    validate_completion_probability_claim,
)


class B10P6ProjectDeliveryTimingTests(unittest.TestCase):
    def _actual(self, project_id="P1", operator="DSO"):
        return ProjectTimingEvidence(
            project_id=project_id,
            network_operator=operator,
            claim_type=ACTUAL_COMPLETION,
            claimed_date="2026-06-15",
            source_id="SRC-ACTUAL",
            source_publication_date="2026-06-15",
            evidence_status=OBS,
            snapshot_status=NOT_APPLICABLE,
        )

    def test_ex_ante_target_and_actual_yield_derived_variance_only(self):
        target = ProjectTimingEvidence(
            project_id="P1",
            network_operator="DSO",
            claim_type=EXPECTED_COMPLETION,
            claimed_date="2026-04-03",
            source_id="SRC-TARGET",
            source_publication_date="2024-09-30",
            evidence_status=OBS,
            snapshot_status=EX_ANTE_VERIFIED,
        )
        decision = evaluate_project_delivery_timing(target, self._actual())
        self.assertEqual(decision.schedule_variance_days, 73)
        self.assertEqual(decision.schedule_variance_status, DER)
        self.assertIsNone(decision.completion_probability)
        self.assertEqual(
            decision.completion_probability_status,
            FULFILMENT_PROBABILITY_UNAVAILABLE,
        )

    def test_current_page_planned_date_cannot_mint_forecast_performance(self):
        target = ProjectTimingEvidence(
            project_id="P1",
            network_operator="DSO",
            claim_type=PLANNED_COMPLETION,
            claimed_date="2026-04-30",
            source_id="SRC-CURRENT-PAGE",
            source_publication_date=None,
            evidence_status=OBS,
            snapshot_status=CURRENT_PAGE_ONLY,
        )
        decision = evaluate_project_delivery_timing(target, self._actual())
        self.assertIsNone(decision.schedule_variance_days)
        self.assertEqual(decision.schedule_variance_status, Q)
        self.assertIsNone(decision.completion_probability)

    def test_target_without_actual_is_not_failure_and_probability_stays_q(self):
        target = ProjectTimingEvidence(
            project_id="P1",
            network_operator="DSO",
            claim_type=EXPECTED_COMPLETION,
            claimed_date="2027-01-01",
            source_id="SRC-TARGET",
            source_publication_date="2026-01-01",
            evidence_status=OBS,
            snapshot_status=EX_ANTE_VERIFIED,
        )
        decision = evaluate_project_delivery_timing(target, None)
        self.assertIsNone(decision.actual_completion_date)
        self.assertIsNone(decision.schedule_variance_days)
        self.assertEqual(decision.schedule_variance_status, Q)
        self.assertEqual(decision.completion_probability_status, FULFILMENT_PROBABILITY_UNAVAILABLE)

    def test_wrong_project_or_operator_pair_fails_closed(self):
        target = ProjectTimingEvidence(
            project_id="P1",
            network_operator="DSO-A",
            claim_type=EXPECTED_COMPLETION,
            claimed_date="2026-04-03",
            source_id="SRC-TARGET",
            source_publication_date="2024-09-30",
            evidence_status=OBS,
            snapshot_status=EX_ANTE_VERIFIED,
        )
        with self.assertRaises(B10ProjectDeliveryTimingError):
            evaluate_project_delivery_timing(target, self._actual(project_id="P2", operator="DSO-A"))
        with self.assertRaises(B10ProjectDeliveryTimingError):
            evaluate_project_delivery_timing(target, self._actual(project_id="P1", operator="DSO-B"))

    def test_actual_completion_must_be_obs_and_not_applicable_snapshot(self):
        with self.assertRaises(B10ProjectDeliveryTimingError):
            ProjectTimingEvidence(
                project_id="P1",
                network_operator="DSO",
                claim_type=ACTUAL_COMPLETION,
                claimed_date="2026-06-15",
                source_id="SRC",
                source_publication_date="2026-06-15",
                evidence_status=Q,
                snapshot_status=NOT_APPLICABLE,
            )
        with self.assertRaises(B10ProjectDeliveryTimingError):
            ProjectTimingEvidence(
                project_id="P1",
                network_operator="DSO",
                claim_type=ACTUAL_COMPLETION,
                claimed_date="2026-06-15",
                source_id="SRC",
                source_publication_date="2026-06-15",
                evidence_status=OBS,
                snapshot_status=EX_ANTE_VERIFIED,
            )

    def test_planned_expected_claim_requires_source_native_obs(self):
        with self.assertRaises(B10ProjectDeliveryTimingError):
            ProjectTimingEvidence(
                project_id="P1",
                network_operator="DSO",
                claim_type=EXPECTED_COMPLETION,
                claimed_date="2026-04-03",
                source_id="SRC",
                source_publication_date="2024-09-30",
                evidence_status=DER,
                snapshot_status=EX_ANTE_VERIFIED,
            )

    def test_postdated_target_publication_fails_closed(self):
        with self.assertRaises(B10ProjectDeliveryTimingError):
            ProjectTimingEvidence(
                project_id="P1",
                network_operator="DSO",
                claim_type=EXPECTED_COMPLETION,
                claimed_date="2026-04-03",
                source_id="SRC",
                source_publication_date="2026-04-04",
                evidence_status=OBS,
                snapshot_status=EX_ANTE_VERIFIED,
            )

    def test_numeric_completion_probability_is_forbidden_without_calibration(self):
        validate_completion_probability_claim(None)
        with self.assertRaises(B10ProjectDeliveryTimingError):
            validate_completion_probability_claim(0.8)
        with self.assertRaises(B10ProjectDeliveryTimingError):
            validate_completion_probability_claim(0.8, calibrated_model_source_ids=("SRC-MODEL",))
        with self.assertRaises(B10ProjectDeliveryTimingError):
            validate_completion_probability_claim(1.1)

    def test_schedule_variance_can_be_negative_without_becoming_probability(self):
        target = ProjectTimingEvidence(
            project_id="P1",
            network_operator="DSO",
            claim_type=PLANNED_COMPLETION,
            claimed_date="2026-07-01",
            source_id="SRC-TARGET",
            source_publication_date="2025-01-01",
            evidence_status=OBS,
            snapshot_status=EX_ANTE_VERIFIED,
        )
        decision = evaluate_project_delivery_timing(target, self._actual())
        self.assertEqual(decision.schedule_variance_days, -16)
        self.assertEqual(decision.schedule_variance_status, DER)
        self.assertIsNone(decision.completion_probability)


if __name__ == "__main__":
    unittest.main()
