from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from modules.B11.county_baseline_contract import (
    NATIONAL_HOUSEHOLD_CONSUMERS_2024,
    NATIONAL_HEATING_CONSUMERS_2024,
    load_county_baseline,
    validate_county_baseline,
)


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "registry" / "b11_county_gas_baseline_2024.csv"


class TestB11P2CountyGasBaseline(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = load_county_baseline(CSV_PATH)

    def test_exact_county_population_and_controls(self) -> None:
        result = validate_county_baseline(self.rows)
        self.assertEqual(result.county_count, 20)
        self.assertEqual(result.household_consumers_sum, NATIONAL_HOUSEHOLD_CONSUMERS_2024)
        self.assertEqual(result.heating_consumers_sum, NATIONAL_HEATING_CONSUMERS_2024)
        self.assertEqual(result.household_gas_sold_thousand_m3_sum, 2_654_310)
        self.assertEqual(result.national_gas_rounding_delta_thousand_m3, -1)
        self.assertAlmostEqual(result.derived_monthly_m3_per_household, 68.23, places=2)
        self.assertFalse(result.programme_volume_authorized)

    def test_heating_count_cannot_exceed_household_count(self) -> None:
        first = self.rows[0]
        bad = (replace(first, heating_consumers=first.household_consumers + 1),) + self.rows[1:]
        with self.assertRaises(ValueError):
            validate_county_baseline(bad)

    def test_missing_county_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            validate_county_baseline(self.rows[:-1])

    def test_non_obs_row_cannot_enter_observed_baseline(self) -> None:
        first = self.rows[0]
        bad = (replace(first, evidence_status="SCN"),) + self.rows[1:]
        with self.assertRaises(ValueError):
            validate_county_baseline(bad)


if __name__ == "__main__":
    unittest.main()
