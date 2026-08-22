from __future__ import annotations

import csv
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def rows(name: str) -> list[dict[str, str]]:
    with (PROCESSED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B03GasPriceEngineTests(unittest.TestCase):
    def test_wholesale_conversion_is_dimensionally_explicit(self) -> None:
        # EUR/MWh -> HUF/m3: multiply by MWh per m3 (MJ/m3 / 3600).
        eur_per_mwh = 50.0
        eur_huf = 360.0
        heating_value_mj_per_m3 = 36.0
        self.assertAlmostEqual(
            eur_per_mwh * eur_huf * (heating_value_mj_per_m3 / 3600.0),
            180.0,
        )

    def test_retail_and_wholesale_layers_never_share_final_value(self) -> None:
        bridge = rows("gas_price_component_bridge.csv")
        layers = {row["layer"] for row in bridge}
        self.assertEqual(
            {"WHOLESALE_IMPORT", "MARKET_RESIDENTIAL_FINAL", "REGULATED_RESIDENTIAL_TARIFF"},
            layers,
        )
        for row in bridge:
            self.assertEqual("", row["final_huf_per_m3"])
            self.assertEqual("Q", row["status"])

    def test_missing_component_fails_closed(self) -> None:
        bridge = rows("gas_price_component_bridge.csv")
        market = next(row for row in bridge if row["layer"] == "MARKET_RESIDENTIAL_FINAL")
        components = (
            "commodity_huf_per_m3",
            "network_huf_per_m3",
            "storage_huf_per_m3",
            "commercial_huf_per_m3",
            "tax_huf_per_m3",
            "vat_huf_per_m3",
            "other_huf_per_m3",
        )
        self.assertTrue(any(not market[field].strip() for field in components))
        self.assertEqual("Q", market["status"])
        self.assertEqual("", market["final_huf_per_m3"])

    def test_regulated_schedule_uses_mj_threshold_and_explicit_tariffs(self) -> None:
        tariff = rows("residential_gas_tariff_schedule.csv")
        self.assertEqual(
            {"DISCOUNTED_BAND", "ABOVE_THRESHOLD_BAND"},
            {r["tariff_band"] for r in tariff},
        )
        for row in tariff:
            self.assertEqual("1729", row["threshold_m3_reference"])
            self.assertEqual("63645", row["threshold_mj"])
            self.assertEqual("OBS", row["price_status"])
            self.assertEqual("OBS", row["status"])
            self.assertEqual("DER", row["illustrative_status"])
            self.assertEqual("34.87", row["reference_heating_value_mj_per_m3"])
        self.assertEqual("2.86512", next(r for r in tariff if r["tariff_band"] == "DISCOUNTED_BAND")["gross_price_huf_per_mj"])
        self.assertEqual("22.002", next(r for r in tariff if r["tariff_band"] == "ABOVE_THRESHOLD_BAND")["gross_price_huf_per_mj"])

    def test_regulated_bill_bands_are_mj_based_and_boundary_safe(self) -> None:
        tariff = rows("residential_gas_tariff_schedule.csv")
        discounted = next(r for r in tariff if r["tariff_band"] == "DISCOUNTED_BAND")
        higher = next(r for r in tariff if r["tariff_band"] == "ABOVE_THRESHOLD_BAND")
        threshold = Decimal(discounted["threshold_mj"])
        discounted_rate = Decimal(discounted["gross_price_huf_per_mj"])
        higher_rate = Decimal(higher["gross_price_huf_per_mj"])
        fixed = Decimal(discounted["annual_fixed_charge_huf"])

        def bill(consumption_mj: Decimal) -> Decimal:
            return (
                min(consumption_mj, threshold) * discounted_rate
                + max(consumption_mj - threshold, Decimal("0")) * higher_rate
                + fixed
            )

        self.assertEqual(bill(threshold - 1) - fixed, (threshold - 1) * discounted_rate)
        self.assertEqual(bill(threshold) - fixed, threshold * discounted_rate)
        self.assertEqual(bill(threshold + 1) - bill(threshold), higher_rate)

    def test_reference_m3_is_not_canonical_and_m3_is_derived(self) -> None:
        tariff = rows("residential_gas_tariff_schedule.csv")
        for row in tariff:
            self.assertEqual("OBS", row["price_status"])
            self.assertEqual("DER", row["illustrative_status"])
            self.assertTrue(row["threshold_m3_reference"])
            self.assertEqual("63645", row["threshold_mj"])

    def test_scenario_forward_to_long_run_transition_is_explicit(self) -> None:
        scenario_rows = rows("gas_price_scenarios.csv")
        self.assertEqual(
            {"GAS-LOW", "GAS-BASE", "GAS-HIGH", "GAS-STRESS"},
            {row["scenario"] for row in scenario_rows},
        )
        for scenario in {row["scenario"] for row in scenario_rows}:
            scoped = [row for row in scenario_rows if row["scenario"] == scenario]
            self.assertEqual({"FORWARD", "LONG_RUN"}, {row["zone"] for row in scoped})
            self.assertLess(
                min(int(row["year"]) for row in scoped),
                max(int(row["year"]) for row in scoped),
            )
            self.assertTrue(all(row["status"] == "SCN" for row in scoped))

    def test_mnb_observations_are_fx_only(self) -> None:
        history = rows("gas_price_history.csv")
        fx = [row for row in history if row["layer"] == "FX"]
        self.assertGreaterEqual(len(fx), 2)
        for row in fx:
            self.assertEqual("OBS", row["status"])
            self.assertTrue(row["eur_huf"].strip())
            self.assertEqual("", row["huf_per_m3"])


if __name__ == "__main__":
    unittest.main()
