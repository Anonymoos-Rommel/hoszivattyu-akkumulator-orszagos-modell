import csv
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    PrimaryEnergyAuthorityCandidate,
    Q,
    QUALIFIED,
    assess_direct_primary_energy_authority,
)


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry" / "b02_primary_energy_authority_audit.csv"
P12 = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
P9 = ROOT / "registry" / "b02_archetype_admission_gate.csv"
MANIFEST = ROOT / "data" / "processed" / "b02" / "ksh_energy_extract_manifest.json"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P17_PRIMARY_ENERGY_WBL_LINK_AUTHORITY.md"


class B02P17PrimaryEnergyWblLinkTests(unittest.TestCase):
    def test_direct_complete_wbl_primary_energy_can_qualify(self):
        candidate = PrimaryEnergyAuthorityCandidate(
            source_id="FIXTURE-DIRECT-WBL-PRIMARY-ENERGY",
            reference_year=2022,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            evidence_status="DER",
            primary_energy_metric="PRIMARY_ENERGY_BIN",
            publishes_complete_assignment=True,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        decision = assess_direct_primary_energy_authority(candidate)
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.reasons, ())

    def test_linked_certificate_sample_is_not_complete_direct_authority(self):
        candidate = PrimaryEnergyAuthorityCandidate(
            source_id="SRC-B02-KSH-ENERGY-METHOD-2025",
            reference_year=2022,
            source_universe="LINKED_CERTIFICATE_SAMPLE_OF_FULL_CENSUS_STOCK",
            source_grain="DWELLING_RECORD",
            evidence_status="OBS",
            primary_energy_metric="SPECIFIC_PRIMARY_ENERGY_KWH_M2_YEAR",
            publishes_complete_assignment=False,
            wbl_compatible_join_key=False,
            reproducible_repository_binding=False,
        )
        decision = assess_direct_primary_energy_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.reasons,
            (
                "NOT_OCCUPIED_DWELLING_STOCK",
                "NO_COMPLETE_PRIMARY_ENERGY_ASSIGNMENT",
                "NO_WBL_COMPATIBLE_JOIN_KEY",
                "NO_REPRODUCIBLE_REPOSITORY_BINDING",
            ),
        )

    def test_ksh_full_stock_random_forest_is_model_not_direct_evidence(self):
        candidate = PrimaryEnergyAuthorityCandidate(
            source_id="SRC-B02-KSH-ENERGY-METHOD-2025",
            reference_year=2022,
            source_universe="FULL_CENSUS_DWELLING_STOCK",
            source_grain="DWELLING_RECORD_INTERNAL",
            evidence_status="MODELLED",
            primary_energy_metric="SPECIFIC_PRIMARY_ENERGY_KWH_M2_YEAR",
            publishes_complete_assignment=True,
            wbl_compatible_join_key=False,
            reproducible_repository_binding=False,
        )
        decision = assess_direct_primary_energy_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.reasons,
            (
                "NOT_OCCUPIED_DWELLING_STOCK",
                "GRAIN_NOT_DIRECT_WBL_LINK",
                "EVIDENCE_NOT_OBS_OR_DER",
                "NO_WBL_COMPATIBLE_JOIN_KEY",
                "NO_REPRODUCIBLE_REPOSITORY_BINDING",
            ),
        )

    def test_primary_energy_audit_has_exact_two_bounded_candidates(self):
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            rows = {row["control_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(
            set(rows),
            {
                "B02-P17-KSH-LINKED-CERTIFICATES",
                "B02-P17-KSH-RF-FULL-STOCK",
            },
        )
        linked = rows["B02-P17-KSH-LINKED-CERTIFICATES"]
        model = rows["B02-P17-KSH-RF-FULL-STOCK"]
        self.assertEqual(linked["evidence_status"], "OBS")
        self.assertEqual(linked["publishes_complete_assignment"], "no")
        self.assertEqual(linked["direct_gate_status"], "Q")
        self.assertEqual(model["evidence_status"], "MODELLED")
        self.assertEqual(model["publishes_complete_assignment"], "yes")
        self.assertEqual(model["direct_gate_status"], "Q")
        self.assertEqual(model["p12_candidate_status"], "Q")
        self.assertEqual(model["q_b02_002_effect"], "OPEN")

    def test_p17_rf_candidate_is_superseded_by_reproducible_p21_public_linkage(self):
        with P12.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        row = rows["CALIBRATED_PRIMARY_ENERGY_LINKAGE"]
        self.assertEqual(
            row["current_model_id"],
            "B02-P21-PUBLIC-KSH-PRIMARY-ENERGY-LINKAGE",
        )
        self.assertEqual(row["approval_status"], "NOT_APPROVED")
        self.assertEqual(row["reference_period_defined"], "yes")
        self.assertEqual(row["target_grain_wbl_compatible"], "yes")
        self.assertEqual(row["representativeness_diagnostics"], "yes")
        self.assertEqual(row["validation_metrics"], "yes")
        self.assertEqual(row["marginal_reconciliation"], "yes")
        self.assertEqual(row["uncertainty_method"], "yes")
        self.assertEqual(row["uncertainty_propagation"], "yes")
        self.assertEqual(row["independence_assumption_controlled"], "yes")
        self.assertEqual(row["output_evidence_status"], "MODELLED")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(row["blockers"], "NO_JOSEPH_APPROVAL")

    def test_current_archetype_blockers_remain_exact(self):
        with P9.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        current = rows["CURRENT_STOCK_ARCHETYPE_ASSIGNMENT"]
        technical = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(
            current["current_blockers"],
            "NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY;NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY",
        )
        self.assertEqual(current["current_status"], "Q")
        self.assertIn("NO_CURRENT_HEAT_EMITTER_EVIDENCE", technical["current_blockers"])
        self.assertIn("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE", technical["current_blockers"])

    def test_repository_energy_controls_are_preserved(self):
        import json

        controls = json.loads(MANIFEST.read_text(encoding="utf-8"))["controls"]
        self.assertEqual(controls["census_dwelling_universe"], 4580538)
        self.assertEqual(controls["linked_energy_certificates"], 279020)
        self.assertEqual(controls["distribution_rows"], 944)
        self.assertEqual(controls["all_records_in_published_bins"], 4575790)
        self.assertEqual(controls["published_bin_residual"], 4748)

    def test_questions_readiness_and_current_dispatch_state_remain_fail_closed(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            questions = {row["question_id"]: row for row in csv.DictReader(handle)}
        for question_id in ("Q-B02-001", "Q-B02-002", "Q-B02-004"):
            self.assertEqual(questions[question_id]["status"], "OPEN")

        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            modules = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(modules["B02"]["readiness_percent"], "55")
        self.assertIn("B02-P17", modules["B02"]["gate_note"])
        self.assertIn("no readiness uplift", modules["B02"]["gate_note"].lower())
        self.assertIn("OÉNY pilot kérés 2026-08-22-én elküldésre került", modules["B02"]["gate_note"])
        self.assertIn("AWAITING_RESPONSE", modules["B02"]["gate_note"])
        self.assertNotIn("OÉNY nem lett elküldve", modules["B02"]["gate_note"])

    def test_document_freezes_primary_energy_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("PRIMARY-ENERGY MODEL EXISTS != REPRODUCIBLE WBL LINK AUTHORITY", text)
        self.assertIn("PUBLIC AGGREGATE MODEL OUTPUT != RECORD-LEVEL WBL BINDING", text)
        self.assertIn("LINKED CERTIFICATE SAMPLE != COMPLETE OCCUPIED-STOCK PRIMARY-ENERGY ASSIGNMENT", text)
        self.assertIn("RAW OBS/DER LINK TOKEN != DIRECT-LINK ADMISSION", text)
        self.assertIn("KSH-RF-2022-PRIMARY-ENERGY", text)
        self.assertIn("B02 readiness: **55%**", text)
        self.assertIn("No external request or microdata transmission is authorized", text)


if __name__ == "__main__":
    unittest.main()
