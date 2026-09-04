import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
OPUS_P44 = ROOT / "registry/dso_service_area_membership_crosswalk_opus_p44.csv"
DEMASZ_P45 = ROOT / "registry/dso_service_area_membership_crosswalk_demasz_p45.csv"
P46 = ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P46_B10_ELMU_KSH_WHOLE_SETTLEMENT_COMPLETION.md"

ELMU = "SRC-B10-ELMU-M1-CANDIDATE-2025"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"
KSH_2025 = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"
KSH_DERIVED = "SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026"
EXPECTED_P46_DIGEST = "4c4f4159b8546b6517230c07276a44a755064813a7aca6368f1f8c94125707e3"

UNRESOLVED_SOURCE_TOKENS = {
    "Budapest",
    "Bankháza (Kiskunlacháza)",
    "Domonyvölgy (Domony)",
    "Tass üdülőterület",
}

IDENTITY_SPECIFIC_SPLITS = {
    ("11934", "Üröm", "Üröm és Visegrád"),
    ("28413", "Visegrád", "Üröm és Visegrád"),
    ("33729", "Verőce", "Verőce Zebegény"),
    ("14960", "Zebegény", "Verőce Zebegény"),
}

DIRECT_KSH_2019 = {
    ("23649", "Göd"),
    ("31963", "Tahitótfalu"),
}


class B10P46ElmuKshWholeSettlementCompletionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def p46_rows(self):
        return self.rows(P46)

    def all_membership_rows(self):
        rows = []
        for path in (TRANCHE, OPUS_P44, DEMASZ_P45, P46):
            rows.extend(self.rows(path))
        return rows

    def test_exact_87_p46_pairs_are_frozen_by_digest(self):
        rows = self.p46_rows()
        self.assertEqual(87, len(rows))
        pairs = sorted((row["ksh_settlement_code"], row["settlement_name"]) for row in rows)
        canonical = "".join(f"{code}|{name}\n" for code, name in pairs)
        self.assertEqual(EXPECTED_P46_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())
        self.assertEqual(87, len(set(pairs)))

    def test_all_p46_rows_are_exact_der_whole_settlement_memberships(self):
        rows = self.p46_rows()
        self.assertTrue(all(row["operator_id"] == "ELMU" for row in rows))
        self.assertTrue(all(row["network_operator"] == "ELMŰ Hálózati Kft." for row in rows))
        self.assertTrue(all(row["service_area_id"] == "ELMU:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "DER" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(ELMU in row["source_ids"].split(";") for row in rows))

    def test_historical_43_plus_p46_87_equals_exact_130_whole_population(self):
        historical = [row for row in self.rows(TRANCHE) if row["operator_id"] == "ELMU"]
        completion = self.p46_rows()
        self.assertEqual(43, len(historical))
        self.assertEqual(87, len(completion))
        historical_pairs = {(row["ksh_settlement_code"], row["settlement_name"]) for row in historical}
        completion_pairs = {(row["ksh_settlement_code"], row["settlement_name"]) for row in completion}
        self.assertFalse(historical_pairs & completion_pairs)
        self.assertEqual(130, len(historical_pairs | completion_pairs))

    def test_four_mixed_or_special_source_tokens_remain_fail_closed(self):
        names = {
            row["settlement_name"]
            for row in self.rows(TRANCHE) + self.p46_rows()
            if row["operator_id"] == "ELMU"
        }
        self.assertFalse(names & UNRESOLVED_SOURCE_TOKENS)
        self.assertNotIn("Tass", names)
        self.assertNotIn("Domony", names)
        self.assertNotIn("Bankháza", names)

    def test_identity_specific_split_is_exactly_four_rows_and_not_generalized(self):
        by_pair = {(row["ksh_settlement_code"], row["settlement_name"]): row for row in self.p46_rows()}
        for code, name, token in IDENTITY_SPECIFIC_SPLITS:
            row = by_pair[(code, name)]
            self.assertIn(token, row["notes"])
            self.assertIn("official ELMŰ településlista corroboration", row["notes"])
            self.assertIn("no general split rule", row["notes"])
            self.assertEqual({ELMU, KSH_2025, KSH_DERIVED}, set(row["source_ids"].split(";")))
        split_rows = [row for row in self.p46_rows() if "identity-specific split" in row["notes"]]
        self.assertEqual(4, len(split_rows))

    def test_god_and_tahitotfalu_use_direct_official_ksh_identity(self):
        by_pair = {(row["ksh_settlement_code"], row["settlement_name"]): row for row in self.p46_rows()}
        for pair in DIRECT_KSH_2019:
            row = by_pair[pair]
            self.assertEqual({ELMU, KSH_2019}, set(row["source_ids"].split(";")))
            self.assertIn("direct KSH 2019 identity", row["notes"])

    def test_other_exact_locator_rows_keep_current_ksh_derivation_chain(self):
        direct_pairs = DIRECT_KSH_2019
        split_pairs = {(code, name) for code, name, _ in IDENTITY_SPECIFIC_SPLITS}
        for row in self.p46_rows():
            pair = (row["ksh_settlement_code"], row["settlement_name"])
            if pair in direct_pairs or pair in split_pairs:
                continue
            self.assertEqual({ELMU, KSH_2025, KSH_DERIVED}, set(row["source_ids"].split(";")))

    def test_ksh_codes_are_unique_across_all_materialized_membership_surfaces(self):
        rows = self.all_membership_rows()
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_source_registry_records_whole_completion_but_keeps_operator_partial(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["ELMU"]
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", src["extraction_status"])
        self.assertIn("P46", src["notes"])
        self.assertIn("130 materialized", src["notes"])
        for token in UNRESOLVED_SOURCE_TOKENS:
            self.assertIn(token, src["notes"])
        self.assertNotEqual("COMPLETE_OPERATOR_M1_MATERIALIZED", src["extraction_status"])

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])

    def test_source_pack_preserves_completion_accounting_and_non_claims(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "completion-first evidence/data slice",
            "132 comma-delimited source tokens",
            "43 historical + 87 P46 = 130 materialized whole-settlement identities",
            "IDENTITY-SPECIFIC TOKEN RESOLUTION != GENERAL SPLIT OR FUZZY RULE",
            "Budapest",
            "Bankháza (Kiskunlacháza)",
            "Domonyvölgy (Domony)",
            "Tass üdülőterület",
            "PARTIAL_TRANCHE_MATERIALIZED",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
