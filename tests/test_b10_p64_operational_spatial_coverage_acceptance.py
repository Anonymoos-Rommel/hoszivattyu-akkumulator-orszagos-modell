import csv
from pathlib import Path
import unittest

from modules.B10.effective_service_area_projection import (
    PARTIAL_SETTLEMENT,
    WHOLE_SETTLEMENT,
    build_effective_service_area_projection,
)
from modules.B10.operational_spatial_coverage_contract import (
    EVIDENCE_NOT_EXHAUSTIVE,
    OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL,
    current_operational_spatial_coverage,
    require_operational_spatial_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "registry/dso_service_area_membership_p64_operational_coverage.csv"
DOC = ROOT / "docs/source_packs/P64_B10_OPERATIONAL_SPATIAL_COVERAGE_ACCEPTANCE.md"


class B10P64OperationalSpatialCoverageAcceptanceTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_exact_national_accounting_is_frozen(self):
        coverage = current_operational_spatial_coverage()
        self.assertEqual(3155, coverage.total_settlements)
        self.assertEqual(3052, coverage.exact_whole_proven)
        self.assertEqual(1, coverage.exact_partial_only)
        self.assertEqual(103, coverage.whole_not_proven)
        self.assertEqual(102, coverage.no_effective_resolution)
        self.assertAlmostEqual(96.73534072900158, coverage.exact_whole_share_pct)
        self.assertAlmostEqual(96.76703645007923, coverage.any_effective_resolution_share_pct)
        self.assertAlmostEqual(3.264659270998415, coverage.whole_not_proven_share_pct)
        self.assertAlmostEqual(3.2329635499207607, coverage.no_effective_resolution_share_pct)

    def test_p64_counts_reconcile_to_p63_projection(self):
        projection = build_effective_service_area_projection(ROOT)
        whole_codes = {
            row.ksh_settlement_code
            for row in projection
            if row.coverage_scope == WHOLE_SETTLEMENT
        }
        partial_only_codes = {
            row.ksh_settlement_code
            for row in projection
            if row.coverage_scope == PARTIAL_SETTLEMENT
        } - whole_codes
        self.assertEqual(3052, len(whole_codes))
        self.assertEqual(1, len(partial_only_codes))
        self.assertEqual({"20525"}, partial_only_codes)

    def test_machine_readable_summary_matches_contract(self):
        rows = self.rows(SUMMARY)
        self.assertEqual(1, len(rows))
        row = rows[0]
        coverage = current_operational_spatial_coverage()
        self.assertEqual("NATIONAL", row["scope"])
        self.assertEqual(coverage.total_settlements, int(row["total_settlements"]))
        self.assertEqual(coverage.exact_whole_proven, int(row["exact_whole_proven"]))
        self.assertEqual(coverage.exact_partial_only, int(row["exact_partial_only"]))
        self.assertEqual(coverage.whole_not_proven, int(row["whole_not_proven"]))
        self.assertEqual(coverage.no_effective_resolution, int(row["no_effective_resolution"]))
        self.assertEqual(OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL, row["operational_status"])
        self.assertEqual(EVIDENCE_NOT_EXHAUSTIVE, row["evidence_completeness_status"])
        self.assertAlmostEqual(coverage.exact_whole_share_pct, float(row["exact_whole_share_pct"]), places=6)
        self.assertAlmostEqual(coverage.any_effective_resolution_share_pct, float(row["any_effective_resolution_share_pct"]), places=6)

    def test_operational_acceptance_does_not_claim_exhaustive_evidence(self):
        coverage = current_operational_spatial_coverage()
        require_operational_spatial_coverage(coverage)
        self.assertEqual(OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL, coverage.operational_status)
        self.assertEqual(EVIDENCE_NOT_EXHAUSTIVE, coverage.evidence_completeness_status)
        self.assertGreater(coverage.whole_not_proven, 0)
        self.assertGreater(coverage.no_effective_resolution, 0)

    def test_document_preserves_residual_semantics(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "OPERATIONALLY COMPLETE != 100% EVIDENCE COMPLETE",
            "3052 EXACT WHOLE MEMBERSHIPS != 3155 EXACT WHOLE MEMBERSHIPS",
            "103 WHOLE-UNPROVEN SETTLEMENTS != 103 INCORRECT SETTLEMENTS",
            "KNOWN RESIDUAL COUNT != ENUMERATED RESIDUAL IDENTITIES",
            "MISSING OR UNRESOLVED GEOGRAPHY != ZERO",
            "DISCLOSED RESIDUAL != AUTHORITY TO IMPUTE DSO MEMBERSHIP",
            "DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE",
        ):
            self.assertIn(marker, text)
        self.assertIn("P64 closes the **operational coverage acquisition loop**", text)


if __name__ == "__main__":
    unittest.main()
