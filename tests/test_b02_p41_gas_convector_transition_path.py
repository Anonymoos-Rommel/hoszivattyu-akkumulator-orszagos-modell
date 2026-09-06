import csv
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    APPROVED_CALIBRATED_MODEL,
    CONTRACTED,
    GAS_CONVECTOR,
    NON_HYDRONIC_ROOM_HEATING,
    NOT_APPLICABLE,
    Q,
    QUALIFIED,
    REPLACE_EXISTING_DISTRIBUTION,
    StockArchetypeInputs,
    ThermalTransitionPathCandidate,
    assess_technical_readiness_enrichment,
    assess_thermal_transition_path,
)


ROOT = Path(__file__).resolve().parents[1]
ADMISSION = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
ARCHETYPE_GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P41_GAS_CONVECTOR_TRANSITION_PATH.md"


def qualified_stock() -> StockArchetypeInputs:
    return StockArchetypeInputs(
        schema_status=CONTRACTED,
        wbl_joint_materialized_complete=True,
        building_type_link_status=APPROVED_CALIBRATED_MODEL,
        primary_energy_link_status="MODELLED_LINKED",
        building_type_model_admission_status=QUALIFIED,
        primary_energy_model_admission_status=QUALIFIED,
    )


def admitted_gas_convector_candidate() -> ThermalTransitionPathCandidate:
    return ThermalTransitionPathCandidate(
        current_emitter_type=GAS_CONVECTOR,
        emitter_category_authority_status=QUALIFIED,
        current_state_explicit=True,
        current_distribution_topology=NON_HYDRONIC_ROOM_HEATING,
        design_temperature_applicability=NOT_APPLICABLE,
        transition_path=REPLACE_EXISTING_DISTRIBUTION,
        replacement_required=True,
    )


class B02P41GasConvectorTransitionPathTests(unittest.TestCase):
    def test_p39_gas_convector_replacement_path_qualifies(self):
        decision = assess_thermal_transition_path(admitted_gas_convector_candidate())
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.reasons, ())

    def test_category_name_cannot_self_authorize(self):
        candidate = admitted_gas_convector_candidate()
        candidate = ThermalTransitionPathCandidate(
            current_emitter_type=candidate.current_emitter_type,
            emitter_category_authority_status=Q,
            current_state_explicit=candidate.current_state_explicit,
            current_distribution_topology=candidate.current_distribution_topology,
            design_temperature_applicability=candidate.design_temperature_applicability,
            transition_path=candidate.transition_path,
            replacement_required=candidate.replacement_required,
        )
        decision = assess_thermal_transition_path(candidate)
        self.assertEqual(decision.status, Q)
        self.assertIn("CURRENT_EMITTER_CATEGORY_NOT_ADMITTED", decision.reasons)

    def test_p41_does_not_generalize_to_other_emitter_classes(self):
        candidate = admitted_gas_convector_candidate()
        candidate = ThermalTransitionPathCandidate(
            current_emitter_type="DIRECT_ELECTRIC",
            emitter_category_authority_status=candidate.emitter_category_authority_status,
            current_state_explicit=candidate.current_state_explicit,
            current_distribution_topology=candidate.current_distribution_topology,
            design_temperature_applicability=candidate.design_temperature_applicability,
            transition_path=candidate.transition_path,
            replacement_required=candidate.replacement_required,
        )
        decision = assess_thermal_transition_path(candidate)
        self.assertEqual(decision.status, Q)
        self.assertIn("P41_EMITTER_CLASS_NOT_ADMITTED", decision.reasons)

    def test_replacement_route_does_not_require_fictional_current_hydronic_temperature(self):
        path = assess_thermal_transition_path(admitted_gas_convector_candidate())
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status=Q,
            design_temperature_status=Q,
            thermal_transition_path=REPLACE_EXISTING_DISTRIBUTION,
            thermal_transition_path_authority_status=path.status,
        )
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_replacement_route_token_cannot_self_authorize(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status=Q,
            design_temperature_status=Q,
            thermal_transition_path=REPLACE_EXISTING_DISTRIBUTION,
            thermal_transition_path_authority_status=Q,
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.blockers, ("THERMAL_REPLACEMENT_PATH_NOT_ADMITTED",))

    def test_default_reuse_route_remains_fail_closed(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status=Q,
            design_temperature_status=Q,
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.blockers,
            ("NO_CURRENT_HEAT_EMITTER_EVIDENCE", "NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE"),
        )

    def test_registry_qualifies_only_gas_convector_subclaim_and_keeps_aggregate_open(self):
        with ADMISSION.open(encoding="utf-8", newline="") as handle:
            admission = {row["claim_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(
            admission["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P39"]["current_status"],
            "QUALIFIED",
        )

        with ARCHETYPE_GATE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["GAS_CONVECTOR_THERMAL_TRANSITION_PATH"]["current_status"], "QUALIFIED")
        self.assertEqual(rows["TECHNICAL_READINESS_ARCHETYPE"]["current_status"], "Q")
        self.assertEqual(
            rows["TECHNICAL_READINESS_ARCHETYPE"]["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )

    def test_source_pack_freezes_transition_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for boundary in (
            "CURRENT SYSTEM REUSE != CURRENT SYSTEM REPLACEMENT",
            "CURRENT GAS CONVECTOR != NEW HEAT-PUMP EMITTER DESIGN",
            "REPLACEMENT REQUIRED != REPLACEMENT READY",
            "GAS-CONVECTOR PATH QUALIFIED != FULL-STOCK THERMAL READINESS",
            "NOT_APPLICABLE CURRENT HYDRONIC TEMPERATURE != UNKNOWN HYDRONIC TEMPERATURE",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
