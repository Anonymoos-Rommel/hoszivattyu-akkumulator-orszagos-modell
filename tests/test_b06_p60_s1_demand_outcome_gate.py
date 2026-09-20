import unittest

from modules.B06.s1_demand_outcome_gate import (
    BLOCKED,
    CERTIFIED_CALCULATION,
    DER,
    MEASURED_USAGE,
    NOT_REQUIRED,
    OBS,
    Q,
    READY,
    S1DemandOutcomeEvidence,
    assess_s1_demand_outcome,
)


def certified(**changes):
    values = dict(
        record_id="HU-REC-001",
        intervention_id="RETROFIT-001",
        evidence_kind=CERTIFIED_CALCULATION,
        evidence_status=DER,
        phase_link_id="S0_TO_S1:HU-REC-001:RETROFIT-001",
        before_value=220.0,
        after_value=128.0,
        before_metric_id="ANNUAL_PRIMARY_ENERGY",
        after_metric_id="ANNUAL_PRIMARY_ENERGY",
        before_unit="kWh_m2a",
        after_unit="kWh_m2a",
        before_method_id="HET_SAME_METHOD",
        after_method_id="HET_SAME_METHOD",
        before_source_refs=("HET-BEFORE",),
        after_source_refs=("HET-AFTER",),
        normalization_basis_documented=False,
        end_use_scope_documented=True,
        minimum_reduction_fraction=0.30,
    )
    values.update(changes)
    return S1DemandOutcomeEvidence(**values)


class B06P60S1DemandOutcomeGateTests(unittest.TestCase):
    def test_certified_before_after_can_open_s1_with_der(self):
        decision = assess_s1_demand_outcome(certified())
        self.assertEqual(READY, decision.status)
        self.assertEqual(DER, decision.evidence_status)
        self.assertAlmostEqual((220.0 - 128.0) / 220.0, decision.reduction_fraction)

    def test_measured_path_requires_obs_and_normalization(self):
        evidence = certified(
            evidence_kind=MEASURED_USAGE,
            evidence_status=OBS,
            normalization_basis_documented=False,
        )
        decision = assess_s1_demand_outcome(evidence)
        self.assertEqual(Q, decision.status)
        self.assertIn("MEASURED_USAGE_NORMALIZATION_MISSING", decision.reasons)

    def test_measured_path_can_open_when_normalized(self):
        evidence = certified(
            evidence_kind=MEASURED_USAGE,
            evidence_status=OBS,
            normalization_basis_documented=True,
        )
        decision = assess_s1_demand_outcome(evidence)
        self.assertEqual(READY, decision.status)
        self.assertEqual(OBS, decision.evidence_status)

    def test_mismatched_metric_or_method_fails_closed(self):
        decision = assess_s1_demand_outcome(
            certified(after_method_id="OTHER_METHOD", after_metric_id="FINAL_ENERGY")
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("METRIC_ID_MISMATCH", decision.reasons)
        self.assertIn("METHOD_ID_MISMATCH", decision.reasons)

    def test_missing_phase_link_fails_closed(self):
        decision = assess_s1_demand_outcome(certified(phase_link_id=""))
        self.assertEqual(Q, decision.status)
        self.assertIn("PHASE_LINK_ID_MISSING", decision.reasons)

    def test_positive_but_subthreshold_reduction_is_blocked(self):
        decision = assess_s1_demand_outcome(
            certified(before_value=100.0, after_value=75.0, minimum_reduction_fraction=0.30)
        )
        self.assertEqual(BLOCKED, decision.status)
        self.assertIn("MINIMUM_DEMAND_REDUCTION_NOT_ACHIEVED", decision.reasons)

    def test_no_reduction_is_explicitly_blocked(self):
        decision = assess_s1_demand_outcome(
            certified(before_value=100.0, after_value=100.0, minimum_reduction_fraction=None)
        )
        self.assertEqual(BLOCKED, decision.status)
        self.assertIn("DEMAND_REDUCTION_NOT_ACHIEVED", decision.reasons)

    def test_not_required_requires_explicit_authority(self):
        evidence = S1DemandOutcomeEvidence(
            record_id="HU-REC-002",
            intervention_id="NO-DEMAND-REDUCTION-001",
            evidence_kind=NOT_REQUIRED,
            evidence_status=DER,
            phase_link_id="S0_TO_S1:HU-REC-002:NOT-REQUIRED",
            not_required_reason="Approved transition does not require a demand-reduction intervention.",
            not_required_authority_refs=("RULE-001",),
        )
        decision = assess_s1_demand_outcome(evidence)
        self.assertEqual(READY, decision.status)
        self.assertIsNone(decision.reduction_fraction)

    def test_not_required_without_authority_stays_q(self):
        evidence = S1DemandOutcomeEvidence(
            record_id="HU-REC-002",
            intervention_id="NO-DEMAND-REDUCTION-001",
            evidence_kind=NOT_REQUIRED,
            evidence_status=DER,
            phase_link_id="S0_TO_S1:HU-REC-002:NOT-REQUIRED",
            not_required_reason="Claimed not required.",
        )
        decision = assess_s1_demand_outcome(evidence)
        self.assertEqual(Q, decision.status)
        self.assertIn("NOT_REQUIRED_AUTHORITY_MISSING", decision.reasons)


if __name__ == "__main__":
    unittest.main()
