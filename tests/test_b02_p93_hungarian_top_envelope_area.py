import csv
import unittest
from pathlib import Path

from modules.B02.hungarian_top_envelope_area import (
    FAMILY_HOUSE,
    MULTI_DWELLING,
    QUALIFIED_HUNGARIAN_TOP_ENVELOPE_AREA_PROXY,
    TABULA_HU_AB_TOP_TO_CONDITIONED_FLOOR_RATIO,
    TABULA_HU_MFH_TOP_TO_CONDITIONED_FLOOR_RATIO,
    TABULA_HU_SFH_TOP_TO_CONDITIONED_FLOOR_RATIO,
    p93_state,
    reference_programme_top_envelope_surface,
    semantic_boundaries,
    top_area_ratio_bound,
    top_envelope_area_bound,
)
from modules.B02.national_design_load_input_coverage import (
    PARTIAL_HUNGARIAN_FACADE_TOP_BOTTOM_GEOMETRY_PROXY,
    national_design_load_input_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p93_hungarian_top_envelope_area.csv"
REG = ROOT / "registry" / "b02_p93_hungarian_top_envelope_area.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P93_HUNGARIAN_TOP_ENVELOPE_AREA.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P93HungarianTopEnvelopeAreaTests(unittest.TestCase):
    def test_exact_published_hungarian_ratios(self):
        self.assertEqual(
            TABULA_HU_SFH_TOP_TO_CONDITIONED_FLOOR_RATIO,
            0.84,
        )
        self.assertEqual(
            TABULA_HU_MFH_TOP_TO_CONDITIONED_FLOOR_RATIO,
            0.35,
        )
        self.assertEqual(
            TABULA_HU_AB_TOP_TO_CONDITIONED_FLOOR_RATIO,
            0.20,
        )

    def test_group_mapping_preserves_set_semantics(self):
        family = top_area_ratio_bound(FAMILY_HOUSE)
        self.assertEqual(family.source_classes, ("HU_SFH",))
        self.assertEqual((family.lower, family.upper), (0.84, 0.84))

        multi = top_area_ratio_bound(MULTI_DWELLING)
        self.assertEqual(multi.source_classes, ("HU_MFH", "HU_AB"))
        self.assertEqual((multi.lower, multi.upper), (0.20, 0.35))

        with self.assertRaises(ValueError):
            top_area_ratio_bound("TERRACED_HOUSE_POINT_DEFAULT")

    def test_scaling_uses_heated_floor_area_not_absolute_example_area(self):
        family = top_envelope_area_bound(
            heated_floor_area_lower_m2=100.0,
            heated_floor_area_upper_m2=200.0,
            building_group=FAMILY_HOUSE,
        )
        self.assertAlmostEqual(family.top_area_lower_m2, 84.0)
        self.assertAlmostEqual(family.top_area_upper_m2, 168.0)

        multi = top_envelope_area_bound(
            heated_floor_area_lower_m2=100.0,
            heated_floor_area_upper_m2=200.0,
            building_group=MULTI_DWELLING,
        )
        self.assertAlmostEqual(multi.top_area_lower_m2, 20.0)
        self.assertAlmostEqual(multi.top_area_upper_m2, 70.0)

    def test_fourteen_stratum_surface_and_global_extrema(self):
        surface = reference_programme_top_envelope_surface()
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
                for group in (FAMILY_HOUSE, MULTI_DWELLING)
            },
        )
        self.assertAlmostEqual(
            min(row.top_envelope_area_lower_m2_per_dwelling for row in surface),
            10.96777777778,
            places=9,
        )
        self.assertAlmostEqual(
            max(row.top_envelope_area_upper_m2_per_dwelling for row in surface),
            196.392,
            places=9,
        )

    def test_materialized_csv_matches_runtime(self):
        data = rows(SURFACE)
        self.assertEqual(len(data), 14)
        self.assertEqual(
            {row["status"] for row in data},
            {"QUALIFIED_HUNGARIAN_TOP_ENVELOPE_AREA_PROXY"},
        )
        self.assertAlmostEqual(
            min(float(row["top_envelope_area_lower_m2_per_dwelling"]) for row in data),
            10.96777777778,
        )
        self.assertAlmostEqual(
            max(float(row["top_envelope_area_upper_m2_per_dwelling"]) for row in data),
            196.392,
        )

    def test_current_geometry_coverage_includes_p93_but_stays_partial(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        geometry = by["POST_RETROFIT_ENVELOPE_GEOMETRY"]
        self.assertEqual(
            geometry.status,
            PARTIAL_HUNGARIAN_FACADE_TOP_BOTTOM_GEOMETRY_PROXY,
        )
        self.assertEqual(
            geometry.blocker,
            "POST_RETROFIT_ENVELOPE_GEOMETRY_SURFACE_REQUIRED",
        )
        self.assertIn("B02-P92", geometry.source_refs)
        self.assertIn("B02-P93", geometry.source_refs)

    def test_state_retires_only_top_area_blocker(self):
        state = p93_state()
        self.assertEqual(state["stratum_count"], 14)
        self.assertEqual(
            state["status"],
            QUALIFIED_HUNGARIAN_TOP_ENVELOPE_AREA_PROXY,
        )
        self.assertIsNone(state["split_blocker"])
        self.assertIn(
            "ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED",
            state["remaining_geometry_residuals"],
        )
        self.assertIn(
            "BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED",
            state["remaining_geometry_residuals"],
        )
        self.assertIn(
            "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
            state["remaining_geometry_residuals"],
        )

    def test_registry_and_provenance_are_explicit(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P93-T07"]["status"],
            "RESOLVED_FOR_REFERENCE_PROGRAMME_TOP_ENVELOPE_PROXY",
        )
        self.assertEqual(
            reg["B02-P93-T09"]["status"],
            "OPEN_NARROWED",
        )

        sources = rows(SOURCES, "source_id")
        note = sources["SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015"]["notes"]
        self.assertIn("P93 top-envelope authority", note)
        self.assertIn("A_Roof=A_Roof_1+A_Roof_2", note)
        self.assertIn("SFH=0.84", note)
        self.assertIn("MFH=0.35", note)
        self.assertIn("AB=0.20", note)

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P93", q["notes"])
        self.assertIn(
            "RESOLVED_FOR_REFERENCE_PROGRAMME_TOP_ENVELOPE_PROXY",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P93", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P93", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        boundary = semantic_boundaries()
        for item in (
            "A_ROOF_IS_THERMAL_ENVELOPE_TOP_AREA",
            "A_ROOF_MAY_BE_ROOF_OR_UPPER_CEILING_DEPENDING_ATTIC_STATE",
            "HU_CLASS_AVERAGE_RATIO_IS_NOT_HOUSEHOLD_RATIO",
            "TOP_AREA_CALIBRATION_IS_NOT_PITCHED_ROOF_U_RESOLUTION",
            "TOP_AREA_CALIBRATION_IS_NOT_BBOX_PLAN_AREA",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "A_Roof = A_Roof_1 + A_Roof_2",
            "0.84 m2/m2",
            "0.20 .. 0.35",
            "TOP-AREA CALIBRATION != PITCHED-ROOF U RESOLUTION",
            "B02 remains **55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
