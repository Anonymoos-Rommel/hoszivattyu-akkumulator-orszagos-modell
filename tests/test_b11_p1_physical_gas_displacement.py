import unittest

from modules.B11.physical_displacement_contract import (
    EvidenceStatus,
    EvidenceValue,
    GasDisplacementInputs,
    calculate_physical_gas_displacement,
)


class B11P1PhysicalGasDisplacementTests(unittest.TestCase):
    def test_explicit_physical_balance(self):
        result = calculate_physical_gas_displacement(
            GasDisplacementInputs(
                baseline_gas_m3=EvidenceValue(1200.0, "m3/year", EvidenceStatus.SCN, "fixture"),
                replaceable_end_use_fraction=EvidenceValue(0.8, "fraction", EvidenceStatus.SCN, "fixture"),
                retrofit_reduction_fraction=EvidenceValue(0.25, "fraction", EvidenceStatus.SCN, "fixture"),
                rebound_fraction=EvidenceValue(0.1, "fraction", EvidenceStatus.SCN, "fixture"),
            )
        )
        self.assertAlmostEqual(result.post_retrofit_gas_m3, 900.0)
        self.assertAlmostEqual(result.displaced_gas_m3, 648.0)
        self.assertAlmostEqual(result.remaining_gas_m3, 252.0)
        self.assertAlmostEqual(
            result.displaced_gas_m3 + result.remaining_gas_m3,
            result.post_retrofit_gas_m3,
        )
        self.assertEqual(result.output_status, EvidenceStatus.SCN)

    def test_q_is_not_zero(self):
        with self.assertRaisesRegex(ValueError, "Q evidence"):
            calculate_physical_gas_displacement(
                GasDisplacementInputs(
                    baseline_gas_m3=EvidenceValue(1200.0, "m3/year", EvidenceStatus.OBS, "fixture"),
                    replaceable_end_use_fraction=EvidenceValue(None, "fraction", EvidenceStatus.Q, None),
                    retrofit_reduction_fraction=EvidenceValue(0.0, "fraction", EvidenceStatus.SCN, "fixture"),
                    rebound_fraction=EvidenceValue(0.0, "fraction", EvidenceStatus.SCN, "fixture"),
                )
            )

    def test_missing_numeric_is_not_zero(self):
        with self.assertRaisesRegex(ValueError, "missing/non-finite"):
            calculate_physical_gas_displacement(
                GasDisplacementInputs(
                    baseline_gas_m3=EvidenceValue(None, "m3/year", EvidenceStatus.OBS, "fixture"),
                    replaceable_end_use_fraction=EvidenceValue(0.8, "fraction", EvidenceStatus.SCN, "fixture"),
                    retrofit_reduction_fraction=EvidenceValue(0.0, "fraction", EvidenceStatus.SCN, "fixture"),
                    rebound_fraction=EvidenceValue(0.0, "fraction", EvidenceStatus.SCN, "fixture"),
                )
            )

    def test_fraction_bounds_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "within \\[0, 1\\]"):
            calculate_physical_gas_displacement(
                GasDisplacementInputs(
                    baseline_gas_m3=EvidenceValue(1200.0, "m3/year", EvidenceStatus.SCN, "fixture"),
                    replaceable_end_use_fraction=EvidenceValue(1.2, "fraction", EvidenceStatus.SCN, "fixture"),
                    retrofit_reduction_fraction=EvidenceValue(0.0, "fraction", EvidenceStatus.SCN, "fixture"),
                    rebound_fraction=EvidenceValue(0.0, "fraction", EvidenceStatus.SCN, "fixture"),
                )
            )

    def test_observed_baseline_does_not_promote_scenario_assumptions(self):
        result = calculate_physical_gas_displacement(
            GasDisplacementInputs(
                baseline_gas_m3=EvidenceValue(1000.0, "m3/year", EvidenceStatus.OBS, "source"),
                replaceable_end_use_fraction=EvidenceValue(0.7, "fraction", EvidenceStatus.SCN, "fixture"),
                retrofit_reduction_fraction=EvidenceValue(0.1, "fraction", EvidenceStatus.DER, "method"),
                rebound_fraction=EvidenceValue(0.05, "fraction", EvidenceStatus.SCN, "fixture"),
            )
        )
        self.assertEqual(result.output_status, EvidenceStatus.SCN)


if __name__ == "__main__":
    unittest.main()
