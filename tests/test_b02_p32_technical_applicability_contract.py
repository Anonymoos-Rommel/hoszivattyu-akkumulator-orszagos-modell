import csv
import json
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    CONTRACTED,
    NOT_APPLICABLE,
    Q,
    QUALIFIED,
    StockArchetypeInputs,
    assess_technical_readiness_enrichment,
)
from tools.validate_oeny_annotations import validate_record


ROOT = Path(__file__).resolve().parents[1]
PILOT_SCHEMA = ROOT / "schemas" / "oeny_readiness_pilot.schema.json"
ANNOTATION_SCHEMA = ROOT / "schemas" / "oeny_heat_emitter_annotation.schema.json"
GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P32_TECHNICAL_APPLICABILITY_CONTRACT_REPAIR.md"


def qualified_stock() -> StockArchetypeInputs:
    return StockArchetypeInputs(
        schema_status=CONTRACTED,
        wbl_joint_materialized_complete=True,
        building_type_link_status="APPROVED_CALIBRATED_MODEL",
        primary_energy_link_status="MODELLED_LINKED",
        building_type_model_admission_status=QUALIFIED,
        primary_energy_model_admission_status=QUALIFIED,
    )


def gas_convector_annotation() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "annotation_id": "ANN-AAAAAAAAAAAAAAAA",
        "document_id": "DOC-0123456789ABCDEF0123456789ABCDEF",
        "redacted_source_sha256": "a" * 64,
        "annotation_role": "ANNOTATOR_A",
        "annotator_id": "RATER-ALFA",
        "emitter_status": "OBS",
        "emitter_types": ["GAS_CONVECTOR"],
        "emitter_evidence": ["TEXT_EXPLICIT"],
        "temperature_status": "NOT_APPLICABLE",
        "supply_temperature_c": None,
        "return_temperature_c": None,
        "temperature_basis": "NOT_APPLICABLE",
        "page_references": [{"page": 2, "evidence_kind": "EMITTER"}],
        "review_flags": [],
        "pii_check": "PASS",
        "adjudication_of": [],
    }


class B02P32TechnicalApplicabilityContractTests(unittest.TestCase):
    def test_current_oeny_taxonomies_encode_gas_convector_and_not_applicable(self):
        pilot = json.loads(PILOT_SCHEMA.read_text(encoding="utf-8"))
        annotation = json.loads(ANNOTATION_SCHEMA.read_text(encoding="utf-8"))

        for schema in (pilot, annotation):
            self.assertIn(
                "GAS_CONVECTOR",
                schema["properties"]["emitter_types"]["items"]["enum"],
            )
            self.assertIn(
                "NOT_APPLICABLE",
                schema["properties"]["temperature_status"]["enum"],
            )
            self.assertIn(
                "NOT_APPLICABLE",
                schema["properties"]["temperature_basis"]["enum"],
            )

    def test_annotation_validator_accepts_explicit_non_hydronic_state(self):
        self.assertEqual([], validate_record(gas_convector_annotation()))

    def test_not_applicable_rejects_numeric_pair_or_wrong_basis(self):
        record = gas_convector_annotation()
        record["supply_temperature_c"] = 55
        record["return_temperature_c"] = 45
        errors = validate_record(record)
        self.assertTrue(any("NOT_APPLICABLE temperature requires" in error for error in errors))

        record = gas_convector_annotation()
        record["temperature_basis"] = "NOT_STATED"
        errors = validate_record(record)
        self.assertTrue(any("NOT_APPLICABLE temperature requires" in error for error in errors))

    def test_hydronic_default_still_requires_design_temperature_evidence(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status="OBS",
            heat_emitter_direct_authority_status=QUALIFIED,
            design_temperature_status=NOT_APPLICABLE,
        )
        self.assertEqual(decision.status, Q)
        self.assertIn("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE", decision.blockers)

    def test_non_hydronic_exception_cannot_self_authorize(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status="OBS",
            heat_emitter_direct_authority_status=QUALIFIED,
            design_temperature_status=NOT_APPLICABLE,
            design_temperature_applicability=NOT_APPLICABLE,
        )
        self.assertEqual(decision.status, Q)
        self.assertIn("DESIGN_TEMPERATURE_APPLICABILITY_NOT_ADMITTED", decision.blockers)

    def test_qualified_non_hydronic_applicability_does_not_require_hydronic_pair(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status="OBS",
            heat_emitter_direct_authority_status=QUALIFIED,
            design_temperature_status=NOT_APPLICABLE,
            design_temperature_applicability=NOT_APPLICABLE,
            design_temperature_applicability_authority_status=QUALIFIED,
        )
        self.assertEqual(decision.status, QUALIFIED)
        self.assertNotIn("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE", decision.blockers)

    def test_non_hydronic_applicability_requires_not_applicable_temperature_status(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status="OBS",
            heat_emitter_direct_authority_status=QUALIFIED,
            design_temperature_status="OBS",
            design_temperature_direct_authority_status=QUALIFIED,
            design_temperature_applicability=NOT_APPLICABLE,
            design_temperature_applicability_authority_status=QUALIFIED,
        )
        self.assertEqual(decision.status, Q)
        self.assertIn(
            "NON_HYDRONIC_TEMPERATURE_STATUS_NOT_NOT_APPLICABLE",
            decision.blockers,
        )

    def test_current_registry_readiness_remains_fail_closed(self):
        with GATE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        row = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(
            row["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )
        self.assertIn("P32 does not create emitter evidence", row["notes"])
        self.assertIn("B02 readiness remains 55%", row["notes"])

    def test_source_pack_preserves_hard_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        required = (
            "EXPLICIT GAS CONVECTOR != GENERIC OTHER",
            "NOT_APPLICABLE != Q",
            "NOT_APPLICABLE != MISSING",
            "NON-HYDRONIC APPLICABILITY STATUS != APPLICABILITY AUTHORITY",
            "P32 closes zero evidence blockers",
            "B02 readiness remains `55%`",
        )
        for marker in required:
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
