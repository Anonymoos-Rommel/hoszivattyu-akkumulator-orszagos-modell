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
DOC = ROOT / "docs/source_packs/P38_B10_DDASZ_KSH_CROSSWALK_EXPANSION.md"

DDASZ = "SRC-B10-EON-DDASZ-M1-CANDIDATE-2025"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"
KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_2025_DERIVATION = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"

EXPECTED_P22_DDASZ = {
    ("12548", "Abaliget"),
    ("06080", "Ádánd"),
    ("08925", "Adony"),
}

EXPECTED_P38 = {
    ("06868", "Adorjás"), ("25812", "Ág"), ("26824", "Alap"),
    ("13329", "Almamellék"), ("23384", "Almásháza"), ("20376", "Almáskeresztúr"),
    ("34184", "Alsóbogát"), ("17385", "Alsómocsolád"), ("29665", "Alsónána"),
    ("11563", "Alsónyék"), ("32081", "Alsópáhok"), ("18829", "Alsórajk"),
    ("25283", "Alsószentiván"), ("33279", "Alsószentmárton"), ("28714", "Andocs"),
    ("26125", "Aparhant"), ("27298", "Apátvarasd"), ("06886", "Aranyosgadány"),
    ("28583", "Áta"), ("32735", "Attala"), ("05403", "Babarc"),
    ("09663", "Babarcszőlős"), ("30474", "Babócsa"), ("28316", "Bábonymegyer"),
    ("04738", "Bak"), ("14395", "Bakháza"), ("22275", "Bakóca"),
    ("08299", "Bakonya"), ("03975", "Baksa"), ("15097", "Baktüttös"),
    ("27377", "Balatonberény"), ("33853", "Balatonboglár"), ("19460", "Balatonendréd"),
    ("20729", "Balatonfenyves"), ("07117", "Balatonföldvár"), ("17002", "Balatongyörök"),
    ("07375", "Balatonkeresztúr"), ("33862", "Balatonlelle"), ("26462", "Balatonmagyaród"),
    ("16601", "Balatonszabadi"),
}

EXCLUDED_NON_WHOLE = {
    "Ágostonpuszta", "Alsóbélatelep", "Alsófakos", "Alsóhetény", "Alsóhídvég",
    "Alsókölked", "Alsókövesd", "Alsópél", "Alsótekeres", "Andormajor",
    "Antalfalu", "Antalszállás", "Bagola", "Bajcsa", "Balatonaliga",
    "Balatonbozsok", "Balatonkiliti", "Balatonmária", "Balatonszabadi - Sóstó",
}


class B10P38DdaszKshCrosswalkExpansionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def p38_rows(self):
        return [
            row for row in self.rows(TRANCHE)
            if row["operator_id"] == "EON_DDASZ"
            and KSH_2025 in row["source_ids"].split(";")
        ]

    def test_exact_40_new_ddasz_name_code_pairs_are_materialized(self):
        rows = self.p38_rows()
        self.assertEqual(40, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P38, actual)

    def test_p38_rows_are_exact_whole_settlement_der(self):
        rows = self.p38_rows()
        self.assertTrue(all(row["operator_id"] == "EON_DDASZ" for row in rows))
        self.assertTrue(all(row["service_area_id"] == "EON_DDASZ:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "DER" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))

    def test_p38_rows_bind_ddasz_primary_ksh_and_derived_locator(self):
        for row in self.p38_rows():
            self.assertEqual({DDASZ, KSH_2025, KSH_2025_DERIVATION}, set(row["source_ids"].split(";")))

        authorities = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        self.assertEqual("OFFICIAL_APPROVED_PACKAGE_M1_ATTACHMENT", authorities[DDASZ]["source_kind"])
        self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", authorities[DDASZ]["currentness_status"])
        self.assertEqual("WHOLE_SETTLEMENT_DSO_MEMBERSHIP_DER_ONLY", authorities[DDASZ]["authorizes"])
        self.assertEqual("OFFICIAL_CURRENT_KSH_DETAILED_GAZETTEER_XLSX", authorities[KSH_2025]["source_kind"])
        self.assertEqual("DERIVED_MACHINE_READABLE_SETTLEMENT_ID_LOCATOR_ONLY", authorities[KSH_2025_DERIVATION]["authorizes"])

    def test_p22_three_ddasz_rows_remain_unchanged_and_ddasz_total_is_43(self):
        rows = [row for row in self.rows(TRANCHE) if row["operator_id"] == "EON_DDASZ"]
        self.assertEqual(43, len(rows))
        historical = [row for row in rows if KSH_2019 in row["source_ids"].split(";")]
        self.assertEqual(3, len(historical))
        self.assertEqual(EXPECTED_P22_DDASZ, {(row["ksh_settlement_code"], row["settlement_name"]) for row in historical})
        self.assertTrue(all(row["evidence_status"] == "DER" for row in historical))

    def test_non_whole_m1_names_are_not_promoted(self):
        names = {row["settlement_name"] for row in self.rows(TRANCHE) if row["operator_id"] == "EON_DDASZ"}
        self.assertFalse(names & EXCLUDED_NON_WHOLE)

    def test_all_ksh_codes_remain_unique_five_digit_identifiers(self):
        rows = self.rows(TRANCHE)
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_source_registry_tracks_p38_bounded_ddasz_state(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["EON_DDASZ"]
        self.assertEqual(DDASZ, src["source_id"])
        self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", src["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", src["extraction_status"])
        self.assertIn("P38", src["notes"])
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
