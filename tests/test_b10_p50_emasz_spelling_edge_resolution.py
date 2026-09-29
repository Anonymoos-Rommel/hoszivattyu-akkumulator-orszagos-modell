import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
OPUS_P44 = ROOT / "registry/dso_service_area_membership_crosswalk_opus_p44.csv"
DEMASZ_P45 = ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv"
ELMU_P46 = ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv"
EMASZ_P47 = ROOT / "registry/dso_service_area_membership_emasz_p47_pairs.csv"
DDASZ_P48 = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
EDASZ_P49 = ROOT / "registry/dso_service_area_membership_edasz_p49_pairs.csv"
PAIRS = ROOT / "registry/dso_service_area_membership_emasz_p50_pairs.csv"
BRIDGES = ROOT / "registry/dso_service_area_membership_emasz_p50_identity_bridges.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_emasz_p50_manifest.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P50_B10_EMASZ_SPELLING_EDGE_RESOLUTION.md"

MVM = "SRC-B10-MVM-EMASZ-M1-2026"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"
EXPECTED_PAIR_DIGEST = "64ac0eb08ac5ff5833a5ad86f4fecdadd3e7382664543349f46109a280aea9e4"
EXPECTED_PAIRS = {("17932", "Fony"), ("25672", "Hidvégardó")}
EXPECTED_BRIDGES = {
    ("Fóny", "17932", "Fony", "FÓNY", "0517932"),
    ("Hídvégardó", "25672", "Hidvégardó", "HÍDVÉGARDÓ", "0525672"),
}


class B10P50EmaszSpellingEdgeResolutionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_two_p50_pairs_are_frozen_by_digest(self):
        rows = self.rows(PAIRS)
        self.assertEqual(2, len(rows))
        actual = {(r["ksh_settlement_code"], r["settlement_name"]) for r in rows}
        self.assertEqual(EXPECTED_PAIRS, actual)
        canonical = "".join(
            f'{r["ksh_settlement_code"]}|{r["settlement_name"]}\n'
            for r in sorted(rows, key=lambda row: (row["ksh_settlement_code"], row["settlement_name"]))
        )
        self.assertEqual(EXPECTED_PAIR_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_identity_bridges_are_exact_and_identity_specific(self):
        rows = self.rows(BRIDGES)
        self.assertEqual(2, len(rows))
        actual = {
            (
                r["source_token"],
                r["ksh_settlement_code"],
                r["ksh_settlement_name"],
                r["bridge_published_name"],
                r["bridge_published_ksh_code"],
            )
            for r in rows
        }
        self.assertEqual(EXPECTED_BRIDGES, actual)
        self.assertTrue(all(r["bridge_status"] == "IDENTITY_SPECIFIC_OFFICIAL_KSH_CODE_BRIDGE" for r in rows))
        self.assertTrue(all(r["official_bridge_url"] == "https://njt.jog.gov.hu/document/d9/d9f220055320000041_13.PDF" for r in rows))
        self.assertTrue(all(r["bridge_published_ksh_code"].endswith(r["ksh_settlement_code"]) for r in rows))
        self.assertTrue(all("no generalized accent normalization" in r["notes"] for r in rows))

    def test_manifest_binds_only_two_rows_to_emasz_der_semantics(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("MVM_EMASZ", row["operator_id"])
        self.assertEqual("MVM Émász Áramhálózati Kft.", row["network_operator"])
        self.assertEqual("MVM_EMASZ:SERVICE_AREA", row["service_area_id"])
        self.assertEqual("WHOLE_SETTLEMENT", row["coverage_scope"])
        self.assertEqual("NONE", row["usage_location_requirement"])
        self.assertEqual("DER", row["evidence_status"])
        self.assertEqual("WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN", row["status"])
        self.assertEqual({MVM, KSH_2019}, set(row["source_ids"].split(";")))
        self.assertEqual(str(PAIRS.relative_to(ROOT)), row["pairs_file"])
        self.assertEqual(str(BRIDGES.relative_to(ROOT)), row["identity_bridge_file"])

    def test_p50_closes_p47_whole_identity_gap_only(self):
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "MVM_EMASZ"]
        p47 = self.rows(EMASZ_P47)
        p50 = self.rows(PAIRS)
        self.assertEqual(45, len(historical))
        self.assertEqual(605, len(p47))
        self.assertEqual(2, len(p50))
        codes = [r["ksh_settlement_code"] for r in historical + p47 + p50]
        self.assertEqual(652, len(codes))
        self.assertEqual(652, len(set(codes)))

    def test_global_materialized_ksh_codes_remain_unique(self):
        codes = []
        for path in (HISTORICAL, OPUS_P44, DEMASZ_P45, ELMU_P46, EMASZ_P47, DDASZ_P48, EDASZ_P49, PAIRS):
            codes.extend(r["ksh_settlement_code"] for r in self.rows(path))
        self.assertEqual(len(codes), len(set(codes)))

    def test_source_registry_records_652_but_keeps_99_special_tokens_open(self):
        by_operator = {r["operator_id"]: r for r in self.rows(SOURCES)}
        row = by_operator["MVM_EMASZ"]
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", row["extraction_status"])
        for marker in ("P50", "652", "99", "Fóny→Fony", "Hídvégardó→Hidvégardó", "identity-specific"):
            self.assertIn(marker, row["notes"])

    def test_source_pack_preserves_fail_closed_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "650 pre-P50 materialized MVM Émász whole-settlement identities + 2 P50 = 652",
            "99 parenthesized named-subsettlement / special-grain tokens",
            "IDENTITY-SPECIFIC OFFICIAL KSH-CODE BRIDGE != GENERAL ACCENT NORMALIZATION",
            "COMPLETE PROVABLE WHOLE-SETTLEMENT MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        by_module = {r["module_id"]: r for r in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
