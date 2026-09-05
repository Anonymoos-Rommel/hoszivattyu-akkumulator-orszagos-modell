import csv
import hashlib
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
P46 = ROOT / "registry/dso_service_area_membership_crosswalk_elmu_p46.csv"
AUDIT = ROOT / "registry/dso_service_area_membership_elmu_p55_residual_authority_audit.csv"
MANIFEST = ROOT / "registry/dso_service_area_membership_elmu_p55_authority_manifest.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P55_B10_ELMU_SPECIAL_GRAIN_AUTHORITY_DECOMPOSITION.md"

EXPECTED_DIGEST = "0bbd9865dc9add46ee7991a5f205457e9b1c755c4be6180051a94d9ec253a384"
EXPECTED_TOKENS = {
    "Budapest",
    "Bankháza (Kiskunlacháza)",
    "Domonyvölgy (Domony)",
    "Tass üdülőterület",
}


class B10P55ElmuSpecialGrainAuthorityDecompositionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_four_residual_rows_are_frozen_by_digest(self):
        rows = self.rows(AUDIT)
        self.assertEqual(4, len(rows))
        canonical = "".join(
            f'{row["source_token"]}|{row["source_occurrence_count"]}|{row["residual_class"]}|{row["admission_status"]}\n'
            for row in sorted(rows, key=lambda r: r["source_token"])
        )
        self.assertEqual(EXPECTED_DIGEST, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_audit_matches_exact_p46_residual_set(self):
        rows = self.rows(AUDIT)
        self.assertEqual(EXPECTED_TOKENS, {row["source_token"] for row in rows})
        self.assertTrue(all(row["source_occurrence_count"] == "1" for row in rows))

    def test_residual_classes_form_exact_partition(self):
        rows = self.rows(AUDIT)
        classes = [row["residual_class"] for row in rows]
        self.assertEqual(1, classes.count("MULTI_DISTRICT_CITY_TOKEN"))
        self.assertEqual(2, classes.count("NAMED_SETTLEMENT_PART_WITH_PARENT_CONTEXT"))
        self.assertEqual(1, classes.count("EXPLICIT_SUBSETTLEMENT_AREA"))
        by_token = {row["source_token"]: row for row in rows}
        self.assertEqual(
            "UNRESOLVED_NO_SINGLE_CANONICAL_WHOLE_SETTLEMENT_ID",
            by_token["Budapest"]["admission_status"],
        )
        for token in ("Bankháza (Kiskunlacháza)", "Domonyvölgy (Domony)", "Tass üdülőterület"):
            self.assertEqual(
                "UNRESOLVED_USAGE_LOCATION_AUTHORITY_REQUIRED",
                by_token[token]["admission_status"],
            )

    def test_manifest_is_classification_only_and_complete(self):
        rows = self.rows(MANIFEST)
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("ELMU_P46_4_RESIDUAL_SOURCE_GRAINS", row["audit_scope"])
        self.assertEqual("SRC-B10-ELMU-M1-CANDIDATE-2025", row["current_source_id"])
        self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", row["currentness_status"])
        self.assertEqual("P46", row["upstream_surface"])
        self.assertEqual("4", row["residual_unique_tokens"])
        self.assertEqual("4", row["residual_occurrences"])
        self.assertEqual("0", row["membership_promotions"])
        self.assertEqual("130", row["operator_whole_identity_count"])
        self.assertEqual("HEADER_ONLY", row["canonical_crosswalk_status"])
        self.assertEqual("15", row["b10_readiness_percent"])
        self.assertIn("classification-only", row["notes"])
        self.assertIn("no usage-location resolution", row["notes"])

    def test_p55_adds_no_elmu_membership_rows(self):
        historical = [row for row in self.rows(TRANCHE) if row["operator_id"] == "ELMU"]
        completion = self.rows(P46)
        self.assertEqual(43, len(historical))
        self.assertEqual(87, len(completion))
        pairs = {
            (row["ksh_settlement_code"], row["settlement_name"])
            for row in historical + completion
        }
        self.assertEqual(130, len(pairs))
        names = {name for _, name in pairs}
        self.assertNotIn("Tass", names)
        self.assertNotIn("Domony", names)
        self.assertNotIn("Bankháza", names)
        self.assertTrue(EXPECTED_TOKENS.isdisjoint(names))

    def test_operator_state_remains_partial(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        row = by_operator["ELMU"]
        self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", row["extraction_status"])
        self.assertNotEqual("COMPLETE_OPERATOR_M1_MATERIALIZED", row["extraction_status"])

    def test_source_pack_preserves_fail_closed_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "4 unique source tokens / 4 source occurrences",
            "MULTI_DISTRICT_CITY_TOKEN",
            "NAMED_SETTLEMENT_PART_WITH_PARENT_CONTEXT",
            "EXPLICIT_SUBSETTLEMENT_AREA",
            "CITY-LEVEL SOURCE TOKEN != AUTHORIZED SINGLE CANONICAL WHOLE-SETTLEMENT IDENTITY",
            "NAMED SETTLEMENT PART + PARENT CONTEXT != WHOLE-PARENT MEMBERSHIP",
            "EXPLICIT SUBSETTLEMENT AREA != WHOLE-SETTLEMENT MEMBERSHIP",
            "COMPLETE RESIDUAL CLASSIFICATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK",
            "SOURCE-GRAIN CLASSIFICATION != MEMBERSHIP AUTHORITY",
            "43 historical + 87 P46 = 130 materialized whole-settlement identities",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

    def test_canonical_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)
        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
