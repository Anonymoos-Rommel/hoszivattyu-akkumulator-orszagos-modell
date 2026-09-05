import csv
from collections import Counter
from pathlib import Path
import unittest

from modules.B10.effective_service_area_projection import (
    PARTIAL_SETTLEMENT,
    USAGE_LOCATION_MEMBERSHIP_PROVEN,
    WHOLE_SETTLEMENT,
    build_effective_service_area_projection,
)
from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "registry/dso_service_area_membership_p63_effective_projection_summary.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P63_B10_EFFECTIVE_PARTIAL_SERVICE_AREA_PROJECTION.md"

EXPECTED_WHOLE_COUNTS = {
    "ELMU": 127,
    "EON_DDASZ": 819,
    "EON_EDASZ": 814,
    "MVM_DEMASZ": 256,
    "MVM_EMASZ": 650,
    "OPUS_TITASZ": 386,
}

SUPERSEDED = {
    ("Csabacsűd", "OPUS_TITASZ"),
    ("Dabas", "ELMU"),
    ("Dévaványa", "OPUS_TITASZ"),
    ("Gyomaendrőd", "OPUS_TITASZ"),
    ("Kunszentmárton", "OPUS_TITASZ"),
    ("Mohács", "EON_DDASZ"),
    ("Péteri", "ELMU"),
    ("Szeghalom", "OPUS_TITASZ"),
    ("Tiszakécske", "OPUS_TITASZ"),
    ("Tiszasas", "OPUS_TITASZ"),
    ("Tiszaug", "OPUS_TITASZ"),
    ("Újhartyán", "ELMU"),
    ("Zsadány", "OPUS_TITASZ"),
}


class B10P63EffectivePartialServiceAreaProjectionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def projection(self):
        return build_effective_service_area_projection(ROOT)

    def test_projection_has_exact_3052_whole_plus_one_usage_location(self):
        rows = self.projection()
        whole = [row for row in rows if row.coverage_scope == WHOLE_SETTLEMENT]
        partial = [row for row in rows if row.coverage_scope == PARTIAL_SETTLEMENT]
        self.assertEqual(3052, len(whole))
        self.assertEqual(1, len(partial))
        self.assertEqual(3053, len(rows))
        self.assertEqual(EXPECTED_WHOLE_COUNTS, Counter(row.operator_id for row in whole))

    def test_exact_p62_supersessions_are_absent_from_effective_whole_surface(self):
        whole_pairs = {
            (row.settlement_name, row.operator_id)
            for row in self.projection()
            if row.coverage_scope == WHOLE_SETTLEMENT
        }
        self.assertTrue(SUPERSEDED.isdisjoint(whole_pairs))

    def test_whole_projection_is_globally_unique_by_ksh_code(self):
        whole = [row for row in self.projection() if row.coverage_scope == WHOLE_SETTLEMENT]
        codes = [row.ksh_settlement_code for row in whole]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_tass_usage_location_is_preserved_without_whole_or_complement_inference(self):
        rows = self.projection()
        tass = [row for row in rows if row.settlement_name == "Tass"]
        usage = [row for row in tass if row.usage_location_id == "ELMU:TASS:UDULOTERULET"]
        self.assertEqual(1, len(usage))
        self.assertEqual("ELMU", usage[0].operator_id)
        self.assertEqual(PARTIAL_SETTLEMENT, usage[0].coverage_scope)
        self.assertEqual(USAGE_LOCATION_MEMBERSHIP_PROVEN, usage[0].status)
        self.assertFalse(any(row.coverage_scope == WHOLE_SETTLEMENT for row in tass))

    def test_representative_effective_whole_membership_is_runtime_usable(self):
        matches = [
            row
            for row in self.projection()
            if row.ksh_settlement_code == "26684"
            and row.settlement_name == "Kecskemét"
            and row.operator_id == "MVM_DEMASZ"
        ]
        self.assertEqual(1, len(matches))
        self.assertEqual("MVM_DEMASZ:SERVICE_AREA", matches[0].service_area_id)
        self.assertEqual(WHOLE_SETTLEMENT, matches[0].coverage_scope)

    def test_compact_completion_exception_source_lineages_are_preserved(self):
        by_key = {
            (row.ksh_settlement_code, row.settlement_name): row
            for row in self.projection()
        }
        for key in (("30456", "Miskolc"), ("33233", "Gödre"), ("29221", "Jánossomorja")):
            row = by_key[key]
            self.assertIn("SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS", row.source_ids)
            self.assertNotIn("SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026", row.source_ids)

    def test_summary_matches_executable_projection(self):
        projection = self.projection()
        whole_counts = Counter(row.operator_id for row in projection if row.coverage_scope == WHOLE_SETTLEMENT)
        usage_counts = Counter(row.operator_id for row in projection if row.coverage_scope == PARTIAL_SETTLEMENT)
        summary = {row["operator_id"]: row for row in self.rows(SUMMARY)}
        for operator, count in EXPECTED_WHOLE_COUNTS.items():
            self.assertEqual(count, int(summary[operator]["effective_whole_count"]))
            self.assertEqual(usage_counts[operator], int(summary[operator]["effective_usage_location_count"]))
            self.assertEqual(
                whole_counts[operator] + usage_counts[operator],
                int(summary[operator]["effective_record_count"]),
            )
        national = summary["NATIONAL_RESOLVED_ONLY"]
        self.assertEqual(3052, int(national["effective_whole_count"]))
        self.assertEqual(1, int(national["effective_usage_location_count"]))
        self.assertEqual(3053, int(national["effective_record_count"]))

    def test_projection_does_not_promote_service_area_to_exact_node(self):
        for row in self.projection():
            self.assertFalse(hasattr(row, "node_id"))
            self.assertFalse(hasattr(row, "grid_headroom_mw"))
            self.assertFalse(hasattr(row, "hosting_capacity_mw"))

    def test_document_freezes_batch_access_and_completeness_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "BATCH AUTHORITY IDENTIFIED != BATCH AUTHORITY MATERIALIZED",
            "AUTHENTICATED MAP ACCESS != REPRODUCIBLE PUBLIC REPOSITORY EVIDENCE",
            "RESOLVED-ONLY EFFECTIVE PROJECTION != COMPLETE NATIONAL KSH-TO-DSO CROSSWALK",
            "USAGE-LOCATION MEMBERSHIP != COMPLEMENT BOUNDARY",
            "DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE",
        ):
            self.assertIn(marker, text)

    def test_canonical_complete_crosswalk_and_global_blockers_remain_fail_closed(self):
        lines = CANONICAL.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        assessment = current_b10_closure_assessment()
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", assessment.blocking_refs)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", assessment.blocking_refs)
        self.assertIn("REGIONAL_READINESS_HEADER_ONLY", assessment.blocking_refs)
        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])


if __name__ == "__main__":
    unittest.main()
