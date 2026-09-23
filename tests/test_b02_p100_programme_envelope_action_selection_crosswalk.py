import csv
import unittest
from pathlib import Path

from modules.B02.national_design_load_input_coverage import (
    QUALIFIED_ACTION_SELECTION_CROSSWALK,
    current_design_load_blockers,
    national_design_load_input_coverage,
)
from modules.B02.programme_envelope_action_selection_crosswalk import (
    COMPONENT_NOT_APPLICABLE,
    CURRENT_ENVELOPE_STATE_UNRESOLVED,
    HP_ONLY_CANDIDATE,
    NEXT_RESIDUAL,
    P100_STATUS,
    PROGRAMME_ACTION_UNRESOLVED,
    REFERENCE_COMPONENT_U_MAX,
    REFERENCE_ENVELOPE_DEFICIT,
    REFERENCE_ENVELOPE_SATISFIED,
    RETROFIT_PLUS_AWHP_REQUIRED,
    PopulationSelectionRecord,
    assess_component_against_reference,
    bounded_population_action_shares,
    p100_state,
    p99_stock_state_selection_crosswalk,
    select_programme_action,
    semantic_boundaries,
)
from modules.B02.keop23_uvalue_poststate import (
    AIR_TO_WATER_HP_ONLY,
    REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT / "data" / "processed" / "b02"
    / "p100_programme_envelope_action_selection_crosswalk.csv"
)
REG = (
    ROOT / "registry"
    / "b02_p100_programme_envelope_action_selection_crosswalk.csv"
)
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = (
    ROOT / "docs" / "source_packs"
    / "B02_P100_PROGRAMME_ENVELOPE_ACTION_SELECTION_CROSSWALK.md"
)


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P100ProgrammeEnvelopeActionSelectionCrosswalkTests(unittest.TestCase):
    def test_reference_component_targets_are_exact(self):
        self.assertEqual(
            REFERENCE_COMPONENT_U_MAX,
            {
                "EXTERNAL_WALL": 0.24,
                "FLAT_ROOF": 0.17,
                "ATTIC_FLOOR": 0.17,
                "BASEMENT_CEILING": 0.26,
                "WINDOW": 1.15,
                "PITCHED_ROOF": 0.17,
            },
        )

    def test_component_selection_is_interval_safe(self):
        satisfied = assess_component_against_reference(
            component="EXTERNAL_WALL",
            current_u_lower_w_m2k=0.18,
            current_u_upper_w_m2k=0.24,
            evidence_status="DER",
        )
        self.assertEqual(satisfied.state, REFERENCE_ENVELOPE_SATISFIED)

        deficit = assess_component_against_reference(
            component="WINDOW",
            current_u_lower_w_m2k=1.2,
            current_u_upper_w_m2k=1.4,
            evidence_status="DER",
        )
        self.assertEqual(deficit.state, REFERENCE_ENVELOPE_DEFICIT)

        straddling = assess_component_against_reference(
            component="ATTIC_FLOOR",
            current_u_lower_w_m2k=0.15,
            current_u_upper_w_m2k=0.25,
        )
        self.assertEqual(straddling.state, CURRENT_ENVELOPE_STATE_UNRESOLVED)
        self.assertIn(
            "CURRENT_COMPONENT_U_INTERVAL_STRADDLES_REFERENCE_LIMIT",
            straddling.blockers,
        )

        missing = assess_component_against_reference(
            component="BASEMENT_CEILING",
            current_u_lower_w_m2k=None,
            current_u_upper_w_m2k=None,
        )
        self.assertEqual(missing.state, CURRENT_ENVELOPE_STATE_UNRESOLVED)

        na = assess_component_against_reference(
            component="FLAT_ROOF",
            current_u_lower_w_m2k=None,
            current_u_upper_w_m2k=None,
            applicable=False,
        )
        self.assertEqual(na.state, COMPONENT_NOT_APPLICABLE)

        with self.assertRaises(ValueError):
            assess_component_against_reference(
                component="EXTERNAL_WALL",
                current_u_lower_w_m2k=0.4,
                current_u_upper_w_m2k=0.2,
            )

    def _full_satisfied(self):
        return tuple(
            assess_component_against_reference(
                component=component,
                current_u_lower_w_m2k=target * 0.8,
                current_u_upper_w_m2k=target,
                evidence_status="DER",
            )
            for component, target in REFERENCE_COMPONENT_U_MAX.items()
        )

    def test_dwelling_action_selection_is_fail_closed(self):
        hp = select_programme_action(self._full_satisfied())
        self.assertEqual(hp.selection_state, HP_ONLY_CANDIDATE)
        self.assertEqual(hp.programme_action, AIR_TO_WATER_HP_ONLY)

        deficit_rows = list(self._full_satisfied())
        deficit_rows[0] = assess_component_against_reference(
            component="EXTERNAL_WALL",
            current_u_lower_w_m2k=0.30,
            current_u_upper_w_m2k=0.40,
        )
        retrofit = select_programme_action(tuple(deficit_rows))
        self.assertEqual(retrofit.selection_state, RETROFIT_PLUS_AWHP_REQUIRED)
        self.assertEqual(
            retrofit.programme_action,
            REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
        )

        unresolved_rows = list(self._full_satisfied())
        unresolved_rows[0] = assess_component_against_reference(
            component="EXTERNAL_WALL",
            current_u_lower_w_m2k=None,
            current_u_upper_w_m2k=None,
        )
        unresolved = select_programme_action(tuple(unresolved_rows))
        self.assertEqual(unresolved.selection_state, PROGRAMME_ACTION_UNRESOLVED)
        self.assertIsNone(unresolved.programme_action)

        incomplete = select_programme_action(self._full_satisfied()[:-1])
        self.assertEqual(incomplete.selection_state, PROGRAMME_ACTION_UNRESOLVED)
        self.assertTrue(
            any(x.startswith("MISSING_COMPONENT_STATE:") for x in incomplete.blockers)
        )

    def test_population_uncertainty_is_propagated_not_split(self):
        out = bounded_population_action_shares(
            (
                PopulationSelectionRecord("A", 20.0, HP_ONLY_CANDIDATE),
                PopulationSelectionRecord("B", 30.0, RETROFIT_PLUS_AWHP_REQUIRED),
                PopulationSelectionRecord("C", 50.0, PROGRAMME_ACTION_UNRESOLVED),
            )
        )
        self.assertEqual(out.status, "PARTIAL_BOUNDED_PROGRAMME_ACTION_SELECTION")
        self.assertAlmostEqual(out.hp_only_share_lower, 0.20)
        self.assertAlmostEqual(out.hp_only_share_upper, 0.70)
        self.assertAlmostEqual(out.retrofit_share_lower, 0.30)
        self.assertAlmostEqual(out.retrofit_share_upper, 0.80)
        self.assertEqual(out.residual, NEXT_RESIDUAL)

        closed = bounded_population_action_shares(
            (
                PopulationSelectionRecord("A", 20.0, HP_ONLY_CANDIDATE),
                PopulationSelectionRecord("B", 80.0, RETROFIT_PLUS_AWHP_REQUIRED),
            )
        )
        self.assertEqual(
            closed.status,
            "QUALIFIED_COMPLETE_PROGRAMME_ACTION_SELECTION",
        )
        self.assertIsNone(closed.residual)
        self.assertAlmostEqual(closed.hp_only_share_lower, 0.20)
        self.assertAlmostEqual(closed.hp_only_share_upper, 0.20)

    def test_p99_stock_state_is_not_promoted_to_programme_selection(self):
        rows_ = p99_stock_state_selection_crosswalk()
        self.assertEqual(len(rows_), 3)
        self.assertEqual({row.selection_authority for row in rows_}, {False})
        self.assertEqual(
            {row.status for row in rows_},
            {"CALIBRATION_ONLY_NOT_PROGRAMME_SELECTION_AUTHORITY"},
        )
        self.assertEqual(
            {round(row.share, 3) for row in rows_},
            {0.350, 0.297, 0.527},
        )
        self.assertEqual({row.blocker for row in rows_}, {NEXT_RESIDUAL})

    def test_runtime_and_materialized_crosswalk_match(self):
        data = rows(DATA, "item_id")
        self.assertEqual(float(data["B02-P100-T01"]["upper_value"]), 0.24)
        self.assertEqual(float(data["B02-P100-T04"]["upper_value"]), 0.17)
        self.assertEqual(float(data["B02-P100-T06"]["upper_value"]), 1.15)
        self.assertEqual(data["B02-P100-S01"]["selection_authority"], "NO")
        self.assertEqual(
            data["B02-P100-S01"]["residual_gap"],
            NEXT_RESIDUAL,
        )

        state = p100_state()
        self.assertEqual(state["status"], P100_STATUS)
        self.assertIsNone(state["crosswalk_blocker"])
        self.assertEqual(
            state["remaining_population_evidence_residual"],
            NEXT_RESIDUAL,
        )
        self.assertFalse(state["national_programme_action_point_share_identified"])

    def test_stale_generic_action_mapping_blocker_is_removed(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        action = by["ACTION_TO_POST_STATE_PHYSICS"]
        self.assertEqual(action.status, QUALIFIED_ACTION_SELECTION_CROSSWALK)
        self.assertIsNone(action.blocker)
        self.assertIn("B02-P100", action.source_refs)

        blockers = set(current_design_load_blockers())
        self.assertNotIn("ACTION_TO_POST_STATE_PHYSICAL_MAPPING_REQUIRED", blockers)
        self.assertEqual(
            blockers,
            {"HEATED_AREA_OR_DIRECT_GEOMETRY_SURFACE_REQUIRED"},
        )

    def test_registry_and_project_state_are_narrowed_not_closed(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P100-C01"]["status"],
            "RESOLVED_EXECUTABLE_CROSSWALK",
        )
        self.assertEqual(
            reg["B02-P100-C07"]["residual_gap"],
            NEXT_RESIDUAL,
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P100", q["notes"])
        self.assertIn("RESOLVED_EXECUTABLE_CROSSWALK", q["notes"])
        self.assertIn(NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P100", module["gate_note"])
        self.assertIn(NEXT_RESIDUAL, module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P100", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        boundaries = semantic_boundaries()
        for item in (
            "INSULATED_FACADE_IS_NOT_REFERENCE_U_COMPLIANT_WALL",
            "WINDOW_REPLACED_IS_NOT_REFERENCE_U_COMPLIANT_WINDOW",
            "REFERENCE_ENVELOPE_SATISFIED_IS_NOT_TECHNICAL_HP_ELIGIBILITY",
            "HP_ONLY_CANDIDATE_IS_NOT_FINAL_PROGRAMME_ELIGIBILITY",
            "UNRESOLVED_IS_NOT_RETROFIT_REQUIRED",
        ):
            self.assertIn(item, boundaries)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "INSULATED FACADE != REFERENCE U COMPLIANT WALL",
            "WINDOW REPLACED != REFERENCE U COMPLIANT WINDOW",
            "UNKNOWN != DEFICIT",
            "AIR_TO_WATER_HP_ONLY candidate",
            "DEFENSIBLE_CURRENT_BASELINE_U_INFERENCE_REQUIRED",
            "B02 remains **55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
