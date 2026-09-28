import csv
import math
import unittest
from pathlib import Path

from modules.B05.fcc06_direct_runtime import (
    CROSS_REVISION_FCC06_2PIPE_3ROW_WATER_CONTENT_L,
    CROSS_REVISION_VOLUME_NOT_EXACT_MASS,
    DIRECT_RUNTIME_QUALIFIED,
    Q_EXACT_WATER_MASS_REQUIRED,
    SOURCE_MEAN_MEDIUM_HEAT_CAPACITY_J_PER_KG_K,
    direct_runtime_step,
    mass_from_volume_l,
    p57_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p57_fcc06_water_content_lineage.csv"
SOURCES = ROOT / "registry" / "sources.csv"
HP_SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P57FCC06DirectRuntimeTests(unittest.TestCase):
    def test_cross_revision_volume_is_not_silently_mass(self):
        self.assertEqual(1.7, CROSS_REVISION_FCC06_2PIPE_3ROW_WATER_CONTENT_L)
        r = mass_from_volume_l(
            volume_l=1.7,
            density_kg_m3=1000.0,
            exact_study_volume_binding=False,
        )
        self.assertEqual(CROSS_REVISION_VOLUME_NOT_EXACT_MASS, r.status)
        self.assertIsNone(r.water_mass_kg)

    def test_exact_bound_volume_still_requires_explicit_density(self):
        r = mass_from_volume_l(
            volume_l=1.7,
            density_kg_m3=None,
            exact_study_volume_binding=True,
        )
        self.assertIsNone(r.water_mass_kg)
        self.assertIn("DENSITY", r.status)

    def test_direct_runtime_fails_closed_without_mass(self):
        r = direct_runtime_step(
            previous_outlet_temperature_c=35.0,
            inlet_temperature_c=45.0,
            zone_air_temperature_c=20.0,
            fan_speed="M",
            water_flow_kg_s=0.027,
            water_mass_kg=None,
            medium_heat_capacity_j_per_kg_k=SOURCE_MEAN_MEDIUM_HEAT_CAPACITY_J_PER_KG_K,
            timestep_s=60.0,
        )
        self.assertEqual(Q_EXACT_WATER_MASS_REQUIRED, r.status)
        self.assertIsNone(r.outlet_temperature_c)

    def test_direct_runtime_is_executable_with_explicit_physical_inputs(self):
        r = direct_runtime_step(
            previous_outlet_temperature_c=35.0,
            inlet_temperature_c=45.0,
            zone_air_temperature_c=20.0,
            fan_speed="M",
            water_flow_kg_s=0.027,
            water_mass_kg=1.7,
            medium_heat_capacity_j_per_kg_k=4504.0,
            timestep_s=60.0,
        )
        self.assertEqual(DIRECT_RUNTIME_QUALIFIED, r.status)
        self.assertIsNotNone(r.outlet_temperature_c)
        self.assertIsNotNone(r.thermal_power_w)
        self.assertGreater(r.state_time_constant_s, 0)
        self.assertTrue(math.isfinite(r.outlet_temperature_c))
        self.assertIn(
            "FCC06_DIRECT_PHYSICAL_RUNTIME != HEM_TAU_OUT_MAPPING",
            p57_boundaries(),
        )

    def test_source_mean_heat_capacity_is_source_specific(self):
        self.assertEqual(4504.0, SOURCE_MEAN_MEDIUM_HEAT_CAPACITY_J_PER_KG_K)
        self.assertIn(
            "SOURCE_MEAN_CW_4504 != UNIVERSAL_WATER_HEAT_CAPACITY",
            p57_boundaries(),
        )

    def test_catalogue_sources_are_registered(self):
        ids = {r["source_id"] for r in rows(SOURCES)}
        hp_ids = {r["source_id"] for r in rows(HP_SOURCES)}
        for sid in (
            "SRC-B05-TRANE-UNITRANE-UNT-PRC006-E4-2010",
            "SRC-B05-TRANE-UNITRANE-PROD-PRC014-E4-2006",
        ):
            self.assertIn(sid, ids)
            self.assertIn(sid, hp_ids)

    def test_registry_resolves_direct_runtime_but_not_mass(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            "RESOLVED_BY_DIRECT_RUNTIME_PATH",
            reg["STATE_DEPENDENT_FCU_RESPONSE_TO_HEM_MAPPING_OR_DIRECT_RUNTIME"]["status"],
        )
        self.assertEqual(
            "OPEN_NARROWED_TO_CITED_EDITION_OR_DIRECT_MASS",
            reg["FCC06_WATER_MASS_AUTHORITY"]["status"],
        )

    def test_q_b05_004_narrows_without_false_scalar_closure(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual("OPEN", q["status"])
        self.assertIn("B05-P57", q["notes"])
        self.assertIn("EXACT_CITED_EDITION_FCC06_WATER_CONTENT_OR_DIRECT_WATER_MASS_REQUIRED", q["notes"])
        variables = {r["variable_id"]: r for r in rows(VARIABLES)}
        self.assertEqual("Q", variables["VAR-B05-FANCOIL-OBS-EMITTER-RESPONSE-TIME"]["status"])

    def test_no_mechanical_readiness_uplift(self):
        ready = {r["component_id"]: r for r in rows(READINESS)}
        self.assertEqual("45", ready["PART_LOAD_MODULATION"]["readiness_percent"])
        self.assertIn("P57", ready["PART_LOAD_MODULATION"]["notes"])
        modules = {r["module_id"]: r for r in rows(MODULES)}
        self.assertEqual("64", modules["B05"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
