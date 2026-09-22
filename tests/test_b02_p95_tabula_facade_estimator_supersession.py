import csv
import unittest
from pathlib import Path

from modules.B02.national_design_load_input_coverage import (
    QUALIFIED_REFERENCE_PROGRAMME_ENVELOPE_GEOMETRY_PROXY,
    current_design_load_blockers,
    national_design_load_input_coverage,
)
from modules.B02.tabula_facade_estimator_supersession import (
    BBOX_ROUTE_SUPERSEDED,
    QUALIFIED_TABULA_FACADE_ESTIMATOR_PROXY,
    TABULA_FACADE_INTERCEPT_BY_NEIGHBOURS,
    TABULA_FACADE_SLOPE,
    all_stratum_facade_surfaces,
    all_type_facade_audits,
    p95_state,
    semantic_boundaries,
    stratum_facade_surface,
    tabula_facade_estimate_m2,
    type_facade_audit,
)


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "processed" / "b02" / "p95_bbox_vs_tabula_facade_audit.csv"
SURFACE = ROOT / "data" / "processed" / "b02" / "p95_tabula_facade_reference_surface.csv"
REG = ROOT / "registry" / "b02_p95_tabula_facade_estimator_supersession.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P95_TABULA_FACADE_ESTIMATOR_SUPERSESSION.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P95TabulaFacadeEstimatorSupersessionTests(unittest.TestCase):
    def test_exact_tabula_facade_estimator_parameters(self):
        self.assertEqual(TABULA_FACADE_SLOPE, 0.7)
        self.assertEqual(
            TABULA_FACADE_INTERCEPT_BY_NEIGHBOURS,
            {0: 50.0, 1: 25.0, 2: 5.0},
        )
        self.assertAlmostEqual(
            tabula_facade_estimate_m2(a_c_ref_m2=100.0, attached_neighbours=0),
            120.0,
        )
        self.assertAlmostEqual(
            tabula_facade_estimate_m2(a_c_ref_m2=100.0, attached_neighbours=1),
            95.0,
        )
        self.assertAlmostEqual(
            tabula_facade_estimate_m2(a_c_ref_m2=100.0, attached_neighbours=2),
            75.0,
        )
        with self.assertRaises(ValueError):
            tabula_facade_estimate_m2(a_c_ref_m2=100.0, attached_neighbours=3)
        with self.assertRaises(ValueError):
            tabula_facade_estimate_m2(a_c_ref_m2=0.0, attached_neighbours=0)

    def test_type_audit_counts_are_frozen(self):
        audits = all_type_facade_audits()
        self.assertEqual(len(audits), 23)
        self.assertEqual(
            sum(a.bbox_overlap_heated_ref_neighbour_set for a in audits),
            2,
        )
        self.assertEqual(
            sum(a.bbox_overlap_area_proxy_neighbour_set for a in audits),
            11,
        )

        t7 = type_facade_audit(7)
        self.assertTrue(t7.bbox_overlap_heated_ref_neighbour_set)

        t6 = type_facade_audit(6)
        self.assertFalse(t6.bbox_overlap_heated_ref_neighbour_set)
        self.assertFalse(t6.bbox_overlap_area_proxy_neighbour_set)

    def test_area_semantic_and_neighbour_uncertainty_are_set_valued(self):
        t1 = type_facade_audit(1)
        self.assertAlmostEqual(t1.tabula_heated_ref_lower_m2_per_dwelling, 53.93)
        self.assertAlmostEqual(t1.tabula_heated_ref_upper_m2_per_dwelling, 98.93)
        self.assertAlmostEqual(t1.tabula_area_proxy_lower_m2_per_dwelling, 53.93)
        self.assertAlmostEqual(t1.tabula_area_proxy_upper_m2_per_dwelling, 121.19)
        self.assertGreater(
            t1.tabula_area_proxy_upper_m2_per_dwelling,
            t1.tabula_heated_ref_upper_m2_per_dwelling,
        )

    def test_fourteen_stratum_canonical_facade_surface(self):
        surface = all_stratum_facade_surfaces()
        self.assertEqual(len(surface), 14)
        self.assertEqual(
            {(x.wbl_period_code, x.building_group) for x in surface},
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
            min(x.gross_facade_lower_m2_per_dwelling for x in surface),
            38.526111111111,
            places=9,
        )
        self.assertAlmostEqual(
            max(x.gross_facade_upper_m2_per_dwelling for x in surface),
            238.58,
            places=9,
        )
        self.assertAlmostEqual(
            min(x.opening_area_lower_m2_per_dwelling for x in surface),
            4.88501016703,
            places=9,
        )
        self.assertAlmostEqual(
            max(x.opening_area_upper_m2_per_dwelling for x in surface),
            26.508888888889,
            places=9,
        )
        self.assertAlmostEqual(
            min(x.net_wall_area_lower_m2_per_dwelling for x in surface),
            29.637374678663,
            places=9,
        )
        self.assertAlmostEqual(
            max(x.net_wall_area_upper_m2_per_dwelling for x in surface),
            212.071111111111,
            places=9,
        )
        self.assertAlmostEqual(
            min(x.facade_transmission_h_upper_w_per_k_per_dwelling for x in surface),
            47.700254335904,
            places=9,
        )
        self.assertAlmostEqual(
            max(x.facade_transmission_h_upper_w_per_k_per_dwelling for x in surface),
            108.368337777778,
            places=9,
        )

    def test_materialized_csvs_match_runtime(self):
        audit = rows(AUDIT)
        self.assertEqual(len(audit), 23)
        self.assertEqual(
            sum(row["bbox_overlap_heated_ref_neighbour_set"] == "true" for row in audit),
            2,
        )
        self.assertEqual(
            sum(row["bbox_overlap_area_proxy_neighbour_set"] == "true" for row in audit),
            11,
        )

        surface = rows(SURFACE)
        self.assertEqual(len(surface), 14)
        self.assertEqual(
            {row["status"] for row in surface},
            {"QUALIFIED_TABULA_FACADE_ESTIMATOR_PROXY"},
        )
        self.assertAlmostEqual(
            max(float(row["gross_facade_upper_m2_per_dwelling"]) for row in surface),
            238.58,
        )

    def test_bbox_is_superseded_not_passed(self):
        state = p95_state()
        self.assertEqual(state["type_count"], 23)
        self.assertEqual(state["strict_heated_ref_bbox_overlap_count"], 2)
        self.assertEqual(state["area_proxy_bbox_overlap_count"], 11)
        self.assertEqual(state["bbox_route_status"], BBOX_ROUTE_SUPERSEDED)
        self.assertEqual(
            state["canonical_facade_status"],
            QUALIFIED_TABULA_FACADE_ESTIMATOR_PROXY,
        )
        self.assertIsNone(state["bbox_blocker"])

        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P95-F07"]["status"],
            "SUPERSEDED_BY_TABULA_FACADE_ESTIMATOR",
        )
        self.assertNotEqual(reg["B02-P95-F07"]["status"], "PASS")

    def test_current_envelope_geometry_is_qualified(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        geometry = by["POST_RETROFIT_ENVELOPE_GEOMETRY"]
        self.assertEqual(
            geometry.status,
            QUALIFIED_REFERENCE_PROGRAMME_ENVELOPE_GEOMETRY_PROXY,
        )
        self.assertIsNone(geometry.blocker)
        self.assertIn("B02-P95", geometry.source_refs)
        self.assertIn("SRC-B02-EU-TABULA-REFERENCE-AREA-WEB", geometry.source_refs)

        blockers = set(current_design_load_blockers())
        self.assertNotIn("POST_RETROFIT_ENVELOPE_GEOMETRY_SURFACE_REQUIRED", blockers)

    def test_registry_provenance_and_current_question(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P95-F04"]["status"],
            "FAILED_CANONICAL_VALIDATION",
        )
        self.assertEqual(
            reg["B02-P95-F05"]["status"],
            "FAILED_CANONICAL_VALIDATION",
        )
        self.assertEqual(
            reg["B02-P95-F10"]["status"],
            "RESOLVED_FOR_REFERENCE_PROGRAMME_ENVELOPE_GEOMETRY_PROXY",
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn(
            "P95 facade-estimator authority",
            sources["SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015"]["notes"],
        )
        self.assertIn(
            "A_facade=b+0.7*A_C_Ref",
            sources["SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015"]["notes"],
        )
        self.assertIn(
            "SRC-B02-EU-TABULA-REFERENCE-AREA-WEB",
            sources,
        )
        self.assertIn(
            "conditioned reference floor area",
            sources["SRC-B02-EU-TABULA-REFERENCE-AREA-WEB"]["notes"],
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P95", q["notes"])
        self.assertIn("SUPERSEDED_BY_TABULA_FACADE_ESTIMATOR", q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P95", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P95", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        boundary = semantic_boundaries()
        for item in (
            "BBOX_AUDIT_FAILURE_IS_NOT_DATA_DELETION",
            "BBOX_PROXY_IS_NOT_CANONICAL_REFERENCE_PROGRAMME_FACADE_AFTER_P95",
            "TABULA_ESTIMATOR_IS_NOT_OBSERVED_FACADE_AREA",
            "HEATED_FLOOR_AREA_IS_NOT_EXACT_TABULA_A_C_REF",
            "TOTAL_FLOOR_AREA_IS_NOT_EXACT_TABULA_A_C_REF",
            "UNKNOWN_NEIGHBOUR_COUNT_IS_NOT_DETACHED_DEFAULT",
            "TOTAL_ENVELOPE_PM30_QUALITY_IS_NOT_FACADE_SPECIFIC_ERROR_BOUND",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "2 / 23 types overlap",
            "11 / 23 types overlap",
            "SUPERSEDED_BY_TABULA_FACADE_ESTIMATOR",
            "TOTAL-ENVELOPE +/-30% != FACADE-SPECIFIC ERROR BOUND",
            "B02 remains **55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
