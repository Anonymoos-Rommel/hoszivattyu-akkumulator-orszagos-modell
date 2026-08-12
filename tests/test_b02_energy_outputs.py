from __future__ import annotations

import csv
from collections import defaultdict
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b02"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B02EnergyOutputTests(unittest.TestCase):
    def test_manifest_controls_and_hashes(self) -> None:
        manifest = json.loads((DATA / "ksh_energy_extract_manifest.json").read_text("utf-8"))
        controls = manifest["controls"]
        self.assertEqual(7, controls["chart_count"])
        self.assertEqual(16, controls["benchmark_rows"])
        self.assertEqual(944, controls["distribution_rows"])
        self.assertEqual(17, controls["energy_class_rows"])
        self.assertEqual(4_580_538, controls["census_dwelling_universe"])
        self.assertEqual(279_020, controls["linked_energy_certificates"])
        self.assertRegex(manifest["publication"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(manifest["methodology"]["sha256"], r"^[0-9a-f]{64}$")

    def test_archetype_benchmarks_match_ksh_controls(self) -> None:
        rows = read_csv("ksh_energy_archetype_benchmarks_2022.csv")
        self.assertEqual(16, len(rows))
        keyed = {(row["building_type"], row["construction_period"]): row for row in rows}
        self.assertEqual(
            "375", keyed[("FAMILY_HOUSE", "1961–1980")]["mean_primary_energy_kwh_m2_year"]
        )
        self.assertEqual(
            "187",
            keyed[("MULTI_DWELLING", "1961–1980")]["mean_primary_energy_kwh_m2_year"],
        )
        self.assertEqual({"MODELLED"}, {row["evidence_status"] for row in rows})

    def test_published_bin_coverage_reconciles(self) -> None:
        rows = read_csv("ksh_energy_coverage_2022.csv")
        values = {row["metric"]: float(row["value"]) for row in rows}
        self.assertEqual(
            values["census_dwelling_universe"],
            values["all_records_in_published_bins"] + values["published_bin_residual"],
        )
        self.assertEqual(4_748, values["published_bin_residual"])
        self.assertAlmostEqual(0.9989634405390808, values["published_bin_coverage"], places=15)

    def test_distribution_is_complete_rectangular_grid(self) -> None:
        rows = read_csv("ksh_energy_distribution_2022.csv")
        self.assertEqual(944, len(rows))
        self.assertEqual({"FAMILY_HOUSE", "MULTI_DWELLING"}, {row["building_type"] for row in rows})
        self.assertEqual(8, len({row["construction_period"] for row in rows}))
        self.assertEqual(59, len({row["published_energy_bin_kwh_m2_year"] for row in rows}))
        self.assertEqual({"MODELLED"}, {row["evidence_status"] for row in rows})

    def test_distribution_weighted_means_reconcile_to_published_means(self) -> None:
        benchmarks = read_csv("ksh_energy_archetype_benchmarks_2022.csv")
        expected = {
            (row["building_type"], row["construction_period"]): float(
                row["mean_primary_energy_kwh_m2_year"]
            )
            for row in benchmarks
        }
        weighted: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0.0, 0.0])
        for row in read_csv("ksh_energy_distribution_2022.csv"):
            key = (row["building_type"], row["construction_period"])
            count = float(row["dwelling_count"])
            weighted[key][0] += float(row["published_energy_bin_kwh_m2_year"]) * count
            weighted[key][1] += count
        for key, (weighted_sum, count) in weighted.items():
            self.assertLessEqual(abs(weighted_sum / count - expected[key]), 1.1, key)


if __name__ == "__main__":
    unittest.main()
