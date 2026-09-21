import csv
import unittest
from pathlib import Path

from modules.B02.transition_response_coverage import (
    PARTIAL_QUANTIFIED_PRODUCT_DOMAIN,
    QUALIFIED_METHOD,
    assess_national_transition_response_materialization,
    assess_reference_product_domain,
    current_reference_supply_coverage,
    national_materialization_method_status,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p77_transition_response_coverage.csv"
P76 = ROOT / "registry" / "b02_p76_reuse_capex_envelope.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P77_TRANSITION_RESPONSE_COVERAGE.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P77TransitionResponseCoverageTests(unittest.TestCase):
    def test_record_project_method_is_already_qualified(self):
        self.assertEqual(national_materialization_method_status().status, QUALIFIED_METHOD)

    def test_reference_product_supply_coverage_is_exact(self):
        c = current_reference_supply_coverage()
        self.assertEqual(set(c), {35.0, 45.0, 55.0})

        self.assertEqual(c[35.0].weather_hours_total, 72)
        self.assertEqual(c[35.0].weather_hours_inside_domain, 35)
        self.assertEqual(c[35.0].weather_hours_below_domain, 37)
        self.assertAlmostEqual(c[35.0].coverage_share, 35 / 72, places=6)
        self.assertEqual(c[35.0].performance_domain_min_outdoor_c, -15.0)
        self.assertEqual(c[35.0].coldest_uncovered_outdoor_c, -21.9)

        self.assertEqual(c[45.0].weather_hours_inside_domain, 9)
        self.assertEqual(c[45.0].weather_hours_below_domain, 63)
        self.assertAlmostEqual(c[45.0].coverage_share, 9 / 72, places=6)
        self.assertEqual(c[45.0].performance_domain_min_outdoor_c, -7.0)

        self.assertEqual(c[55.0].status, "Q")
        self.assertIsNone(c[55.0].coverage_share)

    def test_product_domain_residual_is_specific(self):
        d = assess_reference_product_domain()
        self.assertEqual(d.status, PARTIAL_QUANTIFIED_PRODUCT_DOMAIN)
        self.assertIn("B05_COLD_W45_PRODUCT_GRID_REQUIRED", d.blockers)
        self.assertIn("B05_CONTINUOUS_W55_PRODUCT_SURFACE_REQUIRED", d.blockers)
        self.assertIn(
            "B05_W35_BELOW_MINUS15_PRODUCT_GRID_REQUIRED_IF_EXTREME_IN_SCOPE",
            d.blockers,
        )

    def test_national_materialization_is_ordered_fail_closed(self):
        d = assess_national_transition_response_materialization(
            post_retrofit_design_load_surface_materialized=False,
            p65_required_supply_temperature_surface_materialized=False,
            b05_product_design_point_coverage_complete=False,
        )
        self.assertEqual(d.status, "Q")
        self.assertEqual(
            d.blockers,
            (
                "NATIONAL_POST_RETROFIT_DESIGN_LOAD_SURFACE_REQUIRED",
                "NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED",
                "B05_MATERIALIZED_DESIGN_POINT_COVERAGE_REQUIRED",
            ),
        )

        ok = assess_national_transition_response_materialization(
            post_retrofit_design_load_surface_materialized=True,
            p65_required_supply_temperature_surface_materialized=True,
            b05_product_design_point_coverage_complete=True,
        )
        self.assertEqual(ok.status, QUALIFIED_METHOD)
        self.assertEqual(ok.blockers, ())

    def test_registry_retires_broad_blockers_by_decomposition(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P77-R07"]["status"],
            "PARTIAL_QUANTIFIED_PRODUCT_DOMAIN",
        )
        self.assertEqual(
            reg["B02-P77-R08"]["status"],
            "DECOMPOSED_EXECUTABLE_GATES",
        )
        self.assertIn(
            "NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED",
            reg["B02-P77-R08"]["residual_gap"],
        )

    def test_p76_current_state_is_superseded_not_deleted(self):
        p76 = rows(P76, "item_id")
        self.assertEqual(
            p76["B02-P76-C13"]["status"],
            "SUPERSEDED_BY_P77_CURRENT_STATE",
        )

    def test_q_and_readiness_keep_population_boundary(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P77", q["notes"])
        self.assertIn(
            "NATIONAL_POST_RETROFIT_DESIGN_LOAD_SURFACE_REQUIRED",
            q["notes"],
        )
        self.assertIn(
            "NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED",
            q["notes"],
        )
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P77", b02["gate_note"])

    def test_source_pack_preserves_critical_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "METHOD EXISTS != NATIONAL INPUT SURFACE EXISTS",
            "P21/WBL POPULATION WEIGHT != POST-RETROFIT DESIGN LOAD",
            "EMITTER CLASS != P65 REQUIRED SUPPLY TEMPERATURE",
            "WEATHER-DOMAIN COVERAGE != HEATING-RUNTIME COVERAGE",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
