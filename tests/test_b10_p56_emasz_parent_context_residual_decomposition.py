import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry/dso_service_area_membership_emasz_p56_parent_context_residual_audit.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_emasz_p56_authority_manifest.csv"
HISTORICAL = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
P47 = ROOT / "registry/dso_service_area_membership_emasz_p47_pairs.csv"
P52 = ROOT / "registry/dso_service_area_membership_emasz_p52_spelling_authority_audit.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P56_B10_EMASZ_PARENT_CONTEXT_RESIDUAL_DECOMPOSITION.md"

MVM = "SRC-B10-MVM-EMASZ-M1-2026"
EXPECTED_DIGEST = "a8bd4942fbd3d286ce8444ce8736b358a92e71c3fc56926665da49072e19c165"
MALFORMED = "Mátraszentistván Mátraszentimre)"


class B10P56EmaszParentContextResidualDecompositionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_99_residual_rows_are_frozen_by_digest(self):
        rows = self.rows(AUDIT)
        self.assertEqual(99, len(rows))
        self.assertEqual(99, len({row["source_token"] for row in rows}))
        canonical = "".join(
            f'{row["source_token"]}|{row["source_occurrence_count"]}|{row["residual_class"]}|{row["admission_status"]}\n'
            for row in sorted(rows, key=lambda r: r["source_token"])
        )
        self.assertEqual(EXPECTED_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_residual_partition_is_exactly_98_plus_one_malformed(self):
        rows = self.rows(AUDIT)
        well_formed = [row for row in rows if row["residual_class"] == "PARENTHESIZED_PARENT_CONTEXT"]
        malformed = [row for row in rows if row["residual_class"] == "MALFORMED_PARENT_CONTEXT_TOKEN"]
        self.assertEqual(98, len(well_formed))
        self.assertEqual(1, len(malformed))
        self.assertEqual(MALFORMED, malformed[0]["source_token"])
        self.assertTrue(all(" (" in row["source_token"] and row["source_token"].endswith(")") for row in well_formed))
        self.assertNotIn("(", MALFORMED)
        self.assertTrue(MALFORMED.endswith(")"))

    def test_every_row_is_single_occurrence_and_fail_closed(self):
        rows = self.rows(AUDIT)
        self.assertTrue(all(row["source_occurrence_count"] == "1" for row in rows))
        self.assertTrue(all(row["admission_status"] == "UNRESOLVED_USAGE_LOCATION_REQUIRED" for row in rows))

    def test_representative_source_native_tokens_are_preserved_verbatim(self):
        tokens = {row["source_token"] for row in self.rows(AUDIT)}
        for token in {
            "Abaújdevecser (Encs)",
            "Diósgyőr (Miskolc)",
            "Ipolyszög (Balassagyarmat)",
            "Kékestető (Gyöngyös)",
            "Parádfürdő (Parád)",
            "Somoskő (Salgótarján)",
            "Tiszaszederkény (Tiszaújváros)",
            "Zsunypuszta (Nagylóc)",
            MALFORMED,
        }:
            self.assertIn(token, tokens)

    def test_manifest_freezes_complete_residual_accounting_without_promotion(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("MVM_EMASZ", row["operator_id"])
        self.assertEqual(MVM, row["source_id"])
        self.assertEqual("749", row["current_m1_source_token_count"])
        self.assertEqual("99", row["p47_parent_context_residual_count"])
        self.assertEqual("98", row["well_formed_parent_context_count"])
        self.assertEqual("1", row["malformed_parent_context_count"])
        self.assertEqual(EXPECTED_DIGEST, row["audit_sha256"])
        self.assertEqual("0", row["materialized_membership_delta"])
        self.assertEqual("650", row["materialized_whole_settlement_count"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", row["operator_extraction_status"])
        self.assertEqual("CLASSIFICATION_ONLY_NO_MEMBERSHIP_PROMOTION", row["admission_effect"])
        self.assertEqual("UNRESOLVED_USAGE_LOCATION_REQUIRED", row["usage_location_status"])

    def test_p56_changes_no_emasz_membership_population(self):
        historical = [row for row in self.rows(HISTORICAL) if row["operator_id"] == "MVM_EMASZ"]
        p47 = self.rows(P47)
        self.assertEqual(45, len(historical))
        self.assertEqual(605, len(p47))
        self.assertEqual(650, len(historical) + len(p47))

    def test_p52_spelling_edges_remain_separate_and_unresolved(self):
        rows = self.rows(P52)
        self.assertEqual(2, len(rows))
        self.assertEqual({"Fóny", "Hídvégardó"}, {row["source_token"] for row in rows})
        self.assertTrue(all(row["admission_status"].startswith("UNRESOLVED_") for row in rows))

    def test_operator_state_remains_partial(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        row = by_operator["MVM_EMASZ"]
        self.assertEqual(MVM, row["source_id"])
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", row["extraction_status"])
        self.assertNotEqual("COMPLETE_OPERATOR_M1_MATERIALIZED", row["extraction_status"])

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])

    def test_source_pack_preserves_fail_closed_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "99 unique source forms / 99 source occurrences",
            "98 PARENTHESIZED_PARENT_CONTEXT",
            "1 MALFORMED_PARENT_CONTEXT_TOKEN",
            "PARENTHESIZED PARENT CONTEXT != WHOLE-PARENT MEMBERSHIP",
            "SOURCE-NATIVE PARENT CONTEXT != KSH IDENTITY AUTHORITY",
            "SOURCE-FORM PRESENCE != USAGE-LOCATION RESOLUTION",
            "MALFORMED SOURCE TOKEN != AUTHORITY TO REPAIR OR NORMALIZE",
            "SOURCE-GRAIN CLASSIFICATION != MEMBERSHIP AUTHORITY",
            "COMPLETE RESIDUAL SOURCE-FORM CLASSIFICATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
