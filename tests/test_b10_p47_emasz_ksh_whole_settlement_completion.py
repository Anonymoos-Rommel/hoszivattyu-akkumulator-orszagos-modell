import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
OPUS_P44 = ROOT / "registry/dso_service_area_membership_crosswalk_opus_p44.csv"
DEMASZ_P45 = ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv"
ELMU_P46 = ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv"
PAIRS = ROOT / "registry/dso_service_area_membership_emasz_p47_pairs.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_emasz_p47_manifest.csv"
EXCEPTIONS = ROOT / "registry/dso_service_area_membership_emasz_p47_exceptions.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P47_B10_EMASZ_KSH_WHOLE_SETTLEMENT_COMPLETION.md"

MVM = "SRC-B10-MVM-EMASZ-M1-2026"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"
KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_2025_DERIVATION = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"
EXPECTED_PAIR_DIGEST = "a65a2577fd8757550d94bc245e7e7c9711f9e75057fb210ef26462ce36dddfd0"

EXPECTED_EXCEPTIONS = {
    ("30456", "Miskolc", "KSH2019_DIRECT", "Miskolc"),
    ("33525", "Mátraterenye", "KSH2019_DIRECT", "Mátraterenye"),
    ("14641", "Márkháza", "IDENTITY_SPECIFIC_SOURCE_SPLIT", "Márkháza Mályi"),
    ("27395", "Mályi", "IDENTITY_SPECIFIC_SOURCE_SPLIT", "Márkháza Mályi"),
    ("22169", "Szentistván", "IDENTITY_SPECIFIC_SOURCE_SPLIT", "Szentistván Szentistvánbaksa"),
    ("08484", "Szentistvánbaksa", "IDENTITY_SPECIFIC_SOURCE_SPLIT", "Szentistván Szentistvánbaksa"),
}


class B10P47EmaszKshWholeSettlementCompletionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def p47_pairs(self):
        return self.rows(PAIRS)

    def test_exact_605_p47_pairs_are_frozen_by_digest(self):
        rows = self.p47_pairs()
        self.assertEqual(605, len(rows))
        canonical = "".join(
            f'{row["ksh_settlement_code"]}|{row["settlement_name"]}\n'
            for row in sorted(rows, key=lambda r: (r["ksh_settlement_code"], r["settlement_name"]))
        )
        self.assertEqual(EXPECTED_PAIR_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_p47_pairs_are_unique_five_digit_identifiers(self):
        rows = self.p47_pairs()
        codes = [row["ksh_settlement_code"] for row in rows]
        names = [row["settlement_name"] for row in rows]
        self.assertEqual(605, len(set(codes)))
        self.assertEqual(605, len(set(names)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))
        self.assertIn(("21768", "Megyaszó"), {(r["ksh_settlement_code"], r["settlement_name"]) for r in rows})

    def test_manifest_reconstructs_exact_mvm_emasz_der_semantics(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("MVM_EMASZ", row["operator_id"])
        self.assertEqual("MVM Émász Áramhálózati Kft.", row["network_operator"])
        self.assertEqual("MVM_EMASZ:SERVICE_AREA", row["service_area_id"])
        self.assertEqual("WHOLE_SETTLEMENT", row["coverage_scope"])
        self.assertEqual("NONE", row["usage_location_requirement"])
        self.assertEqual("DER", row["evidence_status"])
        self.assertEqual("WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN", row["status"])
        self.assertEqual({MVM, KSH_2025, KSH_2025_DERIVATION}, set(row["normal_source_ids"].split(";")))
        self.assertEqual(str(PAIRS.relative_to(ROOT)), row["pairs_file"])
        self.assertEqual(str(EXCEPTIONS.relative_to(ROOT)), row["exception_file"])

    def test_six_identity_path_exceptions_are_exact_and_nongeneralized(self):
        rows = self.rows(EXCEPTIONS)
        actual = {
            (r["ksh_settlement_code"], r["settlement_name"], r["exception_class"], r["source_token"])
            for r in rows
        }
        self.assertEqual(EXPECTED_EXCEPTIONS, actual)
        self.assertTrue(all(set(r["source_ids"].split(";")) == {MVM, KSH_2019} for r in rows))
        split_rows = [r for r in rows if r["exception_class"] == "IDENTITY_SPECIFIC_SOURCE_SPLIT"]
        self.assertEqual(4, len(split_rows))
        self.assertEqual(
            {"Márkháza Mályi", "Szentistván Szentistvánbaksa"},
            {r["source_token"] for r in split_rows},
        )
        self.assertTrue(all("no generalized splitter" in r["notes"] for r in split_rows))

    def test_historical_45_plus_p47_605_equals_650_materialized_whole_identities(self):
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "MVM_EMASZ"]
        self.assertEqual(45, len(historical))
        self.assertEqual(5, len([r for r in historical if r["evidence_status"] == "OBS"]))
        self.assertEqual(40, len([r for r in historical if r["evidence_status"] == "DER"]))
        old_pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in historical}
        new_pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.p47_pairs()}
        self.assertFalse(old_pairs & new_pairs)
        self.assertEqual(650, len(old_pairs | new_pairs))

    def test_two_spelling_equivalence_edges_remain_fail_closed(self):
        pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.p47_pairs()}
        for unresolved in {
            ("17932", "Fony"),
            ("17932", "Fóny"),
            ("25672", "Hidvégardó"),
            ("25672", "Hídvégardó"),
        }:
            self.assertNotIn(unresolved, pairs)
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("Fóny` versus KSH `Fony` (`17932`)", text)
        self.assertIn("Hídvégardó` versus KSH `Hidvégardó` (`25672`)", text)
        self.assertIn("does **not** authorize those two equivalences", text)

    def test_global_materialized_ksh_codes_remain_unique(self):
        codes = []
        for path in (HISTORICAL, OPUS_P44, DEMASZ_P45, ELMU_P46):
            codes.extend(r["ksh_settlement_code"] for r in self.rows(path))
        codes.extend(r["ksh_settlement_code"] for r in self.p47_pairs())
        self.assertEqual(len(codes), len(set(codes)))

    def test_source_registry_records_p47_completion_but_keeps_operator_partial(self):
        by_operator = {r["operator_id"]: r for r in self.rows(SOURCES)}
        row = by_operator["MVM_EMASZ"]
        self.assertEqual(MVM, row["source_id"])
        self.assertEqual("CURRENT_2026", row["currentness_status"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", row["extraction_status"])
        for marker in ("P47", "605", "650", "749", "99", "Fóny", "Hídvégardó"):
            self.assertIn(marker, row["notes"])

    def test_source_pack_preserves_complete_accounting_and_normalized_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "749 source tokens",
            "99",
            "652 potential whole-settlement identities",
            "45 historical + 605 P47 = 650",
            "NORMALIZED STORAGE != WEAKER ROW-LEVEL EVIDENCE",
            "COMPLETE PROVABLE WHOLE-SETTLEMENT MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        by_module = {r["module_id"]: r for r in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
