import csv
import unittest
from pathlib import Path

from modules.B02.distribution_nonreuse_assignment import (
    CENTRAL_HYDRONIC_AWHP,
    Q,
    assess_programme_route,
    build_distribution_nonreuse_assignment,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p70_ksh_nheat_distribution_nonreuse.csv"
SOURCES = ROOT / "registry" / "sources.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P70_KSH_NHEAT_DISTRIBUTION_NONREUSE.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P70KshNheatDistributionNonreuseTests(unittest.TestCase):
    def test_route_is_explicitly_bounded(self):
        self.assertEqual(
            assess_programme_route(CENTRAL_HYDRONIC_AWHP).status,
            "QUALIFIED",
        )
        blocked = assess_programme_route("AIR_TO_AIR_HEAT_PUMP")
        self.assertEqual(blocked.status, Q)
        self.assertIn(
            "P70_ONLY_AUTHORIZES_CENTRAL_HYDRONIC_AWHP_ROUTE",
            blocked.blockers,
        )

    def test_p22_nheat_exact_population_control(self):
        a = build_distribution_nonreuse_assignment()
        self.assertEqual(a.occupied_dwellings, 4_008_541)
        self.assertEqual(a.room_by_room_or_no_heat_dwellings, 1_173_639)
        self.assertAlmostEqual(a.room_by_room_or_no_heat_share, 0.292784581722, places=12)

    def test_nheat_strengthens_gas_convector_floor(self):
        a = build_distribution_nonreuse_assignment()
        self.assertGreater(
            a.room_by_room_or_no_heat_share,
            a.gas_convector_calibrated_share,
        )
        self.assertAlmostEqual(
            a.proven_nonreuse_lower_share,
            a.room_by_room_or_no_heat_share,
        )
        self.assertEqual(a.proven_nonreuse_lower_dwellings, 1_173_639)
        self.assertAlmostEqual(a.reuse_upper_share, 0.707215418278, places=12)

    def test_nonreuse_floor_uses_max_not_sum(self):
        a = build_distribution_nonreuse_assignment()
        self.assertAlmostEqual(
            a.proven_nonreuse_lower_share,
            max(a.room_by_room_or_no_heat_share, a.gas_convector_calibrated_share),
        )
        self.assertLess(
            a.proven_nonreuse_lower_share,
            a.room_by_room_or_no_heat_share + a.gas_convector_calibrated_share,
        )

    def test_assignment_is_der_route_conditional_lower_bound(self):
        a = build_distribution_nonreuse_assignment()
        self.assertEqual(a.route_status, "QUALIFIED")
        self.assertEqual(a.evidence_status, "DER_ROUTE_CONDITIONAL_LOWER_BOUND")

    def test_registry_freezes_exact_nheat_and_residual(self):
        reg = rows(REG, "item_id")
        self.assertEqual(reg["B02-P70-D02"]["lower_bound"], "1173639")
        self.assertEqual(reg["B02-P70-D03"]["lower_bound"], "0.292784582")
        self.assertEqual(reg["B02-P70-D05"]["status"], "LOWER_BOUNDED")
        self.assertEqual(reg["B02-P70-D06"]["lower_bound"], "1173639")
        self.assertIn(
            "CENTRAL_AND_DISTRICT_DISTRIBUTION_REUSE_VS_NEW_OR_REPLACE_ASSIGNMENT",
            reg["B02-P70-D09"]["residual_gap"],
        )

    def test_ksh_definition_source_is_registered(self):
        src = rows(SOURCES, "source_id")["SRC-B02-KSH-CENSUS-DEFINITIONS-2022"]
        self.assertEqual(src["institution"], "Központi Statisztikai Hivatal")
        self.assertEqual(src["reliability"], "HIGH")
        self.assertIn("room heating", src["notes"])
        self.assertIn("CENTRAL_HYDRONIC_AWHP", src["notes"])

    def test_q_b02_004_is_narrowed_not_closed(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P70", q["notes"])
        self.assertIn("1 173 639", q["notes"])
        self.assertIn(
            "CENTRAL_AND_DISTRICT_DISTRIBUTION_REUSE_VS_NEW_OR_REPLACE_ASSIGNMENT",
            q["notes"],
        )

    def test_readiness_remains_fixed(self):
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P70", b02["gate_note"])
        self.assertIn("29.278458%", b02["gate_note"])

    def test_source_pack_freezes_non_equivalence_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "NHEAT -> NEW_OR_REPLACE_DISTRIBUTION_REQUIRED",
            "max(NHEAT_SHARE, GAS_CONVECTOR_SHARE)",
            "1,173,639",
            "CENTRAL_AND_DISTRICT_DISTRIBUTION_REUSE_VS_NEW_OR_REPLACE_ASSIGNMENT",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
