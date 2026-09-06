import csv
import json
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    CONTRACTED,
    Q,
    QUALIFIED,
    StockArchetypeInputs,
    assess_technical_readiness_enrichment,
)


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry" / "b02_p31_remaining_technical_gap_audit.csv"
LINKAGE = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
PILOT_SCHEMA = ROOT / "schemas" / "oeny_readiness_pilot.schema.json"
ANNOTATION_SCHEMA = ROOT / "schemas" / "oeny_heat_emitter_annotation.schema.json"
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


def qualified_stock() -> StockArchetypeInputs:
    return StockArchetypeInputs(
        schema_status=CONTRACTED,
        wbl_joint_materialized_complete=True,
        building_type_link_status="APPROVED_CALIBRATED_MODEL",
        primary_energy_link_status="MODELLED_LINKED",
        building_type_model_admission_status=QUALIFIED,
        primary_energy_model_admission_status=QUALIFIED,
    )


class B02P31NegativeSpaceGapAuditTests(unittest.TestCase):
    def test_audit_register_is_complete_and_closes_nothing(self):
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), len(EXPECTED_GAPS))
        keyed = {row["gap_id"]: row for row in rows}
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

    def test_current_oeny_emitter_taxonomies_cannot_encode_gas_convector(self):
        pilot = json.loads(PILOT_SCHEMA.read_text(encoding="utf-8"))
        annotation = json.loads(ANNOTATION_SCHEMA.read_text(encoding="utf-8"))

        pilot_enum = pilot["properties"]["emitter_types"]["items"]["enum"]
        annotation_enum = annotation["properties"]["emitter_types"]["items"]["enum"]

        self.assertNotIn("GAS_CONVECTOR", pilot_enum)
        self.assertNotIn("GAS_CONVECTOR", annotation_enum)
        self.assertIn("OTHER", pilot_enum)
        self.assertIn("OTHER", annotation_enum)

    def test_current_oeny_temperature_statuses_cannot_encode_not_applicable(self):
        pilot = json.loads(PILOT_SCHEMA.read_text(encoding="utf-8"))
        annotation = json.loads(ANNOTATION_SCHEMA.read_text(encoding="utf-8"))

        pilot_enum = pilot["properties"]["temperature_status"]["enum"]
        annotation_enum = annotation["properties"]["temperature_status"]["enum"]

        self.assertNotIn("NOT_APPLICABLE", pilot_enum)
        self.assertNotIn("NOT_APPLICABLE", annotation_enum)

    def test_current_p9_gate_has_no_non_hydronic_temperature_applicability_path(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status="OBS",
            heat_emitter_direct_authority_status=QUALIFIED,
            design_temperature_status="NOT_APPLICABLE",
            design_temperature_direct_authority_status=QUALIFIED,
        )

        self.assertEqual(decision.status, Q)
        self.assertIn("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE", decision.blockers)
        self.assertNotIn("NO_CURRENT_HEAT_EMITTER_EVIDENCE", decision.blockers)

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
