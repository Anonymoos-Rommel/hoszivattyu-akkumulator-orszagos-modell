import csv
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    CONTRACTED,
    Q,
    QUALIFIED,
    StockArchetypeInputs,
    assess_stock_archetype,
    assess_technical_readiness_enrichment,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_archetype_admission_gate.csv"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P9_ARCHETYPE_ADMISSION_GATE.md"


CURRENT = StockArchetypeInputs(
    schema_status=CONTRACTED,
    wbl_joint_materialized_complete=True,
    building_type_link_status="ASS",
    primary_energy_link_status="MODELLED_UNLINKED",
)


class B02P9ArchetypeAdmissionGateTests(unittest.TestCase):
    def test_contracted_schema_does_not_mint_current_stock_archetype(self):
        decision = assess_stock_archetype(CURRENT)
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            set(decision.blockers),
            {
                "NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY",
                "NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY",
            },
        )

    def test_ass_building_type_link_fails_closed_even_with_other_links(self):
        candidate = StockArchetypeInputs(
            schema_status=CONTRACTED,
            wbl_joint_materialized_complete=True,
            building_type_link_status="ASS",
            primary_energy_link_status="MODELLED_LINKED",
        )
        decision = assess_stock_archetype(candidate)
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.blockers,
            (
                "NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY",
                "CALIBRATED_PRIMARY_ENERGY_MODEL_NOT_ADMITTED",
            ),
        )

    def test_modelled_energy_requires_explicit_link_authority(self):
        candidate = StockArchetypeInputs(
            schema_status=CONTRACTED,
            wbl_joint_materialized_complete=True,
            building_type_link_status="DER",
            primary_energy_link_status="MODELLED_UNLINKED",
            building_type_direct_authority_status=QUALIFIED,
        )
        decision = assess_stock_archetype(candidate)
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.blockers, ("NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY",))

    def test_raw_real_link_tokens_require_separate_direct_admission(self):
        candidate = StockArchetypeInputs(
            schema_status=CONTRACTED,
            wbl_joint_materialized_complete=True,
            building_type_link_status="OBS",
            primary_energy_link_status="DER",
        )
        decision = assess_stock_archetype(candidate)
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.blockers,
            (
                "BUILDING_TYPE_DIRECT_LINK_NOT_ADMITTED",
                "PRIMARY_ENERGY_DIRECT_LINK_NOT_ADMITTED",
            ),
        )

    def test_complete_explicit_stock_authority_can_qualify(self):
        candidate = StockArchetypeInputs(
            schema_status=CONTRACTED,
            wbl_joint_materialized_complete=True,
            building_type_link_status="APPROVED_CALIBRATED_MODEL",
            primary_energy_link_status="MODELLED_LINKED",
            building_type_model_admission_status=QUALIFIED,
            primary_energy_model_admission_status=QUALIFIED,
        )
        decision = assess_stock_archetype(candidate)
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_technical_enrichment_requires_emitter_and_temperature(self):
        candidate = StockArchetypeInputs(
            schema_status=CONTRACTED,
            wbl_joint_materialized_complete=True,
            building_type_link_status="DER",
            primary_energy_link_status="DER",
            building_type_direct_authority_status=QUALIFIED,
            primary_energy_direct_authority_status=QUALIFIED,
        )
        decision = assess_technical_readiness_enrichment(
            candidate,
            heat_emitter_status="Q",
            design_temperature_status="Q",
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.blockers,
            (
                "NO_CURRENT_HEAT_EMITTER_EVIDENCE",
                "NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
            ),
        )

    def test_raw_real_readiness_tokens_require_separate_direct_admission(self):
        candidate = StockArchetypeInputs(
            schema_status=CONTRACTED,
            wbl_joint_materialized_complete=True,
            building_type_link_status="OBS",
            primary_energy_link_status="DER",
            building_type_direct_authority_status=QUALIFIED,
            primary_energy_direct_authority_status=QUALIFIED,
        )
        decision = assess_technical_readiness_enrichment(
            candidate,
            heat_emitter_status="OBS",
            design_temperature_status="DER",
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.blockers,
            (
                "HEAT_EMITTER_DIRECT_EVIDENCE_NOT_ADMITTED",
                "DESIGN_TEMPERATURE_DIRECT_EVIDENCE_NOT_ADMITTED",
            ),
        )

    def test_technical_enrichment_can_qualify_only_after_real_admitted_evidence(self):
        candidate = StockArchetypeInputs(
            schema_status=CONTRACTED,
            wbl_joint_materialized_complete=True,
            building_type_link_status="OBS",
            primary_energy_link_status="DER",
            building_type_direct_authority_status=QUALIFIED,
            primary_energy_direct_authority_status=QUALIFIED,
        )
        decision = assess_technical_readiness_enrichment(
            candidate,
            heat_emitter_status="OBS",
            design_temperature_status="DER",
            heat_emitter_direct_authority_status=QUALIFIED,
            design_temperature_direct_authority_status=QUALIFIED,
        )
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_machine_registry_separates_schema_stock_and_readiness_claims(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(
            set(rows),
            {
                "ARCHETYPE_DIMENSION_SCHEMA",
                "CURRENT_STOCK_ARCHETYPE_ASSIGNMENT",
                "TECHNICAL_READINESS_ARCHETYPE",
            },
        )
        self.assertEqual(rows["ARCHETYPE_DIMENSION_SCHEMA"]["current_status"], "CONTRACTED")
        self.assertEqual(rows["CURRENT_STOCK_ARCHETYPE_ASSIGNMENT"]["current_status"], "Q")
        self.assertEqual(rows["TECHNICAL_READINESS_ARCHETYPE"]["current_status"], "Q")

    def test_open_questions_remain_fail_closed(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        for question_id in ("Q-B02-001", "Q-B02-002", "Q-B02-004"):
            self.assertEqual(rows[question_id]["status"], "OPEN")

    def test_b02_readiness_remains_55(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["B02"]["readiness_percent"], "55")

    def test_document_freezes_non_equivalence_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn(
            "CONTRACTED DIMENSION SCHEMA != POPULATED CURRENT-STOCK ARCHETYPE != TECHNICAL READINESS ARCHETYPE",
            text,
        )
        self.assertIn(
            "SOURCE-NATIVE COMPLETE WBL011 JOINT != REPOSITORY-MATERIALIZED COMPLETE WBL011 JOINT != CURRENT-STOCK ARCHETYPE",
            text,
        )
        self.assertIn("MODELLED ENERGY PANEL != PRIMARY-ENERGY-TO-WBL LINK AUTHORITY", text)
        self.assertIn("RAW OBS/DER LINK TOKEN != DIRECT-LINK ADMISSION", text)
        self.assertIn("RAW OBS/DER READINESS TOKEN != TECHNICAL DIRECT AUTHORITY", text)
        self.assertIn("B02 readiness változatlanul **55%**", text)
        self.assertIn("WBL011 repository full-joint materialization: `MATERIALIZED`", text)


if __name__ == "__main__":
    unittest.main()
