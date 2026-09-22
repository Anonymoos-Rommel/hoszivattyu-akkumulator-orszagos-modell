import csv
import unittest
from pathlib import Path

from modules.B02.hungarian_facade_opening_split import (
    FAMILY_HOUSE,
    MULTI_DWELLING,
    HU_AB_OPENING_SHARE,
    HU_MFH_OPENING_SHARE,
    HU_SFH_OPENING_SHARE,
    QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY,
    REFERENCE_AGGREGATE_OPENING_U_UPPER_W_M2K,
    REFERENCE_WALL_CORRECTED_U_UPPER_W_M2K,
    TABULA_HU_AB_OPENING_M2,
    TABULA_HU_AB_WALL_M2,
    TABULA_HU_MFH_OPENING_M2,
    TABULA_HU_MFH_WALL_M2,
    TABULA_HU_SFH_OPENING_M2,
    TABULA_HU_SFH_WALL_M2,
    opening_share_bound,
    p92_state,
    reference_programme_facade_split_surface,
    semantic_boundaries,
    split_gross_facade_proxy,
)
from modules.B02.national_design_load_input_coverage import (
    PARTIAL_HUNGARIAN_FACADE_TOP_BOTTOM_GEOMETRY_PROXY,
    current_design_load_blockers,
    national_design_load_input_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p92_hungarian_facade_opening_split.csv"
REG = ROOT / "registry" / "b02_p92_hungarian_facade_opening_split.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P92_HUNGARIAN_FACADE_OPENING_SPLIT.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P92HungarianFacadeOpeningSplitTests(unittest.TestCase):
    def test_exact_hungarian_tabula_class_averages_and_shares(self):
        self.assertEqual((TABULA_HU_SFH_WALL_M2, TABULA_HU_SFH_OPENING_M2), (128.0, 16.0))
        self.assertEqual((TABULA_HU_MFH_WALL_M2, TABULA_HU_MFH_OPENING_M2), (668.0, 97.0))
        self.assertEqual((TABULA_HU_AB_WALL_M2, TABULA_HU_AB_OPENING_M2), (1197.0, 359.0))

        self.assertAlmostEqual(HU_SFH_OPENING_SHARE, 16.0 / 144.0)
        self.assertAlmostEqual(HU_MFH_OPENING_SHARE, 97.0 / 765.0)
        self.assertAlmostEqual(HU_AB_OPENING_SHARE, 359.0 / 1556.0)

        self.assertAlmostEqual(HU_SFH_OPENING_SHARE, 0.1111111111111111)
        self.assertAlmostEqual(HU_MFH_OPENING_SHARE, 0.12679738562091504)
        self.assertAlmostEqual(HU_AB_OPENING_SHARE, 0.230719794344473)

    def test_building_group_mapping_preserves_set_semantics(self):
        family = opening_share_bound(FAMILY_HOUSE)
        self.assertEqual(family.source_classes, ("HU_SFH",))
        self.assertAlmostEqual(family.lower, HU_SFH_OPENING_SHARE)
        self.assertAlmostEqual(family.upper, HU_SFH_OPENING_SHARE)
        self.assertEqual(
            family.status,
            QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY,
        )

        multi = opening_share_bound(MULTI_DWELLING)
        self.assertEqual(multi.source_classes, ("HU_MFH", "HU_AB"))
        self.assertAlmostEqual(multi.lower, HU_MFH_OPENING_SHARE)
        self.assertAlmostEqual(multi.upper, HU_AB_OPENING_SHARE)

        with self.assertRaises(ValueError):
            opening_share_bound("TERRACED_HOUSE_POINT_DEFAULT")

    def test_split_is_interval_safe_and_preserves_bbox_blocker(self):
        family = split_gross_facade_proxy(
            gross_facade_lower_m2=100.0,
            gross_facade_upper_m2=200.0,
            building_group=FAMILY_HOUSE,
        )
        self.assertAlmostEqual(family.opening_area_lower_m2, 11.11111111111111)
        self.assertAlmostEqual(family.opening_area_upper_m2, 22.22222222222222)
        self.assertAlmostEqual(family.net_wall_area_lower_m2, 88.88888888888889)
        self.assertAlmostEqual(family.net_wall_area_upper_m2, 177.77777777777777)
        self.assertEqual(
            family.blocker,
            "BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED",
        )

        multi = split_gross_facade_proxy(
            gross_facade_lower_m2=100.0,
            gross_facade_upper_m2=200.0,
            building_group=MULTI_DWELLING,
        )
        self.assertAlmostEqual(multi.opening_area_lower_m2, 100.0 * HU_MFH_OPENING_SHARE)
        self.assertAlmostEqual(multi.opening_area_upper_m2, 200.0 * HU_AB_OPENING_SHARE)
        self.assertAlmostEqual(multi.net_wall_area_lower_m2, 100.0 * (1.0 - HU_AB_OPENING_SHARE))
        self.assertAlmostEqual(multi.net_wall_area_upper_m2, 200.0 * (1.0 - HU_MFH_OPENING_SHARE))

        with self.assertRaises(ValueError):
            split_gross_facade_proxy(
                gross_facade_lower_m2=200.0,
                gross_facade_upper_m2=100.0,
                building_group=FAMILY_HOUSE,
            )

    def test_conservative_aggregate_opening_upper_is_explicit(self):
        self.assertEqual(REFERENCE_AGGREGATE_OPENING_U_UPPER_W_M2K, 1.40)
        self.assertEqual(REFERENCE_WALL_CORRECTED_U_UPPER_W_M2K, 0.336)

        x = split_gross_facade_proxy(
            gross_facade_lower_m2=100.0,
            gross_facade_upper_m2=200.0,
            building_group=FAMILY_HOUSE,
        )
        expected = 200.0 * (
            (1.0 - HU_SFH_OPENING_SHARE) * 0.336
            + HU_SFH_OPENING_SHARE * 1.40
        )
        self.assertAlmostEqual(x.facade_transmission_h_upper_w_per_k, expected)

    def test_fourteen_stratum_surface_and_global_extrema(self):
        surface = reference_programme_facade_split_surface()
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
            min(row.opening_area_proxy_lower_m2_per_dwelling for row in surface),
            4.414150670800741,
        )
        self.assertAlmostEqual(
            max(row.opening_area_proxy_upper_m2_per_dwelling for row in surface),
            36.48,
        )
        self.assertAlmostEqual(
            min(row.net_wall_area_proxy_lower_m2_per_dwelling for row in surface),
            26.78066838050257,
        )
        self.assertAlmostEqual(
            max(row.net_wall_area_proxy_upper_m2_per_dwelling for row in surface),
            291.84,
        )
        self.assertAlmostEqual(
            min(row.facade_transmission_h_upper_w_per_k_per_dwelling for row in surface),
            55.194637943445,
            places=9,
        )
        self.assertAlmostEqual(
            max(row.facade_transmission_h_upper_w_per_k_per_dwelling for row in surface),
            149.13024,
            places=9,
        )

    def test_materialized_csv_matches_runtime(self):
        data = rows(SURFACE)
        self.assertEqual(len(data), 14)
        self.assertEqual(
            {row["status"] for row in data},
            {"QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY"},
        )
        self.assertEqual(
            {row["residual"] for row in data},
            {"BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED"},
        )
        self.assertAlmostEqual(
            min(float(row["opening_area_proxy_lower_m2_per_dwelling"]) for row in data),
            4.414150670801,
        )
        self.assertAlmostEqual(
            max(float(row["facade_transmission_h_upper_w_per_k_per_dwelling"]) for row in data),
            149.13024,
        )

    def test_current_geometry_coverage_is_partial_and_still_fail_closed(self):
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
        blockers = set(current_design_load_blockers())
        self.assertIn("POST_RETROFIT_ENVELOPE_GEOMETRY_SURFACE_REQUIRED", blockers)

    def test_p92_state_retires_only_the_split_blocker(self):
        state = p92_state()
        self.assertEqual(state["stratum_count"], 14)
        self.assertEqual(
            state["split_status"],
            QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY,
        )
        self.assertIsNone(state["split_blocker"])
        self.assertEqual(
            state["remaining_geometry_blocker"],
            "BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED",
        )
        self.assertEqual(
            state["realized_claim_residual"],
            "REALIZED_FACADE_GEOMETRY_VERIFICATION_REQUIRED",
        )

    def test_registry_source_and_readiness_are_conservative(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P92-F09"]["status"],
            "RESOLVED_FOR_REFERENCE_PROGRAMME_OPENING_SPLIT",
        )
        self.assertEqual(
            reg["B02-P92-F10"]["status"],
            "OPEN_NARROWED",
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn(
            "SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015",
            sources,
        )
        self.assertIn(
            "A_Window_1+A_Window_2+A_Door_1",
            sources["SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015"]["notes"],
        )
        self.assertIn(
            "P92 opening-area upper-bound control",
            sources["SRC-B06-HU-ENERGY-RULES-2023"]["notes"],
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P92", q["notes"])
        self.assertIn(
            "RESOLVED_FOR_REFERENCE_PROGRAMME_OPENING_SPLIT",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P92", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P92", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        boundary = semantic_boundaries()
        for item in (
            "TABULA_A_WINDOW_INCLUDES_DOOR",
            "OPENING_AREA_IS_NOT_WINDOW_ONLY_AREA",
            "HU_CLASS_AVERAGE_IS_NOT_HOUSEHOLD_AREA_SHARE",
            "P85_BBOX_FACADE_PROXY_IS_NOT_SOURCE_NATIVE_TABULA_FACADE",
            "FACADE_SPLIT_CALIBRATION_IS_NOT_BBOX_VALIDATION",
            "NO_UNIVERSAL_TWENTY_PERCENT_WINDOW_DEFAULT",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "TABULA A_Window != WINDOW-ONLY AREA",
            "FACADE SPLIT CALIBRATION != BBOX VALIDATION",
            "NO UNIVERSAL 20% WINDOW DEFAULT",
            "B02 remains **55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
