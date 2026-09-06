import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p36_hem_2104_public_aggregate_semantic_drift.csv"
LINKAGE = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P36_HEM_2104_PUBLIC_AGGREGATE_SEMANTIC_DRIFT.md"


class B02P36Hem2104PublicAggregateSemanticDriftTests(unittest.TestCase):
    def _findings(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            return {row["finding_id"]: row for row in csv.DictReader(handle)}

    def test_exact_reference_only_policy_is_preserved(self):
        findings = self._findings()
        self.assertEqual(len(findings), 6)
        for row in findings.values():
            self.assertEqual(row["repo_binary_policy"], "REFERENCE_ONLY_NO_BINARY")
            self.assertTrue(row["external_url"].startswith("https://"))
            self.assertTrue(row["exact_locator"].strip())

    def test_public_hem_surface_excludes_measure_and_device_fields(self):
        row = self._findings()["B02-P36-F01"]
        self.assertEqual(row["evidence_role"], "PUBLIC_HEM_FIELD_BOUNDARY")
        self.assertEqual(row["measure_2104_visible"], "NO")
        self.assertEqual(row["preinvestment_device_visible"], "NO")
        self.assertEqual(row["blockers"], "NO_PUBLIC_MEASURE_OR_DEVICE_FIELDS")

    def test_internal_intake_is_richer_but_not_public(self):
        row = self._findings()["B02-P36-F02"]
        self.assertEqual(row["measure_2104_visible"], "YES")
        self.assertEqual(row["preinvestment_device_visible"], "YES")
        self.assertEqual(row["gas_convector_validation_admissible"], "NO")
        self.assertEqual(row["blockers"], "INTERNAL_FIELDS_NOT_PUBLIC")

    def test_current_public_total_is_not_device_denominator(self):
        row = self._findings()["B02-P36-F03"]
        self.assertIn("13524", row["source_native_fact"])
        self.assertIn("24901609.7 GJ", row["source_native_fact"])
        self.assertEqual(row["current_status"], "QUALIFIED_TOTAL_ONLY")
        self.assertEqual(row["blockers"], "NO_2104_OR_DEVICE_DENOMINATOR")

    def test_historical_2104_aggregate_is_pinned(self):
        row = self._findings()["B02-P36-F04"]
        self.assertIn("30446 GJ", row["source_native_fact"])
        self.assertIn("2 projects", row["source_native_fact"])
        self.assertEqual(row["evidence_role"], "HISTORICAL_MEASURE_LEVEL_AGGREGATE")
        self.assertEqual(row["gas_convector_validation_admissible"], "NO")

    def test_historical_2104_scope_is_gas_boiler_only(self):
        row = self._findings()["B02-P36-F05"]
        self.assertIn("traditional or condensing gas boiler", row["source_native_fact"])
        self.assertEqual(row["current_status"], "QUALIFIED_HISTORICAL_SCOPE")
        self.assertEqual(row["blockers"], "GASCONVECTOR_NOT_ELIGIBLE_IN_SOURCE_SNAPSHOT")

    def test_current_2104_scope_explicitly_includes_gas_convector(self):
        row = self._findings()["B02-P36-F06"]
        self.assertIn("gázkonvektor", row["source_native_fact"])
        self.assertEqual(row["current_status"], "QUALIFIED_CURRENT_SCOPE")
        self.assertEqual(row["blockers"], "NO_PUBLIC_DEVICE_SPLIT")

    def test_p30_validation_blockers_remain_open(self):
        with LINKAGE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        row = rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P30"]
        self.assertEqual(row["approval_status"], "NOT_APPROVED")
        self.assertEqual(row["validation_metrics"], "no")
        self.assertEqual(row["independence_assumption_controlled"], "no")
        self.assertEqual(row["output_evidence_status"], "ASS")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(
            row["blockers"],
            "NO_JOSEPH_APPROVAL;NO_VALIDATION_METRICS;UNCONTROLLED_INDEPENDENCE_ASSUMPTION",
        )

    def test_source_pack_locks_semantic_drift_and_fail_closed_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        required = (
            "SAME MEASURE CODE 2104 != SAME PRE-INVESTMENT DEVICE ELIGIBILITY OVER TIME",
            "PUBLIC HEM IDENTIFIER RECORD != PUBLIC MEASURE-SPECIFIC TECHNICAL RECORD",
            "INTERNAL HEM MEASURE DATA > PUBLIC HEM FIELD SET",
            "TOTAL HEM COUNT != 2104 COUNT != GAS-CONVECTOR COUNT",
            "2022 2104 AGGREGATE = HISTORICAL GAS-BOILER-SCOPE AGGREGATE",
            "PUBLIC DEVICE-SPECIFIC 2104 VALIDATION METRIC = NOT AVAILABLE",
            "B02 readiness remains `55%`",
            "REFERENCED SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY",
        )
        for marker in required:
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
