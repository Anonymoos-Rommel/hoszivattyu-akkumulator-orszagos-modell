import unittest

from modules.B05.s2125_passive_defrost_branch import (
    EXPECTED_PASSIVE_MEDIAN_DURATION_S,
    EXPECTED_PASSIVE_STATE_RUNS,
    EXPECTED_PASSIVE_STATE_SAMPLES,
    PINNED_ARCHIVE_SHA256,
    PINNED_NIBE_MEMBER_SHA256,
    PINNED_VICTRON_MEMBER_SHA256,
    PassiveElectricMatchAdmission,
    can_admit_passive_penalty_constant,
    passive_signed_thermal_der_admitted,
    p52_boundaries,
    raw_identity_admitted,
)


class B05P52S2125PassiveDefrostBranchTests(unittest.TestCase):
    def test_p49_passive_identity_is_pinned(self):
        self.assertEqual(102, EXPECTED_PASSIVE_STATE_SAMPLES)
        self.assertEqual(22, EXPECTED_PASSIVE_STATE_RUNS)
        self.assertEqual(180.5, EXPECTED_PASSIVE_MEDIAN_DURATION_S)
        self.assertTrue(
            raw_identity_admitted(
                PINNED_ARCHIVE_SHA256,
                PINNED_NIBE_MEMBER_SHA256,
                PINNED_VICTRON_MEMBER_SHA256,
            )
        )
        self.assertFalse(
            raw_identity_admitted(
                "0" * 64,
                PINNED_NIBE_MEMBER_SHA256,
                PINNED_VICTRON_MEMBER_SHA256,
            )
        )

    def test_passive_electric_match_is_fail_closed(self):
        good = PassiveElectricMatchAdmission(
            mode="HEAT",
            n_controls=3,
            electrical_coverage_fraction=0.98,
            control_has_nonzero_defrost=False,
            stable_control_mode=True,
            event_is_direct_passive_state=True,
        )
        self.assertTrue(good.admitted())
        self.assertFalse(
            PassiveElectricMatchAdmission(
                mode="HEAT",
                n_controls=2,
                electrical_coverage_fraction=1.0,
                control_has_nonzero_defrost=False,
                stable_control_mode=True,
                event_is_direct_passive_state=True,
            ).admitted()
        )
        self.assertFalse(
            PassiveElectricMatchAdmission(
                mode="TRANSITION",
                n_controls=5,
                electrical_coverage_fraction=1.0,
                control_has_nonzero_defrost=False,
                stable_control_mode=True,
                event_is_direct_passive_state=True,
            ).admitted()
        )

    def test_p50_thermal_factor_is_not_auto_transferred(self):
        self.assertFalse(
            passive_signed_thermal_der_admitted(
                p50_factor_domain_validated_for_passive=False,
                flow_and_temperatures_qualified=True,
            )
        )
        self.assertFalse(
            passive_signed_thermal_der_admitted(
                p50_factor_domain_validated_for_passive=True,
                flow_and_temperatures_qualified=False,
            )
        )
        self.assertTrue(
            passive_signed_thermal_der_admitted(
                p50_factor_domain_validated_for_passive=True,
                flow_and_temperatures_qualified=True,
            )
        )

    def test_no_universal_passive_penalty_is_admitted(self):
        self.assertFalse(can_admit_passive_penalty_constant())
        boundaries = p52_boundaries()
        self.assertIn(
            "PASSIVE_DEFROST != ACTIVE_REVERSE_CYCLE_DEFROST",
            boundaries,
        )
        self.assertIn(
            "P50_SIGNED_THERMAL_FACTOR != PASSIVE_THERMAL_DER_WITHOUT_DOMAIN_VALIDATION",
            boundaries,
        )
        self.assertIn("NO_MECHANICAL_READINESS_UPLIFT", boundaries)


if __name__ == "__main__":
    unittest.main()
