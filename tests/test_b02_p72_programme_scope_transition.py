import csv
import unittest
from pathlib import Path

from modules.B02.programme_scope_transition import (
    CENTRAL_PROGRAMME_SCOPE_SHARE,
    NHEAT_PROGRAMME_SCOPE_SHARE,
    build_programme_scope_alignment,
    classify_topology_in_physical_scope,
)
from modules.B02.transition_set_propagation import (
    NEW_OR_REPLACE_DISTRIBUTION_REQUIRED,
    REUSE_EXISTING_DISTRIBUTION,
    DistributionPathCandidate,
    assess_distribution_path_candidate,
    build_distribution_path_envelope,
    distribution_count_bounds,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p72_programme_scope_transition.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P72_PROGRAMME_SCOPE_TRANSITION.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P72ProgrammeScopeTransitionTests(unittest.TestCase):
    def test_exact_scope_reconciliation(self):
        a = build_programme_scope_alignment()
        self.assertEqual(a.occupied_universe_dwellings, 4_008_541)
        self.assertEqual(a.district_out_of_physical_scope_dwellings, 618_724)
        self.assertEqual(a.physical_scope_dwellings, 3_389_817)
        self.assertEqual(a.nheat_dwellings, 1_173_639)
        self.assertEqual(a.central_heating_dwellings, 2_216_178)
        self.assertEqual(
            a.nheat_dwellings + a.central_heating_dwellings,
            a.physical_scope_dwellings,
        )
        self.assertAlmostEqual(a.nheat_scope_share, NHEAT_PROGRAMME_SCOPE_SHARE)
        self.assertAlmostEqual(a.central_scope_share, CENTRAL_PROGRAMME_SCOPE_SHARE)

    def test_district_is_out_of_physical_scope_not_technical_fail(self):
        out = classify_topology_in_physical_scope("DISTRICT_HEATING")
        self.assertEqual(out.status, "OUT_OF_PHYSICAL_SCREENING_SCOPE")
        self.assertFalse(out.in_physical_scope)
        self.assertIsNone(out.distribution_path)
        self.assertEqual(out.blockers, ())

    def test_nheat_is_in_scope_nonreuse(self):
        out = classify_topology_in_physical_scope("ROOM_BY_ROOM_OR_NO_HEAT")
        self.assertEqual(out.status, "IN_SCOPE_QUALIFIED_NONREUSE")
        self.assertTrue(out.in_physical_scope)
        self.assertEqual(
            out.distribution_path,
            NEW_OR_REPLACE_DISTRIBUTION_REQUIRED,
        )

    def test_central_is_only_remaining_distribution_residual(self):
        out = classify_topology_in_physical_scope("CENTRAL_HEATING")
        self.assertEqual(out.status, "IN_SCOPE_Q_REUSE_ADEQUACY")
        self.assertTrue(out.in_physical_scope)
        self.assertIn(
            "CENTRAL_HEATING_REUSE_VS_NONREUSE_ASSIGNMENT",
            out.blockers,
        )

    def test_transition_runtime_uses_physical_scope_denominator(self):
        e = build_distribution_path_envelope()
        self.assertEqual(e.programme_scope_dwellings, 3_389_817)
        self.assertEqual(e.source_occupied_universe_dwellings, 4_008_541)
        self.assertAlmostEqual(
            e.new_or_replace_distribution_required.lower,
            1_173_639 / 3_389_817,
        )
        self.assertAlmostEqual(
            e.reuse_existing_distribution.upper,
            2_216_178 / 3_389_817,
        )

        counts = distribution_count_bounds()
        self.assertAlmostEqual(
            counts[NEW_OR_REPLACE_DISTRIBUTION_REQUIRED][0],
            1_173_639,
        )
        self.assertAlmostEqual(
            counts[NEW_OR_REPLACE_DISTRIBUTION_REQUIRED][1],
            3_389_817,
        )
        self.assertAlmostEqual(
            counts[REUSE_EXISTING_DISTRIBUTION][1],
            2_216_178,
        )

    def test_old_full_universe_share_now_fails_programme_scope_floor(self):
        old_floor = 1_173_639 / 4_008_541
        result = assess_distribution_path_candidate(
            DistributionPathCandidate(
                reuse_share=1.0 - old_floor,
                new_or_replace_share=old_floor,
            )
        )
        self.assertFalse(result.admissible)
        self.assertIn(
            "NEW_OR_REPLACE_DISTRIBUTION_BELOW_KSH_NHEAT_FLOOR",
            result.blockers,
        )

    def test_registry_retires_scope_mixing_residual(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P72-S09"]["status"],
            "RETIRED_AS_SCOPE_MIXING",
        )
        self.assertEqual(
            reg["B02-P72-S05"]["lower_bound"],
            "2216178",
        )
        self.assertIn(
            "CENTRAL_HEATING_REUSE_VS_NONREUSE_ASSIGNMENT",
            reg["B02-P72-S10"]["residual_gap"],
        )

    def test_q_b02_004_is_narrowed_not_closed(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P72", q["notes"])
        self.assertIn("CENTRAL_HEATING_REUSE_VS_NONREUSE_ASSIGNMENT", q["notes"])
        self.assertIn("3 389 817", q["notes"])

    def test_readiness_remains_fixed(self):
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P72", b02["gate_note"])

    def test_source_pack_preserves_scope_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "FULL OCCUPIED UNIVERSE != B02 PHYSICAL-SCREENING DENOMINATOR",
            "OUT_OF_PHYSICAL_SCREENING_SCOPE != TECHNICALLY_INELIGIBLE",
            "CENTRAL_HEATING_REUSE_VS_NONREUSE_ASSIGNMENT",
            "34.622488%",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
