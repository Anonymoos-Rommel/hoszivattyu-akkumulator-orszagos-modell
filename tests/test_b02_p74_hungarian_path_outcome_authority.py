import csv
import unittest
from pathlib import Path

from modules.B02.hungarian_path_outcome_authority import (
    EKR_CAST_IRON_REPLACEMENT_BONUS_SHARE,
    EKR_HEAT_REFLECTOR_BONUS_SHARE,
    EKR_MIN_SUPPLY_TEMP_REDUCTION_C,
    KEHOP_EMITTER_PACKAGE_TOTAL_MAX_HUF,
    QUALIFIED_SCOPE_LIMITED_TECHNICAL_AUTHORITY,
    QUALIFIED_TRANSITION_DERIVED_RESPONSE_METHOD,
    assess_awhp_physical_response_authority,
    assess_ekr_use,
    assess_kehop_path_cost_use,
    assess_p74_path_outcome_completeness,
    build_ekr_reference,
    build_nonreuse_kehop_cost_upper_bound,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p74_hungarian_path_outcome_authority.csv"
SOURCES = ROOT / "registry" / "sources.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P74_HUNGARIAN_PATH_OUTCOME_AUTHORITY.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P74HungarianPathOutcomeAuthorityTests(unittest.TestCase):
    def test_ekr_reference_preserves_source_native_values(self):
        ref = build_ekr_reference()
        self.assertEqual(ref.base_saving_shares, (0.10, 0.06, 0.04))
        self.assertEqual(
            ref.cast_iron_replacement_bonus_share,
            EKR_CAST_IRON_REPLACEMENT_BONUS_SHARE,
        )
        self.assertEqual(ref.cast_iron_replacement_bonus_share, 0.03)
        self.assertEqual(ref.min_supply_temp_reduction_c, EKR_MIN_SUPPLY_TEMP_REDUCTION_C)
        self.assertEqual(ref.min_supply_temp_reduction_c, 7.0)
        self.assertEqual(ref.heat_reflector_bonus_share, EKR_HEAT_REFLECTOR_BONUS_SHARE)
        self.assertEqual(ref.heat_reflector_bonus_share, 0.01)
        self.assertTrue(ref.excludes_new_energy_carrier)

    def test_ekr_is_scope_limited_technical_authority(self):
        ok = assess_ekr_use(
            requested_use="TECHNICAL_ACTION_REFERENCE",
            building_scope="OWN_CENTRAL_HEAT_MULTI_DWELLING",
            new_energy_carrier=True,
        )
        self.assertEqual(ok.status, QUALIFIED_SCOPE_LIMITED_TECHNICAL_AUTHORITY)

        family = assess_ekr_use(
            requested_use="TECHNICAL_ACTION_REFERENCE",
            building_scope="FAMILY_HOUSE",
            new_energy_carrier=True,
        )
        self.assertEqual(family.status, "Q")
        self.assertIn("EKR_211_BUILDING_SCOPE_NOT_COVERED", family.blockers)

    def test_ekr_savings_cannot_be_transferred_to_awhp(self):
        blocked = assess_ekr_use(
            requested_use="AWHP_ENERGY_SAVING_OUTCOME",
            building_scope="OWN_CENTRAL_HEAT_MULTI_DWELLING",
            new_energy_carrier=True,
        )
        self.assertEqual(blocked.status, "Q")
        self.assertIn("EKR_211_NEW_ENERGY_CARRIER_EXCLUSION", blocked.blockers)

    def test_ekr_7c_condition_is_not_awhp_design_temperature(self):
        blocked = assess_ekr_use(
            requested_use="AWHP_DESIGN_TEMPERATURE",
            building_scope="OWN_CENTRAL_HEAT_MULTI_DWELLING",
            new_energy_carrier=True,
        )
        self.assertEqual(blocked.status, "Q")
        self.assertIn(
            "EKR_7C_REDUCTION_IS_MEASURE_CONDITION_NOT_AWHP_DESIGN_SETPOINT",
            blocked.blockers,
        )

    def test_kehop_nonreuse_package_upper_bound_is_exact(self):
        bound = build_nonreuse_kehop_cost_upper_bound()
        self.assertEqual(bound.path, "NEW_OR_REPLACE_DISTRIBUTION_REQUIRED")
        self.assertEqual(bound.upper_huf_per_set, KEHOP_EMITTER_PACKAGE_TOTAL_MAX_HUF)
        self.assertEqual(bound.upper_huf_per_set, 3_556_000.0)
        self.assertEqual(bound.evidence_status, "QUALIFIED_OFFICIAL_UPPER_BOUND")
        self.assertEqual(bound.scope_status, "KEHOP_ELIGIBLE_PROJECT_SET_ONLY")

    def test_kehop_upper_bound_does_not_become_national_or_market_cost(self):
        national = assess_kehop_path_cost_use(
            requested_use="NATIONAL_NONREUSE_POPULATION_COST_UPPER_BOUND"
        )
        self.assertEqual(national.status, "Q")
        self.assertIn(
            "KEHOP_PROJECT_SET_TO_NATIONAL_NONREUSE_SCOPE_CROSSWALK_REQUIRED",
            national.blockers,
        )

        market = assess_kehop_path_cost_use(requested_use="EXPECTED_REALIZED_COST")
        self.assertEqual(market.status, "Q")
        self.assertIn("OFFICIAL_MAXIMUM_IS_NOT_MARKET_DISTRIBUTION", market.blockers)

    def test_existing_b06_b05_chain_is_the_physical_response_method_authority(self):
        method = assess_awhp_physical_response_authority(
            requested_use="RECORD_OR_PROJECT_PHYSICAL_RESPONSE_METHOD"
        )
        self.assertEqual(method.status, QUALIFIED_TRANSITION_DERIVED_RESPONSE_METHOD)
        self.assertEqual(method.blockers, ())

        national = assess_awhp_physical_response_authority(
            requested_use="NATIONAL_PROGRAMME_RESPONSE"
        )
        self.assertEqual(national.status, "Q")
        self.assertIn(
            "NATIONAL_TRANSITION_RESPONSE_MATERIALIZATION_BY_ARCHETYPE_REQUIRED",
            national.blockers,
        )
        self.assertIn("B05_PRODUCT_OPERATING_POINT_COVERAGE_REQUIRED", national.blockers)

        percent = assess_awhp_physical_response_authority(
            requested_use="NATIONAL_PERCENT_SAVING_DEFAULT"
        )
        self.assertEqual(percent.status, "Q")
        self.assertEqual(
            percent.blockers,
            ("GENERIC_AWHP_PERCENT_RESPONSE_IS_NOT_CANONICAL_ESTIMAND",),
        )

    def test_p74_residual_is_claim_specific(self):
        capex = assess_p74_path_outcome_completeness("CAPEX_HUF_PER_SET")
        self.assertEqual(capex.status, "Q")
        self.assertIn("REUSE_PATH_CAPEX_BOUND_REQUIRED", capex.blockers)
        self.assertIn("NONREUSE_KEHOP_SCOPE_CROSSWALK_REQUIRED", capex.blockers)

        percent = assess_p74_path_outcome_completeness("AWHP_ENERGY_SAVING_SHARE")
        self.assertEqual(percent.status, "Q")
        self.assertEqual(
            percent.blockers,
            ("GENERIC_AWHP_PERCENT_RESPONSE_IS_NOT_CANONICAL_ESTIMAND",),
        )

        response = assess_p74_path_outcome_completeness("AWHP_PHYSICAL_RESPONSE")
        self.assertEqual(response.status, "Q")
        self.assertIn(
            "NATIONAL_TRANSITION_RESPONSE_MATERIALIZATION_BY_ARCHETYPE_REQUIRED",
            response.blockers,
        )
        self.assertIn("B05_PRODUCT_OPERATING_POINT_COVERAGE_REQUIRED", response.blockers)

    def test_registry_encodes_no_false_transfer(self):
        reg = rows(REG, "item_id")
        self.assertEqual(reg["B02-P74-A06"]["status"], "TRANSFER_PROHIBITED")
        self.assertEqual(
            reg["B02-P74-A07"]["upper_bound"],
            "3556000",
        )
        self.assertEqual(
            reg["B02-P74-A08"]["status"],
            "PARTIAL_RESOLVED_SCOPE_LIMITED",
        )
        self.assertIn(
            "NATIONAL_TRANSITION_RESPONSE_MATERIALIZATION_BY_ARCHETYPE_REQUIRED",
            reg["B02-P74-A10"]["residual_gap"],
        )

    def test_sources_include_current_ekr_and_official_mfb_scope_page(self):
        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-HU-EKR-211-SECONDARY-HEATING-2026", sources)
        self.assertIn("SRC-B02-HU-KEHOP-417-PROGRAMME-2026", sources)
        self.assertEqual(
            sources["SRC-B02-HU-EKR-211-SECONDARY-HEATING-2026"]["evidence_status"],
            "POL",
        )

    def test_q_b02_004_narrows_but_stays_open(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P74", q["notes"])
        self.assertIn(
            "NATIONAL_TRANSITION_RESPONSE_MATERIALIZATION_BY_ARCHETYPE_REQUIRED",
            q["notes"],
        )
        self.assertIn("NONREUSE_KEHOP_SCOPE_CROSSWALK_REQUIRED", q["notes"])

    def test_readiness_stays_fixed(self):
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P74", b02["gate_note"])

    def test_source_pack_preserves_critical_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "EKR SOURCE-NATIVE SAVING % != AWHP PROGRAMME SAVING %",
            "EKR 7 C CONDITION != AWHP DESIGN FLOW TEMPERATURE",
            "OFFICIAL MAXIMUM != MARKET-TYPICAL COST",
            "KEHOP ELIGIBLE PROJECT SET != ALL NATIONAL NONREUSE DWELLINGS",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
