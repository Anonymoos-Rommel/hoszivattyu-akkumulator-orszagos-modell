import csv
import unittest
from pathlib import Path

from modules.B02.programme_envelope_action_assignment import (
    AIR_TO_WATER_HP_ONLY,
    REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
    SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
    ProgrammeActionAssignment,
    assess_national_envelope_action_assignment,
    current_kehop_policy_calibration,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p81_envelope_action_assignment.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P81_ENVELOPE_ACTION_ASSIGNMENT.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P81EnvelopeActionAssignmentTests(unittest.TestCase):
    def test_current_kehop_policy_is_scope_limited(self):
        out = current_kehop_policy_calibration()
        self.assertEqual(
            out.status,
            "QUALIFIED_SCOPE_LIMITED_POLICY_CALIBRATION",
        )
        self.assertEqual(out.construction_cutoff, "BUILT_AND_PERMITTED_BEFORE_2007")
        self.assertAlmostEqual(out.minimum_primary_energy_saving_share, 0.30)
        self.assertIn("AIR_TO_WATER_HEAT_PUMP", out.eligible_measure_families)
        self.assertIn("NATIONAL_ENVELOPE_ACTION_SHARE", out.forbidden_uses)

    def test_empty_assignment_fails_closed(self):
        out = assess_national_envelope_action_assignment(
            (),
            declared_programme_population=2_000_000,
        )
        self.assertEqual(out.status, "Q")
        self.assertIn("EXPLICIT_PROGRAMME_ACTION_ASSIGNMENT_REQUIRED", out.blockers)
        self.assertIn(
            "PROGRAMME_ACTION_ASSIGNMENT_MUST_CLOSE_TO_DECLARED_POPULATION",
            out.blockers,
        )

    def test_partial_assignment_does_not_default_remainder(self):
        out = assess_national_envelope_action_assignment(
            (
                ProgrammeActionAssignment(
                    population_key="GROUP-A",
                    assigned_dwelling_equivalents=1_200_000,
                    action=AIR_TO_WATER_HP_ONLY,
                    assignment_class=SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
                    authority="OWNER_APPROVED_SCENARIO",
                ),
            ),
            declared_programme_population=2_000_000,
        )
        self.assertEqual(out.status, "Q")
        self.assertAlmostEqual(out.coverage_share, 0.6)
        self.assertEqual(out.envelope_plus_awhp_population, 0.0)
        self.assertIn(
            "PROGRAMME_ACTION_ASSIGNMENT_MUST_CLOSE_TO_DECLARED_POPULATION",
            out.blockers,
        )

    def test_complete_explicit_scenario_assignment_passes(self):
        out = assess_national_envelope_action_assignment(
            (
                ProgrammeActionAssignment(
                    population_key="GROUP-A",
                    assigned_dwelling_equivalents=1_250_000,
                    action=AIR_TO_WATER_HP_ONLY,
                    assignment_class=SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
                    authority="OWNER_APPROVED_SCENARIO",
                ),
                ProgrammeActionAssignment(
                    population_key="GROUP-B",
                    assigned_dwelling_equivalents=750_000,
                    action=REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
                    assignment_class=SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
                    authority="OWNER_APPROVED_SCENARIO",
                ),
            ),
            declared_programme_population=2_000_000,
        )
        self.assertEqual(
            out.status,
            "QUALIFIED_EXPLICIT_PROGRAMME_SCENARIO_ASSIGNMENT",
        )
        self.assertAlmostEqual(out.coverage_share, 1.0)
        self.assertEqual(out.hp_only_population, 1_250_000)
        self.assertEqual(out.envelope_plus_awhp_population, 750_000)
        self.assertEqual(out.blockers, ())

    def test_duplicate_key_and_missing_authority_fail(self):
        out = assess_national_envelope_action_assignment(
            (
                ProgrammeActionAssignment(
                    population_key="GROUP-A",
                    assigned_dwelling_equivalents=1_000_000,
                    action=AIR_TO_WATER_HP_ONLY,
                    assignment_class=SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
                    authority="OWNER_APPROVED_SCENARIO",
                ),
                ProgrammeActionAssignment(
                    population_key="GROUP-A",
                    assigned_dwelling_equivalents=1_000_000,
                    action=REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
                    assignment_class=SCN_EXPLICIT_PROGRAMME_ASSIGNMENT,
                    authority="",
                ),
            ),
            declared_programme_population=2_000_000,
        )
        self.assertEqual(out.status, "Q")
        self.assertIn("DUPLICATE_POPULATION_KEY", out.blockers)
        self.assertIn("ASSIGNMENT_AUTHORITY_REQUIRED", out.blockers)

    def test_registry_narrows_blocker_without_minting_share(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P81-A06"]["status"],
            "PARTIAL_RESOLVED_CONTRACTED",
        )
        self.assertEqual(
            reg["B02-P81-A06"]["residual_gap"],
            "EXPLICIT_PROGRAMME_ACTION_ASSIGNMENT_REQUIRED",
        )
        self.assertEqual(reg["B02-P81-A07"]["status"], "OPEN_NARROWED")

    def test_source_pack_preserves_core_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "ELIGIBLE MEASURE MENU != NATIONAL ACTION ASSIGNMENT",
            "AGE / ELIGIBILITY SCOPE != ACTION FREQUENCY",
            "30% PRIMARY-ENERGY SAVING REQUIREMENT != ENVELOPE-RETROFIT SHARE",
            "PROGRAMME SCENARIO ASSIGNMENT != OBSERVED CURRENT STOCK",
            "INCOMPLETE ASSIGNMENT != HIDDEN DEFAULT",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
