import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P40_B10_OPUS_TITASZ_KSH_CROSSWALK_EXPANSION.md"

OPUS = "SRC-B10-OPUS-TITASZ-M1-2026"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"

EXPECTED_P20_OPUS = {
    ("12441", "Abádszalók"),
    ("27872", "Abony"),
    ("08776", "Ajak"),
    ("25265", "Alattyán"),
    ("29975", "Anarcs"),
    ("20303", "Apagy"),
    ("09353", "Aranyosapáti"),
    ("27641", "Álmosd"),
    ("03319", "Ártánd"),
    ("20011", "Bagamér"),
}

EXPECTED_P40 = {
    ("15167", "Bakonszeg"), ("02325", "Baktalórántháza"),
    ("26958", "Balkány"), ("02918", "Balmazújváros"),
    ("15963", "Balsa"), ("26480", "Barabás"),
    ("26693", "Báránd"), ("02990", "Bátorliget"),
    ("33446", "Bedő"), ("25441", "Benk"),
    ("28246", "Beregdaróc"), ("20677", "Beregsurány"),
    ("18467", "Berekböszörmény"), ("34005", "Berekfürdő"),
    ("12788", "Berettyóújfalu"), ("07472", "Berkesz"),
    ("13639", "Besenyőd"), ("11305", "Besenyszög"),
    ("21227", "Beszterec"), ("02680", "Békésszentandrás"),
    ("25256", "Bihardancsháza"), ("19956", "Biharkeresztes"),
    ("24828", "Biharnagybajom"), ("29887", "Bihartorda"),
    ("29610", "Biharugra"), ("02945", "Biri"),
    ("34102", "Bocskaikert"), ("14137", "Bojt"),
    ("22239", "Botpalád"), ("11299", "Bököny"),
    ("13471", "Bucsa"), ("19707", "Buj"),
    ("09681", "Cégénydányád"), ("22938", "Cibakháza"),
    ("31334", "Csabacsűd"), ("34175", "Csataszög"),
    ("12928", "Csaholc"), ("29416", "Csaroda"),
    ("09715", "Császló"), ("26107", "Csegöld"),
}

P40_SNAPSHOT = EXPECTED_P20_OPUS | EXPECTED_P40


class B10P40OpusTitaszKshCrosswalkExpansionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def opus_rows(self):
        return [row for row in self.rows(TRANCHE) if row["operator_id"] == "OPUS_TITASZ"]

    def p40_rows(self):
        return [
            row for row in self.opus_rows()
            if (row["ksh_settlement_code"], row["settlement_name"]) in EXPECTED_P40
        ]

    def p40_snapshot_rows(self):
        return [
            row for row in self.opus_rows()
            if (row["ksh_settlement_code"], row["settlement_name"]) in P40_SNAPSHOT
        ]

    def test_exact_40_new_opus_name_code_pairs_are_materialized(self):
        rows = self.p40_rows()
        self.assertEqual(40, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P40, actual)

    def test_p20_ten_opus_rows_remain_unchanged_and_p40_snapshot_is_exact_50(self):
        self.assertGreaterEqual(len(self.opus_rows()), 50)
        rows = self.p40_snapshot_rows()
        self.assertEqual(50, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(P40_SNAPSHOT, actual)

        historical = [
            row for row in rows
            if (row["ksh_settlement_code"], row["settlement_name"]) in EXPECTED_P20_OPUS
        ]
        self.assertEqual(10, len(historical))
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in historical))
        self.assertTrue(all(set(row["source_ids"].split(";")) == {OPUS, KSH_2019} for row in historical))

    def test_all_50_p40_snapshot_rows_preserve_observed_whole_settlement_semantics(self):
        rows = self.p40_snapshot_rows()
        self.assertEqual(50, len(rows))
        self.assertTrue(all(row["service_area_id"] == "OPUS_TITASZ:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(set(row["source_ids"].split(";")) == {OPUS, KSH_2019} for row in rows))

    def test_p40_historical_snapshot_is_bounded_to_m1_serial_50_not_51(self):
        names = {row["settlement_name"] for row in self.p40_snapshot_rows()}
        self.assertIn("Bakonszeg", names)
        self.assertIn("Csegöld", names)
        self.assertNotIn("Csenger", names)

    def test_source_registry_preserves_p40_lineage_inside_evolving_opus_state(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["OPUS_TITASZ"]
        self.assertEqual(OPUS, src["source_id"])
        self.assertEqual("OFFICIAL_CURRENT_M1_ATTACHMENT", src["source_kind"])
        self.assertEqual("CURRENT_2026", src["currentness_status"])
        self.assertIn(src["extraction_status"], {"PARTIAL_TRANCHE_MATERIALIZED", "COMPLETE_OPERATOR_M1_MATERIALIZED"})
        self.assertEqual("M1_SETTLEMENT_LIST", src["membership_semantics"])
        self.assertIn("P40", src["notes"])
        self.assertIn("11-50", src["notes"])
        self.assertIn("partial materialization", src["notes"])

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

    def test_source_pack_preserves_evidence_only_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "SETTLEMENT NAME != KSH SETTLEMENT ID",
            "KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP",
            "WHOLE SETTLEMENT != PARTIAL SETTLEMENT OR USAGE-LOCATION MEMBERSHIP",
            "DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE",
            "BOUNDED CURRENT M1 ROWS != COMPLETE OPERATOR CROSSWALK",
            "PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION",
            "serials **11–50**",
            "40 whole-settlement memberships",
            "50 materialized rows",
            "evidence_status = OBS",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

        for forbidden_claim in (
            "complete OPUS TITÁSZ settlement inventory materialization",
            "exact programme entity-to-node mapping",
            "headroom sufficiency",
            "reinforcement need",
            "programme-incremental CAPEX",
        ):
            self.assertIn(forbidden_claim, text)


if __name__ == "__main__":
    unittest.main()
