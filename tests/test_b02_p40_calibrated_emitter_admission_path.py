import csv
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    APPROVED_CALIBRATED_MODEL,
    CONTRACTED,
    Q,
    QUALIFIED,
    CalibratedHeatEmitterAuthorityCandidate,
    StockArchetypeInputs,
    assess_calibrated_heat_emitter_authority,
    assess_technical_readiness_enrichment,
)


ROOT = Path(__file__).resolve().parents[1]
ADMISSION = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
ARCHETYPE_GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P40_CALIBRATED_EMITTER_ADMISSION_PATH.md"


def qualified_stock() -> StockArchetypeInputs:
    return StockArchetypeInputs(
        schema_status=CONTRACTED,
        wbl_joint_materialized_complete=True,
        building_type_link_status=APPROVED_CALIBRATED_MODEL,
        primary_energy_link_status="MODELLED_LINKED",
        building_type_model_admission_status=QUALIFIED,
        primary_energy_model_admission_status=QUALIFIED,
    )


class B02P40CalibratedEmitterAdmissionPathTests(unittest.TestCase):
    def test_complete_current_stock_calibrated_emitter_assignment_can_qualify(self):
        candidate = CalibratedHeatEmitterAuthorityCandidate(
            model_id="TEST-COMPLETE-EMITTER-MODEL",
            model_admission_status=QUALIFIED,
            output_evidence_status="ASS",
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            current_state_explicit=True,
            publishes_complete_assignment=True,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        decision = assess_calibrated_heat_emitter_authority(candidate)
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.reasons, ())

    def test_p39_like_one_category_model_cannot_self_authorize_complete_emitter_stock(self):
        candidate = CalibratedHeatEmitterAuthorityCandidate(
            model_id="B02-P38-EXTERNALLY-BOUNDED-CONVECTOR-LINKAGE-CANDIDATE",
            model_admission_status=QUALIFIED,
            output_evidence_status="ASS",
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            current_state_explicit=True,
            publishes_complete_assignment=False,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        decision = assess_calibrated_heat_emitter_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.reasons, ("NO_COMPLETE_HEAT_EMITTER_ASSIGNMENT",))

    def test_generic_model_approval_without_p40_authority_fails_closed(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status=APPROVED_CALIBRATED_MODEL,
            design_temperature_status="DER",
            design_temperature_direct_authority_status=QUALIFIED,
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.blockers, ("CALIBRATED_HEAT_EMITTER_MODEL_NOT_ADMITTED",))

    def test_complete_calibrated_emitter_authority_is_symmetric_with_direct_path(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status=APPROVED_CALIBRATED_MODEL,
            heat_emitter_calibrated_authority_status=QUALIFIED,
            design_temperature_status="DER",
            design_temperature_direct_authority_status=QUALIFIED,
        )
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_p18_direct_path_remains_unchanged(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status="OBS",
            heat_emitter_direct_authority_status=QUALIFIED,
            design_temperature_status="DER",
            design_temperature_direct_authority_status=QUALIFIED,
        )
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_current_p39_model_is_qualified_but_does_not_close_technical_blocker(self):
        with ADMISSION.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        p39 = rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P39"]
        self.assertEqual(p39["current_status"], "QUALIFIED")
        self.assertEqual(p39["output_evidence_status"], "ASS")

        with ARCHETYPE_GATE.open(encoding="utf-8", newline="") as handle:
            gate = {row["claim_id"]: row for row in csv.DictReader(handle)}
        technical = gate["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(technical["current_status"], "Q")
        self.assertEqual(
            technical["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )
        self.assertIn("direct or calibrated", technical["required_inputs"].lower())

    def test_source_pack_freezes_non_promotion_and_completeness_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "P12 MODEL ADMISSION != COMPLETE HEAT-EMITTER STOCK AUTHORITY",
            "ONE-EMITTER MARGINAL != COMPLETE EMITTER ASSIGNMENT",
            "CALIBRATED ASSIGNMENT != DIRECT OBSERVATION",
            "P40 CLOSES ZERO EVIDENCE BLOCKERS",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
