import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P41_B10_OPUS_TITASZ_KSH_CROSSWALK_EXPANSION.md"

OPUS = "SRC-B10-OPUS-TITASZ-M1-2026"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"

EXPECTED_P41 = {
    ("30641", "Csenger"), ("24095", "Csengersima"),
    ("26851", "Csengerújfalu"), ("05795", "Cserkeszőlő"),
    ("13170", "Csépa"), ("12450", "Csökmő"),
    ("18795", "Darnó"), ("14678", "Darvas"),
    ("15130", "Debrecen"), ("17756", "Demecser"),
    ("05573", "Derecske"), ("24819", "Dévaványa"),
    ("14508", "Dombrád"), ("03647", "Döge"),
    ("14614", "Ebes"), ("09432", "Ecsegfalva"),
    ("15741", "Egyek"), ("32328", "Encsencs"),
    ("18528", "Eperjeske"), ("25469", "Esztár"),
    ("10852", "Érpatak"), ("23250", "Fábiánháza"),
    ("16647", "Fegyvernek"), ("18971", "Fehérgyarmat"),
    ("22415", "Fényeslitke"), ("34014", "Folyás"),
    ("03258", "Földes"), ("16993", "Furta"),
    ("10791", "Fülesd"), ("22150", "Fülöp"),
    ("14377", "Fülpösdaróc"), ("12256", "Füzesgyarmat"),
    ("13727", "Gacsály"), ("04996", "Garbolc"),
    ("18175", "Gáborján"), ("05801", "Gávavencsellő"),
    ("04613", "Gelénes"), ("13000", "Gemzse"),
    ("28893", "Geszteréd"), ("03629", "Géberjén"),
}


class B10P41OpusTitaszKshCrosswalkExpansionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def opus_rows(self):
        return [row for row in self.rows(TRANCHE) if row["operator_id"] == "OPUS_TITASZ"]

    def p41_rows(self):
        return [
            row for row in self.opus_rows()
            if (row["ksh_settlement_code"], row["settlement_name"]) in EXPECTED_P41
        ]

    def test_exact_40_p41_name_code_pairs_are_materialized(self):
        rows = self.p41_rows()
        self.assertEqual(40, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P41, actual)

    def test_p41_exact_40_rows_remain_inside_evolving_opus_tranche(self):
        rows = self.opus_rows()
        self.assertGreaterEqual(len(rows), 90)
        self.assertEqual(40, len(self.p41_rows()))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertTrue(EXPECTED_P41.issubset(actual))

    def test_evolving_opus_rows_preserve_direct_observed_whole_settlement_semantics(self):
        rows = self.opus_rows()
        self.assertGreaterEqual(len(rows), 90)
        self.assertTrue(all(row["service_area_id"] == "OPUS_TITASZ:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(set(row["source_ids"].split(";")) == {OPUS, KSH_2019} for row in rows))

    def test_p41_historical_set_is_bounded_to_m1_serial_90_not_91(self):
        names = {row["settlement_name"] for row in self.p41_rows()}
        self.assertIn("Csenger", names)
        self.assertIn("Géberjén", names)
        self.assertNotIn("Gégény", names)

    def test_source_registry_preserves_p20_p40_p41_lineage_inside_evolving_state(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["OPUS_TITASZ"]
        self.assertEqual(OPUS, src["source_id"])
        self.assertEqual("OFFICIAL_CURRENT_M1_ATTACHMENT", src["source_kind"])
        self.assertEqual("CURRENT_2026", src["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", src["extraction_status"])
        self.assertEqual("M1_SETTLEMENT_LIST", src["membership_semantics"])
        for marker in ("P20", "1-10", "P40", "11-50", "P41", "51-90", "partial materialization"):
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

    def test_source_pack_preserves_p41_evidence_only_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "serials **51–90**",
            "90 materialized rows",
            "serial **90, Géberjén**",
            "serial **91, Gégény**",
            "SETTLEMENT NAME != KSH SETTLEMENT ID",
            "KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP",
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
