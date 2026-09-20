import unittest

from modules.B06.peak_effect_gate import (
    BLOCKED,
    DER,
    PLANNED_DESIGN,
    Q,
    QUALIFIED,
    PeakEffectEvidence,
    assess_peak_effect,
)


def zalavar(**changes):
    values = dict(
        record_id="HU-ZALAVAR-2015",
        intervention_id="ZALAVAR-ENVELOPE-2015",
        evidence_status=DER,
        post_state_kind=PLANNED_DESIGN,
        before_annual_space_heat_kwh=207172.0,
        after_annual_space_heat_kwh=36687.0,
        before_peak_heat_load_kw=132.35,
        after_peak_heat_load_kw=46.47,
        before_method_id="KESZ-ZBR-EH09-3",
        after_method_id="KESZ-ZBR-EH09-3",
        before_source_refs=("SRC-B06-HU-ZALAVAR-ZBR-PRE-2015",),
        after_source_refs=("SRC-B06-HU-ZALAVAR-ZBR-POST-2015",),
        before_phase_id="PRE_RETROFIT",
        after_phase_id="POST_RETROFIT_PLANNED",
        before_design_indoor_temperature_c=20.0,
        after_design_indoor_temperature_c=20.0,
        before_design_outdoor_temperature_c=-13.0,
        after_design_outdoor_temperature_c=-13.0,
        before_heated_floor_area_m2=1419.63,
        after_heated_floor_area_m2=1419.63,
        before_heated_volume_m3=4174.5,
        after_heated_volume_m3=4174.5,
        intervention_scope_documented=True,
        dhw_separate_from_space_heat=True,
        reproducible_repository_binding=True,
    )
    values.update(changes)
    return PeakEffectEvidence(**values)


class B06P62PeakEffectGateTests(unittest.TestCase):
    def test_zalavar_same_method_pair_qualifies(self):
        decision = assess_peak_effect(zalavar())
        self.assertEqual(QUALIFIED, decision.status)
        self.assertAlmostEqual(
            (207172.0 - 36687.0) / 207172.0,
            decision.annual_reduction_fraction,
        )
        self.assertAlmostEqual(
            (132.35 - 46.47) / 132.35,
            decision.peak_reduction_fraction,
        )

    def test_annual_and_peak_reductions_are_independent(self):
        decision = assess_peak_effect(zalavar())
        self.assertNotEqual(
            decision.annual_reduction_fraction,
            decision.peak_reduction_fraction,
        )

    def test_design_method_must_match(self):
        decision = assess_peak_effect(zalavar(after_method_id="OTHER-METHOD"))
        self.assertEqual(Q, decision.status)
        self.assertIn("METHOD_ID_MISMATCH", decision.reasons)

    def test_design_temperatures_must_match(self):
        decision = assess_peak_effect(
            zalavar(after_design_outdoor_temperature_c=-11.0)
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("DESIGN_OUTDOOR_TEMPERATURE_MISMATCH", decision.reasons)

    def test_annual_to_peak_inference_is_prohibited(self):
        decision = assess_peak_effect(zalavar(annual_to_peak_inference_used=True))
        self.assertEqual(Q, decision.status)
        self.assertIn("ANNUAL_TO_PEAK_INFERENCE_PROHIBITED", decision.reasons)

    def test_intervention_and_dhw_boundaries_are_required(self):
        decision = assess_peak_effect(
            zalavar(
                intervention_scope_documented=False,
                dhw_separate_from_space_heat=False,
            )
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("INTERVENTION_SCOPE_MISSING", decision.reasons)
        self.assertIn("DHW_SPACE_HEAT_BOUNDARY_MISSING", decision.reasons)

    def test_non_reducing_peak_is_blocked(self):
        decision = assess_peak_effect(zalavar(after_peak_heat_load_kw=132.35))
        self.assertEqual(BLOCKED, decision.status)
        self.assertIn("PEAK_REDUCTION_NOT_ACHIEVED", decision.reasons)


if __name__ == "__main__":
    unittest.main()
