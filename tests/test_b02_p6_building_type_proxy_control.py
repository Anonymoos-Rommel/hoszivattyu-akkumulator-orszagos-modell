from pathlib import Path
import csv
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "registry/b02_building_type_proxy_control.csv"
OPEN_QUESTIONS = ROOT / "registry/open_questions.csv"
DOC = ROOT / "docs/source_packs/B02_P6_BUILDING_TYPE_PROXY_CONTROL.md"
QUESTIONNAIRE_MANIFEST = ROOT / "evidence/history/SRC-B02-KSH-MICROCENSUS-TOPICS-2016/manifest.csv"
INDICATOR_MANIFEST = ROOT / "evidence/history/SRC-B02-KSH-HOUSING-STRUCTURE-INDICATOR-2016/manifest.csv"


class B02P6BuildingTypeProxyControlTests(unittest.TestCase):
    def _controls(self):
        with CONTROL.open(encoding="utf-8", newline="") as handle:
            return {row["control_id"]: row for row in csv.DictReader(handle)}

    def test_2016_source_native_categories_are_semantic_controls_only(self):
        rows = self._controls()
        family = rows["B02-P6-MC2016-SCHEMA-FAMILY"]
        multi = rows["B02-P6-MC2016-SCHEMA-MULTI"]
        self.assertEqual("FAMILY_HOUSE", family["canonical_building_type"])
        self.assertEqual("MULTI_DWELLING", multi["canonical_building_type"])
        self.assertEqual("OBS", family["source_evidence_status"])
        self.assertEqual("SEMANTIC_CATEGORY_CONTROL", family["gate_use"])
        self.assertEqual("no", family["can_upgrade_2022_proxy"])
        self.assertEqual("no", multi["can_upgrade_2022_proxy"])

    def test_national_2016_shares_are_exact_and_complementary(self):
        rows = self._controls()
        family = rows["B02-P6-MC2016-NATIONAL-FAMILY"]
        multi = rows["B02-P6-MC2016-NATIONAL-MULTI"]
        self.assertAlmostEqual(0.62, float(family["source_share"]), places=12)
        self.assertAlmostEqual(0.38, float(multi["source_share"]), places=12)
        self.assertAlmostEqual(1.0, float(family["source_share"]) + float(multi["source_share"]), places=12)
        self.assertEqual("NATIONAL", family["source_grain"])
        self.assertEqual("OCCUPIED_DWELLINGS", family["source_universe"])

    def test_historical_national_control_cannot_promote_2022_proxy(self):
        rows = self._controls()
        for control_id in (
            "B02-P6-MC2016-NATIONAL-FAMILY",
            "B02-P6-MC2016-NATIONAL-MULTI",
        ):
            row = rows[control_id]
            self.assertEqual("OBS", row["source_evidence_status"])
            self.assertEqual("ASS", row["comparison_evidence_status"])
            self.assertEqual("NATIONAL_MAGNITUDE_CONTROL", row["gate_use"])
            self.assertEqual("no", row["can_upgrade_2022_proxy"])
            self.assertEqual("OPEN", row["q_b02_002_effect"])

    def test_diagnostic_delta_is_reproducible_without_a_tolerance_gate(self):
        rows = self._controls()
        family = rows["B02-P6-MC2016-NATIONAL-FAMILY"]
        multi = rows["B02-P6-MC2016-NATIONAL-MULTI"]
        family_delta = (float(family["current_2022_proxy_share"]) - float(family["source_share"])) * 100.0
        multi_delta = (float(multi["current_2022_proxy_share"]) - float(multi["source_share"])) * 100.0
        self.assertAlmostEqual(float(family["current_minus_source_delta_pp"]), family_delta, places=12)
        self.assertAlmostEqual(float(multi["current_minus_source_delta_pp"]), multi_delta, places=12)
        self.assertAlmostEqual(-family_delta, multi_delta, places=12)
        self.assertAlmostEqual(-1.5506744224394908, family_delta, places=12)

    def test_q_b02_002_remains_open_in_canonical_registry(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            questions = {row["question_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual("OPEN", questions["Q-B02-002"]["status"])

    def test_history_manifests_are_reuse_cleared_but_exact_snapshots_pending(self):
        for path in (QUESTIONNAIRE_MANIFEST, INDICATOR_MANIFEST):
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(1, len(rows))
            row = rows[0]
            self.assertEqual("REPOSITORY_COPY_CLEARED_ATTRIBUTION_REQUIRED", row["reuse_status"])
            self.assertEqual("", row["sha256"])
            self.assertTrue(row["snapshot_status"].startswith("PENDING_"))

    def test_source_pack_freezes_non_inference_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "2016 NATIONAL OBS CONTROL != 2022 SETTLEMENT-TYPE OBS != WBL SUBCELL JOINABILITY",
            "Q-B02-002` remains **OPEN**",
            "No arbitrary tolerance is introduced",
            "No readiness uplift",
            "B02 remains 55%",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
