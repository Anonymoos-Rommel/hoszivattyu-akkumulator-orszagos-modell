import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P43_B10_OPUS_TITASZ_KSH_CROSSWALK_EXPANSION.md"

OPUS = "SRC-B10-OPUS-TITASZ-M1-2026"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"

EXPECTED_P43 = {
    ("19992", "Kemecse"), ("17145", "Kenderes"),
    ("07418", "Kengyel"), ("12618", "Kertészsziget"),
    ("28431", "Kék"), ("14359", "Kékcse"),
    ("32869", "Kérsemjén"), ("19813", "Kétpó"),
    ("19424", "Kisar"), ("08509", "Kishódos"),
    ("28477", "Kisléta"), ("15477", "Kismarja"),
    ("16036", "Kisnamény"), ("29300", "Kispalád"),
    ("09751", "Kisszekeres"), ("25919", "Kisújszállás"),
    ("12672", "Kisvarsány"), ("09265", "Kisvárda"),
    ("07445", "Kocsord"), ("17455", "Kokad"),
    ("02167", "Komádi"), ("22336", "Komlódtótfalu"),
    ("27146", "Komoró"), ("25964", "Konyár"),
    ("23728", "Kótaj"), ("16665", "Kölcse"),
    ("23612", "Kömörő"), ("10764", "Körösnagyharsány"),
    ("31130", "Körösszakál"), ("08943", "Körösszegapáti"),
    ("32975", "Kőröstetétlen"), ("30164", "Körösújfalu"),
    ("11235", "Kőtelek"), ("05254", "Kuncsorba"),
    ("22567", "Kunhegyes"), ("23171", "Kunmadaras"),
    ("32504", "Kunszentmárton"), ("21290", "Laskod"),
    ("30979", "Levelek"), ("05768", "Létavértes"),
}


class B10P43OpusTitaszKshCrosswalkExpansionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def opus_rows(self):
        return [row for row in self.rows(TRANCHE) if row["operator_id"] == "OPUS_TITASZ"]

    def p43_rows(self):
        return [
            row for row in self.opus_rows()
            if (row["ksh_settlement_code"], row["settlement_name"]) in EXPECTED_P43
        ]

    def test_exact_40_p43_name_code_pairs_are_materialized(self):
        rows = self.p43_rows()
        self.assertEqual(40, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P43, actual)

    def test_current_opus_tranche_has_170_rows_and_p43_adds_40(self):
        rows = self.opus_rows()
        self.assertEqual(170, len(rows))
        self.assertEqual(40, len(self.p43_rows()))
        self.assertEqual(170, len({(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}))

    def test_all_170_opus_rows_preserve_direct_observed_whole_settlement_semantics(self):
        rows = self.opus_rows()
        self.assertEqual(170, len(rows))
        self.assertTrue(all(row["service_area_id"] == "OPUS_TITASZ:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(set(row["source_ids"].split(";")) == {OPUS, KSH_2019} for row in rows))

    def test_p43_is_bounded_to_m1_serial_170_not_171(self):
        names = {row["settlement_name"] for row in self.opus_rows()}
        self.assertIn("Kemecse", names)
        self.assertIn("Létavértes", names)
        self.assertNotIn("Lónya", names)

    def test_source_registry_tracks_p20_through_p43_lineage_and_170_row_state(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["OPUS_TITASZ"]
        self.assertEqual(OPUS, src["source_id"])
        self.assertEqual("OFFICIAL_CURRENT_M1_ATTACHMENT", src["source_kind"])
        self.assertEqual("CURRENT_2026", src["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", src["extraction_status"])
        self.assertEqual("M1_SETTLEMENT_LIST", src["membership_semantics"])
        for marker in (
            "P20", "1-10", "P40", "11-50", "P41", "51-90",
            "P42", "91-130", "P43", "131-170", "170 OBS",
            "partial materialization",
        ):
            self.assertIn(marker, src["notes"])

    def test_all_ksh_codes_remain_unique_five_digit_identifiers(self):
        rows = self.rows(TRANCHE)
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)

        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])

    def test_source_pack_preserves_p43_evidence_only_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "serials **131–170**",
            "170 materialized rows",
            "serial **170, Létavértes**",
            "serial **171, Lónya**",
            "SETTLEMENT NAME != KSH SETTLEMENT ID",
            "KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP",
            "WHOLE SETTLEMENT != PARTIAL SETTLEMENT OR USAGE-LOCATION MEMBERSHIP",
            "DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE",
            "BOUNDED CURRENT M1 ROWS != COMPLETE OPERATOR CROSSWALK",
            "PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION",
            "evidence_status = OBS",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

        for forbidden_claim in (
            "complete OPUS TITÁSZ settlement inventory materialization",
            "exact programme entity-to-node mapping",
            "headroom sufficiency",
            "limiting-node status",
            "reinforcement need",
            "programme-incremental CAPEX",
        ):
            self.assertIn(forbidden_claim, text)


if __name__ == "__main__":
    unittest.main()
