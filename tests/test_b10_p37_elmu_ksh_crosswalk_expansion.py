import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
AUTHORITIES = ROOT / "registry/dso_service_area_crosswalk_authorities.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P37_B10_ELMU_KSH_CROSSWALK_EXPANSION.md"

ELMU = "SRC-B10-ELMU-M1-CANDIDATE-2025"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"
KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_2025_DERIVATION = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"

EXPECTED_P22_ELMU = {
    ("18573", "Acsa"),
    ("23199", "Alsónémedi"),
    ("33561", "Apaj"),
}

EXPECTED_P37 = {
    ("10108", "Áporka"), ("18777", "Bernecebaráti"), ("08891", "Biatorbágy"),
    ("03407", "Budajenő"), ("23463", "Budakalász"), ("12052", "Budakeszi"),
    ("23278", "Budaörs"), ("32027", "Bugyi"), ("06822", "Csobánka"),
    ("33118", "Csomád"), ("22804", "Csömör"), ("34333", "Csörög"),
    ("26985", "Csővár"), ("09247", "Dabas"), ("09973", "Délegyháza"),
    ("24013", "Diósd"), ("29647", "Dömsöd"), ("25362", "Dunabogdány"),
    ("09584", "Dunaharaszti"), ("18616", "Dunakeszi"), ("20534", "Dunavarsány"),
    ("24518", "Ecser"), ("30988", "Érd"), ("13480", "Erdőkertes"),
    ("06035", "Felsőpakony"), ("32610", "Fót"), ("13295", "Galgagyörk"),
    ("27128", "Galgamácsa"), ("32559", "Gödöllő"), ("25627", "Gyál"),
    ("29735", "Gyömrő"), ("09690", "Halásztelek"), ("33552", "Herceghalom"),
    ("32106", "Inárcs"), ("28097", "Ipolydamásd"), ("04978", "Ipolytölgyes"),
    ("07807", "Isaszeg"), ("32230", "Kakucs"), ("22345", "Kemence"),
    ("34166", "Kerepes"),
}

EXCLUDED_NON_WHOLE = {
    "Bankháza", "Domonyvölgy", "Tass üdülőterület", "Budapest", "Göd",
}


class B10P37ElmuKshCrosswalkExpansionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def p37_rows(self):
        return [
            row for row in self.rows(TRANCHE)
            if row["operator_id"] == "ELMU"
            and KSH_2025 in row["source_ids"].split(";")
        ]

    def test_exact_40_new_elmu_name_code_pairs_are_materialized(self):
        rows = self.p37_rows()
        self.assertEqual(40, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P37, actual)

    def test_p37_rows_are_exact_whole_settlement_der(self):
        rows = self.p37_rows()
        self.assertTrue(all(row["operator_id"] == "ELMU" for row in rows))
        self.assertTrue(all(row["service_area_id"] == "ELMU:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "DER" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))

    def test_p37_rows_bind_elmu_primary_ksh_and_derived_locator(self):
        for row in self.p37_rows():
            self.assertEqual({ELMU, KSH_2025, KSH_2025_DERIVATION}, set(row["source_ids"].split(";")))

        authorities = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        self.assertEqual("OFFICIAL_APPROVED_PACKAGE_M1_ATTACHMENT", authorities[ELMU]["source_kind"])
        self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", authorities[ELMU]["currentness_status"])
        self.assertEqual("WHOLE_SETTLEMENT_DSO_MEMBERSHIP_DER_ONLY", authorities[ELMU]["authorizes"])
        self.assertEqual("OFFICIAL_CURRENT_KSH_DETAILED_GAZETTEER_XLSX", authorities[KSH_2025]["source_kind"])
        self.assertEqual("DERIVED_MACHINE_READABLE_SETTLEMENT_ID_LOCATOR_ONLY", authorities[KSH_2025_DERIVATION]["authorizes"])

    def test_p22_three_elmu_rows_remain_unchanged_and_elmu_total_is_43(self):
        rows = [row for row in self.rows(TRANCHE) if row["operator_id"] == "ELMU"]
        self.assertEqual(43, len(rows))
        historical = [row for row in rows if KSH_2019 in row["source_ids"].split(";")]
        self.assertEqual(3, len(historical))
        self.assertEqual(EXPECTED_P22_ELMU, {(row["ksh_settlement_code"], row["settlement_name"]) for row in historical})
        self.assertTrue(all(row["evidence_status"] == "DER" for row in historical))

    def test_non_whole_or_ambiguous_locator_names_are_not_promoted(self):
        names = {row["settlement_name"] for row in self.rows(TRANCHE) if row["operator_id"] == "ELMU"}
        self.assertFalse(names & EXCLUDED_NON_WHOLE)

    def test_all_ksh_codes_remain_unique_five_digit_identifiers(self):
        rows = self.rows(TRANCHE)
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_source_registry_tracks_p37_bounded_elmu_state(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["ELMU"]
        self.assertEqual(ELMU, src["source_id"])
        self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", src["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", src["extraction_status"])
        self.assertIn("P37", src["notes"])
        self.assertIn("40", src["notes"])

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)

        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])

    def test_source_pack_preserves_evidence_only_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "SETTLEMENT NAME != KSH SETTLEMENT ID",
            "KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP",
            "WHOLE SETTLEMENT != NAMED SUBSETTLEMENT OR SETTLEMENT PART",
            "DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE",
            "DER CURRENTNESS EDGE CAPS CURRENT MEMBERSHIP AT DER",
            "PRIMARY KSH LOCATOR + DERIVED MACHINE LOCATOR != DIRECT PRIMARY ROW OBSERVATION",
            "PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION",
            "40 additional",
            "43 materialized rows",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
