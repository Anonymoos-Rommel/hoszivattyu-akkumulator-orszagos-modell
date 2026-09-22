import unittest

from modules.B02.terminal_eligibility_population_inference import (
    PHYSICAL_SCOPE_DWELLINGS,
    QUALIFIED_BOUNDED_POPULATION_INFERENCE,
    StratumEligibilityBound,
    build_population_controls,
    current_repository_envelope,
    inference_boundary,
    poststratify_terminal_eligibility,
)


class B02P84TerminalEligibilityPopulationInferenceTests(unittest.TestCase):
    def test_exact_population_control_surface(self):
        controls = build_population_controls()
        self.assertEqual(len(controls), 40)
        self.assertEqual(len({row.county_code for row in controls}), 20)
        self.assertEqual(
            {row.heating_system_class for row in controls},
            {"CENTRAL_HEATING", "ROOM_BY_ROOM_OR_NO_HEAT"},
        )
        self.assertEqual(
            sum(row.dwelling_count for row in controls),
            PHYSICAL_SCOPE_DWELLINGS,
        )

    def test_current_repository_does_not_invent_positive_lower_bound(self):
        out = current_repository_envelope()
        self.assertEqual(out.status, "Q")
        self.assertEqual(out.eligible_lower_dwellings, 0.0)
        self.assertEqual(
            out.eligible_upper_dwellings,
            float(PHYSICAL_SCOPE_DWELLINGS),
        )
        self.assertEqual(out.covered_population_dwellings, 0)
        self.assertEqual(len(out.uncovered_strata), 40)
        self.assertIn(
            "REPRESENTATIVE_OR_CALIBRATED_TERMINAL_TRANSITION_OUTCOME_EVIDENCE_REQUIRED",
            out.residuals,
        )

    def test_complete_stratum_bounds_poststratify(self):
        controls = build_population_controls()
        bounds = [
            StratumEligibilityBound(
                stratum_id=row.stratum_id,
                eligible_lower_share=0.4,
                eligible_upper_share=0.6,
                evidence_status="DER",
                source_refs=("SRC-TEST",),
            )
            for row in controls
        ]
        out = poststratify_terminal_eligibility(bounds)
        self.assertEqual(out.status, QUALIFIED_BOUNDED_POPULATION_INFERENCE)
        self.assertAlmostEqual(
            out.eligible_lower_dwellings,
            PHYSICAL_SCOPE_DWELLINGS * 0.4,
        )
        self.assertAlmostEqual(
            out.eligible_upper_dwellings,
            PHYSICAL_SCOPE_DWELLINGS * 0.6,
        )
        self.assertEqual(
            out.covered_population_dwellings,
            PHYSICAL_SCOPE_DWELLINGS,
        )
        self.assertEqual(out.uncovered_strata, ())

    def test_missing_stratum_fails_closed_without_imputation(self):
        controls = build_population_controls()
        bounds = [
            StratumEligibilityBound(
                stratum_id=row.stratum_id,
                eligible_lower_share=0.4,
                eligible_upper_share=0.6,
                evidence_status="MODELLED",
                source_refs=("SRC-TEST",),
            )
            for row in controls[:-1]
        ]
        out = poststratify_terminal_eligibility(bounds)
        self.assertEqual(out.status, "Q")
        self.assertEqual(out.eligible_lower_dwellings, 0.0)
        self.assertEqual(
            out.eligible_upper_dwellings,
            float(PHYSICAL_SCOPE_DWELLINGS),
        )
        self.assertEqual(len(out.uncovered_strata), 1)
        self.assertIn("NO_MISSING_STRATUM_IMPUTATION", out.warnings)

    def test_invalid_share_bounds_rejected(self):
        control = build_population_controls()[0]
        with self.assertRaisesRegex(ValueError, "0 <= lower <= upper <= 1"):
            poststratify_terminal_eligibility(
                [
                    StratumEligibilityBound(
                        stratum_id=control.stratum_id,
                        eligible_lower_share=0.8,
                        eligible_upper_share=0.2,
                        evidence_status="DER",
                        source_refs=("SRC-TEST",),
                    )
                ]
            )

    def test_record_and_programme_boundaries_preserved(self):
        boundary = inference_boundary()
        self.assertIn(
            "POPULATION_ESTIMATE_CANNOT_AUTHORIZE_A_SPECIFIC_DWELLING",
            boundary,
        )
        self.assertIn(
            "Q_B02_004_IS_NOT_A_Q_B02_001_PRECONDITION",
            boundary,
        )
        self.assertIn(
            "LEGAL_ECONOMIC_AND_FINAL_PROGRAMME_ELIGIBILITY_REMAIN_SEPARATE",
            boundary,
        )


if __name__ == "__main__":
    unittest.main()
