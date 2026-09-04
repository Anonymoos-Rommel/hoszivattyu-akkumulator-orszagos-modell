import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
AUTHORITIES = ROOT / "registry/dso_service_area_crosswalk_authorities.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P35_B10_DEMASZ_KSH_CROSSWALK_EXPANSION.md"

KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_2025_DERIVATION = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"
MVM = "SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026"

EXPECTED_P35 = {
    ("03656", "Bátmonostor"),
    ("11961", "Bátya"),
    ("08305", "Bócsa"),
    ("19327", "Borota"),
    ("32823", "Bugac"),
    ("33631", "Bugacpusztaháza"),
    ("10472", "Császártöltés"),
    ("26471", "Csátalja"),
    ("16373", "Csávoly"),
    ("12344", "Csengőd"),
    ("15699", "Csikéria"),
    ("12025", "Csólyospálos"),
    ("10533", "Dávod"),
    ("07524", "Drágszél"),
    ("21069", "Dunaegyháza"),
    ("12566", "Dunafalva"),
    ("07861", "Dunapataj"),
    ("11606", "Dunaszentbenedek"),
    ("14766", "Dunatetétlen"),
    ("07612", "Dunavecse"),
    ("04109", "Dusnok"),
    ("33589", "Érsekhalma"),
    ("03230", "Fajsz"),
    ("33598", "Felsőlajos"),
    ("02954", "Felsőszentiván"),
    ("02149", "Foktő"),
    ("31468", "Fülöpháza"),
    ("33622", "Fülöpjakab"),
    ("14058", "Fülöpszállás"),
    ("31848", "Gara"),
}

PARTIAL = {
    "Baja", "Csongrád", "Érsekcsanád", "Gyomaendrőd",
    "Kunszentmárton", "Mohács", "Solt", "Szeghalom", "Szentes",
    "Tápiószőlős", "Tass", "Tiszakécske", "Tiszasas", "Tiszaug",
    "Újhartyán", "Zsadány",
}


class B10P35DemaszKshCrosswalkExpansionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def p35_rows(self):
        return [
            row
            for row in self.rows(TRANCHE)
            if row["operator_id"] == "MVM_DEMASZ"
            and KSH_2025 in row["source_ids"].split(";")
        ]

    def test_exact_30_new_demasz_name_code_pairs_are_materialized(self):
        rows = self.p35_rows()
        self.assertEqual(30, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P35, actual)

    def test_p35_rows_are_der_not_obs_and_keep_exact_whole_settlement_semantics(self):
        rows = self.p35_rows()
        self.assertTrue(all(row["evidence_status"] == "DER" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["service_area_id"] == "MVM_DEMASZ:SERVICE_AREA" for row in rows))

    def test_p35_rows_bind_official_dso_primary_ksh_and_derived_locator(self):
        rows = self.p35_rows()
        for row in rows:
            refs = set(row["source_ids"].split(";"))
            self.assertEqual({MVM, KSH_2025, KSH_2025_DERIVATION}, refs)

        authorities = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        self.assertEqual("Központi Statisztikai Hivatal", authorities[KSH_2025]["authority_owner"])
        self.assertEqual("OFFICIAL_CURRENT_KSH_DETAILED_GAZETTEER_XLSX", authorities[KSH_2025]["source_kind"])
        self.assertEqual("DERIVED_MACHINE_READABLE_SETTLEMENT_ID_LOCATOR_ONLY", authorities[KSH_2025_DERIVATION]["authorizes"])

    def test_mvm_demasz_tranche_now_has_40_rows_without_partial_settlement_promotion(self):
        rows = [row for row in self.rows(TRANCHE) if row["operator_id"] == "MVM_DEMASZ"]
        self.assertEqual(40, len(rows))
        self.assertFalse({row["settlement_name"] for row in rows} & PARTIAL)

    def test_ksh_codes_are_unique_five_digit_identifiers(self):
        rows = self.rows(TRANCHE)
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_canonical_crosswalk_and_closure_blockers_remain_fail_closed(self):
        lines = CANONICAL.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        self.assertIn("Q-B01-002", blockers)

    def test_b10_readiness_remains_15(self):
        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])

    def test_source_pack_preserves_evidence_only_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("evidence/data slice", text)
        self.assertIn("KSH PRIMARY SOURCE LOCATOR + REPRODUCIBLE DERIVED ROW LOCATOR != DIRECT PRIMARY ROW OBSERVATION", text)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", text)
        self.assertIn("30 additional", text)
        self.assertIn("readiness remains **15%**", text)


if __name__ == "__main__":
    unittest.main()
