import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry/dso_service_area_membership_emasz_p52_spelling_authority_audit.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_emasz_p52_authority_manifest.csv"
P47_PAIRS = ROOT / "registry/dso_service_area_membership_emasz_p47_pairs.csv"
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P52_B10_EMASZ_SPELLING_AUTHORITY_AUDIT.md"

EXPECTED_AUDIT_DIGEST = "9f68e7eb5c915be7e355ac6384414a00d80e41078fbe067ae92a983ff9979769"
EXPECTED_TARGETS = {
    ("17932", "Fony"),
    ("25672", "Hidvégardó"),
}


class B10P52EmaszSpellingAuthorityAuditTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_two_edge_audit_is_frozen_by_digest(self):
        rows = self.rows(AUDIT)
        self.assertEqual(2, len(rows))
        canonical = "".join(
            f'{r["source_token"]}|{r["diagnostic_ksh_code"]}|{r["diagnostic_ksh_name"]}|'
            f'{r["historical_comparison_status"]}|{r["admission_status"]}\n'
            for r in sorted(rows, key=lambda r: r["source_token"])
        )
        self.assertEqual(EXPECTED_AUDIT_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_audit_matches_exact_p47_spelling_target_set(self):
        rows = self.rows(AUDIT)
        actual = {(r["diagnostic_ksh_code"], r["diagnostic_ksh_name"]) for r in rows}
        self.assertEqual(EXPECTED_TARGETS, actual)
        self.assertEqual({"Fóny", "Hídvégardó"}, {r["source_token"] for r in rows})

    def test_historical_repetition_cannot_authorize_equivalence(self):
        rows = self.rows(AUDIT)
        for row in rows:
            self.assertEqual(row["source_token"], row["historical_source_form"])
            self.assertEqual("HISTORICAL_REPEATS_CURRENT_VARIANT", row["historical_comparison_status"])
            self.assertEqual("UNRESOLVED_NO_EQUIVALENCE_AUTHORITY", row["admission_status"])
            self.assertNotEqual(row["source_token"], row["diagnostic_ksh_name"])

    def test_authority_manifest_is_comparison_only_and_non_promoting(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("MVM_EMASZ_P47_2_SPELLING_EDGES", row["audit_scope"])
        self.assertIn("uzletszabalyzat-20260526", row["current_source_url"])
        self.assertIn("uzletszabalyzat-20221221", row["historical_source_url"])
        self.assertEqual("2022-12-21", row["historical_reference_date"])
        self.assertEqual("HISTORICAL_COMPARISON_ONLY", row["historical_use"])
        self.assertEqual("NONE", row["currentness_claim"])
        self.assertEqual("NO_INDEPENDENT_EQUIVALENCE_AUTHORITY", row["equivalence_authority_result"])

    def test_p52_adds_no_membership_rows(self):
        p47 = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.rows(P47_PAIRS)}
        self.assertEqual(605, len(p47))
        self.assertTrue(EXPECTED_TARGETS.isdisjoint(p47))
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "MVM_EMASZ"]
        self.assertEqual(45, len(historical))
        historical_pairs = {(r["ksh_settlement_code"], r["settlement_name"]) for r in historical}
        self.assertEqual(650, len(historical_pairs | p47))
        self.assertTrue(EXPECTED_TARGETS.isdisjoint(historical_pairs | p47))

    def test_source_pack_preserves_fail_closed_authority_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "HISTORICAL REPETITION OF THE SAME SOURCE VARIANT != INDEPENDENT IDENTITY-EQUIVALENCE AUTHORITY",
            "SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE",
            "P52 adds **zero** new service-area membership rows",
            "45 historical + 605 P47 = 650",
            "99 parenthesized named-subsettlement / special-grain M1 tokens",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

    def test_canonical_crosswalk_and_b10_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        by_module = {r["module_id"]: r for r in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
