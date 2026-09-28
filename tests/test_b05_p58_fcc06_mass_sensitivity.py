import csv
import math
import unittest
from pathlib import Path

from modules.B05.fcc06_mass_sensitivity import (
    ASS_CROSS_REVISION_SENSITIVITY,
    CROSS_REVISION_SOURCE_IDS,
    CROSS_REVISION_WATER_CONTENT_L,
    cross_revision_sensitivity_mass_kg,
    normalized_state_time_constant_s_per_kg,
    p58_boundaries,
    steady_state_outlet_temperature_c,
)
from modules.B05.fcc06_direct_runtime import direct_runtime_step

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p58_fcc06_mass_sensitivity.csv"
SOURCES = ROOT / "registry" / "sources.csv"
HP_SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P58FCC06MassSensitivityTests(unittest.TestCase):
    def test_two_cross_revision_sources_support_same_candidate(self):
        self.assertEqual(1.7, CROSS_REVISION_WATER_CONTENT_L)
        self.assertEqual(2, len(CROSS_REVISION_SOURCE_IDS))
        ids = {r["source_id"] for r in rows(SOURCES)}
        hp_ids = {r["source_id"] for r in rows(HP_SOURCES)}
        for sid in CROSS_REVISION_SOURCE_IDS:
            self.assertIn(sid, ids)
            self.assertIn(sid, hp_ids)

    def test_cross_revision_mass_is_ass_only(self):
        r = cross_revision_sensitivity_mass_kg(density_kg_m3=1000.0)
        self.assertEqual(ASS_CROSS_REVISION_SENSITIVITY, r.status)
        self.assertEqual("ASS", r.evidence_status)
        self.assertAlmostEqual(1.7, r.water_mass_kg)

    def test_steady_state_is_independent_of_mass(self):
        kwargs = dict(
            inlet_temperature_c=45.0,
            zone_air_temperature_c=20.0,
            fan_speed="M",
            water_flow_kg_s=0.027,
            medium_heat_capacity_j_per_kg_k=4504.0,
        )
        expected = steady_state_outlet_temperature_c(**kwargs)
        for mass in (0.5, 1.0, 1.7, 3.0):
            r = direct_runtime_step(
                previous_outlet_temperature_c=10.0,
                water_mass_kg=mass,
                timestep_s=100000.0,
                **kwargs,
            )
            self.assertTrue(math.isclose(r.outlet_temperature_c, expected, rel_tol=0, abs_tol=1e-10))

    def test_tau_scales_linearly_with_mass(self):
        norm = normalized_state_time_constant_s_per_kg(
            fan_speed="M",
            water_flow_kg_s=0.027,
            medium_heat_capacity_j_per_kg_k=4504.0,
        )
        r1 = direct_runtime_step(
            previous_outlet_temperature_c=35.0,
            inlet_temperature_c=45.0,
            zone_air_temperature_c=20.0,
            fan_speed="M",
            water_flow_kg_s=0.027,
            water_mass_kg=1.0,
            medium_heat_capacity_j_per_kg_k=4504.0,
            timestep_s=60.0,
        )
        r2 = direct_runtime_step(
            previous_outlet_temperature_c=35.0,
            inlet_temperature_c=45.0,
            zone_air_temperature_c=20.0,
            fan_speed="M",
            water_flow_kg_s=0.027,
            water_mass_kg=2.0,
            medium_heat_capacity_j_per_kg_k=4504.0,
            timestep_s=60.0,
        )
        self.assertAlmostEqual(norm, r1.state_time_constant_s)
        self.assertAlmostEqual(2.0 * norm, r2.state_time_constant_s)

    def test_exact_2010_identity_is_not_claimed_from_stability(self):
        self.assertIn(
            "CROSS_REVISION_STABILITY != EXACT_STUDY_IDENTITY",
            p58_boundaries(),
        )
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            "QUALIFIED_REPEATED_VALUE",
            reg["FCC06_CROSS_REVISION_WATER_CONTENT_STABILITY"]["status"],
        )
        self.assertIn(
            "EXACT_CITED_EDITION",
            reg["FCC06_CROSS_REVISION_WATER_CONTENT_STABILITY"]["residual_gap"],
        )

    def test_q_b05_004_and_audit_narrow_mass_to_transient_validation(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual("OPEN", q["status"])
        self.assertIn("B05-P58", q["notes"])
        self.assertIn("FOR_OBS_TRANSIENT_VALIDATION", q["notes"])
        audit = {r["blocker_id"]: r for r in rows(AUDIT)}["Q-B05-004"]
        self.assertIn("EXACT_CITED_EDITION_FCC06_WATER_CONTENT_OR_DIRECT_WATER_MASS_REQUIRED_FOR_OBS_TRANSIENT_VALIDATION", audit["validation_debt"])
        self.assertIn("steady state", audit["closure_requirement"])

    def test_no_mechanical_readiness_uplift(self):
        ready = {r["component_id"]: r for r in rows(READINESS)}
        self.assertGreaterEqual(int(ready["PART_LOAD_MODULATION"]["readiness_percent"]), 45)
        self.assertIn("P58", ready["PART_LOAD_MODULATION"]["notes"])
        modules = {r["module_id"]: r for r in rows(MODULES)}
        self.assertEqual("64", modules["B05"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
