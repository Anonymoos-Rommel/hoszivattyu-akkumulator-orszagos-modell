import csv
import unittest
from pathlib import Path

from modules.B02.national_supply_temperature_envelope import (
    B05_AUDIT_CONTROL_POINTS_C,
    QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
    REFERENCE_PROGRAMME_MAX_DESIGN_FLOW_C,
    SUPPLY_TEMPERATURE_BANDS,
    classify_design_flow_temperature,
    national_reference_programme_supply_temperature_surface,
    p98_state,
    reference_programme_action_for_required_flow,
    semantic_boundaries,
)
from modules.B02.transition_response_coverage import (
    assess_national_transition_response_materialization,
)


ROOT = Path(__file__).resolve().parents[1]
SURFACE = (
    ROOT / "data" / "processed" / "b02"
    / "p98_national_supply_temperature_envelope.csv"
)
REG = ROOT / "registry" / "b02_p98_national_supply_temperature_envelope.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = (
    ROOT / "docs" / "source_packs"
    / "B02_P98_NATIONAL_SUPPLY_TEMPERATURE_ENVELOPE.md"
)


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P98NationalSupplyTemperatureEnvelopeTests(unittest.TestCase):
    def test_exact_category_set_and_programme_ceiling(self):
        self.assertEqual(
            tuple(x.band_id for x in SUPPLY_TEMPERATURE_BANDS),
            ("LE_35", "C36_40", "C41_45", "C46_50", "C51_55"),
        )
        self.assertEqual(REFERENCE_PROGRAMME_MAX_DESIGN_FLOW_C, 55.0)
        self.assertEqual(B05_AUDIT_CONTROL_POINTS_C, (35.0, 45.0, 55.0))

        le35 = SUPPLY_TEMPERATURE_BANDS[0]
        self.assertIsNone(le35.lower_c)
        self.assertEqual(le35.upper_c, 35.0)

        top = SUPPLY_TEMPERATURE_BANDS[-1]
        self.assertEqual(top.lower_c, 51.0)
        self.assertEqual(top.upper_c, 55.0)

    def test_exact_temperature_is_classified_but_never_created(self):
        self.assertEqual(classify_design_flow_temperature(30.0), "LE_35")
        self.assertEqual(classify_design_flow_temperature(35.0), "LE_35")
        self.assertEqual(classify_design_flow_temperature(36.0), "C36_40")
        self.assertEqual(classify_design_flow_temperature(43.0), "C41_45")
        self.assertEqual(classify_design_flow_temperature(49.0), "C46_50")
        self.assertEqual(classify_design_flow_temperature(55.0), "C51_55")
        self.assertEqual(
            classify_design_flow_temperature(55.1),
            "ABOVE_REFERENCE_PROGRAMME_55",
        )
        with self.assertRaises(ValueError):
            classify_design_flow_temperature(0.0)

    def test_above_55_triggers_action_not_hidden_acceptance(self):
        self.assertEqual(
            reference_programme_action_for_required_flow(55.0),
            "WITHIN_REFERENCE_PROGRAMME_SUPPLY_ENVELOPE",
        )
        self.assertEqual(
            reference_programme_action_for_required_flow(60.0),
            "EMITTER_OR_HYDRAULIC_ADAPTATION_OR_EXPLICIT_EXCEPTION_REQUIRED",
        )

    def test_fourteen_stratum_surface_has_latent_weights(self):
        surface = national_reference_programme_supply_temperature_surface()
        self.assertEqual(len(surface), 14)
        expected_bands = ("LE_35", "C36_40", "C41_45", "C46_50", "C51_55")
        for row in surface:
            self.assertEqual(row.admissible_band_ids, expected_bands)
            self.assertEqual(row.max_reference_programme_design_flow_c, 55.0)
            self.assertEqual(row.b05_audit_control_points_c, (35.0, 45.0, 55.0))
            self.assertEqual(
                row.allocation_status,
                "LATENT_SET_PROPAGATION_NO_POINT_WEIGHTS",
            )
            self.assertEqual(
                row.status,
                QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
            )

    def test_materialized_csv_matches_runtime(self):
        data = rows(SURFACE)
        self.assertEqual(len(data), 14)
        self.assertEqual(
            {row["admissible_design_flow_bands"] for row in data},
            {"LE_35;C36_40;C41_45;C46_50;C51_55"},
        )
        self.assertEqual(
            {float(row["max_reference_programme_design_flow_c"]) for row in data},
            {55.0},
        )
        self.assertEqual(
            {row["population_weight_status"] for row in data},
            {"LATENT_SET_PROPAGATION_NO_POINT_WEIGHTS"},
        )

    def test_p77_gate2_is_resolved_but_gate3_remains(self):
        d = assess_national_transition_response_materialization(
            post_retrofit_design_load_surface_materialized=False,
            p65_required_supply_temperature_surface_materialized=True,
            b05_product_design_point_coverage_complete=False,
        )
        self.assertNotIn(
            "NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED",
            d.blockers,
        )
        self.assertIn(
            "NATIONAL_POST_RETROFIT_DESIGN_LOAD_SURFACE_REQUIRED",
            d.blockers,
        )
        self.assertIn(
            "B05_MATERIALIZED_DESIGN_POINT_COVERAGE_REQUIRED",
            d.blockers,
        )

    def test_registry_resolves_national_supply_surface_without_b05_promotion(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P98-S08"]["status"],
            "RESOLVED_FOR_REFERENCE_PROGRAMME_SET_PROPAGATION",
        )
        self.assertEqual(
            reg["B02-P98-S09"]["status"],
            "RESOLVED_AS_SET_VALUED_SURFACE",
        )
        self.assertIn(
            "B05_MATERIALIZED_DESIGN_POINT_COVERAGE_REQUIRED",
            reg["B02-P98-S09"]["residual_gap"],
        )
        self.assertEqual(
            reg["B02-P98-S10"]["status"],
            "REPORT_AND_COVERAGE_ANCHORS",
        )

    def test_source_provenance_is_explicit(self):
        sources = rows(SOURCES, "source_id")
        self.assertIn(
            "P98 category authority",
            sources["SRC-B06-MCS-021-2-1-2015"]["notes"],
        )
        self.assertIn(
            "P98 temperature-envelope support",
            sources["SRC-B02-EHI-HMR-2024-SURFACE-PENETRATION"]["notes"],
        )
        self.assertIn(
            "P98 validation",
            sources["SRC-B02-FRAUNHOFER-HP-TEMP-META-2023"]["notes"],
        )
        self.assertIn(
            "P98 Hungarian design validation",
            sources["SRC-B06-HU-ULLOI411-MEP-2024"]["notes"],
        )
        self.assertIn(
            "P98 programme-action support",
            sources["SRC-B02-HU-KEHOP-417-MAX-COST-2025"]["notes"],
        )

    def test_q_and_readiness_stay_fail_closed(self):
        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P98", q["notes"])
        self.assertIn(
            "RESOLVED_FOR_REFERENCE_PROGRAMME_SET_PROPAGATION",
            q["notes"],
        )
        self.assertIn(
            "FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P98", module["gate_note"])

        readiness = rows(READINESS, "component_id")
        self.assertEqual(
            readiness["SUPPLY_TEMPERATURE_EFFECT"]["readiness_percent"],
            "70",
        )
        self.assertEqual(
            readiness["B05_HANDOFF"]["readiness_percent"],
            "65",
        )
        self.assertIn("B02-P98", readiness["SUPPLY_TEMPERATURE_EFFECT"]["notes"])
        self.assertIn("B02-P98", readiness["B05_HANDOFF"]["notes"])

    def test_state_and_nonpromotion_boundaries(self):
        state = p98_state()
        self.assertEqual(state["stratum_count"], 14)
        self.assertIsNone(state["population_temperature_weights"])
        self.assertIsNone(state["national_supply_temperature_blocker"])
        self.assertEqual(
            state["status"],
            QUALIFIED_REFERENCE_PROGRAMME_SUPPLY_TEMPERATURE_SET,
        )
        self.assertIn(
            "B05_MATERIALIZED_DESIGN_POINT_COVERAGE_REQUIRED",
            state["independent_downstream_residuals"],
        )

        boundaries = semantic_boundaries()
        for item in (
            "NATIONAL_CATEGORY_SET_IS_NOT_NATIONAL_TEMPERATURE_DISTRIBUTION",
            "EMITTER_CLASS_IS_NOT_FIXED_SUPPLY_TEMPERATURE",
            "REFERENCE_PROGRAMME_55C_CEILING_IS_NOT_PHYSICAL_EQUIPMENT_LIMIT",
            "B05_W35_W45_W55_CONTROL_POINTS_ARE_NOT_BUILDING_TEMPERATURE_SNAPPING",
            "FOREIGN_MEAN_OPERATING_TEMPERATURE_IS_NOT_HUNGARIAN_DESIGN_TEMPERATURE",
            "P98_NATIONAL_SURFACE_IS_NOT_P65_RECORD_LEVEL_AUTHORITY",
        ):
            self.assertIn(item, boundaries)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "NATIONAL CATEGORY SET != NATIONAL TEMPERATURE DISTRIBUTION",
            "REFERENCE-PROGRAMME 55 C CEILING != PHYSICAL EQUIPMENT LIMIT",
            "RESOLVED_AS_SET_VALUED_SURFACE",
            "B02 remains **55%**",
            "SUPPLY_TEMPERATURE_EFFECT",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
