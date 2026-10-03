import csv
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import unittest

from modules.B10.project_delivery_timing_contract import (
    ACTUAL_COMPLETION,
    CAPABILITY_TARGET,
    EXACT,
    ON_OR_BEFORE,
    PHYSICAL_IN_SERVICE,
    PROJECT_COMPLETION,
    PUBLICATION_REPORTING_BOUND,
    SOURCE_STATED_EVENT_DATE,
    SOURCE_STATED_TARGET_DATE,
    VERIFIED_SAME_MILESTONE_SCOPE,
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
            milestone_type=PHYSICAL_IN_SERVICE,
            scope_id="SYNTHETIC:P1:FULL_SCOPE",
            scope_source_id="SRC-ACTUAL",
            date_relation=EXACT,
            date_precision="DAY",
            date_authority=SOURCE_STATED_EVENT_DATE,
            snapshot_status=NOT_APPLICABLE,
        )

    def test_synthetic_same_scope_exact_pair_yields_derived_variance_only(self):
        target = ProjectTimingEvidence(
            project_id="P1",
            network_operator="DSO",
            claim_type=EXPECTED_COMPLETION,
            claimed_date="2026-04-03",
            source_id="SRC-TARGET",
            source_publication_date="2024-09-30",
            evidence_status=OBS,
            milestone_type=PHYSICAL_IN_SERVICE,
            scope_id="SYNTHETIC:P1:FULL_SCOPE",
            scope_source_id="SRC-TARGET",
            date_relation=EXACT,
            date_precision="DAY",
            date_authority=SOURCE_STATED_TARGET_DATE,
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
            milestone_type=PHYSICAL_IN_SERVICE,
            scope_id="SYNTHETIC:P1:FULL_SCOPE",
            scope_source_id="SRC-CURRENT-PAGE",
            date_relation=EXACT,
            date_precision="DAY",
            date_authority=SOURCE_STATED_TARGET_DATE,
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
            milestone_type=PHYSICAL_IN_SERVICE,
            scope_id="SYNTHETIC:P1:FULL_SCOPE",
            scope_source_id="SRC-TARGET",
            date_relation=EXACT,
            date_precision="DAY",
            date_authority=SOURCE_STATED_TARGET_DATE,
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
            milestone_type=PHYSICAL_IN_SERVICE,
            scope_id="SYNTHETIC:P1:FULL_SCOPE",
            scope_source_id="SRC-TARGET",
            date_relation=EXACT,
            date_precision="DAY",
            date_authority=SOURCE_STATED_TARGET_DATE,
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
                milestone_type=PHYSICAL_IN_SERVICE,
                scope_id="SYNTHETIC:P1:FULL_SCOPE",
                scope_source_id="SRC",
                date_relation=EXACT,
                date_precision="DAY",
                date_authority=SOURCE_STATED_EVENT_DATE,
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
                milestone_type=PHYSICAL_IN_SERVICE,
                scope_id="SYNTHETIC:P1:FULL_SCOPE",
                scope_source_id="SRC",
                date_relation=EXACT,
                date_precision="DAY",
                date_authority=SOURCE_STATED_EVENT_DATE,
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
                milestone_type=PHYSICAL_IN_SERVICE,
                scope_id="SYNTHETIC:P1:FULL_SCOPE",
                scope_source_id="SRC",
                date_relation=EXACT,
                date_precision="DAY",
                date_authority=SOURCE_STATED_TARGET_DATE,
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
                milestone_type=PHYSICAL_IN_SERVICE,
                scope_id="SYNTHETIC:P1:FULL_SCOPE",
                scope_source_id="SRC",
                date_relation=EXACT,
                date_precision="DAY",
                date_authority=SOURCE_STATED_TARGET_DATE,
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
            milestone_type=PHYSICAL_IN_SERVICE,
            scope_id="SYNTHETIC:P1:FULL_SCOPE",
            scope_source_id="SRC-TARGET",
            date_relation=EXACT,
            date_precision="DAY",
            date_authority=SOURCE_STATED_TARGET_DATE,
            snapshot_status=EX_ANTE_VERIFIED,
        )
        decision = evaluate_project_delivery_timing(target, self._actual())
        self.assertEqual(decision.schedule_variance_days, -16)
        self.assertEqual(decision.schedule_variance_status, DER)
        self.assertIsNone(decision.completion_probability)


    def _target(self):
        return ProjectTimingEvidence(
            project_id="P1", network_operator="DSO", claim_type=EXPECTED_COMPLETION,
            claimed_date="2026-04-03", source_id="SRC-TARGET",
            source_publication_date="2024-09-30", evidence_status=OBS,
            snapshot_status=EX_ANTE_VERIFIED, milestone_type=PHYSICAL_IN_SERVICE,
            scope_id="SYNTHETIC:P1:FULL_SCOPE", scope_source_id="SRC-TARGET",
            date_relation=EXACT, date_precision="DAY", date_authority=SOURCE_STATED_TARGET_DATE,
        )

    def test_publication_date_cannot_substitute_for_exact_event(self):
        with self.assertRaisesRegex(B10ProjectDeliveryTimingError, "exact event"):
            replace(self._actual(), date_authority=PUBLICATION_REPORTING_BOUND)

    def test_completed_by_bound_is_preserved_without_exact_event_or_variance(self):
        actual = replace(self._actual(), date_relation=ON_OR_BEFORE,
                         date_authority=PUBLICATION_REPORTING_BOUND)
        result = evaluate_project_delivery_timing(self._target(), actual)
        self.assertIsNone(result.actual_completion_date)
        self.assertIsNone(result.actual_event_lower_bound)
        self.assertEqual("2026-06-15", result.actual_event_upper_bound)
        self.assertIsNone(result.physical_actual_completion_date)
        self.assertIsNone(result.schedule_variance_days)
        self.assertEqual(Q, result.schedule_variance_status)

    def test_matching_project_operator_does_not_prove_matching_milestone_or_scope(self):
        for actual in (
            replace(self._actual(), milestone_type=PROJECT_COMPLETION),
            replace(self._actual(), scope_id="SYNTHETIC:P1:OTHER_PHASE"),
            replace(self._actual(), scope_id="SYNTHETIC:P1:OTHER_CAPABILITY_METRIC"),
            replace(self._actual(), scope_source_id=None),
        ):
            with self.subTest(actual=actual):
                result = evaluate_project_delivery_timing(self._target(), actual)
                self.assertEqual("UNRESOLVED", result.pairing_status)
                self.assertIsNone(result.schedule_variance_days)

    def test_missing_ex_ante_source_date_cannot_assert_verified_authority(self):
        with self.assertRaisesRegex(B10ProjectDeliveryTimingError, "dated source"):
            replace(self._target(), source_publication_date=None)

    def test_source_published_after_actual_cannot_be_ex_ante_performance_target(self):
        target = replace(self._target(), claimed_date="2027-01-01",
                         source_publication_date="2026-06-16")
        self.assertIsNone(evaluate_project_delivery_timing(target, self._actual()).schedule_variance_days)

    def test_legacy_untyped_dates_fail_closed_instead_of_becoming_delivery_events(self):
        target = ProjectTimingEvidence("P1", "DSO", EXPECTED_COMPLETION, "2026-04-03",
                                       "SRC-T", "2024-09-30", OBS, EX_ANTE_VERIFIED)
        actual = ProjectTimingEvidence("P1", "DSO", ACTUAL_COMPLETION, "2026-06-15",
                                       "SRC-A", "2026-06-15", OBS, NOT_APPLICABLE)
        result = evaluate_project_delivery_timing(target, actual)
        self.assertIsNone(result.actual_completion_date)
        self.assertIsNone(result.physical_actual_completion_date)
        self.assertIsNone(result.schedule_variance_days)

    def test_real_rrf_rows_reproduce_source_bound_semantics(self):
        path = Path(__file__).resolve().parents[1] / "registry/project_delivery_timing.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            def evidence(prefix, claim_type, claimed_date, snapshot):
                return ProjectTimingEvidence(
                    project_id=row["project_id"], network_operator=row["network_operator"],
                    claim_type=claim_type, claimed_date=claimed_date,
                    source_id=row[f"{prefix}_source_id"],
                    source_publication_date=row[f"{prefix}_source_publication_date"] or None,
                    evidence_status=OBS, snapshot_status=snapshot,
                    milestone_type=row[f"{prefix}_milestone_type"],
                    scope_id=row[f"{prefix}_scope_id"], scope_source_id=row[f"{prefix}_scope_source_id"],
                    date_relation=row[f"{prefix}_date_relation"], date_precision=row[f"{prefix}_date_precision"],
                    date_authority=row[f"{prefix}_date_authority"],
                )
            target = evidence("target", row["target_claim_type"], row["target_date"], row["target_snapshot_status"])
            actual = evidence("actual", ACTUAL_COMPLETION, row["actual_claimed_date"], NOT_APPLICABLE)
            result = evaluate_project_delivery_timing(target, actual)
            with self.subTest(project=row["project_id"]):
                self.assertEqual(row["actual_completion_date"], result.actual_completion_date or "")
                self.assertEqual(row["actual_event_lower_bound"], result.actual_event_lower_bound or "")
                self.assertEqual(row["actual_event_upper_bound"], result.actual_event_upper_bound or "")
                self.assertEqual(row["pairing_status"], result.pairing_status)
                self.assertIsNone(result.schedule_variance_days)
                self.assertEqual(Q, result.schedule_variance_status)
                self.assertIsNone(result.physical_actual_completion_date)
                self.assertFalse(result.physical_target_proven)
                if "OPUS" in row["timing_id"]:
                    self.assertEqual(CAPABILITY_TARGET, target.milestone_type)
                    self.assertEqual(PROJECT_COMPLETION, actual.milestone_type)
                    self.assertEqual("SRC-B10-OPUS-TITASZ-RRF-PROJECT-2026", actual.source_id)

    def test_registry_validator_rejects_old_event_delay_and_operating_overclaims(self):
        from tools import validate_registry as validator
        original_read = validator.read_csv
        _, sources = original_read(validator.REGISTRY / "sources.csv")
        source_ids = {row["source_id"] for row in sources}
        baseline_errors = []
        validator.validate_b10_artifacts(baseline_errors, source_ids)
        self.assertEqual([], baseline_errors)
        mutations = (
            ("project_delivery_timing.csv", 0, "actual_completion_date", "2026-06-15"),
            ("project_delivery_timing.csv", 1, "schedule_variance_days", "73"),
            ("project_delivery_timing.csv", 1, "actual_source_id", "SRC-B10-OPUS-TITASZ-RRF-COMPLETION-2026"),
            ("baseline_infrastructure.csv", 0, "status_taxonomy", "OPERATING"),
            ("baseline_infrastructure.csv", 1, "physical_in_service_date", "2026-06-15"),
        )
        for filename, index, field, value in mutations:
            def mutated_read(path):
                fields, rows = original_read(path)
                if path.name == filename:
                    rows[index][field] = value
                return fields, rows
            errors = []
            with self.subTest(field=field), patch.object(validator, "read_csv", side_effect=mutated_read):
                validator.validate_b10_artifacts(errors, source_ids)
                self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
