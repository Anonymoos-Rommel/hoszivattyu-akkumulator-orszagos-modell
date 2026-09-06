import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p34_ksh_stadat_heating_derivation_recovery.csv"
LINKAGE = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P34_KSH_STADAT_HEATING_DERIVATION_RECOVERY.md"


class B02P34KshStadatHeatingDerivationRecoveryTests(unittest.TestCase):
    def _findings(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            return {row["finding_id"]: row for row in csv.DictReader(handle)}

    def test_exact_reference_only_policy_is_preserved(self):
        findings = self._findings()
        self.assertEqual(len(findings), 5)
        for row in findings.values():
            self.assertEqual(row["repo_binary_policy"], "REFERENCE_ONLY_NO_BINARY")
            self.assertTrue(row["external_url"].startswith("https://"))

    def test_stadat_2020_aligns_to_2021_reference_year_instrument(self):
        row = self._findings()["B02-P34-F01"]
        self.assertEqual(row["reference_period"], "2021 survey / 2020 reference year")
        self.assertIn("FUTMOD=4", row["source_native_fact"])
        self.assertIn("code 1 is Gázzal", row["source_native_fact"])
        self.assertEqual(row["gas_convector_validation_effect"], "EXCLUDES_DEVICE_SPECIFIC_INTERPRETATION")
        self.assertEqual(row["blockers"], "NO_GAS_CONVECTOR_SUBTYPE_VARIABLE")

    def test_stadat_row_is_not_promoted_to_gas_convector(self):
        row = self._findings()["B02-P34-F02"]
        self.assertEqual(row["classification"], "INDEPENDENT_HEATING_MODE_PRIMARY_FUEL_CONTROL")
        self.assertEqual(row["gas_convector_validation_effect"], "EXCLUDED_AS_GAS_CONVECTOR_VALIDATION")
        self.assertEqual(row["current_status"], "QUALIFIED")
        self.assertEqual(row["blockers"], "NO_EMITTER_SUBTYPE_IN_SOURCE_INSTRUMENT")
        self.assertIn("11.7%", row["source_native_fact"])

    def test_2022_explicit_gas_convector_taxonomy_has_no_stadat_overlap(self):
        row = self._findings()["B02-P34-F03"]
        self.assertIn("EGYEDI=1 is Gázkonvektorral", row["source_native_fact"])
        self.assertEqual(row["gas_convector_validation_effect"], "NO_OVERLAP_WITH_ARCHIVED_STADAT_2020")
        self.assertEqual(row["blockers"], "NO_OVERLAPPING_STADAT_REFERENCE_YEAR")

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

    def test_source_pack_locks_negative_semantic_result(self):
        text = DOC.read_text(encoding="utf-8")
        required = (
            "STADAT EGYEDI HELYISÉGFŰTÉS GÁZZAL != SOURCE-NATIVE GAS-CONVECTOR CATEGORY",
            "ROOM-HEATING MODE + GAS != GAS-CONVECTOR DEVICE",
            "STADAT 2020 row -> FUTMOD=4 AND EGYEDI=1",
            "temporally and instrument-semantically invalid",
            "B02 readiness remains `55%`",
            "REFERENCED SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY",
        )
        for marker in required:
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
