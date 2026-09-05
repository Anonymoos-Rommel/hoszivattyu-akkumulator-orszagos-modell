import csv
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    CONTRACTED,
    Q,
    QUALIFIED,
    DesignTemperatureAuthorityCandidate,
    HeatEmitterAuthorityCandidate,
    StockArchetypeInputs,
    assess_direct_design_temperature_authority,
    assess_direct_heat_emitter_authority,
    assess_technical_readiness_enrichment,
)


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_MAPPING = ROOT / "registry" / "oeny_public_field_mapping.csv"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
P18_DOC = ROOT / "docs" / "source_packs" / "B02_P18_TECHNICAL_READINESS_DIRECT_AUTHORITY.md"
REQUEST_DRAFT = ROOT / "docs" / "data_requests" / "P1F_OENY_DATA_REQUEST_DRAFT.md"


def qualified_stock() -> StockArchetypeInputs:
    return StockArchetypeInputs(
        schema_status=CONTRACTED,
        wbl_joint_materialized_complete=True,
        building_type_link_status="OBS",
        primary_energy_link_status="DER",
        building_type_direct_authority_status=QUALIFIED,
        primary_energy_direct_authority_status=QUALIFIED,
    )


class B02P18TechnicalReadinessDirectAuthorityTests(unittest.TestCase):
    def test_complete_current_emitter_assignment_can_qualify(self):
        candidate = HeatEmitterAuthorityCandidate(
            source_id="TEST-EMITTER",
            reference_year=2022,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            evidence_status="OBS",
            current_state_explicit=True,
            emitter_evidence_type="TABLE_EXPLICIT",
            evidence_locator_present=True,
            publishes_complete_assignment=True,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        decision = assess_direct_heat_emitter_authority(candidate)
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.reasons, ())

    def test_proposed_or_unlocated_emitter_evidence_is_not_current_authority(self):
        candidate = HeatEmitterAuthorityCandidate(
            source_id="TEST-PROPOSED-EMITTER",
            reference_year=2026,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            evidence_status="OBS",
            current_state_explicit=False,
            emitter_evidence_type="NONE",
            evidence_locator_present=False,
            publishes_complete_assignment=True,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        decision = assess_direct_heat_emitter_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertIn("CURRENT_EMITTER_STATE_NOT_EXPLICIT", decision.reasons)
        self.assertIn("EMITTER_EVIDENCE_NOT_EXPLICIT", decision.reasons)
        self.assertIn("NO_EMITTER_EVIDENCE_LOCATOR", decision.reasons)

    def test_oeny_public_emitter_surface_cannot_qualify(self):
        candidate = HeatEmitterAuthorityCandidate(
            source_id="SRC-B02-OENY-PUBLIC-CERT-BASICS-2026",
            reference_year=2026,
            source_universe="PUBLIC_CERTIFICATE_SEARCH",
            source_grain="CERTIFICATE_OR_DOCUMENT",
            evidence_status="Q",
            current_state_explicit=False,
            emitter_evidence_type="NONE",
            evidence_locator_present=False,
            publishes_complete_assignment=False,
            wbl_compatible_join_key=False,
            reproducible_repository_binding=False,
        )
        decision = assess_direct_heat_emitter_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertIn("NOT_OCCUPIED_DWELLING_STOCK", decision.reasons)
        self.assertIn("GRAIN_NOT_DIRECT_WBL_LINK", decision.reasons)
        self.assertIn("NO_COMPLETE_HEAT_EMITTER_ASSIGNMENT", decision.reasons)
        self.assertIn("NO_WBL_COMPATIBLE_JOIN_KEY", decision.reasons)
        self.assertIn("NO_REPRODUCIBLE_REPOSITORY_BINDING", decision.reasons)

    def test_complete_design_temperature_assignment_can_qualify(self):
        candidate = DesignTemperatureAuthorityCandidate(
            source_id="TEST-DESIGN-TEMP",
            reference_year=2022,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="DWELLING_RECORD",
            evidence_status="DER",
            current_state_explicit=True,
            temperature_basis="DESIGN_EXPLICIT",
            supply_temperature_c=50.0,
            return_temperature_c=40.0,
            evidence_locator_present=True,
            publishes_complete_assignment=True,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        decision = assess_direct_design_temperature_authority(candidate)
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.reasons, ())

    def test_reference_55_45_is_not_design_temperature_authority(self):
        candidate = DesignTemperatureAuthorityCandidate(
            source_id="SRC-B02-HU-ENERGY-RULES-2023",
            reference_year=2026,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            evidence_status="DER",
            current_state_explicit=False,
            temperature_basis="REFERENCE_ASSUMPTION",
            supply_temperature_c=55.0,
            return_temperature_c=45.0,
            evidence_locator_present=True,
            publishes_complete_assignment=True,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        decision = assess_direct_design_temperature_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertIn("CURRENT_SYSTEM_STATE_NOT_EXPLICIT", decision.reasons)
        self.assertIn("TEMPERATURE_BASIS_NOT_DESIGN_AUTHORITY", decision.reasons)

    def test_operating_measurement_is_observed_but_not_design_authority(self):
        candidate = DesignTemperatureAuthorityCandidate(
            source_id="TEST-OPERATING-TEMP",
            reference_year=2026,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            evidence_status="OBS",
            current_state_explicit=True,
            temperature_basis="OPERATING_MEASURED",
            supply_temperature_c=48.0,
            return_temperature_c=38.0,
            evidence_locator_present=True,
            publishes_complete_assignment=True,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        decision = assess_direct_design_temperature_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.reasons, ("TEMPERATURE_BASIS_NOT_DESIGN_AUTHORITY",))

    def test_invalid_or_partial_temperature_pair_fails_closed(self):
        partial = DesignTemperatureAuthorityCandidate(
            source_id="TEST-PARTIAL",
            reference_year=2026,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            evidence_status="OBS",
            current_state_explicit=True,
            temperature_basis="CALCULATION_INPUT",
            supply_temperature_c=55.0,
            return_temperature_c=None,
            evidence_locator_present=True,
            publishes_complete_assignment=True,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        reversed_pair = DesignTemperatureAuthorityCandidate(
            source_id="TEST-REVERSED",
            reference_year=2026,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="WBL_FULL_JOINT",
            evidence_status="OBS",
            current_state_explicit=True,
            temperature_basis="CALCULATION_INPUT",
            supply_temperature_c=40.0,
            return_temperature_c=45.0,
            evidence_locator_present=True,
            publishes_complete_assignment=True,
            wbl_compatible_join_key=True,
            reproducible_repository_binding=True,
        )
        self.assertIn(
            "DESIGN_TEMPERATURE_PAIR_INCOMPLETE",
            assess_direct_design_temperature_authority(partial).reasons,
        )
        self.assertIn(
            "DESIGN_TEMPERATURE_PAIR_INVALID",
            assess_direct_design_temperature_authority(reversed_pair).reasons,
        )

    def test_raw_obs_der_readiness_statuses_do_not_self_authorize(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status="OBS",
            design_temperature_status="DER",
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.blockers,
            (
                "HEAT_EMITTER_DIRECT_EVIDENCE_NOT_ADMITTED",
                "DESIGN_TEMPERATURE_DIRECT_EVIDENCE_NOT_ADMITTED",
            ),
        )

    def test_separate_direct_admissions_are_required_for_technical_qualification(self):
        decision = assess_technical_readiness_enrichment(
            qualified_stock(),
            heat_emitter_status="OBS",
            design_temperature_status="DER",
            heat_emitter_direct_authority_status=QUALIFIED,
            design_temperature_direct_authority_status=QUALIFIED,
        )
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_public_oeny_mapping_keeps_emitter_and_temperature_fields_unavailable(self):
        with PUBLIC_MAPPING.open(encoding="utf-8", newline="") as handle:
            rows = {row["field_name"]: row for row in csv.DictReader(handle)}
        for field in (
            "emitter_status",
            "emitter_types",
            "emitter_evidence",
            "temperature_status",
            "supply_temperature_c",
            "return_temperature_c",
            "temperature_basis",
            "evidence_pages",
        ):
            self.assertEqual(rows[field]["availability_status"], "NOT_PUBLICLY_AVAILABLE")

    def test_questions_readiness_and_no_send_remain_fail_closed(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            questions = {row["question_id"]: row for row in csv.DictReader(handle)}
        for question_id in ("Q-B02-001", "Q-B02-002", "Q-B02-004"):
            self.assertEqual(questions[question_id]["status"], "OPEN")

        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            modules = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(modules["B02"]["readiness_percent"], "55")

        request = REQUEST_DRAFT.read_text(encoding="utf-8")
        self.assertIn("nem küldhető ki", request.lower())

    def test_document_freezes_direct_authority_boundaries(self):
        text = P18_DOC.read_text(encoding="utf-8")
        for boundary in (
            "RAW OBS/DER READINESS TOKEN != TECHNICAL DIRECT AUTHORITY",
            "DOCUMENT-LEVEL EVIDENCE != STOCK-LEVEL ASSIGNMENT",
            "OPERATING TEMPERATURE EVIDENCE != DESIGN TEMPERATURE AUTHORITY",
            "REFERENCE 55/45 C != CURRENT BUILDING DESIGN TEMPERATURE",
            "PROPOSED EMITTER != CURRENT EMITTER",
        ):
            self.assertIn(boundary, text)
        self.assertIn("55%", text)
        self.assertIn("Q-B02-004", text)


if __name__ == "__main__":
    unittest.main()
