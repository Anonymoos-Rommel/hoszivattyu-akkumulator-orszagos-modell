import unittest

from modules.B06.baseline_demand_gate import (
    DER,
    DIRECT_ANNUAL,
    DIRECT_PEAK,
    BaselineDemandEvidence,
)
from modules.B06.effect_surface import (
    EffectSurfaceDomain,
    EffectSurfaceEvidence,
    MonthlyHeatBalanceInput,
    PhysicalState,
    assess_effect_surface,
    calculate_state_demand,
)
from modules.B06.engine import (
    EvidenceValue,
    RetrofitBaseline,
    RetrofitIntervention,
    evaluate_retrofit,
)
from modules.B06.peak_effect_gate import PeakEffectEvidence, PLANNED_DESIGN


MONTH_T = (2.1, -0.1, 3.5, 10.9, 16.8, 20.8, 21.9, 21.0, 17.8, 8.3, 7.6, -0.1)
MONTH_H = (744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744)


def state(state_id, direct_h, vent_h, design_h, *, record_id="P63-REC"):
    return PhysicalState(
        record_id=record_id,
        building_type="SINGLE_FAMILY_HOUSE",
        construction_period="1945-1979",
        state_id=state_id,
        climate_id="HU-REF",
        heated_floor_area_m2=120.0,
        heated_volume_m3=330.0,
        indoor_temperature_c=20.0,
        design_outdoor_temperature_c=-13.0,
        design_total_h_w_per_k=design_h,
        months=tuple(
            MonthlyHeatBalanceInput(
                month=i + 1,
                hours=MONTH_H[i],
                external_temperature_c=MONTH_T[i],
                annual_external_temperature_c=10.9,
                direct_unconditioned_h_w_per_k=direct_h,
                ground_h_w_per_k=20.0,
                ventilation_h_w_per_k=vent_h,
                solar_gain_kwh=100.0,
                internal_gain_kwh=160.0,
                gain_utilization_factor=0.8,
                intermittent_operation_factor=1.0,
            )
            for i in range(12)
        ),
        source_refs=("SRC-B06-HU-ENERGY-METHOD-2023",),
        evidence_status=DER,
    )


def domain(before_states=("EXISTING", "WALL_DONE"), after_states=("WALL_DONE", "FINAL")):
    return EffectSurfaceDomain(
        domain_id="P63-TEST-DOMAIN",
        allowed_building_types=("SINGLE_FAMILY_HOUSE",),
        allowed_construction_periods=("1945-1979",),
        allowed_before_states=before_states,
        allowed_after_states=after_states,
        source_refs=("SRC-B06-HU-TABULA-TYPOLOGY-2014",),
        national_prevalence_claim=False,
    )


def surface(intervention_id, before, after, keys):
    return EffectSurfaceEvidence(
        intervention_id=intervention_id,
        before=before,
        after=after,
        domain=domain(),
        changed_parameter_keys=keys,
        applicability_source_refs=("SRC-B06-HU-TABULA-TYPOLOGY-2014",),
        reproducible_repository_binding=True,
    )


def baseline(before):
    demand = calculate_state_demand(before)
    assert demand.annual_space_heat_kwh is not None
    assert demand.design_peak_heat_kw is not None
    pair = BaselineDemandEvidence(
        record_id=before.record_id,
        phase_id="PRE_RETROFIT",
        annual_space_heat_kwh=demand.annual_space_heat_kwh,
        annual_evidence_status=DER,
        annual_method=DIRECT_ANNUAL,
        annual_source_refs=("P63-ANNUAL",),
        peak_heat_load_kw=demand.design_peak_heat_kw,
        peak_evidence_status=DER,
        peak_method=DIRECT_PEAK,
        peak_source_refs=("P63-PEAK",),
        annual_record_link=before.record_id,
        peak_record_link=before.record_id,
        annual_phase_link="PRE_RETROFIT",
        peak_phase_link="PRE_RETROFIT",
        reproducible_repository_binding=True,
    )
    return RetrofitBaseline(
        archetype_id=EvidenceValue(before.record_id, DER),
        baseline_annual_space_heat_kwh=EvidenceValue(demand.annual_space_heat_kwh, DER),
        baseline_peak_heat_load_kw=EvidenceValue(demand.design_peak_heat_kw, DER),
        baseline_demand_evidence=pair,
    )


def intervention_from_surface(intervention_id, evidence):
    decision = assess_effect_surface(evidence)
    assert decision.status == "QUALIFIED"
    return RetrofitIntervention(
        intervention_id,
        "envelope",
        decision.annual_reduction_fraction,
        decision.peak_reduction_fraction,
        evidence_status=DER,
        applicability_status=DER,
        effect_surface_evidence=evidence,
    )


class B06P63EngineIntegrationTests(unittest.TestCase):
    def test_exact_p63_surface_can_supply_real_der_intervention_effect(self):
        before = state("EXISTING", 180.0, 55.0, 250.0)
        after = state("FINAL", 110.0, 45.0, 170.0)
        ev = surface(
            "P63-PACKAGE",
            before,
            after,
            ("TRANSMISSION", "VENTILATION"),
        )
        result = evaluate_retrofit(
            baseline(before),
            [intervention_from_surface("P63-PACKAGE", ev)],
        )
        target = calculate_state_demand(after)
        self.assertEqual(DER, result.status)
        self.assertAlmostEqual(
            target.annual_space_heat_kwh,
            result.post_retrofit_annual_space_heat_kwh,
            places=8,
        )
        self.assertAlmostEqual(
            target.design_peak_heat_kw,
            result.post_retrofit_peak_heat_load_kw,
            places=10,
        )
        self.assertEqual("S1_CANDIDATE", result.post_state_candidate)

    def test_real_der_effect_without_p62_or_p63_authority_is_q(self):
        before = state("EXISTING", 180.0, 55.0, 250.0)
        result = evaluate_retrofit(
            baseline(before),
            [
                RetrofitIntervention(
                    "UNBOUND",
                    "envelope",
                    0.2,
                    0.1,
                    evidence_status=DER,
                    applicability_status=DER,
                )
            ],
        )
        self.assertEqual("Q", result.status)
        self.assertTrue(
            any("P62 linked pair or P63 physical surface" in g for g in result.remaining_readiness_gaps)
        )

    def test_p62_and_p63_authorities_together_are_rejected(self):
        before = state("EXISTING", 180.0, 55.0, 250.0)
        after = state("FINAL", 110.0, 45.0, 170.0)
        ev = surface("MULTI", before, after, ("TRANSMISSION", "VENTILATION"))
        decision = assess_effect_surface(ev)
        p62 = PeakEffectEvidence(
            record_id="P63-REC",
            intervention_id="MULTI",
            evidence_status=DER,
            post_state_kind=PLANNED_DESIGN,
            before_annual_space_heat_kwh=100.0,
            after_annual_space_heat_kwh=80.0,
            before_peak_heat_load_kw=10.0,
            after_peak_heat_load_kw=8.0,
            before_method_id="X",
            after_method_id="X",
            before_source_refs=("A",),
            after_source_refs=("B",),
            before_phase_id="PRE",
            after_phase_id="POST",
            before_design_indoor_temperature_c=20.0,
            after_design_indoor_temperature_c=20.0,
            before_design_outdoor_temperature_c=-13.0,
            after_design_outdoor_temperature_c=-13.0,
            intervention_scope_documented=True,
            dhw_separate_from_space_heat=True,
            reproducible_repository_binding=True,
        )
        intervention = RetrofitIntervention(
            "MULTI",
            "envelope",
            decision.annual_reduction_fraction,
            decision.peak_reduction_fraction,
            evidence_status=DER,
            applicability_status=DER,
            peak_effect_evidence=p62,
            effect_surface_evidence=ev,
        )
        result = evaluate_retrofit(baseline(before), [intervention])
        self.assertEqual("Q", result.status)
        self.assertTrue(any("MULTIPLE_EFFECT_AUTHORITIES" in g for g in result.remaining_readiness_gaps))

    def test_overlapping_surface_keys_are_rejected(self):
        s0 = state("EXISTING", 180.0, 55.0, 250.0)
        s1 = state("WALL_DONE", 140.0, 55.0, 210.0)
        s2 = state("FINAL", 110.0, 45.0, 170.0)
        first = surface("WALL", s0, s1, ("TRANSMISSION",))
        second = surface("WINDOW_AND_AIR", s1, s2, ("TRANSMISSION", "VENTILATION"))
        result = evaluate_retrofit(
            baseline(s0),
            [
                intervention_from_surface("WALL", first),
                intervention_from_surface("WINDOW_AND_AIR", second),
            ],
        )
        self.assertEqual("Q", result.status)
        self.assertTrue(
            any("overlapping physical effect keys" in g for g in result.remaining_readiness_gaps)
        )

    def test_nonoverlapping_sequential_surface_starts_from_current_state(self):
        s0 = state("EXISTING", 180.0, 55.0, 250.0)
        s1 = state("WALL_DONE", 140.0, 55.0, 210.0)
        s2 = state("FINAL", 140.0, 40.0, 190.0)
        first = surface("WALL", s0, s1, ("TRANSMISSION",))
        second = surface("VENT", s1, s2, ("VENTILATION",))
        result = evaluate_retrofit(
            baseline(s0),
            [
                intervention_from_surface("WALL", first),
                intervention_from_surface("VENT", second),
            ],
        )
        target = calculate_state_demand(s2)
        self.assertEqual(DER, result.status)
        self.assertAlmostEqual(
            target.annual_space_heat_kwh,
            result.post_retrofit_annual_space_heat_kwh,
            places=8,
        )
        self.assertAlmostEqual(
            target.design_peak_heat_kw,
            result.post_retrofit_peak_heat_load_kw,
            places=10,
        )

    def test_surface_from_wrong_before_state_is_rejected_in_sequence(self):
        s0 = state("EXISTING", 180.0, 55.0, 250.0)
        s1 = state("WALL_DONE", 140.0, 55.0, 210.0)
        wrong_before = state("WALL_DONE", 150.0, 55.0, 220.0)
        s2 = state("FINAL", 150.0, 40.0, 195.0)
        first = surface("WALL", s0, s1, ("TRANSMISSION",))
        second = surface("VENT", wrong_before, s2, ("VENTILATION",))
        result = evaluate_retrofit(
            baseline(s0),
            [
                intervention_from_surface("WALL", first),
                intervention_from_surface("VENT", second),
            ],
        )
        self.assertEqual("Q", result.status)
        self.assertTrue(
            any("current sequential state" in g for g in result.remaining_readiness_gaps)
        )


if __name__ == "__main__":
    unittest.main()
