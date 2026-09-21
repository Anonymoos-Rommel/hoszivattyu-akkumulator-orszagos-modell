import json
import unittest

from modules.B02.kehop_scope_crosswalk import (
    build_kehop_scope_crosswalk,
    as_log_dict,
)


class B02P75KehopScopeCrosswalkTests(unittest.TestCase):
    def test_crosswalk_reconciles_to_canonical_physical_scope(self):
        x = build_kehop_scope_crosswalk()
        self.assertEqual(x.physical_scope_dwellings, 3_389_817)
        self.assertEqual(x.evidence_status, "ASS")
        self.assertEqual(
            x.age_cutoff_status,
            "SET_BOUNDED_BY_WBL_CONSTRUCTION_PERIOD",
        )
        self.assertEqual(
            x.legal_eligibility_status,
            "Q_ADDITIONAL_PROGRAMME_CONDITIONS",
        )

    def test_age_censoring_and_nonreuse_bounds_are_ordered(self):
        x = build_kehop_scope_crosswalk()
        self.assertGreater(x.structural_candidate_lower, 0.0)
        self.assertGreaterEqual(
            x.structural_candidate_upper,
            x.structural_candidate_lower,
        )
        self.assertGreater(x.proven_nonreuse_overlap_lower, 0.0)
        self.assertLessEqual(
            x.proven_nonreuse_overlap_lower,
            x.possible_nonreuse_overlap_upper,
        )
        self.assertEqual(
            x.possible_nonreuse_overlap_upper,
            x.structural_candidate_upper,
        )

    def test_each_p21_scenario_preserves_component_additivity(self):
        x = build_kehop_scope_crosswalk()
        for s in (x.central, x.flat):
            self.assertAlmostEqual(
                s.physical_family_definite_pre2007,
                s.nheat_family_definite_pre2007
                + s.central_family_definite_pre2007,
            )
            self.assertAlmostEqual(
                s.physical_family_possible_pre2007,
                s.nheat_family_possible_pre2007
                + s.central_family_possible_pre2007,
            )
            self.assertGreaterEqual(
                s.physical_family_possible_pre2007,
                s.physical_family_definite_pre2007,
            )

    def test_print_reproducible_crosswalk_for_registry_freeze(self):
        # This one-line deterministic JSON is intentionally emitted into CI
        # so P75 can freeze exact numeric results after the first clean run.
        print("B02_P75_CROSSWALK=" + json.dumps(as_log_dict(), sort_keys=True))


if __name__ == "__main__":
    unittest.main()
