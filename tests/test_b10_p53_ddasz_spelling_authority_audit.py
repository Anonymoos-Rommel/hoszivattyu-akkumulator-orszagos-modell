import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry/dso_service_area_membership_ddasz_p53_spelling_authority_audit.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_ddasz_p53_authority_manifest.csv"
P48_PAIRS = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P53_B10_DDASZ_SPELLING_AUTHORITY_AUDIT.md"

EXPECTED_AUDIT_DIGEST = "e3a7e8e3b25964b3964eaaac027edc9fb52c4420f06391aed016fcc34639a2ce"
EXPECTED_TARGETS = {
    ("11916", "Balatonőszöd"), ("20464", "Baranyahídvég"),
    ("30094", "Csikóstőttős"), ("11086", "Cún"),
    ("16531", "Fűzvölgy"), ("05537", "Kallósd"),
    ("16683", "Káloz"), ("26888", "Kazsok"),
    ("15510", "Kőröshegy"), ("06992", "Kővágótöttös"),
    ("08961", "Őcsény"), ("18740", "Szabadhídvég"),
    ("18582", "Túrony"), ("05892", "Vokány"),
}
CANONICAL_CORROBORATIONS = {
    ("Kálóz", "Káloz"),
    ("Kazsók", "Kazsok"),
    ("Köröshegy", "Kőröshegy"),
    ("Kövágótöttös", "Kővágótöttös"),
}


class B10P53DdaszSpellingAuthorityAuditTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_fourteen_edge_audit_is_frozen_by_digest(self):
        rows = self.rows(AUDIT)
        self.assertEqual(14, len(rows))
        canonical = "".join(
            f'{r["source_token"]}|{r["diagnostic_ksh_code"]}|{r["diagnostic_ksh_name"]}|'
            f'{r["historical_eon_form"]}|{r["historical_comparison_status"]}|{r["admission_status"]}\n'
            for r in sorted(rows, key=lambda r: r["source_token"])
        )
        self.assertEqual(EXPECTED_AUDIT_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_audit_matches_exact_p48_spelling_target_set(self):
        rows = self.rows(AUDIT)
        actual = {(r["diagnostic_ksh_code"], r["diagnostic_ksh_name"]) for r in rows}
        self.assertEqual(EXPECTED_TARGETS, actual)
        self.assertEqual(14, len({r["source_token"] for r in rows}))

    def test_historical_comparison_is_exactly_four_canonical_and_ten_repetitions(self):
        rows = self.rows(AUDIT)
        canonical = [r for r in rows if r["historical_comparison_status"] == "HISTORICAL_CANONICAL_FORM_DSO_CORROBORATION"]
        repeated = [r for r in rows if r["historical_comparison_status"] == "HISTORICAL_REPEATS_CURRENT_VARIANT"]
        self.assertEqual(4, len(canonical))
        self.assertEqual(10, len(repeated))
        self.assertEqual(CANONICAL_CORROBORATIONS, {(r["source_token"], r["historical_eon_form"]) for r in canonical})
        self.assertTrue(all(r["historical_eon_form"] == r["diagnostic_ksh_name"] for r in canonical))
        self.assertTrue(all(r["historical_eon_form"] == r["source_token"] for r in repeated))

    def test_all_fourteen_edges_remain_fail_closed(self):
        rows = self.rows(AUDIT)
        self.assertTrue(all(r["admission_status"].startswith("UNRESOLVED_NO_") for r in rows))
        p48 = {(r["ksh_settlement_code"], r["settlement_name"]) for r in self.rows(P48_PAIRS)}
        self.assertEqual(777, len(p48))
        self.assertTrue(EXPECTED_TARGETS.isdisjoint(p48))
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "EON_DDASZ"]
        self.assertEqual(43, len(historical))
        self.assertEqual(820, len({(r["ksh_settlement_code"], r["settlement_name"]) for r in historical} | p48))

    def test_authority_manifest_is_historical_comparison_only_and_non_promoting(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("EON_DDASZ_P48_14_SPELLING_EDGES", row["audit_scope"])
        self.assertIn("EDD_elo_usz_melleklet_20241209", row["current_source_url"])
        self.assertIn("EON_Aramszolg_egyetemes_USZ_fugg_mell_korrekturazott_tervezet.pdf", row["historical_source_url"])
        self.assertEqual("2022", row["historical_reference_date"])
        self.assertEqual("HISTORICAL_COMPARISON_ONLY", row["historical_use"])
        self.assertEqual("NONE", row["currentness_claim"])
        self.assertEqual("MIXED_4_CANONICAL_CORROBORATIONS_10_VARIANT_REPETITIONS_NO_CURRENT_EQUIVALENCE", row["equivalence_authority_result"])

    def test_source_pack_preserves_fail_closed_authority_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "HISTORICAL E.ON NETWORK-LICENSEE TABLE != CURRENT DDÁSZ M1 AUTHORITY",
            "HISTORICAL CANONICAL-FORM DSO CORROBORATION != CURRENT M1 SOURCE-FORM EQUIVALENCE",
            "HISTORICAL REPETITION OF THE SAME SOURCE VARIANT != INDEPENDENT IDENTITY-EQUIVALENCE AUTHORITY",
            "P53 adds **zero** service-area membership rows",
            "820 materialized current provable whole-settlement identities",
            "296",
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
