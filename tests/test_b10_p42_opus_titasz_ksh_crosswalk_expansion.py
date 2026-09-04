import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P42_B10_OPUS_TITASZ_KSH_CROSSWALK_EXPANSION.md"

OPUS = "SRC-B10-OPUS-TITASZ-M1-2026"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"

EXPECTED_P42 = {
    ("05670", "Gégény"), ("16568", "Görbeháza"),
    ("29443", "Gulács"), ("33455", "Gyomaendrőd"),
    ("28945", "Győröcske"), ("10126", "Győrtelek"),
    ("07676", "Gyulaháza"), ("19558", "Gyügye"),
    ("33774", "Gyüre"), ("26170", "Hajdúbagos"),
    ("03045", "Hajdúböszörmény"), ("12803", "Hajdúdorog"),
    ("10393", "Hajdúhadház"), ("22406", "Hajdúnánás"),
    ("31097", "Hajdúsámson"), ("05175", "Hajdúszoboszló"),
    ("17473", "Hajdúszovát"), ("29391", "Hencida"),
    ("12061", "Hermánszeg"), ("05616", "Hetefejércse"),
    ("13019", "Hodász"), ("04118", "Hortobágy"),
    ("06266", "Hosszúpályi"), ("34050", "Hunyadfalva"),
    ("25636", "Ibrány"), ("09654", "Ilk"),
    ("17075", "Jánd"), ("07843", "Jánkmajtis"),
    ("22859", "Jánoshida"), ("17589", "Jármi"),
    ("30711", "Jászalsószentgyörgy"), ("15811", "Jászboldogháza"),
    ("11004", "Jászkarajenő"), ("21111", "Jászladány"),
    ("13143", "Jéke"), ("02307", "Kaba"),
    ("04923", "Karcag"), ("31404", "Kállósemjén"),
    ("27225", "Kálmánháza"), ("02671", "Kántorjánosi"),
}


class B10P42OpusTitaszKshCrosswalkExpansionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def opus_rows(self):
        return [row for row in self.rows(TRANCHE) if row["operator_id"] == "OPUS_TITASZ"]

    def p42_rows(self):
        return [
            row for row in self.opus_rows()
            if (row["ksh_settlement_code"], row["settlement_name"]) in EXPECTED_P42
        ]

    def test_exact_40_p42_name_code_pairs_are_materialized(self):
        rows = self.p42_rows()
        self.assertEqual(40, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P42, actual)

    def test_p42_exact_40_rows_remain_inside_evolving_opus_tranche(self):
        rows = self.opus_rows()
        self.assertGreaterEqual(len(rows), 130)
        self.assertEqual(40, len(self.p42_rows()))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertTrue(EXPECTED_P42.issubset(actual))

    def test_evolving_opus_rows_preserve_direct_observed_whole_settlement_semantics(self):
        rows = self.opus_rows()
        self.assertGreaterEqual(len(rows), 130)
        self.assertTrue(all(row["service_area_id"] == "OPUS_TITASZ:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(set(row["source_ids"].split(";")) == {OPUS, KSH_2019} for row in rows))

    def test_p42_historical_set_is_bounded_to_m1_serial_130_not_131(self):
        names = {row["settlement_name"] for row in self.p42_rows()}
        self.assertIn("Gégény", names)
        self.assertIn("Kántorjánosi", names)
        self.assertNotIn("Kemecse", names)

    def test_source_registry_preserves_p20_p40_p41_p42_lineage_inside_evolving_state(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["OPUS_TITASZ"]
        self.assertEqual(OPUS, src["source_id"])
        self.assertEqual("OFFICIAL_CURRENT_M1_ATTACHMENT", src["source_kind"])
        self.assertEqual("CURRENT_2026", src["currentness_status"])
        self.assertIn(src["extraction_status"], {"PARTIAL_TRANCHE_MATERIALIZED", "COMPLETE_OPERATOR_M1_MATERIALIZED"})
        self.assertEqual("M1_SETTLEMENT_LIST", src["membership_semantics"])
        for marker in (
            "P20", "1-10", "P40", "11-50", "P41", "51-90",
            "P42", "91-130", "partial materialization",
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

    def test_source_pack_preserves_p42_evidence_only_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "serials **91–130**",
            "130 materialized rows",
            "serial **130, Kántorjánosi**",
            "serial **131, Kemecse**",
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
