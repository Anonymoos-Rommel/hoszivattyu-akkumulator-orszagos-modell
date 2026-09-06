import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p35_ekr_hem_gas_convector_admin_route.csv"
LINKAGE = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P35_EKR_HEM_GAS_CONVECTOR_ADMIN_ROUTE.md"


class B02P35EkrHemGasConvectorAdminRouteTests(unittest.TestCase):
    def _findings(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            return {row["finding_id"]: row for row in csv.DictReader(handle)}

    def test_exact_reference_only_policy_is_preserved(self):
        findings = self._findings()
        self.assertEqual(len(findings), 5)
        for row in findings.values():
            self.assertEqual(row["repo_binary_policy"], "REFERENCE_ONLY_NO_BINARY")
            self.assertTrue(row["external_url"].startswith("https://"))
            self.assertTrue(row["exact_locator"].strip())

    def test_current_ekr_catalogue_has_explicit_preinvestment_gas_convector(self):
        row = self._findings()["B02-P35-F01"]
        self.assertEqual(row["administrative_device_specific"], "YES")
        self.assertIn("gázkonvektor", row["source_native_fact"])
        self.assertEqual(row["current_status"], "QUALIFIED_ADMIN_ROUTE")
        self.assertEqual(row["validation_admissible"], "NO")
        self.assertEqual(row["blockers"], "PUBLIC_DEVICE_SPECIFIC_SURFACE_NOT_PROVEN")

    def test_preinvestment_device_requires_document_backing(self):
        row = self._findings()["B02-P35-F02"]
        self.assertEqual(row["evidence_role"], "DOCUMENT_BACKED_PREINVESTMENT_DEVICE_EVIDENCE")
        self.assertIn("nominal power", row["source_native_fact"])
        self.assertIn("type", row["source_native_fact"])
        self.assertEqual(row["public_device_specific_surface"], "NO")
        self.assertEqual(row["blockers"], "NO_PUBLIC_AGGREGATED_COUNT")

    def test_hem_intake_capability_is_not_promoted_to_public_surface(self):
        row = self._findings()["B02-P35-F03"]
        self.assertEqual(row["administrative_device_specific"], "YES")
        self.assertEqual(row["public_device_specific_surface"], "NO")
        self.assertEqual(row["validation_admissible"], "NO")
        self.assertEqual(row["blockers"], "DETAILS_NOT_PROVEN_PUBLIC")

    def test_registry_vs_submission_boundary_is_fail_closed(self):
        row = self._findings()["B02-P35-F04"]
        self.assertEqual(row["evidence_role"], "REGISTRY_VS_SUBMISSION_BOUNDARY")
        self.assertEqual(row["current_status"], "QUALIFIED_NEGATIVE_BOUNDARY")
        self.assertEqual(row["public_device_specific_surface"], "NO")
        self.assertEqual(row["blockers"], "PREINVESTMENT_DEVICE_NOT_IN_2A_REGISTRY_FIELDS")

    def test_publication_obligation_does_not_create_missing_device_field(self):
        row = self._findings()["B02-P35-F05"]
        self.assertEqual(row["evidence_role"], "PUBLICATION_AUTHORITY_BOUNDARY")
        self.assertEqual(row["administrative_device_specific"], "NO")
        self.assertEqual(row["public_device_specific_surface"], "NO")
        self.assertEqual(row["blockers"], "PUBLICATION_SCOPE_DOES_NOT_PROVE_DEVICE_FIELD")

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

    def test_source_pack_locks_admin_vs_public_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        required = (
            "ADMINISTRATIVE GAS-CONVECTOR EVIDENCE EXISTS != PUBLIC GAS-CONVECTOR STOCK SURFACE EXISTS",
            "EKR CATALOGUE DEVICE-SPECIFIC BASELINE = QUALIFIED",
            "HEM SUBMISSION DATA > HEM PUBLIC-REGISTRY STATUTORY FIELD SET",
            "PUBLIC HEM REGISTRY != PROVEN PUBLIC PRE-INVESTMENT GAS-CONVECTOR DATASET",
            "PUBLIC VALIDATION METRIC = NOT AVAILABLE",
            "B02 readiness remains `55%`",
            "REFERENCED SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY",
        )
        for marker in required:
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
