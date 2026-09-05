import csv
import unittest
from pathlib import Path

from modules.B02.building_type_authority_gate import (
    BuildingTypeAuthorityCandidate,
    Q,
    QUALIFIED,
    assess_building_type_authority,
)


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry" / "b02_current_building_type_authority_audit.csv"
COVERAGE = ROOT / "data" / "processed" / "b02" / "ksh_energy_coverage_2022.csv"
P9_GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P16_CURRENT_BUILDING_TYPE_DIRECT_LINK_AUTHORITY.md"


class B02P16CurrentBuildingTypeDirectLinkTests(unittest.TestCase):
    def test_coarse_margin_is_not_direct_wbl_link(self):
        candidate = BuildingTypeAuthorityCandidate(
            source_id="FIXTURE-COARSE-MARGIN",
            reference_year=2022,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="COUNTY_X_SETTLEMENT_TYPE",
            building_type_taxonomy="FAMILY_HOUSE_VS_MULTI_DWELLING_COMPATIBLE",
            evidence_status="OBS",
            publishes_stock_distribution=True,
            wbl_compatible_join_key=True,
        )
        decision = assess_building_type_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.reasons, ("GRAIN_NOT_DIRECT_WBL_LINK",))

    def test_direct_full_joint_can_qualify(self):
        candidate = BuildingTypeAuthorityCandidate(
            source_id="FIXTURE-DIRECT-WBL-JOINT",
            reference_year=2022,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            building_type_taxonomy="FAMILY_HOUSE_VS_MULTI_DWELLING_COMPATIBLE",
            evidence_status="DER",
            publishes_stock_distribution=True,
            wbl_compatible_join_key=True,
        )
        decision = assess_building_type_authority(candidate)
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.reasons, ())

    def test_current_ksh_analytic_classification_is_not_public_direct_authority(self):
        candidate = BuildingTypeAuthorityCandidate(
            source_id="SRC-B02-KSH-ENERGY-METHOD-2025",
            reference_year=2022,
            source_universe="FULL_CENSUS_DWELLING_STOCK",
            source_grain="DWELLING_RECORD",
            building_type_taxonomy="FAMILY_HOUSE_VS_MULTI_DWELLING_COMPATIBLE",
            evidence_status="OBS",
            publishes_stock_distribution=False,
            wbl_compatible_join_key=False,
        )
        decision = assess_building_type_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertIn("NOT_OCCUPIED_DWELLING_STOCK", decision.reasons)
        self.assertIn("NO_STOCK_DISTRIBUTION", decision.reasons)
        self.assertIn("NO_WBL_COMPATIBLE_JOIN_KEY", decision.reasons)
        self.assertNotIn("GRAIN_NOT_DIRECT_WBL_LINK", decision.reasons)

    def test_current_audit_contains_p16_ksh_method_row(self):
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            rows = {row["control_id"]: row for row in csv.DictReader(handle)}
        row = rows["B02-P16-KSH-ENERGY-METHOD"]
        self.assertEqual(row["source_id"], "SRC-B02-KSH-ENERGY-METHOD-2025")
        self.assertEqual(row["reference_period"], "2022")
        self.assertEqual(row["source_universe"], "FULL_CENSUS_DWELLING_STOCK")
        self.assertEqual(row["source_grain"], "DWELLING_RECORD")
        self.assertEqual(row["gate_status"], "Q")
        self.assertEqual(row["q_b02_002_effect"], "OPEN")
        self.assertEqual(row["publishes_occupied_stock_distribution"], "no")
        self.assertEqual(row["wbl_compatible_join_key"], "no")

    def test_published_energy_bins_do_not_equal_complete_census_stock(self):
        with COVERAGE.open(encoding="utf-8", newline="") as handle:
            rows = {row["metric"]: row for row in csv.DictReader(handle)}
        family = int(rows["family_house_records_in_published_bins"]["value"])
        multi = int(rows["multi_dwelling_records_in_published_bins"]["value"])
        published = int(rows["all_records_in_published_bins"]["value"])
        census = int(rows["census_dwelling_universe"]["value"])
        residual = int(rows["published_bin_residual"]["value"])
        self.assertEqual(family, 2881310)
        self.assertEqual(multi, 1694480)
        self.assertEqual(family + multi, published)
        self.assertEqual(published, 4575790)
        self.assertEqual(census, 4580538)
        self.assertEqual(census - published, residual)
        self.assertEqual(residual, 4748)
        self.assertEqual(rows["family_house_records_in_published_bins"]["evidence_status"], "MODELLED")
        self.assertEqual(rows["multi_dwelling_records_in_published_bins"]["evidence_status"], "MODELLED")

    def test_current_archetype_blockers_are_unchanged(self):
        with P9_GATE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        current = rows["CURRENT_STOCK_ARCHETYPE_ASSIGNMENT"]
        technical = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(current["current_status"], "Q")
        self.assertEqual(
            current["current_blockers"],
            "NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY;NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY",
        )
        self.assertEqual(technical["current_status"], "Q")
        self.assertIn("NO_CURRENT_HEAT_EMITTER_EVIDENCE", technical["current_blockers"])
        self.assertIn("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE", technical["current_blockers"])

    def test_questions_readiness_and_no_send_remain_fail_closed(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            questions = {row["question_id"]: row for row in csv.DictReader(handle)}
        for question_id in ("Q-B02-001", "Q-B02-002", "Q-B02-004"):
            self.assertEqual(questions[question_id]["status"], "OPEN")

        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            modules = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(modules["B02"]["readiness_percent"], "55")
        self.assertIn("B02-P16", modules["B02"]["gate_note"])
        self.assertIn("no readiness uplift", modules["B02"]["gate_note"].lower())
        self.assertIn("OÉNY nem lett elküldve", modules["B02"]["gate_note"])

    def test_document_freezes_direct_link_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("COARSE BUILDING-TYPE MARGIN != WBL SUBCELL JOINT", text)
        self.assertIn("MATCHED MARGINS != DIRECT LINK", text)
        self.assertIn("MODELLED ENERGY-BIN COUNTS != COMPLETE BUILDING-TYPE STOCK DISTRIBUTION", text)
        self.assertIn("WBL_FULL_JOINT", text)
        self.assertIn("DWELLING_RECORD", text)
        self.assertIn("No external request is sent by this slice", text)
        self.assertIn("B02 readiness: **55%**", text)


if __name__ == "__main__":
    unittest.main()
