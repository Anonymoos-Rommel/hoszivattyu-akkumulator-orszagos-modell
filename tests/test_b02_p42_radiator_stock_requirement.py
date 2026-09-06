import csv
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    QUALIFIED,
    Q,
    RADIATOR,
    RADIATOR_PROPOSED_TEMPERATURE_ARRANGEMENT,
    REUSE_EXISTING_RADIATOR,
    RadiatorRoomAssessment,
    RadiatorThermalArrangementCandidate,
    assess_radiator_thermal_arrangement,
)
from modules.B02.radiator_stock_requirement import (
    RadiatorProgrammeStockCandidate,
    assess_radiator_programme_stock,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p42_radiator_stock_requirement.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P42_RADIATOR_STOCK_AND_RETROFIT_REQUIREMENT.md"
B06_CONTRACT = ROOT / "modules" / "B06" / "data_contract.md"


class B02P42RadiatorStockRequirementTests(unittest.TestCase):
    def test_room_level_radiator_sizing_can_qualify_without_claiming_national_stock(self):
        candidate = RadiatorThermalArrangementCandidate(
            current_emitter_type=RADIATOR,
            emitter_category_authority_status=QUALIFIED,
            current_state_explicit=True,
            complete_heated_room_coverage=True,
            reproducible_repository_binding=True,
            room_assessments=(
                RadiatorRoomAssessment(
                    room_id="living",
                    design_heat_loss_w=1200.0,
                    design_heat_loss_evidence_status="DER",
                    emitter_output_at_target_w=1350.0,
                    emitter_output_evidence_status="DER",
                    target_supply_temperature_c=45.0,
                    target_return_temperature_c=40.0,
                    heat_pump_target_domain_status=QUALIFIED,
                    arrangement_action=REUSE_EXISTING_RADIATOR,
                    arrangement_action_evidence_status="DER",
                    evidence_refs_present=True,
                ),
            ),
        )
        decision = assess_radiator_thermal_arrangement(candidate)
        self.assertEqual(QUALIFIED, decision.status)
        self.assertEqual((), decision.reasons)
        self.assertEqual("RADIATOR_PROPOSED_TEMPERATURE_ARRANGEMENT", RADIATOR_PROPOSED_TEMPERATURE_ARRANGEMENT)

    def test_room_level_shortfall_fails_closed(self):
        candidate = RadiatorThermalArrangementCandidate(
            current_emitter_type=RADIATOR,
            emitter_category_authority_status=QUALIFIED,
            current_state_explicit=True,
            complete_heated_room_coverage=True,
            reproducible_repository_binding=True,
            room_assessments=(
                RadiatorRoomAssessment(
                    room_id="bedroom",
                    design_heat_loss_w=1000.0,
                    design_heat_loss_evidence_status="DER",
                    emitter_output_at_target_w=850.0,
                    emitter_output_evidence_status="DER",
                    target_supply_temperature_c=45.0,
                    target_return_temperature_c=40.0,
                    heat_pump_target_domain_status=QUALIFIED,
                    arrangement_action=REUSE_EXISTING_RADIATOR,
                    arrangement_action_evidence_status="DER",
                    evidence_refs_present=True,
                ),
            ),
        )
        decision = assess_radiator_thermal_arrangement(candidate)
        self.assertEqual(Q, decision.status)
        self.assertIn("ROOM_EMITTER_CAPACITY_SHORTFALL:bedroom", decision.reasons)

    def test_programme_stock_requires_quantity_type_and_retrofit_need(self):
        candidate = RadiatorProgrammeStockCandidate(
            scope_id="NATIONAL_OCCUPIED_STOCK",
            represented_dwellings=4_008_541,
            current_radiator_dwellings=None,
            current_radiator_units=None,
            stock_evidence_status="Q",
            stock_authority_status=Q,
            type_size_distribution_complete=False,
            type_size_authority_status=Q,
            retrofit_need_classification_complete=False,
            retrofit_need_authority_status=Q,
            replacement_units_required=None,
            replacement_quantity_authority_status=Q,
            uncertainty_documented=False,
            reproducible_repository_binding=False,
        )
        decision = assess_radiator_programme_stock(candidate)
        self.assertEqual(Q, decision.status)
        for reason in (
            "CURRENT_RADIATOR_DWELLING_COUNT_MISSING_OR_INVALID",
            "CURRENT_RADIATOR_UNIT_COUNT_MISSING_OR_INVALID",
            "RADIATOR_TYPE_SIZE_DISTRIBUTION_INCOMPLETE",
            "RADIATOR_RETROFIT_NEED_CLASSIFICATION_INCOMPLETE",
            "REPLACEMENT_RADIATOR_UNIT_COUNT_MISSING_OR_INVALID",
        ):
            self.assertIn(reason, decision.reasons)

    def test_complete_hypothetical_programme_stock_can_qualify(self):
        candidate = RadiatorProgrammeStockCandidate(
            scope_id="ARCHETYPE-X",
            represented_dwellings=1000,
            current_radiator_dwellings=700,
            current_radiator_units=4200,
            stock_evidence_status="ASS",
            stock_authority_status=QUALIFIED,
            type_size_distribution_complete=True,
            type_size_authority_status=QUALIFIED,
            retrofit_need_classification_complete=True,
            retrofit_need_authority_status=QUALIFIED,
            replacement_units_required=1100,
            replacement_quantity_authority_status=QUALIFIED,
            uncertainty_documented=True,
            reproducible_repository_binding=True,
        )
        decision = assess_radiator_programme_stock(candidate)
        self.assertEqual(QUALIFIED, decision.status)
        self.assertEqual((), decision.reasons)

    def test_registry_keeps_all_programme_quantity_outputs_q(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(
            {
                "RADIATOR_STOCK_DWELLING_COUNT",
                "RADIATOR_STOCK_UNIT_COUNT",
                "RADIATOR_TYPE_SIZE_DISTRIBUTION",
                "RADIATOR_REUSE_UPGRADE_REQUIREMENT",
                "RADIATOR_REPLACEMENT_QUANTITY",
            },
            set(rows),
        )
        for row in rows.values():
            self.assertEqual("Q", row["current_status"])
            self.assertEqual("NO", row["programme_use_allowed"])

    def test_b06_contract_requires_real_inventory_detail(self):
        text = B06_CONTRACT.read_text(encoding="utf-8")
        normalized = text.replace("\n", "")
        self.assertIn("gyártót, modellt/típust, méreteket", text)
        self.assertIn("inventory-darabszám", normalized)
        self.assertIn("Más modell vagy méret outputja nem skálázható feltételezéssel", text)

    def test_source_pack_freezes_programme_intent_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "GATE PASS != PROGRAMME SUFFICIENCY",
            "RADIATOR DWELLINGS != RADIATOR UNITS",
            "PRODUCT PERFORMANCE RECORD != EXISTING STOCK INVENTORY",
            "RADIATOR PRESENT != RADIATOR REUSABLE",
            "B02 RETROFIT NEED != B06 PRODUCT SELECTION != B06 CAPEX",
            "HOW MANY + WHAT TYPE + KEEP/CHANGE + HOW MANY NEW UNITS -> B06",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
