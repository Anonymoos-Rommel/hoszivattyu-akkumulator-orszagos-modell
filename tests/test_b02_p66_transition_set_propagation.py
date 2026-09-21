import unittest

from modules.B02.transition_set_propagation import (
    ADD,
    CHANGE,
    DISTRIBUTION_PATHS,
    KEEP,
    REPLACE_EXISTING_DISTRIBUTION,
    REUSE_EXISTING_DISTRIBUTION,
    UPSIZE,
    DistributionOutcomeBound,
    DistributionPathCandidate,
    EmitterActionIncidence,
    assess_distribution_path_candidate,
    assess_emitter_action_incidence,
    build_distribution_path_envelope,
    distribution_count_bounds,
    legacy_five_way_action_simplex_status,
    propagate_distribution_metric_bounds,
)


class B02P69LayeredTransitionSetPropagationTests(unittest.TestCase):
    def test_distribution_envelope_uses_gas_convector_replacement_floor(self):
        e = build_distribution_path_envelope()
        self.assertEqual(e.occupied_dwellings, 4_008_541)
        self.assertAlmostEqual(e.replace_existing_distribution.lower, 0.233)
        self.assertAlmostEqual(e.reuse_existing_distribution.upper, 0.767)

    def test_reuse_only_distribution_candidate_is_rejected(self):
        result = assess_distribution_path_candidate(
            DistributionPathCandidate(reuse_share=1.0, replace_share=0.0)
        )
        self.assertFalse(result.admissible)
        self.assertIn(
            "REPLACE_DISTRIBUTION_BELOW_GAS_CONVECTOR_FLOOR",
            result.blockers,
        )

    def test_floor_distribution_candidate_is_admissible(self):
        result = assess_distribution_path_candidate(
            DistributionPathCandidate(reuse_share=0.767, replace_share=0.233)
        )
        self.assertTrue(result.admissible)

    def test_distribution_paths_are_exclusive(self):
        result = assess_distribution_path_candidate(
            DistributionPathCandidate(reuse_share=0.8, replace_share=0.3)
        )
        self.assertFalse(result.admissible)
        self.assertIn("DISTRIBUTION_PATH_SHARES_MUST_SUM_TO_ONE", result.blockers)

    def test_emitter_actions_are_not_an_exclusive_simplex(self):
        incidence = EmitterActionIncidence(
            keep=0.8,
            upsize=0.5,
            change=0.4,
            add=0.3,
        )
        result = assess_emitter_action_incidence(incidence)
        self.assertTrue(result.admissible)
        self.assertGreater(sum(incidence.as_dict().values()), 1.0)
        self.assertEqual(tuple(incidence.as_dict()), (KEEP, UPSIZE, CHANGE, ADD))

    def test_distribution_replacement_count_lower_bound_is_preserved(self):
        bounds = distribution_count_bounds()
        self.assertAlmostEqual(
            bounds[REPLACE_EXISTING_DISTRIBUTION][0],
            4_008_541 * 0.233,
        )
        self.assertEqual(
            bounds[REPLACE_EXISTING_DISTRIBUTION][1],
            4_008_541,
        )

    def test_complete_distribution_response_bounds_are_propagated(self):
        rows = (
            DistributionOutcomeBound(
                path=REUSE_EXISTING_DISTRIBUTION,
                metric="X",
                lower=1.0,
                upper=2.0,
                evidence_status="DER",
            ),
            DistributionOutcomeBound(
                path=REPLACE_EXISTING_DISTRIBUTION,
                metric="X",
                lower=3.0,
                upper=4.0,
                evidence_status="DER",
            ),
        )
        result = propagate_distribution_metric_bounds(rows, "X")
        self.assertEqual(result.status, "SET_BOUNDED")
        self.assertLessEqual(result.lower, result.upper)

    def test_missing_distribution_response_fails_closed(self):
        rows = (
            DistributionOutcomeBound(
                path=REUSE_EXISTING_DISTRIBUTION,
                metric="X",
                lower=1.0,
                upper=2.0,
                evidence_status="DER",
            ),
        )
        result = propagate_distribution_metric_bounds(rows, "X")
        self.assertEqual(result.status, "Q")
        self.assertIn(
            "COMPLETE_DISTRIBUTION_PATH_OUTCOME_BOUNDS_REQUIRED",
            result.blockers,
        )

    def test_monetary_distribution_metric_requires_price_authority(self):
        rows = tuple(
            DistributionOutcomeBound(
                path=path,
                metric="CAPEX_HUF",
                lower=0.0,
                upper=1_000_000.0,
                evidence_status="DER",
                monetary=True,
                price_authority_status="Q",
            )
            for path in DISTRIBUTION_PATHS
        )
        result = propagate_distribution_metric_bounds(rows, "CAPEX_HUF")
        self.assertEqual(result.status, "Q")
        self.assertTrue(any(x.startswith("NO_PRICE_AUTHORITY:") for x in result.blockers))

    def test_legacy_five_way_simplex_is_explicitly_superseded(self):
        self.assertEqual(
            legacy_five_way_action_simplex_status(),
            "SUPERSEDED_BY_B02_P69_LAYERED_ACTION_MODEL",
        )


if __name__ == "__main__":
    unittest.main()
