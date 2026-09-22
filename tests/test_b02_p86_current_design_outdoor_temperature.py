import csv
import unittest
from pathlib import Path

from modules.B02.design_outdoor_temperature_current import (
    CITY_ANCHORS_C,
    CURRENT_STANDARD_EFFECTIVE_DATE,
    CURRENT_STANDARD_ID,
    CURRENT_ZONE_VALUES_C,
    assess_location,
    current_standard_domain,
    mapping_boundary,
    resolve_named_city_anchor,
)


ROOT = Path(__file__).resolve().parents[1]
ANCHORS = ROOT / "data" / "processed" / "b02" / "p86_current_design_temperature_city_anchors.csv"
REG = ROOT / "registry" / "b02_p86_current_design_outdoor_temperature.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P86_CURRENT_DESIGN_OUTDOOR_TEMPERATURE.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P86CurrentDesignOutdoorTemperatureTests(unittest.TestCase):
    def test_current_standard_identity_and_zone_domain(self):
        self.assertEqual(CURRENT_STANDARD_ID, "MSZ_24140_2026")
        self.assertEqual(CURRENT_STANDARD_EFFECTIVE_DATE, "2026-04-01")
        self.assertEqual(CURRENT_ZONE_VALUES_C, (-12.0, -11.0, -10.0))
        d = current_standard_domain()
        self.assertEqual(d.status, "QUALIFIED_CURRENT_STANDARD_ZONE_DOMAIN")
        self.assertEqual(d.lower_c, -12.0)
        self.assertEqual(d.upper_c, -10.0)
        self.assertIsNone(d.point_c)

    def test_20_public_city_anchors_are_materialized(self):
        self.assertEqual(len(CITY_ANCHORS_C), 20)
        self.assertEqual(CITY_ANCHORS_C["Budapest"], -11.0)
        self.assertEqual(CITY_ANCHORS_C["Debrecen"], -12.0)
        self.assertEqual(CITY_ANCHORS_C["Pécs"], -10.0)

        data = rows(ANCHORS, "city_name")
        self.assertEqual(len(data), 20)
        for city, value in CITY_ANCHORS_C.items():
            self.assertAlmostEqual(
                float(data[city]["design_outdoor_temperature_c"]),
                value,
            )
            self.assertIn("HOUSEHOLD_POINT_AUTHORITY", data[city]["forbidden_use"])

    def test_named_anchor_resolves_but_unknown_location_fails_closed(self):
        budapest = resolve_named_city_anchor("Budapest")
        self.assertEqual(budapest.status, "QUALIFIED_PUBLIC_CITY_ANCHOR")
        self.assertEqual(budapest.point_c, -11.0)
        self.assertIn(
            "PUBLIC_CITY_ANCHOR_IS_NOT_RECORD_LEVEL_ENGINEERING_AUTHORITY",
            budapest.warnings,
        )

        unknown = resolve_named_city_anchor("Unknown")
        self.assertEqual(unknown.status, "Q_EXACT_LOCATION_ZONE")
        self.assertEqual(unknown.lower_c, -12.0)
        self.assertEqual(unknown.upper_c, -10.0)
        self.assertIn(
            "MACHINE_READABLE_CURRENT_STANDARD_ZONE_GEOMETRY_REQUIRED",
            unknown.blockers,
        )

    def test_baseline_scope_and_adjustment_are_fail_closed(self):
        qualified = assess_location(
            city_name="Budapest",
            settlement_population=1_700_000,
            elevation_m=105.0,
        )
        self.assertEqual(
            qualified.status,
            "QUALIFIED_CURRENT_STANDARD_LOCATION_INPUT",
        )
        self.assertEqual(qualified.point_c, -11.0)

        small = assess_location(
            city_name="Budapest",
            settlement_population=25_000,
            elevation_m=105.0,
        )
        self.assertEqual(
            small.status,
            "Q_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE",
        )
        self.assertIn(
            "LOCAL_DESIGN_AUTHORITY_REQUIRED_FOR_SMALLER_SETTLEMENT",
            small.blockers,
        )

        high = assess_location(
            city_name="Budapest",
            settlement_population=1_700_000,
            elevation_m=350.0,
        )
        self.assertIn(
            "LOCAL_DESIGN_AUTHORITY_REQUIRED_FOR_HIGHER_ELEVATION",
            high.blockers,
        )

        unauthorised_adjustment = assess_location(
            city_name="Budapest",
            settlement_population=1_700_000,
            elevation_m=105.0,
            project_specific_adjustment_c=-1.0,
            project_adjustment_authorized=False,
        )
        self.assertEqual(
            unauthorised_adjustment.status,
            "Q_PROJECT_SPECIFIC_ADJUSTMENT_AUTHORITY",
        )

    def test_explicit_current_standard_zone_is_bounded_to_three_values(self):
        x = assess_location(
            city_name=None,
            settlement_population=100_000,
            elevation_m=100.0,
            explicit_standard_zone_c=-12.0,
        )
        self.assertEqual(x.point_c, -12.0)

        with self.assertRaisesRegex(ValueError, "must be -12, -11 or -10"):
            assess_location(
                city_name=None,
                settlement_population=100_000,
                elevation_m=100.0,
                explicit_standard_zone_c=-13.0,
            )

    def test_registry_and_source_state(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P86-T02"]["status"],
            "QUALIFIED_CURRENT_STANDARD_ZONE_DOMAIN",
        )
        self.assertEqual(reg["B02-P86-T02"]["lower_bound"], "-12")
        self.assertEqual(reg["B02-P86-T02"]["upper_bound"], "-10")
        self.assertEqual(
            reg["B02-P86-T09"]["status"],
            "RETIRED_AS_CURRENT",
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-MSZ-24140-2026", sources)
        self.assertIn("SRC-B02-BIMLINE-MSZ24140-2026", sources)

    def test_q_b02_004_and_module_readiness_remain_fail_closed(self):
        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P86", q["notes"])
        self.assertIn(
            "COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P86", module["gate_note"])

    def test_nonpromotion_boundaries(self):
        b = mapping_boundary()
        self.assertIn(
            "OLD_MINUS15_MINUS13_MINUS11_MAP != CURRENT_STANDARD_MAP",
            b,
        )
        self.assertIn(
            "2023_GOVERNMENT_METEO_STANDARD_YEAR != DESIGN_OUTDOOR_TEMPERATURE_MAP",
            b,
        )
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "CURRENT_STANDARD_DESIGN_OUTDOOR_DOMAIN = [-12, -10] C",
            "GOVERNMENT METEO STANDARD YEAR != DESIGN OUTDOOR TEMPERATURE MAP",
            "B05-P9 HISTORICAL EXTREME STRESS != DESIGN OUTDOOR TEMPERATURE",
            "B02 remains **55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
