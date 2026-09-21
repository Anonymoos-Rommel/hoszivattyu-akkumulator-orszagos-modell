import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMANTICS = ROOT / "registry" / "b02_p63_design_temperature_semantics.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
DIMENSIONS = ROOT / "registry" / "archetype_dimensions.csv"
AUDIT = ROOT / "registry" / "b02_public_emitter_evidence_audit.csv"
SOURCES = ROOT / "registry" / "sources.csv"
ADMISSION = ROOT / "registry" / "b02_archetype_admission_gate.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P63_DESIGN_TEMPERATURE_SEMANTIC_REPAIR.md"


class B02P63DesignTemperatureSemanticRepairTests(unittest.TestCase):
    def test_q_b02_004_retires_baseline_temperature_distribution_requirement(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        q4 = rows["Q-B02-004"]
        self.assertEqual(q4["status"], "OPEN")
        self.assertIn("33–66%", q4["evidence_needed"])
        self.assertIn("P21/WBL", q4["evidence_needed"])
        self.assertIn("P65-kompatibilis", q4["evidence_needed"])
        self.assertIn("DESIGN_TEMPERATURE_DISTRIBUTION", q4["notes"])
        self.assertIn("RETIRED", q4["notes"])
        self.assertIn("TRANSITION_MODEL_POPULATION_WEIGHTING", q4["notes"])
        self.assertIn("2026-08-22", q4["notes"])
        self.assertIn("record-level evidence", q4["notes"])

    def test_heat_emitter_dimension_is_not_eligibility_input(self):
        with DIMENSIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["dimension_id"]: row for row in csv.DictReader(handle)}
        emitter = rows["DIM-B02-HEAT-EMITTER"]
        self.assertEqual(emitter["role"], "archetype_key")
        self.assertEqual(emitter["status"], "GAP")
        self.assertIn("nem aggregate technical-eligibility", emitter["aggregation_rule"])
        self.assertIn("P65", emitter["notes"])
        self.assertNotIn("Hiányzó hőleadó nem minősíthető alkalmasnak", emitter["unknown_policy"])

    def test_semantics_separate_current_design_transition_and_operation(self):
        with SEMANTICS.open(encoding="utf-8", newline="") as handle:
            rows = {row["semantic_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["B02-P63-S02"]["canonical_role"], "VALIDATION_CALIBRATION_INPUT")
        self.assertEqual(rows["B02-P63-S02"]["population_use"], "NO_MANDATORY_NATIONAL_DISTRIBUTION")
        self.assertEqual(rows["B02-P63-S03"]["canonical_role"], "DERIVED_TRANSITION_OUTPUT")
        self.assertEqual(rows["B02-P63-S03"]["record_use"], "YES_REQUIRED_FOR_B05_HANDOFF")
        self.assertEqual(rows["B02-P63-S04"]["canonical_role"], "MEASURED_OR_HEAT_WEIGHTED_OUTCOME")
        self.assertIn("DESIGN_TEMP_EQUALS_SEASONAL_OPERATING_TEMP", rows["B02-P63-S04"]["forbidden_inference"])
        self.assertIn("TRANSITION_MODEL_POPULATION_WEIGHTING", rows["B02-P63-S06"]["residual_gap"])
        self.assertNotIn("DESIGN_TEMPERATURE_DISTRIBUTION", rows["B02-P63-S06"]["residual_gap"])

    def test_external_authorities_are_registered_without_hungarian_weight_promotion(self):
        with SOURCES.open(encoding="utf-8", newline="") as handle:
            sources = {row["source_id"]: row for row in csv.DictReader(handle)}
        self.assertIn("SRC-B02-EHI-EPBD-LOW-TEMP-EMITTERS-2021", sources)
        self.assertIn("SRC-B02-FRAUNHOFER-HP-TEMP-META-2023", sources)
        self.assertIn("not an emitter-specific feature", sources["SRC-B02-EHI-EPBD-LOW-TEMP-EMITTERS-2021"]["notes"])
        self.assertIn("n=23 mixed", sources["SRC-B02-FRAUNHOFER-HP-TEMP-META-2023"]["notes"])
        self.assertIn("not Hungarian prevalence", sources["SRC-B02-FRAUNHOFER-HP-TEMP-META-2023"]["notes"])

    def test_field_validation_preserves_mixed_system_overlap(self):
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            rows = {row["audit_id"]: row for row in csv.DictReader(handle)}
        ehi = rows["B02-P63-A14"]
        field = rows["B02-P63-A15"]
        self.assertEqual(ehi["status"], "QUALIFIED_BOUNDARY_ONLY")
        self.assertIn("NO_HUNGARIAN_POPULATION_WEIGHT", ehi["blockers"])
        self.assertEqual(field["status"], "QUALIFIED_VALIDATION_ONLY")
        self.assertIn("NOT_HUNGARIAN_PREVALENCE", field["blockers"])
        self.assertIn("mixed radiator+floor systems n=23", field["notes"])

    def test_legacy_archetype_gate_is_marked_as_superseded_at_programme_layer(self):
        with ADMISSION.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        row = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertIn("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE", row["current_blockers"])
        self.assertIn("P63 CURRENT-PROGRAMME SUPERSESSION", row["notes"])
        self.assertIn("post-retrofit temperature is P65-derived", row["notes"])

    def test_module_readiness_stays_fixed(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        b02 = rows["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("33–66%", b02["gate_note"])
        self.assertIn("P63", b02["gate_note"])
        self.assertIn("TRANSITION_MODEL_SET_PROPAGATION", b02["gate_note"])

    def test_source_pack_freezes_causal_direction(self):
        text = SOURCE_PACK.read_text(encoding="utf-8")
        for boundary in (
            "CURRENT DESIGN TEMPERATURE != POST-RETROFIT DESIGN TEMPERATURE",
            "EMITTER CLASS != FIXED WATER TEMPERATURE",
            "BASELINE NATIONAL DESIGN-TEMPERATURE DISTRIBUTION != REQUIRED PROGRAMME INPUT",
            "POST-RETROFIT DESIGN TEMPERATURE = TRANSITION-DERIVED OUTPUT",
            "MIXED SYSTEM != ONE FIXED TEMPERATURE",
            "RADIATOR PRESENCE != HIGH-TEMPERATURE REQUIREMENT",
            "TRANSITION_MODEL_POPULATION_WEIGHTING",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
