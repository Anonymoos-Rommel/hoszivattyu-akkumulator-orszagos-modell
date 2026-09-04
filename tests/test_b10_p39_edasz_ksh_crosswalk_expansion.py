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
DOC = ROOT / "docs/source_packs/P39_B10_EDASZ_KSH_CROSSWALK_EXPANSION.md"

EDASZ = "SRC-B10-EON-EDASZ-M1-CANDIDATE-2025"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"
KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_2025_DERIVATION = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"

EXPECTED_P22_EDASZ = {
    ("17376", "Aba"),
    ("11882", "Abda"),
    ("04428", "Ács"),
}

EXPECTED_P39 = {
    ("04561", "Ábrahámhegy"), ("07214", "Acsád"), ("33385", "Acsalag"),
    ("18139", "Ácsteszér"), ("07302", "Adásztevel"), ("31307", "Adorjánháza"),
    ("04880", "Ágfalva"), ("29407", "Agyagosszergény"), ("06673", "Ajka"),
    ("06682", "Aka"), ("02644", "Alibánfa"), ("15176", "Alcsútdoboz"),
    ("32346", "Almásfüzitő"), ("19512", "Alsónemesapáti"), ("30526", "Alsóörs"),
    ("08767", "Alsószenterzsébet"), ("22549", "Alsószölnök"), ("22725", "Alsóújlak"),
    ("12317", "Andrásfa"), ("34227", "Annavölgy"), ("28370", "Apácatorna"),
    ("08873", "Apátistvánfalva"), ("32249", "Árpás"), ("26921", "Ásványráró"),
    ("07339", "Aszófő"), ("19363", "Bábolna"), ("21263", "Babosdöbréte"),
    ("15042", "Babót"), ("22327", "Badacsonytomaj"), ("03267", "Badacsonytördemic"),
    ("11059", "Baglad"), ("30368", "Bagod"), ("28769", "Bágyogszovát"),
    ("29212", "Baj"), ("17020", "Bajánsenye"), ("16744", "Bajna"),
    ("29355", "Bajót"), ("24244", "Bakonybánk"), ("23746", "Bakonybél"),
    ("08730", "Bakonycsernye"), ("28936", "Bakonygyirót"), ("29513", "Bakonyjákó"),
}

EXCLUDED_NON_WHOLE = {"Ács-Jegespuszta"}
EXPLICIT_EQUIVALENCES = {
    "Alcsútdoboz": "Alcsutdoboz",
    "Alsóörs": "Alsóőrs",
}


class B10P39EdaszKshCrosswalkExpansionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def p39_rows(self):
        return [
            row for row in self.rows(TRANCHE)
            if row["operator_id"] == "EON_EDASZ"
            and KSH_2025 in row["source_ids"].split(";")
        ]

    def test_exact_42_new_edasz_name_code_pairs_are_materialized(self):
        rows = self.p39_rows()
        self.assertEqual(42, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P39, actual)

    def test_p39_rows_are_exact_whole_settlement_der(self):
        rows = self.p39_rows()
        self.assertTrue(all(row["operator_id"] == "EON_EDASZ" for row in rows))
        self.assertTrue(all(row["service_area_id"] == "EON_EDASZ:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "DER" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))

    def test_p39_rows_bind_edasz_primary_ksh_and_derived_locator(self):
        for row in self.p39_rows():
            self.assertEqual({EDASZ, KSH_2025, KSH_2025_DERIVATION}, set(row["source_ids"].split(";")))

        authorities = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        self.assertEqual("OFFICIAL_APPROVED_PACKAGE_M1_ATTACHMENT", authorities[EDASZ]["source_kind"])
        self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", authorities[EDASZ]["currentness_status"])
        self.assertEqual("WHOLE_SETTLEMENT_DSO_MEMBERSHIP_DER_ONLY", authorities[EDASZ]["authorizes"])
        self.assertEqual("OFFICIAL_CURRENT_KSH_DETAILED_GAZETTEER_XLSX", authorities[KSH_2025]["source_kind"])
        self.assertEqual("DERIVED_MACHINE_READABLE_SETTLEMENT_ID_LOCATOR_ONLY", authorities[KSH_2025_DERIVATION]["authorizes"])

    def test_p22_three_edasz_rows_remain_unchanged_and_edasz_total_is_45(self):
        rows = [row for row in self.rows(TRANCHE) if row["operator_id"] == "EON_EDASZ"]
        self.assertEqual(45, len(rows))
        historical = [row for row in rows if KSH_2019 in row["source_ids"].split(";")]
        self.assertEqual(3, len(historical))
        self.assertEqual(EXPECTED_P22_EDASZ, {(row["ksh_settlement_code"], row["settlement_name"]) for row in historical})
        self.assertTrue(all(row["evidence_status"] == "DER" for row in historical))

    def test_non_whole_m1_names_are_not_promoted(self):
        names = {row["settlement_name"] for row in self.rows(TRANCHE) if row["operator_id"] == "EON_EDASZ"}
        self.assertFalse(names & EXCLUDED_NON_WHOLE)

    def test_two_explicit_name_equivalence_overrides_are_identity_specific(self):
        by_name = {row["settlement_name"]: row for row in self.p39_rows()}
        for current_name, m1_name in EXPLICIT_EQUIVALENCES.items():
            row = by_name[current_name]
            self.assertIn(m1_name, row["notes"])
            self.assertIn("explicit project equivalence", row["notes"])
            self.assertIn("does not authorize fuzzy matching", row["notes"])

        names = {row["settlement_name"] for row in self.p39_rows()}
        self.assertNotIn("Alcsutdoboz", names)
        self.assertNotIn("Alsóőrs", names)

    def test_all_ksh_codes_remain_unique_five_digit_identifiers(self):
        rows = self.rows(TRANCHE)
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_source_registry_tracks_p39_bounded_edasz_state_and_overrides(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["EON_EDASZ"]
        self.assertEqual(EDASZ, src["source_id"])
        self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", src["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", src["extraction_status"])
        self.assertIn("P39", src["notes"])
        self.assertIn("42", src["notes"])
        self.assertIn("Alcsutdoboz→Alcsútdoboz", src["notes"])
        self.assertIn("Alsóőrs→Alsóörs", src["notes"])
        self.assertIn("do not establish a general fuzzy-name", src["notes"])

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
            "EXPLICIT NAME EQUIVALENCE OVERRIDE != GENERAL FUZZY MATCHING RULE",
            "PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION",
            "42 additional",
            "45 materialized rows",
            "Alcsutdoboz` → current KSH `Alcsútdoboz` (`15176`)",
            "Alsóőrs` → current KSH `Alsóörs` (`30526`)",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
