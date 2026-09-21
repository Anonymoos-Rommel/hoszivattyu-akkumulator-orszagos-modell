import csv
import unittest
from pathlib import Path

from modules.B02.distribution_nonreuse_assignment import (
    PROGRAMME_ROUTE,
    NHEAT_NONREUSE_SHARE,
    build_nheat_nonreuse_authority,
    classify_heating_topology_for_programme,
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
REG = ROOT / "registry" / "b02_p70_ksh_nheat_nonreuse_floor.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P70_KSH_NHEAT_NONREUSE_FLOOR.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P70KshNheatNonreuseFloorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority = build_nheat_nonreuse_authority()

    def test_exact_p22_topology_controls_reconcile(self):
        a = self.authority
        self.assertEqual(a.occupied_dwellings, 4_008_541)
        self.assertEqual(a.nheat_dwellings, 1_173_639)
        self.assertEqual(a.central_dwellings, 2_216_178)
        self.assertEqual(a.district_dwellings, 618_724)
        self.assertEqual(
            a.central_dwellings + a.district_dwellings + a.nheat_dwellings,
            a.occupied_dwellings,
        )
        self.assertAlmostEqual(a.nheat_share, NHEAT_NONREUSE_SHARE)
        self.assertEqual(a.evidence_status, "DER")

    def test_nheat_is_qualified_nonreuse_only_for_authorized_programme_route(self):
        out = classify_heating_topology_for_programme(
            "ROOM_BY_ROOM_OR_NO_HEAT",
            programme_route=PROGRAMME_ROUTE,
        )
        self.assertEqual(out.status, "QUALIFIED")
        self.assertEqual(out.distribution_path, NEW_OR_REPLACE_DISTRIBUTION_REQUIRED)

        other = classify_heating_topology_for_programme(
            "ROOM_BY_ROOM_OR_NO_HEAT",
            programme_route="AIR_TO_AIR",
        )
        self.assertEqual(other.status, "Q")
        self.assertIn("PROGRAMME_ROUTE_NOT_P70_AUTHORIZED", other.blockers)

    def test_central_and_district_remain_unassigned(self):
        for topology in ("CENTRAL_HEATING", "DISTRICT_HEATING"):
            out = classify_heating_topology_for_programme(topology)
            self.assertEqual(out.status, "Q")
            self.assertIsNone(out.distribution_path)
            self.assertIn("CURRENT_DISTRIBUTION_REUSE_NOT_IDENTIFIED", out.blockers)

    def test_transition_envelope_uses_ksh_der_floor(self):
        e = build_distribution_path_envelope()
        self.assertAlmostEqual(
            e.new_or_replace_distribution_required.lower,
            1_173_639 / 3_389_817,
        )
        self.assertAlmostEqual(
            e.reuse_existing_distribution.upper,
            2_216_178 / 3_389_817,
        )
        self.assertEqual(e.evidence_status, "SET_IDENTIFIED_WITH_KSH_DER_NONREUSE_FLOOR")

        counts = distribution_count_bounds()
        self.assertAlmostEqual(counts[NEW_OR_REPLACE_DISTRIBUTION_REQUIRED][0], 1_173_639)
        self.assertAlmostEqual(counts[REUSE_EXISTING_DISTRIBUTION][1], 2_216_178)

    def test_old_233_candidate_now_fails_stronger_floor(self):
        result = assess_distribution_path_candidate(
            DistributionPathCandidate(
                reuse_share=0.767,
                new_or_replace_share=0.233,
            )
        )
        self.assertFalse(result.admissible)
        self.assertIn("NEW_OR_REPLACE_DISTRIBUTION_BELOW_KSH_NHEAT_FLOOR", result.blockers)

    def test_registry_records_der_floor_and_narrowed_residual(self):
        reg = rows(REG, "item_id")
        self.assertEqual(reg["B02-P70-N01"]["lower_bound"], "1173639")
        self.assertEqual(reg["B02-P70-N06"]["status"], "LOWER_BOUNDED")
        self.assertEqual(reg["B02-P70-N06"]["evidence_status"], "DER")
        self.assertIn(
            "CENTRAL_DISTRICT_REUSE_VS_NONREUSE_ASSIGNMENT",
            reg["B02-P70-N10"]["residual_gap"],
        )

    def test_q_b02_004_narrows_but_stays_open(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P70", q["notes"])
        self.assertIn("1 173 639", q["notes"])
        self.assertIn("CENTRAL_DISTRICT_REUSE_VS_NONREUSE_ASSIGNMENT", q["notes"])
        self.assertNotIn("Current residual: HUNGARIAN_DISTRIBUTION_NONREUSE_ASSIGNMENT +", q["notes"][-700:])

    def test_readiness_stays_fixed(self):
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P70", b02["gate_note"])
        self.assertIn("29.278458", b02["gate_note"])

    def test_source_pack_preserves_nonclaims(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "NHEAT -> NEW_OR_REPLACE_DISTRIBUTION_REQUIRED",
            "NHEAT FLOOR + GAS-CONVECTOR FLOOR != VALID UNION",
            "CENTRAL_DISTRICT_REUSE_VS_NONREUSE_ASSIGNMENT",
            "air-to-air",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
