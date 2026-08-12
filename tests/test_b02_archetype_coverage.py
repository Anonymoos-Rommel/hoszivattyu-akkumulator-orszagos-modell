from __future__ import annotations

import csv
from decimal import Decimal
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b02"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B02ArchetypeCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.coverage = read_csv("b02_archetype_cell_coverage_2022.csv")
        cls.joinability = read_csv("b02_archetype_joinability_2022.csv")
        cls.manifest = json.loads(
            (DATA / "b02_archetype_coverage_manifest.json").read_text(
                encoding="utf-8"
            )
        )

    def test_energy_cells_reconcile_without_new_observation_status(self) -> None:
        self.assertEqual(16, len(self.coverage))
        self.assertEqual(
            4_575_790,
            sum(int(row["modelled_dwelling_count"]) for row in self.coverage),
        )
        self.assertEqual({"DER"}, {row["evidence_status"] for row in self.coverage})
        self.assertEqual(
            {"MODELLED"}, {row["source_evidence_status"] for row in self.coverage}
        )
        shares = sum(
            Decimal(row["modelled_dwelling_share"]) for row in self.coverage
        )
        self.assertLess(abs(shares - Decimal(1)), Decimal("0.00000000000001"))

    def test_rank_and_cumulative_share_are_count_ordered(self) -> None:
        ranked = sorted(
            self.coverage, key=lambda row: int(row["dwelling_count_rank_desc"])
        )
        counts = [int(row["modelled_dwelling_count"]) for row in ranked]
        cumulative = [
            Decimal(row["cumulative_modelled_dwelling_share_desc"])
            for row in ranked
        ]
        self.assertEqual(sorted(counts, reverse=True), counts)
        self.assertEqual(list(range(1, 17)), [int(row["dwelling_count_rank_desc"]) for row in ranked])
        self.assertEqual(sorted(cumulative), cumulative)
        self.assertEqual(Decimal("1.000000000000000"), cumulative[-1])

    def test_energy_bin_sparsity_is_exact_not_threshold_labelled(self) -> None:
        self.assertEqual(
            944,
            sum(int(row["published_energy_bin_count"]) for row in self.coverage),
        )
        self.assertEqual(
            864,
            sum(int(row["positive_energy_bin_count"]) for row in self.coverage),
        )
        self.assertEqual(
            80,
            sum(int(row["zero_energy_bin_count"]) for row in self.coverage),
        )

    def test_full_joint_fails_closed(self) -> None:
        by_id = {row["join_id"]: row for row in self.joinability}
        full = by_id["JOIN-B02-FULL-ARCHETYPE"]
        self.assertEqual("Q", full["evidence_status"])
        self.assertEqual("NOT_IDENTIFIED", full["materialization_status"])
        self.assertIn("Cross-multiplying", full["prohibited_inference"])
        self.assertEqual(
            "MODELLED", by_id["JOIN-B02-KSH-ENERGY"]["evidence_status"]
        )
        self.assertEqual(
            "ASS", by_id["JOIN-B02-BUILDING-TYPE-PROXY"]["evidence_status"]
        )
        self.assertEqual(
            "Q", by_id["JOIN-B02-OENY-EMITTER"]["evidence_status"]
        )

    def test_manifest_controls_and_hashes(self) -> None:
        controls = self.manifest["controls"]
        self.assertEqual(16, controls["benchmark_cells"])
        self.assertEqual(944, controls["distribution_bins"])
        self.assertEqual(864, controls["positive_distribution_bins"])
        self.assertEqual(80, controls["zero_distribution_bins"])
        self.assertEqual(22_145, controls["smallest_benchmark_cell_dwellings"])
        self.assertEqual(902_651, controls["largest_benchmark_cell_dwellings"])
        self.assertEqual("Q", controls["full_joint_evidence_status"])
        for name, metadata in self.manifest["inputs"].items():
            self.assertEqual(
                metadata["sha256"], hashlib.sha256((DATA / name).read_bytes()).hexdigest()
            )
        for name, metadata in self.manifest["outputs"].items():
            self.assertEqual(
                metadata["sha256"], hashlib.sha256((DATA / name).read_bytes()).hexdigest()
            )

    def test_source_pack_rejects_independence_cross_product(self) -> None:
        text = (
            ROOT
            / "docs"
            / "source_packs"
            / "P1G_B02_ARCHETYPE_COVERAGE_AND_JOINABILITY.md"
        ).read_text(encoding="utf-8")
        self.assertIn("nem áll rendelkezésre teljes közös eloszlás", text)
        self.assertIn("keresztbeszorzása tilos", text)
        self.assertIn("nincs új technikailag alkalmas lakásszám", text)


if __name__ == "__main__":
    unittest.main()
