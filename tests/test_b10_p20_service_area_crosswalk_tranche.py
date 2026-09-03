import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
AUTHORITIES = ROOT / "registry/dso_service_area_crosswalk_authorities.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"


class B10P20ServiceAreaCrosswalkTrancheTests(unittest.TestCase):
    def tranche_rows(self):
        with TRANCHE.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def authority_ids(self):
        with AUTHORITIES.open(encoding="utf-8", newline="") as handle:
            return {row["source_id"] for row in csv.DictReader(handle)}

    def test_tranche_is_real_but_not_national(self):
        rows = self.tranche_rows()
        self.assertEqual(20, len(rows))
        self.assertEqual({"MVM_DEMASZ", "OPUS_TITASZ"}, {row["operator_id"] for row in rows})
        self.assertEqual(10, sum(row["operator_id"] == "MVM_DEMASZ" for row in rows))
        self.assertEqual(10, sum(row["operator_id"] == "OPUS_TITASZ" for row in rows))

    def test_every_row_is_proven_whole_settlement_membership(self):
        rows = self.tranche_rows()
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(row["service_area_id"] == f"{row['operator_id']}:SERVICE_AREA" for row in rows))

    def test_ksh_identifiers_are_canonical_five_digit_values(self):
        rows = self.tranche_rows()
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(code and code.isdigit() and len(code) == 5 for code in codes))
        self.assertIn("17686", codes)
        self.assertIn("08697", codes)
        self.assertIn("12441", codes)
        self.assertIn("08776", codes)
        self.assertNotIn("1768", codes)

    def test_every_source_reference_is_registered(self):
        authorities = self.authority_ids()
        self.assertEqual(
            {
                "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS",
                "SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026",
                "SRC-B10-OPUS-TITASZ-M1-2026",
            },
            authorities,
        )
        for row in self.tranche_rows():
            refs = set(row["source_ids"].split(";"))
            self.assertTrue(refs.issubset(authorities))
            self.assertIn("SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS", refs)

    def test_mvm_partial_settlements_are_not_promoted(self):
        names = {row["settlement_name"] for row in self.tranche_rows() if row["operator_id"] == "MVM_DEMASZ"}
        partial = {
            "Baja", "Csongrád", "Érsekcsanád", "Gyomaendrőd",
            "Kunszentmárton", "Mohács", "Solt", "Szeghalom", "Szentes",
            "Tápiószőlős", "Tass", "Tiszakécske", "Tiszasas", "Tiszaug",
            "Újhartyán", "Zsadány",
        }
        self.assertFalse(names & partial)

    def test_national_canonical_crosswalk_remains_header_only(self):
        lines = CANONICAL.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("ksh_settlement_code,settlement_name,operator_id,"))

    def test_source_pack_preserves_identity_completeness_and_partial_settlement_gates(self):
        text = (ROOT / "docs/source_packs/P20_B10_DSO_KSH_SERVICE_AREA_CROSSWALK_TRANCHE.md").read_text(encoding="utf-8")
        self.assertIn("5 jegyű", text)
        self.assertIn("PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION", text)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", text)
        self.assertIn("readiness **15**", text)


if __name__ == "__main__":
    unittest.main()
