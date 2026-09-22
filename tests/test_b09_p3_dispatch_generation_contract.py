import unittest

from modules.B09.dispatch_generation_contract import (
    DispatchMode,
    assess_dispatch_authority,
    assess_national_generation_baseline,
    dispatch_boundaries,
    materialization_boundary,
    regional_generation_boundary,
)


class B09P3DispatchGenerationContractTests(unittest.TestCase):
    def test_no_dispatch_baseline_is_explicit_and_qualified(self):
        result = assess_dispatch_authority(
            mode=DispatchMode.NO_DISPATCH_BASELINE,
            b07_household_storage_already_reflected_in_b08=True,
        )
        self.assertEqual(
            result.status,
            "QUALIFIED_PHYSICAL_ADEQUACY_WITHOUT_DISPATCH",
        )
        self.assertEqual(result.blockers, ())

    def test_b07_household_storage_must_not_be_reintroduced(self):
        result = assess_dispatch_authority(
            mode=DispatchMode.NO_DISPATCH_BASELINE,
            b07_household_storage_already_reflected_in_b08=False,
        )
        self.assertEqual(result.status, "Q_DISPATCH_BOUNDARY")
        self.assertIn(
            "B07_TO_B08_STORAGE_ACCOUNTING_BOUNDARY_REQUIRED",
            result.blockers,
        )

    def test_system_storage_requires_complete_separate_authority(self):
        result = assess_dispatch_authority(
            mode=DispatchMode.EXPLICIT_SYSTEM_STORAGE_SCHEDULE,
            b07_household_storage_already_reflected_in_b08=True,
            explicit_system_storage_asset_identity=True,
            explicit_charge_discharge_schedule=True,
            storage_power_energy_limits=True,
            storage_soc_state_transition=True,
            storage_efficiency_authority=True,
            schedule_evidence_authority=True,
        )
        self.assertEqual(
            result.status,
            "QUALIFIED_EXPLICIT_SYSTEM_STORAGE_DISPATCH",
        )
        self.assertEqual(result.blockers, ())
        self.assertIn(
            "NO_MARKET_VALUE_OR_OPTIMALITY_CLAIM_FROM_PHYSICAL_DISPATCH",
            result.warnings,
        )

    def test_missing_system_storage_inputs_fail_closed(self):
        result = assess_dispatch_authority(
            mode=DispatchMode.EXPLICIT_SYSTEM_STORAGE_SCHEDULE,
            b07_household_storage_already_reflected_in_b08=True,
        )
        self.assertEqual(result.status, "Q_SYSTEM_STORAGE_DISPATCH")
        self.assertIn("SYSTEM_STORAGE_ASSET_IDENTITY_REQUIRED", result.blockers)
        self.assertIn("SYSTEM_STORAGE_SOC_STATE_TRANSITION_REQUIRED", result.blockers)

    def test_regional_mapping_not_required_for_national_generation(self):
        result = assess_national_generation_baseline(
            source_is_hungarian_control_area=True,
            production_type_grain_explicit=True,
            numeric_panel_available=True,
            model_use_authorized=True,
            provenance_complete=True,
            expected_production_type_manifest_complete=True,
            regional_mapping_available=False,
        )
        self.assertEqual(
            result.status,
            "QUALIFIED_NATIONAL_CONTROL_AREA_GENERATION_BASELINE",
        )
        self.assertEqual(result.blockers, ())
        self.assertIn(
            "REGIONAL_DSO_COUNTY_GENERATION_REMAINS_SEPARATE_Q",
            result.warnings,
        )

    def test_real_numeric_national_generation_still_requires_panel_and_manifest(self):
        result = assess_national_generation_baseline(
            source_is_hungarian_control_area=True,
            production_type_grain_explicit=True,
            numeric_panel_available=False,
            model_use_authorized=False,
            provenance_complete=False,
            expected_production_type_manifest_complete=False,
            regional_mapping_available=False,
        )
        self.assertEqual(
            result.status,
            "Q_NATIONAL_NUMERIC_GENERATION_BASELINE",
        )
        self.assertIn("REAL_NUMERIC_GENERATION_PANEL_REQUIRED", result.blockers)
        self.assertIn("EXPECTED_PRODUCTION_TYPE_MANIFEST_REQUIRED", result.blockers)

    def test_boundaries_are_explicit(self):
        self.assertIn(
            "B07_HOUSEHOLD_BATTERY_ACTION_MUST_NOT_BE_DISPATCHED_AGAIN_IN_B09",
            dispatch_boundaries(),
        )
        self.assertIn(
            "NATIONAL_CONTROL_AREA_GENERATION_CANNOT_BE_DOWNSCALED_TO_DSO_OR_COUNTY_WITHOUT_AUTHORITY",
            regional_generation_boundary(),
        )
        self.assertIn(
            "PUBLIC_REPOSITORY_RAW_SNAPSHOT_REQUIRES_REUSE_PERMISSION",
            materialization_boundary(),
        )


if __name__ == "__main__":
    unittest.main()
