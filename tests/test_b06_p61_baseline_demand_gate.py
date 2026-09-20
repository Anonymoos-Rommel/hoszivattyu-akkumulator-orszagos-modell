import unittest

from modules.B06.baseline_demand_gate import (
    DER,
    DIRECT_PEAK,
    PHYSICAL_DESIGN_DERIVATION,
    Q,
    QUALIFIED,
    SPECIFIC_TIMES_AREA,
    BaselineDemandEvidence,
    assess_baseline_demand,
)


def zalavar_candidate(**changes):
    values = dict(
        record_id="HU-ZALAVAR-2015",
        phase_id="PRE_RETROFIT",
        annual_space_heat_kwh=207119.64,
        annual_evidence_status=DER,
        annual_method=SPECIFIC_TIMES_AREA,
        annual_source_refs=("SRC-B06-HU-ZALAVAR-HET-ZBR-2015",),
        peak_heat_load_kw=132.35,
        peak_evidence_status=DER,
        peak_method=DIRECT_PEAK,
        peak_source_refs=("SRC-B06-HU-ZALAVAR-HET-ZBR-2015",),
        heated_floor_area_m2=1419.6,
        specific_annual_space_heat_kwh_m2a=145.9,
        design_indoor_temperature_c=20.0,
        design_outdoor_temperature_c=-13.0,
        annual_record_link="HU-ZALAVAR-2015",
        peak_record_link="HU-ZALAVAR-2015",
        annual_phase_link="PRE_RETROFIT",
        peak_phase_link="PRE_RETROFIT",
        reproducible_repository_binding=True,
    )
    values.update(changes)
    return BaselineDemandEvidence(**values)


class B06P61BaselineDemandGateTests(unittest.TestCase):
    def test_exact_same_record_same_phase_pair_qualifies(self):
        decision = assess_baseline_demand(zalavar_candidate())
        self.assertEqual(QUALIFIED, decision.status)
        self.assertEqual((), decision.reasons)

    def test_annual_and_peak_must_share_record(self):
        decision = assess_baseline_demand(
            zalavar_candidate(peak_record_link="OTHER-BUILDING")
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("PEAK_RECORD_LINK_MISMATCH", decision.reasons)

    def test_annual_and_peak_must_share_phase(self):
        decision = assess_baseline_demand(
            zalavar_candidate(peak_phase_link="POST_RETROFIT")
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("PEAK_PHASE_LINK_MISMATCH", decision.reasons)

    def test_specific_times_area_is_recomputed_exactly(self):
        decision = assess_baseline_demand(
            zalavar_candidate(annual_space_heat_kwh=207000.0)
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("ANNUAL_DERIVATION_MISMATCH", decision.reasons)

    def test_annual_to_peak_inference_is_prohibited(self):
        decision = assess_baseline_demand(
            zalavar_candidate(annual_to_peak_inference_used=True)
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("ANNUAL_TO_PEAK_INFERENCE_PROHIBITED", decision.reasons)

    def test_installed_capacity_is_not_design_peak(self):
        decision = assess_baseline_demand(
            zalavar_candidate(installed_capacity_used_as_peak=True)
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("INSTALLED_CAPACITY_AS_PEAK_PROHIBITED", decision.reasons)

    def test_full_load_hours_proxy_is_not_design_peak(self):
        decision = assess_baseline_demand(
            zalavar_candidate(full_load_hours_proxy_used=True)
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("FULL_LOAD_HOURS_PROXY_PROHIBITED", decision.reasons)

    def test_physical_peak_derivation_requires_design_temperatures(self):
        decision = assess_baseline_demand(
            zalavar_candidate(
                peak_method=PHYSICAL_DESIGN_DERIVATION,
                design_outdoor_temperature_c=None,
            )
        )
        self.assertEqual(Q, decision.status)
        self.assertIn("DESIGN_OUTDOOR_TEMPERATURE_MISSING", decision.reasons)


if __name__ == "__main__":
    unittest.main()
