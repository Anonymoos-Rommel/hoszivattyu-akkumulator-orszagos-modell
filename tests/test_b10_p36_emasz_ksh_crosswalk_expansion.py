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
DOC = ROOT / "docs/source_packs/P36_B10_EMASZ_KSH_CROSSWALK_EXPANSION.md"

MVM = "SRC-B10-MVM-EMASZ-M1-2026"
KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_2025_DERIVATION = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"

EXPECTED_P21_OBS = {
    ("24554", "Abasár"),
    ("23241", "Adács"),
    ("09362", "Aggtelek"),
    ("06345", "Aldebrő"),
    ("05847", "Harsány"),
}

EXPECTED_P36 = {
    ("15662", "Abaújalpár"), ("26718", "Abaújkér"), ("02820", "Abaújlak"),
    ("03595", "Abaújszántó"), ("26338", "Abaújszolnok"), ("02273", "Abaújvár"),
    ("10357", "Abod"), ("33093", "Alacska"), ("20482", "Alsóberecki"),
    ("19664", "Alsódobsza"), ("14429", "Alsógagy"), ("16425", "Alsópetény"),
    ("23223", "Alsóregmec"), ("28839", "Alsószuha"), ("08217", "Alsótelekes"),
    ("07621", "Alsótold"), ("29814", "Alsóvadász"), ("21032", "Alsózsolca"),
    ("17987", "Andornaktálya"), ("07241", "Apc"), ("26198", "Arka"),
    ("14331", "Arló"), ("03771", "Arnót"), ("03823", "Ároktő"),
    ("04233", "Aszaló"), ("16188", "Aszód"), ("06503", "Átány"),
    ("16090", "Atkár"), ("09131", "Bag"), ("18184", "Baktakék"),
    ("22521", "Balajt"), ("13657", "Balassagyarmat"), ("11527", "Balaton"),
    ("25159", "Bánhorváti"), ("24341", "Bánk"), ("21953", "Bánréve"),
    ("20048", "Bárna"), ("08846", "Baskó"), ("33534", "Bátonyterenye"),
    ("24022", "Bátor"),
}

NAMED_SUBSETTLEMENTS = {
    "Abaújdevecser", "Alatka", "Aranyospuszta", "Baglyasalja",
    "Bagolyírtás", "Bánszállás", "Benczúrfalva", "Bükkszentlászló",
}


class B10P36EmaszKshCrosswalkExpansionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def p36_rows(self):
        return [
            row for row in self.rows(TRANCHE)
            if row["operator_id"] == "MVM_EMASZ"
            and KSH_2025 in row["source_ids"].split(";")
        ]

    def test_exact_40_new_emasz_name_code_pairs_are_materialized(self):
        rows = self.p36_rows()
        self.assertEqual(40, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P36, actual)

    def test_p36_rows_are_exact_whole_settlement_der(self):
        rows = self.p36_rows()
        self.assertTrue(all(row["operator_id"] == "MVM_EMASZ" for row in rows))
        self.assertTrue(all(row["service_area_id"] == "MVM_EMASZ:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "DER" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))

    def test_p36_rows_bind_mvm_primary_ksh_and_derived_locator(self):
        for row in self.p36_rows():
            self.assertEqual({MVM, KSH_2025, KSH_2025_DERIVATION}, set(row["source_ids"].split(";")))

        authorities = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        self.assertEqual("OFFICIAL_CURRENT_M1_ATTACHMENT", authorities[MVM]["source_kind"])
        self.assertIn("20260526", authorities[MVM]["source_url"])
        self.assertEqual("OFFICIAL_CURRENT_KSH_DETAILED_GAZETTEER_XLSX", authorities[KSH_2025]["source_kind"])
        self.assertEqual("DERIVED_MACHINE_READABLE_SETTLEMENT_ID_LOCATOR_ONLY", authorities[KSH_2025_DERIVATION]["authorizes"])

    def test_p21_five_obs_rows_remain_unchanged_and_emasz_total_is_45(self):
        rows = [row for row in self.rows(TRANCHE) if row["operator_id"] == "MVM_EMASZ"]
        self.assertEqual(45, len(rows))
        obs = [row for row in rows if row["evidence_status"] == "OBS"]
        self.assertEqual(EXPECTED_P21_OBS, {(row["ksh_settlement_code"], row["settlement_name"]) for row in obs})
        self.assertEqual(5, len(obs))

    def test_named_subsettlements_are_not_promoted(self):
        names = {row["settlement_name"] for row in self.rows(TRANCHE) if row["operator_id"] == "MVM_EMASZ"}
        self.assertFalse(names & NAMED_SUBSETTLEMENTS)

    def test_all_ksh_codes_remain_unique_five_digit_identifiers(self):
        rows = self.rows(TRANCHE)
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_source_registry_tracks_current_20260526_m1(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["MVM_EMASZ"]
        self.assertEqual(MVM, src["source_id"])
        self.assertIn("20260526", src["source_url"])
        self.assertEqual("CURRENT_2026", src["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", src["extraction_status"])

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
            "WHOLE SETTLEMENT != NAMED SUBSETTLEMENT",
            "DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE",
            "PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION",
            "PRIMARY KSH LOCATOR + DERIVED MACHINE LOCATOR != DIRECT PRIMARY ROW OBSERVATION",
            "40 additional",
            "45 materialized rows",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
