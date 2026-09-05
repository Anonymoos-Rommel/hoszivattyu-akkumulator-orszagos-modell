import csv
import hashlib
from pathlib import Path
import re
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry/dso_service_area_membership_ddasz_p59_residual_authority_audit.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_ddasz_p59_authority_manifest.csv"
P53 = ROOT / "registry/dso_service_area_membership_ddasz_p53_spelling_authority_audit.csv"
P54 = ROOT / "registry/dso_service_area_membership_ddasz_p54_cross_dso_conflict_audit.csv"
P54_MANIFEST = ROOT / "registry/dso_service_area_membership_ddasz_p54_authority_manifest.csv"
P48_PAIRS = ROOT / "registry/dso_service_area_membership_ddasz_p48_pairs.csv"
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P59_B10_DDASZ_RESIDUAL_SOURCE_GRAIN_DECOMPOSITION.md"

EXPECTED_AUDIT_DIGEST = "3ff17b98c20a869add06f535e7143a9d6302d27ee2ea68750ed270d22210a44a"
EXPECTED_CLASSES = {
    "EXPLICIT_DELIMITED_MULTI_COMPONENT_SOURCE_FORM": 86,
    "COMPACT_HYPHENATED_SOURCE_FORM": 7,
    "STANDALONE_NONEXACT_SOURCE_FORM": 187,
}
COMPACT = {
    "Cserkút-szőlőhegy",
    "Dióspuszta-Hitmes-Zalasor",
    "Gyapa-puszta",
    "Pécs-Szikuti d.",
    "Pécs-Vasas",
    "Söjtör-barátipuszta",
    "Söjtör-Szénásvölgy",
}


class B10P59DdaszResidualSourceGrainDecompositionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_280_rows_are_frozen_by_digest(self):
        rows = self.rows(AUDIT)
        self.assertEqual(280, len(rows))
        self.assertEqual(280, len({r["source_token"] for r in rows}))
        self.assertTrue(all(r["source_occurrence_count"] == "1" for r in rows))
        canonical = "".join(
            f'{r["source_token"]}|{r["source_occurrence_count"]}|{r["residual_class"]}\n'
            for r in sorted(rows, key=lambda r: r["source_token"])
        )
        self.assertEqual(EXPECTED_AUDIT_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_class_partition_is_exact(self):
        rows = self.rows(AUDIT)
        counts = {name: 0 for name in EXPECTED_CLASSES}
        for row in rows:
            self.assertIn(row["residual_class"], counts)
            counts[row["residual_class"]] += 1
        self.assertEqual(EXPECTED_CLASSES, counts)
        self.assertEqual(COMPACT, {r["source_token"] for r in rows if r["residual_class"] == "COMPACT_HYPHENATED_SOURCE_FORM"})

    def test_class_assignment_is_deterministic_source_syntax_only(self):
        for row in self.rows(AUDIT):
            token = row["source_token"]
            explicit = bool(re.search(r"\s-\s|- ", token))
            compact = "-" in token and not explicit
            expected = (
                "EXPLICIT_DELIMITED_MULTI_COMPONENT_SOURCE_FORM" if explicit
                else "COMPACT_HYPHENATED_SOURCE_FORM" if compact
                else "STANDALONE_NONEXACT_SOURCE_FORM"
            )
            self.assertEqual(expected, row["residual_class"], token)

    def test_p59_is_disjoint_from_p53_and_p54(self):
        p59 = {r["source_token"] for r in self.rows(AUDIT)}
        p53 = {r["source_token"] for r in self.rows(P53)}
        p54 = {r["current_ddasz_source_form"] for r in self.rows(P54)}
        self.assertEqual(14, len(p53))
        self.assertEqual(2, len(p54))
        self.assertFalse(p59 & p53)
        self.assertFalse(p59 & p54)
        self.assertFalse(p53 & p54)

    def test_p54_accounting_reconciles_exactly(self):
        self.assertEqual(296, len(self.rows(AUDIT)) + len(self.rows(P53)) + len(self.rows(P54)))
        manifest = self.rows(P54_MANIFEST)
        self.assertEqual(1, len(manifest))
        self.assertEqual("296=14_SPELLING+2_CROSS_DSO+280_OTHER_UNRESOLVED", manifest[0]["p48_residual_accounting"])

    def test_representative_source_native_forms_are_not_repaired(self):
        tokens = {r["source_token"] for r in self.rows(AUDIT)}
        for token in (
            "Dombovár - Gunarasfürdő",
            "Molványhid",
            "Mozsgó- Mozsgó szőlőhegy- Jedinka",
            "Pécs-Szikuti d.",
            "Ujberek puszta",
            "Vörrü",
            "Szentlászló - Szentegyed - Riticspuszta",
            "Báta- Furkótelep",
            "Cserkút-szőlőhegy",
        ):
            self.assertIn(token, tokens)
        for repaired in ("Dombóvár - Gunarasfürdő", "Molványhíd", "Újberek puszta"):
            self.assertNotIn(repaired, tokens)

    def test_ddasz_membership_population_is_unchanged(self):
        historical = [r for r in self.rows(HISTORICAL) if r["operator_id"] == "EON_DDASZ"]
        p48 = self.rows(P48_PAIRS)
        self.assertEqual(43, len(historical))
        self.assertEqual(777, len(p48))
        self.assertEqual(820, len(historical) + len(p48))
        p48_names = {r["settlement_name"] for r in p48}
        self.assertTrue({r["source_token"] for r in self.rows(AUDIT)}.isdisjoint(p48_names))

    def test_manifest_freezes_non_promoting_state_and_source_lineage(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("EON_DDASZ", row["operator_id"])
        self.assertEqual("SRC-B10-EON-DDASZ-M1-CANDIDATE-2025", row["current_source_id"])
        for field, expected in {
            "p48_unique_source_tokens": "1116",
            "p48_materialized_whole_identities": "820",
            "p48_residual_tokens": "296",
            "p53_spelling_tokens": "14",
            "p54_cross_dso_conflict_tokens": "2",
            "p59_other_residual_tokens": "280",
            "explicit_delimited_count": "86",
            "compact_hyphenated_count": "7",
            "standalone_nonexact_count": "187",
        }.items():
            self.assertEqual(expected, row[field])
        self.assertEqual(EXPECTED_AUDIT_DIGEST, row["audit_sha256"])
        self.assertEqual("UNRESOLVED_AUTHORITY_REQUIRED", row["admission_status"])
        self.assertEqual("IDENTITY_GRAIN_OR_USAGE_LOCATION_AUTHORITY", row["required_future_authority"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", row["operator_extraction_state"])
        self.assertEqual("ZERO_NEW_MEMBERSHIP_ROWS", row["admission_impact"])

        source = [r for r in self.rows(SOURCES) if r["operator_id"] == "EON_DDASZ"]
        self.assertEqual(1, len(source))
        self.assertEqual(source[0]["source_url"], row["current_source_url"])
        self.assertIn("P48_PROBE_HEAD_9f7540c84eb1508427168ccb593cb88b5c121624_RUN_33903341019", row["reconstruction_lineage"])

    def test_source_pack_preserves_fail_closed_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "299 - 5 - 14 = 280",
            "296 = 14 spelling diagnostics + 2 cross-DSO conflicts + 280 P59 other unresolved source forms",
            "86 + 7 + 187 = 280",
            "SOURCE-FORM SYNTAX != SETTLEMENT-PART SEMANTICS",
            "DELIMITER PRESENCE != PARENT-CHILD AUTHORITY",
            "COMPACT HYPHEN != AUTHORITY TO SPLIT A SOURCE TOKEN",
            "STANDALONE SOURCE FORM != WHOLE-SETTLEMENT IDENTITY",
            "SOURCE-GRAIN CLASSIFICATION != MEMBERSHIP AUTHORITY",
            "COMPLETE RESIDUAL FORM CLASSIFICATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK",
            "zero service-area membership rows",
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
