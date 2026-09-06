import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry" / "b02_p31_remaining_technical_gap_audit.csv"
LINKAGE = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P31_NEGATIVE_SPACE_TECHNICAL_GAP_AUDIT.md"

EXPECTED_GAPS = {
    "B02-P31-G01": "MISSING_EVIDENCE",
    "B02-P31-G02": "EXCLUDED_AS_INDEPENDENT_VALIDATION",
    "B02-P31-G03": "EXCLUDED_AS_EMITTER_CONDITIONAL_CONTROL",
    "B02-P31-G04": "MISSING_EXTERNAL_DATA",
    "B02-P31-G05": "FALSIFIED_DOMAIN",
    "B02-P31-G06": "EXCLUDED_AS_PUBLIC_BULK_AUTHORITY",
    "B02-P31-G07": "PENDING_EXTERNAL_RESPONSE",
    "B02-P31-G08": "EXCLUDED_AS_NATIONAL_AUTHORITY",
    "B02-P31-G09": "INTERNAL_TAXONOMY_GAP",
    "B02-P31-G10": "INTERNAL_APPLICABILITY_GAP",
    "B02-P31-G11": "INTERNAL_GATE_SEMANTIC_GAP",
    "B02-P31-G12": "EXCLUDED_FROM_STOCK_AUTHORITY",
    "B02-P31-G13": "PROHIBITED_INFERENCE",
    "B02-P31-G14": "MISSING_STOCK_AUTHORITY",
    "B02-P31-G15": "MISSING_STOCK_AUTHORITY_PLUS_CONTRACT_GAP",
}


class B02P31NegativeSpaceGapAuditTests(unittest.TestCase):
    def _audit_rows(self) -> dict[str, dict[str, str]]:
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            return {row["gap_id"]: row for row in csv.DictReader(handle)}

    def test_audit_register_is_complete_and_closes_nothing(self):
        keyed = self._audit_rows()
        self.assertEqual(len(keyed), len(EXPECTED_GAPS))
        self.assertEqual(set(keyed), set(EXPECTED_GAPS))

        for gap_id, classification in EXPECTED_GAPS.items():
            self.assertEqual(keyed[gap_id]["classification"], classification)
            self.assertEqual(keyed[gap_id]["closure_effect"], "NONE")

    def test_p30_linkage_remains_unclosed(self):
        with LINKAGE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}

        row = rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P30"]
        self.assertEqual(row["approval_status"], "NOT_APPROVED")
        self.assertEqual(row["validation_metrics"], "no")
        self.assertEqual(row["marginal_reconciliation"], "yes")
        self.assertEqual(row["uncertainty_method"], "yes")
        self.assertEqual(row["uncertainty_propagation"], "yes")
        self.assertEqual(row["independence_assumption_controlled"], "no")
        self.assertEqual(row["output_evidence_status"], "ASS")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(
            row["blockers"],
            "NO_JOSEPH_APPROVAL;NO_VALIDATION_METRICS;UNCONTROLLED_INDEPENDENCE_ASSUMPTION",
        )

    def test_p31_recorded_gas_convector_taxonomy_gap(self):
        row = self._audit_rows()["B02-P31-G09"]
        self.assertEqual(row["classification"], "INTERNAL_TAXONOMY_GAP")
        self.assertIn("cannot encode GAS_CONVECTOR", row["current_fact"])
        self.assertEqual(row["closure_effect"], "NONE")

    def test_p31_recorded_not_applicable_temperature_gap(self):
        row = self._audit_rows()["B02-P31-G10"]
        self.assertEqual(row["classification"], "INTERNAL_APPLICABILITY_GAP")
        self.assertIn("no NOT_APPLICABLE temperature state", row["current_fact"])
        self.assertEqual(row["closure_effect"], "NONE")

    def test_p31_recorded_unconditional_gate_gap(self):
        row = self._audit_rows()["B02-P31-G11"]
        self.assertEqual(row["classification"], "INTERNAL_GATE_SEMANTIC_GAP")
        self.assertIn("requires design-temperature evidence unconditionally", row["current_fact"])
        self.assertEqual(row["closure_effect"], "NONE")

    def test_source_pack_preserves_negative_space_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        required = (
            "P31 closes zero blockers",
            "EXPLICIT GAS CONVECTOR != GENERIC OTHER",
            "UNKNOWN TEMPERATURE != NON-HYDRONIC NOT-APPLICABLE TEMPERATURE",
            "HYDRONIC CURRENT SYSTEM -> DESIGN/CALCULATION PAIR REQUIRED",
            "NON-HYDRONIC CURRENT SYSTEM -> HYDRONIC PAIR NOT APPLICABLE",
            "B02 readiness remains `55%`",
        )
        for marker in required:
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
