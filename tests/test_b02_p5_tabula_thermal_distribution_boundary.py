from pathlib import Path
import csv
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry/b02_tabula_thermal_distribution_audit.csv"
GAPS = ROOT / "registry/b02_s0_s2_evidence_gap_matrix.csv"
MANIFEST = ROOT / "evidence/history/SRC-B02-TABULA-HU-TYPOLOGY-BROCHURE-2014/manifest.csv"
DOC = ROOT / "docs/source_packs/B02_P5_TABULA_THERMAL_DISTRIBUTION_BOUNDARY.md"


class B02P5TabulaThermalDistributionBoundaryTests(unittest.TestCase):
    def test_tabula_hu_s22_is_explicitly_not_available_for_gate(self):
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        s22 = rows["TABULA-HU-S2-2"]
        self.assertEqual("NOT_AVAILABLE", s22["availability_status"])
        self.assertEqual("Q", s22["evidence_status"])
        self.assertEqual("NO_TECHNICAL_GATE", s22["gate_use"])

    def test_heat_generation_is_not_promoted_to_emitter_evidence(self):
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual("AVAILABLE", rows["TABULA-HU-S2-3"]["availability_status"])
        self.assertEqual("CONTEXT_ONLY", rows["TABULA-HU-S2-3"]["gate_use"])
        self.assertEqual("NOT_PROVEN", rows["TABULA-HU-CURRENT-EMITTER"]["availability_status"])
        self.assertEqual("Q", rows["TABULA-HU-CURRENT-EMITTER"]["evidence_status"])
        self.assertEqual("NOT_PROVEN", rows["TABULA-HU-DESIGN-TEMPERATURE"]["availability_status"])

    def test_existing_b02_gaps_remain_fail_closed(self):
        with GAPS.open(encoding="utf-8", newline="") as handle:
            gaps = {row["gap_id"]: row for row in csv.DictReader(handle)}
        emitter = gaps["GAP-B02-S2-HEAT-EMITTER"]
        temp = gaps["GAP-B02-S2-DESIGN-TEMPERATURE"]
        hydraulic = gaps["GAP-B02-S2-HYDRAULIC"]
        self.assertEqual("Q", emitter["evidence_status"])
        self.assertEqual("no", emitter["allow_for_gate"])
        self.assertEqual("Q", temp["evidence_status"])
        self.assertEqual("Q", hydraulic["evidence_status"])
        self.assertEqual("no", hydraulic["allow_for_gate"])
        self.assertIn("TABULA", emitter["current_source_coverage"])
        self.assertIn("S-2.2", hydraulic["current_source_coverage"])

    def test_history_manifest_is_cleared_but_binary_is_pending(self):
        with MANIFEST.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("REPOSITORY_COPY_CLEARED_ATTRIBUTION_REQUIRED", row["reuse_status"])
        self.assertEqual("PENDING_BINARY_ACQUISITION", row["snapshot_status"])
        self.assertEqual("", row["sha256"])
        self.assertTrue(row["repo_snapshot_path"].endswith("HU_TABULA_TypologyBrochure_BME.pdf"))
        self.assertIn("base64", row["notes"])

    def test_source_pack_freezes_core_non_inference_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "HEAT GENERATION DATA != HEAT DISTRIBUTION DATA != CURRENT EMITTER EVIDENCE",
            "S-2.2",
            "Q-B02-004",
            "PENDING_BINARY_ACQUISITION",
            "No readiness uplift",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
