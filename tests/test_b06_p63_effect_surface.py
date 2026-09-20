import unittest

from modules.B06.effect_surface import (
    DER,
    Q,
    QUALIFIED,
    EffectSurfaceDomain,
    EffectSurfaceEvidence,
    MonthlyHeatBalanceInput,
    PhysicalState,
    assess_effect_surface,
    calculate_state_demand,
)


MONTH_T = (2.1, -0.1, 3.5, 10.9, 16.8, 20.8, 21.9, 21.0, 17.8, 8.3, 7.6, -0.1)
MONTH_H = (744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744)


def state(
    record_id="SURFACE-1",
    building_type="SINGLE_FAMILY_HOUSE",
    construction_period="1945-1979",
    state_id="EXISTING",
    direct_h=180.0,
    vent_h=55.0,
    design_h=250.0,
):
    months = tuple(
        MonthlyHeatBalanceInput(
            month=i + 1,
            hours=MONTH_H[i],
            external_temperature_c=MONTH_T[i],
            annual_external_temperature_c=10.9,
            direct_unconditioned_h_w_per_k=direct_h,
            ground_h_w_per_k=20.0,
            ventilation_h_w_per_k=vent_h,
            solar_gain_kwh=120.0,
            internal_gain_kwh=180.0,
            gain_utilization_factor=0.8,
            intermittent_operation_factor=1.0,
        )
        for i in range(12)
    )
    return PhysicalState(
        record_id=record_id,
        building_type=building_type,
        construction_period=construction_period,
        state_id=state_id,
        climate_id="HU-2023-REF",
        heated_floor_area_m2=115.6,
        heated_volume_m3=323.8,
        indoor_temperature_c=20.0,
        design_outdoor_temperature_c=-13.0,
        design_total_h_w_per_k=design_h,
        months=months,
        source_refs=("SRC-B06-HU-ENERGY-METHOD-2023",),
        evidence_status=DER,
    )


def domain():
    return EffectSurfaceDomain(
        domain_id="HU-SFH-1945-1979",
        allowed_building_types=("SINGLE_FAMILY_HOUSE",),
        allowed_construction_periods=("1945-1979",),
        allowed_before_states=("EXISTING",),
        allowed_after_states=("STANDARD_REFURBISHMENT", "AMBITIOUS_REFURBISHMENT"),
        source_refs=("SRC-B06-HU-TABULA-TYPOLOGY-2014",),
        national_prevalence_claim=False,
    )


def evidence(**changes):
    before = state()
    after = state(
        state_id="STANDARD_REFURBISHMENT",
        direct_h=95.0,
        vent_h=45.0,
        design_h=145.0,
    )
    values = dict(
        intervention_id="ENVELOPE-PACKAGE-1",
        before=before,
        after=after,
        domain=domain(),
        changed_parameter_keys=("TRANSMISSION", "VENTILATION"),
        applicability_source_refs=("SRC-B06-HU-TABULA-TYPOLOGY-2014",),
        reproducible_repository_binding=True,
    )
    values.update(changes)
    return EffectSurfaceEvidence(**values)


class B06P63EffectSurfaceTests(unittest.TestCase):
    def test_surface_recalculates_annual_and_peak_independently(self):
        decision = assess_effect_surface(evidence())
        self.assertEqual(QUALIFIED, decision.status)
        self.assertIsNotNone(decision.annual_reduction_fraction)
        self.assertIsNotNone(decision.peak_reduction_fraction)
        self.assertNotEqual(
            decision.annual_reduction_fraction,
            decision.peak_reduction_fraction,
        )

    def test_building_state_changes_surface_result(self):
        sfh = assess_effect_surface(evidence())
        before = state(
            record_id="AB-1",
            building_type="APARTMENT_BLOCK",
            construction_period="1980-1989",
            direct_h=420.0,
            vent_h=110.0,
            design_h=560.0,
        )
        after = state(
            record_id="AB-1",
            building_type="APARTMENT_BLOCK",
            construction_period="1980-1989",
            state_id="STANDARD_REFURBISHMENT",
            direct_h=300.0,
            vent_h=100.0,
            design_h=430.0,
        )
        ab_domain = EffectSurfaceDomain(
            "HU-AB-1980-1989",
            ("APARTMENT_BLOCK",),
            ("1980-1989",),
            ("EXISTING",),
            ("STANDARD_REFURBISHMENT",),
            ("SRC-B06-HU-TABULA-TYPOLOGY-2014",),
            False,
        )
        ab = assess_effect_surface(
            EffectSurfaceEvidence(
                "AB-PACKAGE",
                before,
                after,
                ab_domain,
                ("TRANSMISSION", "VENTILATION"),
                ("SRC-B06-HU-TABULA-TYPOLOGY-2014",),
                True,
            )
        )
        self.assertEqual(QUALIFIED, ab.status)
        self.assertNotEqual(
            sfh.annual_reduction_fraction,
            ab.annual_reduction_fraction,
        )
        self.assertNotEqual(
            sfh.peak_reduction_fraction,
            ab.peak_reduction_fraction,
        )

    def test_same_climate_and_service_are_mandatory(self):
        after = state(
            state_id="STANDARD_REFURBISHMENT",
            direct_h=95.0,
            vent_h=45.0,
            design_h=145.0,
        )
        altered_months = list(after.months)
        m = altered_months[0]
        altered_months[0] = MonthlyHeatBalanceInput(
            **{**m.__dict__, "external_temperature_c": 5.0}
        )
        after = PhysicalState(**{**after.__dict__, "months": tuple(altered_months)})
        decision = assess_effect_surface(evidence(after=after))
        self.assertEqual(Q, decision.status)
        self.assertTrue(any("CLIMATE_MISMATCH" in r for r in decision.reasons))

    def test_undeclared_physical_change_fails_closed(self):
        decision = assess_effect_surface(
            evidence(changed_parameter_keys=("TRANSMISSION",))
        )
        self.assertEqual(Q, decision.status)
        self.assertTrue(
            any("CHANGED_PARAMETER_KEYS_MISMATCH" in r for r in decision.reasons)
        )

    def test_tabula_domain_is_not_national_prevalence(self):
        bad_domain = EffectSurfaceDomain(
            **{**domain().__dict__, "national_prevalence_claim": True}
        )
        decision = assess_effect_surface(evidence(domain=bad_domain))
        self.assertEqual(Q, decision.status)
        self.assertIn("NATIONAL_PREVALENCE_CLAIM_PROHIBITED", decision.reasons)

    def test_current_monthly_method_is_executable(self):
        result = calculate_state_demand(state())
        self.assertFalse(result.gaps)
        self.assertGreater(result.annual_space_heat_kwh, 0)
        self.assertAlmostEqual(250.0 * 33.0 / 1000.0, result.design_peak_heat_kw)


if __name__ == "__main__":
    unittest.main()
