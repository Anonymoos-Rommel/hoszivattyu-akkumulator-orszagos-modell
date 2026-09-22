import csv
import unittest
from pathlib import Path

from modules.B02.reference_programme_airtightness_target import (
    GOOD_AIRTIGHTNESS_MULTI_OR_SHAFT_NFILT_H,
    GOOD_AIRTIGHTNESS_ONE_FACADE_NFILT_H,
    MULTIPLE_FACADES_OR_VENTILATION_SHAFT,
    ONE_FACADE,
    QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET,
    REALIZED_AIRTIGHTNESS_VERIFICATION_REQUIRED,
    UNRESOLVED_FACADE_CONDITION,
    reference_programme_target_state,
    reference_programme_ventilation_target_surface,
    reference_target_infiltration_bound,
    semantic_boundaries,
)
from modules.B02.national_design_load_input_coverage import (
    QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE,
    current_design_load_blockers,
    national_design_load_input_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p90_reference_programme_airtightness_target.csv"
REG = ROOT / "registry" / "b02_p90_reference_programme_airtightness_target.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P90_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P90ReferenceProgrammeAirtightnessTargetTests(unittest.TestCase):
    def test_exact_current_method_target_cases(self):
        self.assertEqual(GOOD_AIRTIGHTNESS_ONE_FACADE_NFILT_H, 0.03)
        self.assertEqual(GOOD_AIRTIGHTNESS_MULTI_OR_SHAFT_NFILT_H, 0.06)

        one = reference_target_infiltration_bound(ONE_FACADE)
        self.assertEqual(one.lower_h, 0.03)
        self.assertEqual(one.upper_h, 0.03)

        multi = reference_target_infiltration_bound(
            MULTIPLE_FACADES_OR_VENTILATION_SHAFT
        )
        self.assertEqual(multi.lower_h, 0.06)
        self.assertEqual(multi.upper_h, 0.06)

        unresolved = reference_target_infiltration_bound(
            UNRESOLVED_FACADE_CONDITION
        )
        self.assertEqual(unresolved.lower_h, 0.03)
        self.assertEqual(unresolved.upper_h, 0.06)
        self.assertEqual(
            unresolved.status,
            QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET,
        )

        with self.assertRaises(ValueError):
            reference_target_infiltration_bound("MIDPOINT_DEFAULT")

    def test_fourteen_stratum_target_surface_is_exact(self):
        surface = reference_programme_ventilation_target_surface()
        self.assertEqual(len(surface), 14)
        self.assertEqual(
            {(row.wbl_period_code, row.building_group) for row in surface},
            {
                (period, group)
                for period in (
                    "Y_LT1919",
                    "Y1919-1945",
                    "Y1946-1960",
                    "Y1961-1980",
                    "Y1981-2000",
                    "Y2001-2010",
                    "Y_GE2011",
                )
                for group in ("FAMILY_HOUSE", "MULTI_DWELLING")
            },
        )
        self.assertAlmostEqual(
            min(row.h_vent_target_lower_w_per_k for row in surface),
            26.957426806,
        )
        self.assertAlmostEqual(
            max(row.h_vent_target_upper_w_per_k for row in surface),
            123.72696,
        )
        self.assertAlmostEqual(
            min(row.q_vent_target_lower_kw for row in surface),
            0.808722804,
        )
        self.assertAlmostEqual(
            max(row.q_vent_target_upper_kw for row in surface),
            3.95926272,
        )

    def test_materialized_csv_matches_runtime(self):
        data = rows(SURFACE)
        self.assertEqual(len(data), 14)
        self.assertEqual(
            {row["status"] for row in data},
            {"QUALIFIED_REFERENCE_PROGRAMME_AIRTIGHTNESS_TARGET"},
        )
        self.assertEqual(
            {float(row["n_filt_target_lower_h"]) for row in data},
            {0.03},
        )
        self.assertEqual(
            {float(row["n_filt_target_upper_h"]) for row in data},
            {0.06},
        )
        self.assertAlmostEqual(
            min(float(row["h_vent_target_lower_w_per_k"]) for row in data),
            26.957426806,
        )
        self.assertAlmostEqual(
            max(float(row["q_vent_target_upper_kw"]) for row in data),
            3.95926272,
        )

    def test_prospective_reference_programme_has_no_ventilation_blocker(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        vent = by["POST_RETROFIT_VENTILATION"]
        self.assertEqual(
            vent.status,
            QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE,
        )
        self.assertIsNone(vent.blocker)
        self.assertIn("B02-P90", vent.source_refs)

        blockers = set(current_design_load_blockers())
        self.assertNotIn(
            "POST_RETROFIT_ABSOLUTE_AIRTIGHTNESS_STATE_OR_PROGRAMME_TARGET_REQUIRED",
            blockers,
        )
        self.assertNotIn(
            REALIZED_AIRTIGHTNESS_VERIFICATION_REQUIRED,
            blockers,
        )
        self.assertNotIn("POST_RETROFIT_THERMAL_BRIDGE_SURFACE_REQUIRED", blockers)

    def test_target_state_keeps_realized_claim_separate(self):
        state = reference_programme_target_state()
        self.assertEqual(state["stratum_count"], 14)
        self.assertEqual(state["n_filt_target_lower_h"], 0.03)
        self.assertEqual(state["n_filt_target_upper_h"], 0.06)
        self.assertIsNone(state["prospective_reference_programme_blocker"])
        self.assertEqual(
            state["realized_claim_residual"],
            REALIZED_AIRTIGHTNESS_VERIFICATION_REQUIRED,
        )

    def test_registry_current_question_and_readiness_are_conservative(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P90-T06"]["status"],
            "RESOLVED_FOR_REFERENCE_PROGRAMME_SCENARIO",
        )
        self.assertEqual(
            reg["B02-P90-T07"]["status"],
            "RECORD_LEVEL_RESIDUAL",
        )
        self.assertEqual(
            reg["B02-P90-T08"]["status"],
            "QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE",
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P90", q["notes"])
        self.assertIn(
            "RESOLVED_FOR_REFERENCE_PROGRAMME_SCENARIO",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P90", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P90", peak["notes"])

    def test_source_non_equivalence_is_explicit(self):
        sources = rows(SOURCES, "source_id")
        self.assertIn(
            "P90 authority",
            sources["SRC-B06-HU-ENERGY-RULES-2023"]["notes"],
        )
        self.assertIn(
            "0.03/0.06",
            sources["SRC-B06-HU-ENERGY-METHOD-2023"]["notes"],
        )
        self.assertIn(
            "no building-level n50 target is stated",
            sources["SRC-B06-HU-OFP-KEHOP-2026"]["notes"],
        )

    def test_nonpromotion_boundaries_are_frozen(self):
        boundary = semantic_boundaries()
        for item in (
            "REFERENCE_PROGRAMME_TARGET_IS_NOT_OBSERVED_POST_RETROFIT_STATE",
            "REFERENCE_PROGRAMME_TARGET_IS_NOT_CURRENT_MFB_N50_REQUIREMENT",
            "GOOD_AIRTIGHTNESS_METHOD_CLASS_IS_NOT_BLOWER_DOOR_N50",
            "UNRESOLVED_FACADE_CONDITION_REMAINS_SET_VALUED_003_TO_006",
            "DESIGN_TARGET_IS_NOT_REALIZED_COMMISSIONED_PERFORMANCE",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "PROGRAMME TARGET != OBSERVED FUTURE STATE",
            "REFERENCE PROGRAMME TARGET != CURRENT MFB N50 REQUIREMENT",
            "B02 remains **55%**",
            "Q-B02-004",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
