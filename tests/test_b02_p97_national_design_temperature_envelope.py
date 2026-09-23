import csv
import unittest
from pathlib import Path

from modules.B02.design_outdoor_temperature_current import assess_location
from modules.B02.national_design_load_input_coverage import (
    QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE,
    current_design_load_blockers,
    national_design_load_input_coverage,
)
from modules.B02.national_design_temperature_envelope import (
    CURRENT_STANDARD_ZONE_SET_C,
    DESIGN_DELTA_T_LOWER_K,
    DESIGN_DELTA_T_SET_K,
    DESIGN_DELTA_T_UPPER_K,
    DESIGN_INDOOR_TEMPERATURE_C,
    LOCATION_ONLY_LOAD_SPREAD_RATIO,
    QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE as P97_STATUS,
    design_load_bounds_from_heat_loss_coefficient,
    national_reference_programme_design_temperature,
    p97_state,
    semantic_boundaries,
)


ROOT = Path(__file__).resolve().parents[1]
SURFACE = (
    ROOT / "data" / "processed" / "b02"
    / "p97_national_design_temperature_envelope.csv"
)
REG = ROOT / "registry" / "b02_p97_national_design_temperature_envelope.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P97_NATIONAL_DESIGN_TEMPERATURE_ENVELOPE.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P97NationalDesignTemperatureEnvelopeTests(unittest.TestCase):
    def test_exact_zone_and_delta_t_sets(self):
        self.assertEqual(CURRENT_STANDARD_ZONE_SET_C, (-12.0, -11.0, -10.0))
        self.assertEqual(DESIGN_INDOOR_TEMPERATURE_C, 20.0)
        self.assertEqual(DESIGN_DELTA_T_SET_K, (32.0, 31.0, 30.0))
        self.assertEqual(DESIGN_DELTA_T_LOWER_K, 30.0)
        self.assertEqual(DESIGN_DELTA_T_UPPER_K, 32.0)
        self.assertAlmostEqual(LOCATION_ONLY_LOAD_SPREAD_RATIO, 32.0 / 30.0)

        x = national_reference_programme_design_temperature()
        self.assertEqual(x.status, P97_STATUS)
        self.assertIsNone(x.blocker)
        self.assertEqual(x.outdoor_zone_values_c, (-12.0, -11.0, -10.0))
        self.assertEqual(x.delta_t_lower_k, 30.0)
        self.assertEqual(x.delta_t_upper_k, 32.0)

    def test_monotone_load_propagation(self):
        self.assertEqual(
            design_load_bounds_from_heat_loss_coefficient(100.0),
            (3000.0, 3200.0),
        )
        self.assertEqual(
            design_load_bounds_from_heat_loss_coefficient(0.0),
            (0.0, 0.0),
        )
        with self.assertRaises(ValueError):
            design_load_bounds_from_heat_loss_coefficient(-1.0)

    def test_fourteen_stratum_surface_is_materialized(self):
        data = rows(SURFACE)
        self.assertEqual(len(data), 14)
        self.assertEqual(
            {(r["wbl_period_code"], r["building_group"]) for r in data},
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
        self.assertEqual(
            {r["outdoor_zone_set_c"] for r in data},
            {"-12;-11;-10"},
        )
        self.assertEqual(
            {float(r["delta_t_lower_k"]) for r in data},
            {30.0},
        )
        self.assertEqual(
            {float(r["delta_t_upper_k"]) for r in data},
            {32.0},
        )
        self.assertEqual(
            {r["status"] for r in data},
            {"QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE"},
        )

    def test_current_design_outdoor_temperature_is_nonblocking(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        item = by["DESIGN_OUTDOOR_TEMPERATURE"]
        self.assertEqual(
            item.status,
            QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE,
        )
        self.assertIsNone(item.blocker)
        self.assertIn("B02-P82", item.source_refs)
        self.assertIn("B02-P86", item.source_refs)
        self.assertIn("B02-P97", item.source_refs)

        blockers = set(current_design_load_blockers())
        self.assertNotIn(
            "COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED",
            blockers,
        )

    def test_project_level_p86_resolver_remains_fail_closed(self):
        unknown = assess_location(
            city_name=None,
            settlement_population=100_000,
            elevation_m=100.0,
        )
        self.assertEqual(
            unknown.status,
            "Q_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE",
        )
        self.assertIn(
            "MACHINE_READABLE_CURRENT_STANDARD_ZONE_GEOMETRY_REQUIRED",
            unknown.blockers,
        )

        small = assess_location(
            city_name="Budapest",
            settlement_population=25_000,
            elevation_m=105.0,
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

    def test_registry_and_provenance(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P97-T08"]["status"],
            "SUPERSEDED_FOR_NATIONAL_REFERENCE_PROGRAMME",
        )
        self.assertEqual(
            reg["B02-P97-T09"]["status"],
            "QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE",
        )
        self.assertEqual(
            reg["B02-P97-T10"]["status"],
            "RECORD_LEVEL_RESIDUAL",
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn(
            "P97 national-envelope authority",
            sources["SRC-B02-MSZ-24140-2026"]["notes"],
        )
        self.assertIn(
            "P97 set-valued national inference",
            sources["SRC-B02-BIMLINE-MSZ24140-2026"]["notes"],
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P97", q["notes"])
        self.assertIn(
            "SUPERSEDED_FOR_NATIONAL_REFERENCE_PROGRAMME",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P97", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P97", peak["notes"])

    def test_state_and_semantic_boundaries(self):
        state = p97_state()
        self.assertEqual(state["zone_set_c"], (-12.0, -11.0, -10.0))
        self.assertEqual(state["delta_t_bound_k"], (30.0, 32.0))
        self.assertAlmostEqual(
            state["location_only_load_spread_percent"],
            6.666666666666665,
        )
        self.assertIsNone(state["national_mapping_blocker"])

        boundary = semantic_boundaries()
        for item in (
            "NATIONAL_ZONE_SET_IS_NOT_EXACT_SETTLEMENT_ZONE",
            "CURRENT_STANDARD_DOMAIN_IS_NOT_PROJECT_DESIGN_AUTHORITY",
            "SET_VALUED_PROPAGATION_IS_NOT_MOST_LIKELY_ZONE",
            "COUNTY_SETTLEMENT_TYPE_GRAIN_IS_NOT_SETTLEMENT_COORDINATE",
            "BASELINE_MAP_SCOPE_IS_NOT_AUTOMATIC_PROJECT_COMPLIANCE_OUTSIDE_SCOPE",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "NO FULL-POPULATION DATA != BLOCKER",
            "Delta T in [30,32] K",
            "6.6666666667%",
            "COUNTY + SETTLEMENT TYPE GRAIN != SETTLEMENT COORDINATE",
            "B02 remains **55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
