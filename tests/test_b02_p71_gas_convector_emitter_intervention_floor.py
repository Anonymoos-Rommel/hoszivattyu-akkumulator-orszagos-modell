import csv
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    GAS_CONVECTOR,
    NON_HYDRONIC_ROOM_HEATING,
    QUALIFIED,
    REPLACE_EXISTING_DISTRIBUTION,
)
from modules.B02.emitter_intervention_assignment import (
    PROGRAMME_ROUTE,
    assess_gas_convector_emitter_requirement,
    build_gas_convector_emitter_intervention_floor,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p71_gas_convector_emitter_intervention_floor.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P71_GAS_CONVECTOR_EMITTER_INTERVENTION_FLOOR.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P71GasConvectorEmitterInterventionFloorTests(unittest.TestCase):
    def test_exact_calibrated_lower_bound_is_preserved(self):
        e = build_gas_convector_emitter_intervention_floor()
        self.assertEqual(e.occupied_dwellings, 4_008_541)
        self.assertEqual(e.required_share_lower, 0.233)
        self.assertAlmostEqual(
            e.required_expected_dwelling_equivalents_lower,
            933_990.053,
        )
        self.assertEqual(e.evidence_status, "ASS")
        self.assertEqual(e.authority_status, "QUALIFIED_LOWER_BOUND")

    def test_proven_gas_convector_route_requires_new_hydronic_emission(self):
        result = assess_gas_convector_emitter_requirement(
            current_emitter_type=GAS_CONVECTOR,
            emitter_category_authority_status=QUALIFIED,
            current_distribution_topology=NON_HYDRONIC_ROOM_HEATING,
            transition_path=REPLACE_EXISTING_DISTRIBUTION,
            programme_route=PROGRAMME_ROUTE,
        )
        self.assertEqual(
            result.status,
            "QUALIFIED_NEW_HYDRONIC_HEAT_EMISSION_REQUIRED",
        )
        self.assertTrue(result.new_hydronic_heat_emission_required)
        self.assertEqual(result.blockers, ())

    def test_non_gas_convector_does_not_inherit_requirement(self):
        result = assess_gas_convector_emitter_requirement(
            current_emitter_type="RADIATOR",
            emitter_category_authority_status=QUALIFIED,
            current_distribution_topology=NON_HYDRONIC_ROOM_HEATING,
            transition_path=REPLACE_EXISTING_DISTRIBUTION,
        )
        self.assertEqual(result.status, "Q")
        self.assertIsNone(result.new_hydronic_heat_emission_required)
        self.assertIn("CURRENT_EMITTER_NOT_GAS_CONVECTOR", result.blockers)

    def test_cross_route_promotion_fails_closed(self):
        result = assess_gas_convector_emitter_requirement(
            current_emitter_type=GAS_CONVECTOR,
            emitter_category_authority_status=QUALIFIED,
            current_distribution_topology=NON_HYDRONIC_ROOM_HEATING,
            transition_path=REPLACE_EXISTING_DISTRIBUTION,
            programme_route="AIR_TO_AIR",
        )
        self.assertEqual(result.status, "Q")
        self.assertIn("PROGRAMME_ROUTE_NOT_P71_AUTHORIZED", result.blockers)

    def test_registry_keeps_household_and_unit_grains_separate(self):
        reg = rows(REG, "item_id")
        self.assertEqual(reg["B02-P71-E04"]["status"], "LOWER_BOUNDED")
        self.assertEqual(reg["B02-P71-E04"]["lower_bound"], "0.233")
        self.assertIn(
            "NEW_RADIATOR_UNIT_SHARE",
            reg["B02-P71-E04"]["forbidden_use"],
        )
        self.assertIn(
            "NON_GAS_CONVECTOR_EMITTER_INTERVENTION_ASSIGNMENT",
            reg["B02-P71-E06"]["residual_gap"],
        )

    def test_p70_nheat_is_not_promoted_to_emitter_share(self):
        reg = rows(REG, "item_id")
        guard = reg["B02-P71-E07"]
        self.assertEqual(guard["claim"], "P70_NHEAT_NONREUSE_NOT_EMITTER_PROMOTION")
        self.assertIn(
            "NHEAT_SHARE_EQUALS_NEW_EMITTER_SHARE",
            guard["forbidden_use"],
        )

    def test_q_b02_004_is_narrowed_but_open(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P71", q["notes"])
        self.assertIn("PARTIAL_RESOLVED_LOWER_BOUND", q["notes"])
        self.assertIn("NON_GAS_CONVECTOR_EMITTER_INTERVENTION_ASSIGNMENT", q["notes"])

    def test_readiness_remains_55(self):
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P71", b02["gate_note"])

    def test_source_pack_preserves_grain_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "NEW_HYDRONIC_HEAT_EMISSION_SYSTEM_REQUIRED_SHARE >= 0.233",
            "DWELLING REQUIRES NEW HYDRONIC HEAT-EMISSION SYSTEM != EMITTER UNIT COUNT",
            "NHEAT NONREUSE FLOOR != NEW EMITTER UNIT FLOOR",
            "NON_GAS_CONVECTOR_EMITTER_INTERVENTION_ASSIGNMENT",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
