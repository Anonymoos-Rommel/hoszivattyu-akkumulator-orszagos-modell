import csv
import unittest
from pathlib import Path

from modules.B02.current_legal_envelope_uvalues import (
    AIR_TO_WATER_HP_ONLY,
    APPLICABLE_PROTECTION_EXEMPTION,
    CURRENT_EKM_REGIME,
    EXEMPTION_STATUS_UNKNOWN,
    LEGACY_TNM_PROGRAM_REGIME,
    NO_APPLICABLE_EXEMPTION,
    QUALIFIED_CURRENT_LEGAL_U_REQUIREMENT,
    REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
    assess_action_legal_envelope_mapping,
    assess_national_current_legal_u_surface,
    current_legal_u_requirement,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p81_current_legal_envelope_uvalues.csv"
P80 = ROOT / "registry" / "b02_p80_keop23_uvalue_poststate.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P81_CURRENT_LEGAL_ENVELOPE_UVALUES.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P81CurrentLegalEnvelopeUValueTests(unittest.TestCase):
    def test_all_p80_components_have_current_legal_requirement(self):
        expected = {
            "EXTERNAL_WALL": 0.24,
            "FLAT_ROOF": 0.17,
            "PITCHED_ROOF": 0.17,
            "ATTIC_FLOOR": 0.17,
            "BASEMENT_CEILING": 0.26,
            "WINDOW": 1.10,
        }
        for component, upper in expected.items():
            out = current_legal_u_requirement(
                component,
                affected_by_energy_saving_renovation=True,
                protection_exemption_status=NO_APPLICABLE_EXEMPTION,
                legal_regime=CURRENT_EKM_REGIME,
            )
            self.assertEqual(out.status, QUALIFIED_CURRENT_LEGAL_U_REQUIREMENT)
            self.assertEqual(out.upper_u_w_m2k, upper)
            self.assertEqual(out.blockers, ())

    def test_unaffected_component_does_not_inherit_requirement(self):
        out = current_legal_u_requirement(
            "EXTERNAL_WALL",
            affected_by_energy_saving_renovation=False,
        )
        self.assertEqual(out.status, "NOT_APPLICABLE_UNTOUCHED_COMPONENT")
        self.assertIsNone(out.upper_u_w_m2k)
        self.assertEqual(out.blockers, ())

    def test_protection_exception_fails_closed(self):
        out = current_legal_u_requirement(
            "EXTERNAL_WALL",
            affected_by_energy_saving_renovation=True,
            protection_exemption_status=APPLICABLE_PROTECTION_EXEMPTION,
        )
        self.assertEqual(out.status, "Q")
        self.assertIn(
            "HERITAGE_OR_LOCAL_PROTECTION_EXCEPTION_APPLIES",
            out.blockers,
        )

        unknown = current_legal_u_requirement(
            "EXTERNAL_WALL",
            affected_by_energy_saving_renovation=True,
            protection_exemption_status=EXEMPTION_STATUS_UNKNOWN,
        )
        self.assertEqual(unknown.status, "Q")
        self.assertIn("PROTECTION_EXCEPTION_STATUS_REQUIRED", unknown.blockers)

    def test_legacy_program_regime_fails_closed(self):
        out = current_legal_u_requirement(
            "EXTERNAL_WALL",
            affected_by_energy_saving_renovation=True,
            legal_regime=LEGACY_TNM_PROGRAM_REGIME,
        )
        self.assertEqual(out.status, "Q")
        self.assertIn(
            "LEGACY_TNM_SUPPORTED_PROGRAM_REQUIREMENT_APPLIES",
            out.blockers,
        )

    def test_hp_only_does_not_trigger_envelope_legal_requirement(self):
        out = assess_action_legal_envelope_mapping(
            action=AIR_TO_WATER_HP_ONLY,
            envelope_component_is_affected=False,
        )
        self.assertEqual(
            out.status,
            "NO_ENVELOPE_LEGAL_U_TRIGGER_FROM_HP_ONLY_ACTION",
        )
        self.assertEqual(out.blockers, ())

    def test_reference_retrofit_plus_awhp_maps_to_current_legal_scope(self):
        out = assess_action_legal_envelope_mapping(
            action=REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
            envelope_component_is_affected=True,
        )
        self.assertEqual(
            out.status,
            "QUALIFIED_ACTION_TO_CURRENT_LEGAL_ENVELOPE_REQUIREMENT",
        )

    def test_national_surface_still_needs_assignment_exceptions_baseline_area(self):
        out = assess_national_current_legal_u_surface(
            national_affected_component_assignment_materialized=False,
            legal_exception_regime_materialized=False,
            current_no_action_baseline_materialized=False,
            component_area_surface_materialized=False,
        )
        self.assertEqual(out.status, "Q")
        self.assertEqual(
            out.blockers,
            (
                "NATIONAL_AFFECTED_ENVELOPE_COMPONENT_ASSIGNMENT_REQUIRED",
                "NATIONAL_LEGAL_ENVELOPE_EXCEPTION_REGIME_REQUIRED",
                "CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED",
                "COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED",
            ),
        )

    def test_registry_resolves_pitched_roof_gap_for_current_legal_scope(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P81-L08"]["status"],
            "RESOLVED_BY_CURRENT_LEGAL_AUTHORITY",
        )
        self.assertEqual(reg["B02-P81-L08"]["upper_bound"], "0.17")
        self.assertEqual(
            reg["B02-P81-L12"]["status"],
            "PARTIAL_RESOLVED_CURRENT_LEGAL_ACTION_CONDITIONED",
        )

    def test_p80_current_state_is_superseded_not_deleted(self):
        p80 = rows(P80, "item_id")
        self.assertEqual(
            p80["B02-P80-U12"]["status"],
            "SUPERSEDED_BY_P81_CURRENT_STATE",
        )

    def test_q_and_readiness_remain_fail_closed(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P81", q["notes"])
        self.assertIn(
            "NATIONAL_AFFECTED_ENVELOPE_COMPONENT_ASSIGNMENT_REQUIRED",
            q["notes"],
        )
        self.assertIn(
            "NATIONAL_LEGAL_ENVELOPE_EXCEPTION_REGIME_REQUIRED",
            q["notes"],
        )

        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P81", b02["gate_note"])

    def test_source_pack_preserves_legal_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "CURRENT LEGAL U REQUIREMENT != CURRENT STOCK U OBSERVATION",
            "LEGAL REQUIREMENT FOR AFFECTED COMPONENT != REQUIREMENT FOR UNTOUCHED COMPONENT",
            "LEGAL U-MAX != REALIZED POST-RETROFIT U POINT",
            "HP_ONLY -> NO ENVELOPE LEGAL U TRIGGER",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
