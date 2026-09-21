import csv
import json
import unittest
from pathlib import Path

from modules.B02.kehop_scope_crosswalk import (
    build_kehop_scope_crosswalk,
    as_log_dict,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p75_kehop_scope_crosswalk.csv"
SOURCES = ROOT / "registry" / "sources.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P75_KEHOP_SCOPE_CROSSWALK.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


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
                delta=1e-6,
            )
            self.assertAlmostEqual(
                s.physical_family_possible_pre2007,
                s.nheat_family_possible_pre2007
                + s.central_family_possible_pre2007,
                delta=1e-6,
            )
            self.assertGreaterEqual(
                s.physical_family_possible_pre2007,
                s.physical_family_definite_pre2007,
            )

    def test_exact_ci_materialized_crosswalk_is_frozen(self):
        x = build_kehop_scope_crosswalk()
        self.assertAlmostEqual(
            x.structural_candidate_lower,
            1_902_145.42579707,
            delta=1e-6,
        )
        self.assertAlmostEqual(
            x.structural_candidate_upper,
            2_108_846.960997694,
            delta=1e-6,
        )
        self.assertAlmostEqual(
            x.proven_nonreuse_overlap_lower,
            784_618.1481627779,
            delta=1e-6,
        )
        self.assertAlmostEqual(
            x.possible_nonreuse_overlap_upper,
            2_108_846.960997694,
            delta=1e-6,
        )

    def test_registry_freezes_structural_not_legal_scope(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P75-K10"]["status"],
            "PARTIAL_RESOLVED_STRUCTURAL_BOUNDS",
        )
        self.assertEqual(
            reg["B02-P75-K06"]["lower_bound"],
            "1902145.425797070",
        )
        self.assertEqual(
            reg["B02-P75-K06"]["upper_bound"],
            "2108846.960997694",
        )
        self.assertIn(
            "LEGAL_ELIGIBLE_COUNT",
            reg["B02-P75-K06"]["forbidden_use"],
        )
        self.assertEqual(
            reg["B02-P75-K12"]["status"],
            "UNRESOLVED_AFTER_STRUCTURAL_CROSSWALK",
        )

    def test_combined_mfb_scope_source_is_registered(self):
        sources = rows(SOURCES, "source_id")
        src = sources["SRC-B02-HU-KEHOP-417-418-SCOPE-2026"]
        self.assertEqual(src["evidence_status"], "POL")
        self.assertEqual(src["reliability"], "HIGH")
        self.assertIn("4.1.7", src["reference_period"])
        self.assertIn("4.1.8", src["reference_period"])

    def test_q_and_readiness_keep_legal_boundary(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P75", q["notes"])
        self.assertIn("KEHOP_LEGAL_ELIGIBILITY_CONDITIONS", q["notes"])
        self.assertIn(
            "NONREUSE_OUTSIDE_KEHOP_STRUCTURAL_SCOPE_CAPEX_BOUND_REQUIRED",
            q["notes"],
        )
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P75", b02["gate_note"])

    def test_source_pack_preserves_no_false_precision_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "Y2001-2010 != PROVEN PRE-2007",
            "P21 FAMILY_HOUSE != LEGAL PROPERTY-REGISTER FAMILY-HOUSE CLASSIFICATION",
            "STRUCTURAL_SCOPE_COMPATIBILITY != LEGAL_PROGRAMME_ELIGIBILITY",
        ):
            self.assertIn(phrase, text)

    def test_print_reproducible_crosswalk_for_registry_freeze(self):
        # This one-line deterministic JSON is intentionally emitted into CI
        # so P75 can freeze exact numeric results after the first clean run.
        print("B02_P75_CROSSWALK=" + json.dumps(as_log_dict(), sort_keys=True))


if __name__ == "__main__":
    unittest.main()
