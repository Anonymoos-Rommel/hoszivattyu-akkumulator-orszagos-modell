import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry/dso_service_area_membership_edasz_p50_spelling_authority_audit.csv"
P49_PAIRS = ROOT / "registry/dso_service_area_membership_edasz_p49_pairs.csv"
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P50_B10_EDASZ_SPELLING_AUTHORITY_AUDIT.md"

EXPECTED_AUDIT_DIGEST = "d99b1835dbe625b6524447a1d1642fe2aaf915fe0c1ea988c2ce8e0da2acb206"
EXPECTED_TARGETS = {
    ("23153", "Bakonykúti"), ("21917", "Dör"), ("25946", "Egyházasrádóc"),
    ("29939", "Felcsút"), ("24369", "Felsőörs"), ("18193", "Gógánfa"),
    ("11156", "Gór"), ("02060", "Gönyű"), ("29771", "Gősfa"),
    ("27030", "Gyanógeregye"), ("15918", "Gyúró"), ("12733", "Horvátlövő"),
    ("08749", "Karakószörcsök"), ("19734", "Kemeneshőgyész"), ("02413", "Kisbabot"),
    ("23454", "Kővágóörs"), ("31194", "Lövő"), ("24509", "Nemesbőd"),
    ("22318", "Nyőgér"), ("27775", "Óhíd"), ("22044", "Ólmod"),
    ("13453", "Őrimagyarósd"), ("17011", "Paloznak"), ("07551", "Rádóckölked"),
    ("22983", "Sótony"), ("31990", "Súr"), ("22619", "Szomód"),
    ("20853", "Úrkút"), ("29373", "Vasszécseny"), ("30313", "Zalalövő"),
}


class B10P50EdaszSpellingAuthorityAuditTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_30_edge_audit_is_frozen_by_digest(self):
        rows = self.rows(AUDIT)
        self.assertEqual(30, len(rows))
        canonical = "".join(
            f'{r["source_token"]}|{r["diagnostic_ksh_code"]}|{r["diagnostic_ksh_name"]}|'
            f'{r["historical_comparison_status"]}|{r["admission_status"]}\n'
            for r in sorted(rows, key=lambda r: r["source_token"])
        )
        self.assertEqual(EXPECTED_AUDIT_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_audit_matches_exact_p49_spelling_target_set(self):
        rows = self.rows(AUDIT)
        actual = {(r["diagnostic_ksh_code"], r["diagnostic_ksh_name"]) for r in rows}
        self.assertEqual(EXPECTED_TARGETS, actual)
        self.assertEqual(30, len({r["source_token"] for r in rows}))

    def test_historical_repetition_cannot_authorize_equivalence(self):
        rows = self.rows(AUDIT)
        for row in rows:
            self.assertEqual(row["source_token"], row["historical_source_form"])
            self.assertEqual("HISTORICAL_REPEATS_CURRENT_VARIANT", row["historical_comparison_status"])
            self.assertEqual("UNRESOLVED_NO_EQUIVALENCE_AUTHORITY", row["admission_status"])
            self.assertNotEqual(row["source_token"], row["diagnostic_ksh_name"])

    def test_p50_adds_no_membership_rows(self):
        p49 = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.rows(P49_PAIRS)}
        self.assertEqual(769, len(p49))
        self.assertTrue(EXPECTED_TARGETS.isdisjoint(p49))
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "EON_EDASZ"]
        self.assertEqual(45, len(historical))
        self.assertEqual(814, len({(r["ksh_settlement_code"], r["settlement_name"]) for r in historical} | p49))

    def test_source_pack_preserves_fail_closed_authority_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "HISTORICAL REPETITION OF THE SAME SOURCE VARIANT != INDEPENDENT IDENTITY-EQUIVALENCE AUTHORITY",
            "SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE",
            "P50 adds **zero** new service-area membership rows",
            "unresolved ÉDÁSZ unique-token count remains **59**",
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
