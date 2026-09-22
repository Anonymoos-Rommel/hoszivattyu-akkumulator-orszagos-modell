import csv
import unittest
from pathlib import Path

from modules.B02.component_geometry_proxy import (
    all_stratum_geometry_envelopes,
    all_type_geometry_proxies,
    component_geometry_state,
    record_level_boundary,
    stratum_geometry_envelope,
    type_geometry_proxy,
)
from modules.B02.keop23_wbl_crosswalk import candidates_for, load_types


ROOT = Path(__file__).resolve().parents[1]
TYPE_PROXY = ROOT / "data" / "processed" / "b02" / "p85_keop23_component_geometry_proxy.csv"
STRATUM = ROOT / "data" / "processed" / "b02" / "p85_component_geometry_stratum_envelope.csv"
COMBINED = ROOT / "data" / "processed" / "b02" / "p85_reference_retrofit_physical_input_surface.csv"
REG = ROOT / "registry" / "b02_p85_component_geometry_proxy.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P85_COMPONENT_GEOMETRY_PROXY.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B02P85ComponentGeometryProxyTests(unittest.TestCase):
    def test_all_23_types_have_reproducible_proxy_rows(self):
        source = load_types()
        proxies = all_type_geometry_proxies()
        self.assertEqual(len(source), 23)
        self.assertEqual(len(proxies), 23)
        self.assertEqual({p.type_id for p in proxies}, set(range(1, 24)))

        for p in proxies:
            s = source[p.type_id]
            dwellings = float(s.dwelling_count_model)
            self.assertAlmostEqual(
                p.heated_volume_m3_per_dwelling,
                s.heated_floor_area_m2 * s.ceiling_height_m / dwellings,
            )
            self.assertAlmostEqual(
                p.mean_storey_floorplate_m2_per_dwelling,
                s.total_floor_area_m2 / s.storeys / dwellings,
            )
            self.assertAlmostEqual(
                p.bbox_plan_area_m2_per_dwelling,
                s.bbox_x_m * s.bbox_y_m / dwellings,
            )
            self.assertAlmostEqual(
                p.bbox_rectangular_facade_proxy_m2_per_dwelling,
                2.0
                * (s.bbox_x_m + s.bbox_y_m)
                * s.ceiling_height_m
                * s.storeys
                / dwellings,
            )
            self.assertAlmostEqual(
                p.max_usable_roof_area_m2_per_dwelling,
                s.max_usable_roof_area_m2 / dwellings,
            )

        t1 = type_geometry_proxy(1)
        self.assertAlmostEqual(t1.heated_volume_m3_per_dwelling, 185.235)
        self.assertAlmostEqual(t1.bbox_rectangular_facade_proxy_m2_per_dwelling, 111.3)

    def test_materialized_type_proxy_matches_runtime(self):
        data = {int(r["type_id"]): r for r in rows(TYPE_PROXY)}
        self.assertEqual(len(data), 23)
        for type_id, r in data.items():
            p = type_geometry_proxy(type_id)
            self.assertAlmostEqual(float(r["heated_volume_m3_per_dwelling"]), p.heated_volume_m3_per_dwelling)
            self.assertAlmostEqual(float(r["mean_storey_floorplate_m2_per_dwelling"]), p.mean_storey_floorplate_m2_per_dwelling)
            self.assertAlmostEqual(float(r["bbox_plan_area_m2_per_dwelling"]), p.bbox_plan_area_m2_per_dwelling)
            self.assertAlmostEqual(float(r["bbox_rectangular_facade_proxy_m2_per_dwelling"]), p.bbox_rectangular_facade_proxy_m2_per_dwelling)
            self.assertEqual(r["status"], "DERIVED_SYNTHETIC_GEOMETRY_PROXY")
            self.assertIn("HOUSEHOLD_COMPONENT_AREA", r["forbidden_use"])

    def test_all_14_strata_preserve_exact_p79_candidate_sets(self):
        envelopes = all_stratum_geometry_envelopes()
        self.assertEqual(len(envelopes), 14)
        self.assertEqual(
            {(e.wbl_period_code, e.building_group) for e in envelopes},
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
        for e in envelopes:
            rule = candidates_for(e.wbl_period_code, e.building_group)
            self.assertEqual(e.candidate_type_ids, rule.candidate_type_ids)
            self.assertEqual(e.candidate_count, len(rule.candidate_type_ids))
            self.assertLessEqual(
                e.heated_volume_lower_m3_per_dwelling,
                e.heated_volume_upper_m3_per_dwelling,
            )
            self.assertLessEqual(
                e.bbox_facade_proxy_lower_m2_per_dwelling,
                e.bbox_facade_proxy_upper_m2_per_dwelling,
            )

    def test_materialized_stratum_surface_matches_runtime(self):
        data = rows(STRATUM)
        self.assertEqual(len(data), 14)
        for r in data:
            e = stratum_geometry_envelope(r["wbl_period_code"], r["building_group"])
            self.assertEqual(
                r["candidate_type_ids"],
                ";".join(str(x) for x in e.candidate_type_ids),
            )
            self.assertAlmostEqual(
                float(r["heated_volume_lower_m3_per_dwelling"]),
                e.heated_volume_lower_m3_per_dwelling,
            )
            self.assertAlmostEqual(
                float(r["heated_volume_upper_m3_per_dwelling"]),
                e.heated_volume_upper_m3_per_dwelling,
            )
            self.assertIn(
                "NET_EXTERNAL_WALL_AND_WINDOW_AREA_SPLIT_INFERENCE_REQUIRED",
                r["residuals"],
            )

    def test_combined_reference_retrofit_surface_is_partial_not_design_load_truth(self):
        data = rows(COMBINED)
        self.assertEqual(len(data), 14)
        self.assertEqual(
            {r["status"] for r in data},
            {"PARTIAL_REFERENCE_RETROFIT_PHYSICAL_INPUT_SURFACE"},
        )
        self.assertEqual({r["pitched_roof_u_status"] for r in data}, {"Q"})
        for r in data:
            self.assertEqual(float(r["external_wall_u_max_w_m2k"]), 0.24)
            self.assertEqual(float(r["window_u_max_w_m2k"]), 1.15)
            self.assertIn(
                "ACTUAL_TOP_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED",
                r["residuals"],
            )
            self.assertIn(
                "DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED",
                r["residuals"],
            )

    def test_blocker_is_narrowed_but_not_false_resolved(self):
        state = component_geometry_state()
        self.assertEqual(state["type_proxy_count"], 23)
        self.assertEqual(state["stratum_envelope_count"], 14)
        self.assertEqual(
            state["generic_component_geometry_blocker"],
            "PARTIAL_RESOLVED_SYNTHETIC_PROXY",
        )
        self.assertIn(
            "NET_EXTERNAL_WALL_AND_WINDOW_AREA_SPLIT_INFERENCE_REQUIRED",
            state["residuals"],
        )
        self.assertIn(
            "BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED",
            state["residuals"],
        )

    def test_record_level_and_semantic_boundaries_are_frozen(self):
        boundary = record_level_boundary()
        self.assertIn(
            "P85_SYNTHETIC_PROXY_CANNOT_PASS_A_SPECIFIC_BUILDING",
            boundary,
        )
        self.assertIn(
            "P85_BBOX_FACADE_PROXY_IS_NOT_NET_WALL_AREA",
            boundary,
        )
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "BOUNDING RECTANGLE FACADE PROXY != NET EXTERNAL WALL AREA",
            "BOUNDING PLAN AREA != ROOF OR GROUND CONTACT AREA",
            "B02 overall readiness remains **55%**",
        ):
            self.assertIn(phrase, text)

    def test_registry_and_current_q_state(self):
        reg = {r["item_id"]: r for r in rows(REG)}
        self.assertEqual(reg["B02-P85-G07"]["lower_bound"], "14")
        self.assertEqual(
            reg["B02-P85-G09"]["status"],
            "PARTIAL_RESOLVED_SYNTHETIC_PROXY",
        )
        self.assertEqual(reg["B02-P85-G10"]["status"], "OPEN_NARROWED")

        questions = {r["question_id"]: r for r in rows(QUESTIONS)}
        q = questions["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P85", q["notes"])
        self.assertIn("OPEN_NARROWED", q["notes"])

        modules = {r["module_id"]: r for r in rows(MODULES)}
        self.assertEqual(modules["B02"]["readiness_percent"], "55")
        self.assertIn("B02-P85", modules["B02"]["gate_note"])


if __name__ == "__main__":
    unittest.main()
