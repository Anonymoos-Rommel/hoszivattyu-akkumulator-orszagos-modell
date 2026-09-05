import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment

ROOT = Path(__file__).resolve().parents[1]
P53_MANIFEST = ROOT / "registry/dso_service_area_membership_ddasz_p53_authority_manifest.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
P48_PAIRS = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P58_B10_DDASZ_CURRENT_M1_URL_INTEGRITY_REPAIR.md"

SOURCE_ID = "SRC-B10-EON-DDASZ-M1-CANDIDATE-2025"
EXPECTED_URL = "https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EDE/2025/EDE_elo_usz_melleklet_20241209%20%28v1%29.pdf"


class B10P58DdaszCurrentM1UrlIntegrityRepairTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_p53_manifest_matches_canonical_ddasz_source_url_exactly(self):
        manifest_rows = self.rows(P53_MANIFEST)
        self.assertEqual(1, len(manifest_rows))
        manifest = manifest_rows[0]

        source_rows = [r for r in self.rows(SOURCES) if r["source_id"] == SOURCE_ID]
        self.assertEqual(1, len(source_rows))
        source = source_rows[0]

        self.assertEqual("EON_DDASZ", source["operator_id"])
        self.assertEqual(EXPECTED_URL, source["source_url"])
        self.assertEqual(EXPECTED_URL, manifest["current_source_url"])
        self.assertEqual(source["source_url"], manifest["current_source_url"])

    def test_stale_edd_path_identity_is_rejected(self):
        url = self.rows(P53_MANIFEST)[0]["current_source_url"]
        self.assertNotIn("/EDD/2025/", url)
        self.assertNotIn("EDD_elo_usz_melleklet_20241209", url)
        self.assertIn("/EDE/2025/", url)
        self.assertIn("EDE_elo_usz_melleklet_20241209", url)

    def test_p53_authority_semantics_are_unchanged(self):
        row = self.rows(P53_MANIFEST)[0]
        self.assertEqual("EON_DDASZ_P48_14_SPELLING_EDGES", row["audit_scope"])
        self.assertEqual("HISTORICAL_COMPARISON_ONLY", row["historical_use"])
        self.assertEqual("NONE", row["currentness_claim"])
        self.assertEqual(
            "MIXED_4_CANONICAL_CORROBORATIONS_10_VARIANT_REPETITIONS_NO_CURRENT_EQUIVALENCE",
            row["equivalence_authority_result"],
        )
        self.assertIn("zero promotions", row["notes"])

    def test_ddasz_membership_counts_remain_unchanged(self):
        p48 = self.rows(P48_PAIRS)
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "EON_DDASZ"]
        self.assertEqual(777, len(p48))
        self.assertEqual(43, len(historical))
        self.assertEqual(820, len({(r["ksh_settlement_code"], r["settlement_name"]) for r in historical} | {(r["ksh_settlement_code"], r["settlement_name"]) for r in p48}))

    def test_source_pack_freezes_integrity_only_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "P53 SOURCE-URL TYPO REPAIR != NEW DDÁSZ AUTHORITY",
            "SOURCE-LINEAGE CONSISTENCY REPAIR != IDENTITY-EQUIVALENCE AUTHORITY",
            "P53 CURRENT SOURCE URL == CANONICAL DDÁSZ CURRENT M1 SOURCE URL",
            "P58 adds **zero** service-area membership rows",
            "296 = 14 spelling diagnostics + 2 cross-DSO conflicts + 280 other unresolved source tokens",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

    def test_b10_closure_state_remains_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        by_module = {r["module_id"]: r for r in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
